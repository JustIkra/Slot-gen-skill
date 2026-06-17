#!/usr/bin/env python3
"""
split_character.py — Generate a body-part sprite-sheet atlas from a single
character image using OpenRouter (Nano Banana 2 / Pro) and segment it into
individual transparent PNGs.

Pipeline:
  1. Send the reference character image to OpenRouter → flat atlas with all
     body parts laid out and separated on a white background.
  2. (Optional) Run remove.bg on the atlas before segmentation.
  3. Use OpenCV connected-components analysis to crop each part into its own
     transparent PNG.

Usage:
    python3 split_character.py character.png \\
        --output-dir parts/ \\
        --atlas-out atlas.png \\
        [--model nano-banana-2] [--size 2K] [--aspect-ratio 1:1] \\
        [--remove-bg-atlas] [--remove-bg-parts] \\
        [--min-area 500] [--padding 12] [--bg-threshold 240]

Env:
    OPENROUTER_KEY     required
    REMOVEBG_API_KEY   required if --remove-bg-atlas or --remove-bg-parts is set
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atlas_prompts import DEFAULT_PARTS, build_atlas_prompt  # noqa: E402
from openrouter_image import (  # noqa: E402
    OpenRouterError,
    generate_image,
    remove_background,
)


def generate_atlas(input_image: str, atlas_out: str, *, model: str, size: str,
                   aspect_ratio: str, parts: list[str], grid_cols: int) -> str:
    prompt = build_atlas_prompt(parts=parts, grid_cols=grid_cols)
    print(f"[1/3] Generating atlas via OpenRouter ({model}, {size}, {aspect_ratio})…")
    print(f"      Parts requested: {len(parts)} in {grid_cols}-col grid")
    generate_image(
        prompt=prompt,
        output=atlas_out,
        model=model,
        size=size,
        aspect_ratio=aspect_ratio,
        reference_image=input_image,
    )
    print(f"      Atlas saved: {atlas_out}")
    return atlas_out


def segment_parts(atlas_path: str, output_dir: str, *, min_area: int,
                  padding: int, bg_threshold: int) -> list[str]:
    img = cv2.imread(atlas_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit(f"ERROR: Could not read atlas image: {atlas_path}")

    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    bgr = img[:, :, :3]
    alpha = img[:, :, 3]

    if alpha.min() == 255:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        corner_brightness = float(np.mean([
            gray[0, 0], gray[0, -1], gray[-1, 0], gray[-1, -1]
        ]))
        if corner_brightness < 128:
            _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
        else:
            _, mask = cv2.threshold(gray, bg_threshold, 255, cv2.THRESH_BINARY_INV)
    else:
        _, mask = cv2.threshold(alpha, 8, 255, cv2.THRESH_BINARY)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    part_idx = 0
    h_img, w_img = img.shape[:2]

    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area < min_area:
            continue

        x = stats[label_id, cv2.CC_STAT_LEFT]
        y = stats[label_id, cv2.CC_STAT_TOP]
        w = stats[label_id, cv2.CC_STAT_WIDTH]
        h = stats[label_id, cv2.CC_STAT_HEIGHT]

        x1 = max(x - padding, 0)
        y1 = max(y - padding, 0)
        x2 = min(x + w + padding, w_img)
        y2 = min(y + h + padding, h_img)

        crop = img[y1:y2, x1:x2].copy()
        label_region = labels[y1:y2, x1:x2]
        component_mask = label_region == label_id
        crop[~component_mask] = [0, 0, 0, 0]

        out_path = os.path.join(output_dir, f"part_{part_idx:02d}.png")
        cv2.imwrite(out_path, crop)
        saved.append(out_path)
        part_idx += 1

    return saved


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deconstructed body-part atlas via OpenRouter and "
            "segment it into individual transparent PNGs."
        )
    )
    parser.add_argument("input_image", help="Reference character image")
    parser.add_argument("--output-dir", default="output_parts",
                        help="Directory for cropped part PNGs")
    parser.add_argument("--atlas-out", default="atlas.png",
                        help="Path for the generated atlas PNG")
    parser.add_argument("--model", default="nano-banana-2",
                        choices=["nano-banana-2", "nano-banana-pro"])
    parser.add_argument("--size", default="2K",
                        choices=["1K", "2K", "4K"])
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--remove-bg-atlas", action="store_true",
                        help="Run remove.bg on the generated atlas before segmentation")
    parser.add_argument("--remove-bg-parts", action="store_true",
                        help="Run remove.bg on each segmented part PNG")
    parser.add_argument("--parts", nargs="+", default=None,
                        help="Override the body-part list (defaults to atlas_prompts.DEFAULT_PARTS)")
    parser.add_argument("--grid-cols", type=int, default=4,
                        help="Number of columns in the requested grid layout")
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument("--padding", type=int, default=12)
    parser.add_argument("--bg-threshold", type=int, default=240)
    args = parser.parse_args()

    if not Path(args.input_image).is_file():
        raise SystemExit(f"ERROR: Input image not found: {args.input_image}")

    try:
        generate_atlas(
            args.input_image,
            args.atlas_out,
            model=args.model,
            size=args.size,
            aspect_ratio=args.aspect_ratio,
            parts=args.parts or DEFAULT_PARTS,
            grid_cols=args.grid_cols,
        )

        if args.remove_bg_atlas:
            print("[1.5/3] Running remove.bg on atlas…")
            remove_background(args.atlas_out, overwrite=True)

        print("[2/3] Segmenting parts…")
        parts = segment_parts(
            args.atlas_out,
            args.output_dir,
            min_area=args.min_area,
            padding=args.padding,
            bg_threshold=args.bg_threshold,
        )
        print(f"      Found {len(parts)} parts → {args.output_dir}/")
        for p in parts:
            print(f"        - {os.path.basename(p)}")

        if args.remove_bg_parts:
            print("[2.5/3] Running remove.bg on each part…")
            for p in parts:
                remove_background(p, overwrite=True)

        print("[3/3] Done.")
        print(f"\nParts are in: {args.output_dir}/")
        print("Next step: position_parts.py against the reference image.")
    except OpenRouterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
