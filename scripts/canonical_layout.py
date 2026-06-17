#!/usr/bin/env python3
"""
canonical_layout.py — generate a layout.json with hardcoded anatomical
positions for a generic 3/4 humanoid character. Coordinates are in pixels on
a 1000×1500 canvas, expressed as top-left corner + width/height per part.

Centres are anatomical guesses; widths/heights are read from each part PNG
so the slots match the actual sprite sizes.

Usage:
    python3 canonical_layout.py --parts-dir parts/ --output layout.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from PIL import Image


CANVAS_W = 1000
CANVAS_H = 1500


CENTRES: dict[str, tuple[int, int]] = {
    "head":             (500, 230),
    "nemes":            (500, 250),
    "ear":              (430, 200),
    "brow":             (530, 215),
    "eye":              (530, 240),
    "nose":             (600, 260),
    "mouth":            (580, 295),
    "collar":           (500, 460),
    "torso":            (500, 600),
    "belt":             (500, 780),
    "kilt":             (500, 900),
    "left_upper_arm":   (340, 600),
    "left_lower_arm":   (310, 760),
    "left_hand":        (300, 870),
    "right_upper_arm":  (660, 600),
    "right_lower_arm":  (690, 760),
    "right_hand":       (700, 870),
    "left_lower_leg":   (430, 1100),
    "left_foot":        (430, 1280),
    "right_lower_leg":  (570, 1100),
    "right_foot":       (570, 1280),
}


def build(parts_dir: str, output: str) -> dict:
    parts_path = Path(parts_dir)
    layout: dict[str, dict] = {}

    for name, (cx, cy) in CENTRES.items():
        png_path = parts_path / f"{name}.png"
        if not png_path.is_file():
            continue
        with Image.open(png_path) as im:
            w, h = im.size
        x = int(cx - w / 2)
        y = int(cy - h / 2)
        layout[name] = {"x": x, "y": y, "width": w, "height": h,
                         "file": png_path.name}

    out = {
        "reference_image": "canonical-3q-pose",
        "canvas_width": CANVAS_W,
        "canvas_height": CANVAS_H,
        "parts": layout,
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(out, indent=2))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = build(args.parts_dir, args.output)
    print(f"Canonical layout saved: {args.output}")
    print(f"  {len(out['parts'])} parts on {out['canvas_width']}x{out['canvas_height']} canvas")


if __name__ == "__main__":
    main()
