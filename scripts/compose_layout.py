#!/usr/bin/env python3
"""
compose_layout.py — render a composite PNG from a layout.json + parts folder.

Each part is pasted at its top-left position from the layout. Useful to
eyeball-compare different positioning strategies (canonical / SIFT / Vision).

Usage:
    python3 compose_layout.py --layout layout.json --parts-dir parts/ \\
        --output composite.png [--background "#0f0f1a"]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageColor


DRAW_ORDER = [
    "shadow", "left_lower_leg", "right_lower_leg", "left_foot", "right_foot",
    "kilt", "belt",
    "left_upper_arm", "right_upper_arm", "left_lower_arm", "right_lower_arm",
    "left_hand", "right_hand",
    "torso", "collar",
    "nemes", "head", "ear", "brow", "eye", "nose", "mouth",
]


def compose(layout_path: str, parts_dir: str, output: str, bg: str) -> None:
    layout = json.loads(Path(layout_path).read_text())
    cw = layout["canvas_width"]
    ch = layout["canvas_height"]
    parts = layout["parts"]

    bg_rgba = ImageColor.getrgb(bg) + (255,)
    canvas = Image.new("RGBA", (cw, ch), bg_rgba)

    drawn: list[str] = []
    seen = set()
    for name in DRAW_ORDER:
        if name in parts:
            drawn.append(name)
            seen.add(name)
    for name in parts:
        if name not in seen:
            drawn.append(name)

    for name in drawn:
        p = parts[name]
        png = Path(parts_dir) / p.get("file", f"{name}.png")
        if not png.is_file():
            print(f"  miss: {png}")
            continue
        sprite = Image.open(png).convert("RGBA")
        canvas.paste(sprite, (int(p["x"]), int(p["y"])), sprite)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    print(f"  saved: {output}  ({cw}x{ch}, {len(drawn)} parts)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True)
    parser.add_argument("--parts-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--background", default="#0f0f1a")
    args = parser.parse_args()
    compose(args.layout, args.parts_dir, args.output, args.background)


if __name__ == "__main__":
    main()
