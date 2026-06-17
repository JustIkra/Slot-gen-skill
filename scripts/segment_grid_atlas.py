#!/usr/bin/env python3
"""
segment_grid_atlas.py — slice a labelled grid atlas into one PNG per part.

Companion to atlas_prompts.build_atlas_prompt(): we asked Gemini for a uniform
grid of named parts, so we already know:
  * how many columns we asked for,
  * the order of parts (row-major top-left),
  * that each part lives inside one grid cell, with a label printed below it.

Instead of relying on connected-components (which over-splits cuffs / eyes /
labels), this script just walks the grid, masks out the background, and keeps
the largest blob per cell — saved under the canonical part name.

Usage:
    python3 segment_grid_atlas.py atlas.png \\
        --parts head torso kilt left_upper_arm ... \\
        --grid-cols 4 \\
        --output-dir parts/ \\
        [--label-strip 0.18] [--min-area 800] [--padding 8]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np


def _bg_color(rgb: np.ndarray) -> tuple[int, int, int]:
    """Estimate background color from the four corner pixels (median)."""
    h, w = rgb.shape[:2]
    samples = np.stack([
        rgb[0, 0], rgb[0, w - 1], rgb[h - 1, 0], rgb[h - 1, w - 1]
    ]).astype(int)
    return tuple(np.median(samples, axis=0).astype(int).tolist())


def _foreground_mask(rgb: np.ndarray, bg_rgb: tuple[int, int, int],
                      tol: int = 28) -> np.ndarray:
    diff = np.linalg.norm(rgb.astype(int) - np.array(bg_rgb), axis=2)
    return (diff > tol).astype(np.uint8) * 255


def _largest_blob(mask: np.ndarray, min_area: int) -> np.ndarray | None:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    best_id = -1
    best_area = 0
    for label_id in range(1, num_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area > best_area and area >= min_area:
            best_area = area
            best_id = label_id
    if best_id < 0:
        return None
    return (labels == best_id).astype(np.uint8) * 255


def _trim_alpha(rgba: np.ndarray, padding: int) -> np.ndarray:
    alpha = rgba[:, :, 3]
    coords = cv2.findNonZero(alpha)
    if coords is None:
        return rgba
    x, y, w, h = cv2.boundingRect(coords)
    H, W = rgba.shape[:2]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(W, x + w + padding)
    y2 = min(H, y + h + padding)
    return rgba[y1:y2, x1:x2].copy()


def segment_grid(
    atlas_path: str,
    parts: list[str],
    output_dir: str,
    *,
    grid_cols: int,
    label_strip_frac: float = 0.18,
    min_area: int = 800,
    padding: int = 8,
    bg_tolerance: int = 28,
    inner_margin_frac: float = 0.04,
) -> dict[str, str]:
    """Slice *atlas_path* into one PNG per requested part. Returns label→path."""

    img = cv2.imread(atlas_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"could not read atlas: {atlas_path}")
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    bgra = img
    rgb = cv2.cvtColor(bgra[:, :, :3], cv2.COLOR_BGR2RGB)

    h, w = bgra.shape[:2]
    rows = math.ceil(len(parts) / grid_cols)
    cell_w = w // grid_cols
    cell_h = h // rows
    print(f"  atlas: {w}x{h}, grid {grid_cols}x{rows}, cell {cell_w}x{cell_h}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}

    inner_dx = int(cell_w * inner_margin_frac)
    inner_dy = int(cell_h * inner_margin_frac)

    for idx, name in enumerate(parts):
        if name in ("_skip_", "_", "-"):
            continue
        row = idx // grid_cols
        col = idx % grid_cols
        x0 = col * cell_w + inner_dx
        y0 = row * cell_h + inner_dy
        x1 = (col + 1) * cell_w - inner_dx
        y1 = (row + 1) * cell_h - inner_dy
        # Drop the bottom strip where the label lives.
        y1_content = y0 + int((y1 - y0) * (1.0 - label_strip_frac))

        cell_rgb = rgb[y0:y1_content, x0:x1]
        cell_bgra = bgra[y0:y1_content, x0:x1].copy()
        if cell_rgb.size == 0:
            print(f"  [{name}] empty cell, skipping")
            continue

        cell_bg = _bg_color(cell_rgb)
        mask = _foreground_mask(cell_rgb, cell_bg, tol=bg_tolerance)
        blob = _largest_blob(mask, min_area=min_area)
        if blob is None:
            print(f"  [{name}] no blob above min_area={min_area}, skipping")
            continue

        cell_bgra[:, :, 3] = blob
        trimmed = _trim_alpha(cell_bgra, padding=padding)
        out_path = Path(output_dir) / f"{name}.png"
        cv2.imwrite(str(out_path), trimmed)
        out[name] = str(out_path)
        ph, pw = trimmed.shape[:2]
        print(f"  [{name:>18}] {pw}x{ph} → {out_path.name}")

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("atlas")
    parser.add_argument("--parts", nargs="+", required=True,
                        help="Part labels in row-major order (left-to-right, top-to-bottom)")
    parser.add_argument("--grid-cols", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--label-strip", type=float, default=0.18,
                        help="Bottom fraction of each cell that contains the label text")
    parser.add_argument("--min-area", type=int, default=800)
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument("--bg-tolerance", type=int, default=28,
                        help="How far an RGB pixel can be from background colour and still count as background")
    args = parser.parse_args()

    out = segment_grid(
        args.atlas,
        args.parts,
        args.output_dir,
        grid_cols=args.grid_cols,
        label_strip_frac=args.label_strip,
        min_area=args.min_area,
        padding=args.padding,
        bg_tolerance=args.bg_tolerance,
    )
    print(f"\nSegmented {len(out)} parts into {args.output_dir}")
    expected = [p for p in args.parts if p not in ("_skip_", "_", "-")]
    if len(out) < len(expected):
        missing = [p for p in expected if p not in out]
        print(f"WARN: {len(missing)} parts not segmented: {missing}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
