#!/usr/bin/env python3
"""
detect_parts.py — direct body-part extraction from a reference character image.

No atlas redraw, no SIFT. Sends the original image to Gemini Flash via
OpenRouter, asks for bounding boxes of each body part as JSON, then crops
those regions out of the original PNG.

Usage:
    python3 detect_parts.py character.png \\
        --output-dir parts/ \\
        [--layout-out layout.json] \\
        [--model gemini-flash | gemini-pro] \\
        [--padding 8]

Env:
    OPENROUTER_KEY     required
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from openrouter_image import OpenRouterError, query_image  # noqa: E402


DEFAULT_PARTS = [
    "head",
    "torso",
    "kilt",
    "left-upper-arm",
    "left-lower-arm",
    "right-upper-arm",
    "right-lower-arm",
    "left-upper-leg",
    "left-lower-leg",
    "right-upper-leg",
    "right-lower-leg",
    "left-foot",
    "right-foot",
]


def _prompt(parts: list[str]) -> str:
    items = ", ".join(parts)
    return (
        "You are looking at a 2D cartoon character standing in A-pose against "
        "a plain background. Identify the tight bounding box of each of the "
        f"following body parts in this image: {items}. "
        "Left and right are from the viewer's point of view (the character's "
        "anatomical left is on the viewer's right). "
        "Return ONLY a single JSON object — no prose, no markdown fences — "
        "mapping each part name to its bounding box using normalized "
        "coordinates in the range 0.0 to 1.0, where x and y are the top-left "
        "corner and w and h are width and height. "
        "Schema: {\"<part-name>\": {\"x\": <float>, \"y\": <float>, "
        "\"w\": <float>, \"h\": <float>}, ...}. "
        "If a part is not clearly visible or is fully occluded, omit it. "
        "Do not invent parts that are not in the list. "
        "Keep boxes as tight as possible around each part — exclude adjacent body parts."
    )


_JSON_RE = re.compile(r"\{.*\}", re.S)


def _parse_bboxes(raw: str) -> dict[str, dict[str, float]]:
    match = _JSON_RE.search(raw)
    if not match:
        raise SystemExit(f"Vision response did not contain JSON:\n{raw}")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Vision response JSON malformed: {exc}\n---\n{raw}")

    cleaned: dict[str, dict[str, float]] = {}
    for name, bbox in data.items():
        if not isinstance(bbox, dict):
            continue
        try:
            x = float(bbox["x"])
            y = float(bbox["y"])
            w = float(bbox["w"])
            h = float(bbox["h"])
        except (KeyError, TypeError, ValueError):
            continue
        if w <= 0 or h <= 0:
            continue
        cleaned[name] = {"x": x, "y": y, "w": w, "h": h}
    return cleaned


def detect(
    image_path: str,
    *,
    parts: list[str] = DEFAULT_PARTS,
    model: str = "gemini-flash",
) -> dict[str, dict[str, float]]:
    raw = query_image(_prompt(parts), [image_path], model=model)
    return _parse_bboxes(raw)


def crop_parts(
    image_path: str,
    bboxes: dict[str, dict[str, float]],
    output_dir: str,
    *,
    padding_px: int = 8,
) -> dict[str, dict]:
    img = Image.open(image_path).convert("RGBA")
    iw, ih = img.size
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    layout: dict[str, dict] = {}
    for name, b in bboxes.items():
        x = max(0, int(b["x"] * iw) - padding_px)
        y = max(0, int(b["y"] * ih) - padding_px)
        w = min(iw - x, int(b["w"] * iw) + padding_px * 2)
        h = min(ih - y, int(b["h"] * ih) + padding_px * 2)
        if w < 4 or h < 4:
            print(f"  skip {name}: bbox too small ({w}x{h})")
            continue
        crop = img.crop((x, y, x + w, y + h))
        out_path = out / f"{name}.png"
        crop.save(out_path)
        layout[name] = {"x": x, "y": y, "width": w, "height": h, "file": out_path.name}
        print(f"  {name:>18}: pos=({x:>4},{y:>4}) size={w:>3}x{h:>3}")
    return layout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_image")
    parser.add_argument("--output-dir", default="parts")
    parser.add_argument("--layout-out", default=None,
                        help="Where to write the layout JSON (defaults to <output-dir>/layout.json)")
    parser.add_argument("--model", default="gemini-flash",
                        choices=["gemini-flash", "gemini-pro"])
    parser.add_argument("--parts", nargs="+", default=None,
                        help="Override default body-part list")
    parser.add_argument("--padding", type=int, default=8)
    args = parser.parse_args()

    if not Path(args.input_image).is_file():
        raise SystemExit(f"input image not found: {args.input_image}")

    parts = args.parts or DEFAULT_PARTS

    try:
        print(f"[1/2] Detecting bboxes via Gemini ({args.model})…")
        bboxes = detect(args.input_image, parts=parts, model=args.model)
        if not bboxes:
            raise SystemExit("Gemini did not return any bounding boxes")
        print(f"      Detected {len(bboxes)} parts: {list(bboxes.keys())}")

        print("[2/2] Cropping parts from the original image…")
        img = Image.open(args.input_image)
        layout = crop_parts(
            args.input_image,
            bboxes,
            args.output_dir,
            padding_px=args.padding,
        )

        layout_obj = {
            "reference_image": Path(args.input_image).name,
            "canvas_width": img.width,
            "canvas_height": img.height,
            "parts": layout,
        }
        layout_path = args.layout_out or str(Path(args.output_dir) / "layout.json")
        Path(layout_path).parent.mkdir(parents=True, exist_ok=True)
        Path(layout_path).write_text(json.dumps(layout_obj, indent=2))
        print(f"      Layout: {layout_path}")

        print(f"\nDone. {len(layout)} parts in {args.output_dir}/")
    except OpenRouterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
