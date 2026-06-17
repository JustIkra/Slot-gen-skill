#!/usr/bin/env python3
"""recolor_lut.py — re-theme images/animations by luminance->gradient mapping.

Why this exists
---------------
To re-skin an existing ANIMATION (a frame sequence) or effect to a new colour
theme, regenerating every frame with AI is wrong: there is no temporal
coherence between independently generated frames. Instead, map each pixel's
luminance through a colour ramp. Motion and alpha are preserved 1:1 — only the
hue changes. Used this session to turn a blue electric plasma sphere (31 frames)
+ glow/shockwave into gold, and to gold-tint structural UI parts.

Built-in ramps: gold, amber, ice, purple, red, green. Or pass --stops.

Usage
-----
  # single file
  python3 recolor_lut.py --ramp gold --input frame.png --output frame.png
  # whole sequence in place (glob)
  python3 recolor_lut.py --ramp gold --glob "sphere/s_*.png"
  # custom ramp: luminance 0..1 -> r,g,b stops
  python3 recolor_lut.py --input x.png --output x.png \
      --stops "0:50,18,0; 0.55:235,150,30; 1:255,250,235"

Alpha is always preserved. Only RGB is remapped.
"""

import argparse
import glob as globmod
import sys

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("recolor_lut.py needs Pillow + numpy: pip install pillow numpy")

RAMPS = {
    # warm polished gold: dark amber -> gold -> white-hot core
    "gold":   [(0.0, (50, 18, 0)), (0.30, (150, 70, 8)), (0.55, (235, 150, 30)),
               (0.78, (255, 210, 90)), (1.0, (255, 250, 235))],
    "amber":  [(0.0, (40, 12, 0)), (0.5, (200, 110, 20)), (1.0, (255, 235, 170))],
    "ice":    [(0.0, (5, 20, 45)), (0.5, (40, 150, 220)), (1.0, (235, 250, 255))],
    "purple": [(0.0, (25, 5, 40)), (0.5, (120, 40, 180)), (1.0, (240, 220, 255))],
    "red":    [(0.0, (40, 0, 0)), (0.5, (180, 25, 20)), (1.0, (255, 230, 210))],
    "green":  [(0.0, (5, 35, 10)), (0.5, (30, 160, 60)), (1.0, (225, 255, 230))],
}


def parse_stops(s: str):
    stops = []
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        t, rgb = part.split(":")
        r, g, b = (int(v) for v in rgb.split(","))
        stops.append((float(t), (r, g, b)))
    return sorted(stops)


def build_lut(stops):
    xs = [s[0] for s in stops]
    t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, [s[1][c] for s in stops]) for c in range(3)], axis=1).astype(np.uint8)


def recolor(path_in, path_out, lut):
    a = np.array(Image.open(path_in).convert("RGBA"))
    rgb = a[:, :, :3].astype(np.float32)
    L = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]).clip(0, 255).astype(np.uint8)
    a[:, :, 0] = lut[L, 0]
    a[:, :, 1] = lut[L, 1]
    a[:, :, 2] = lut[L, 2]
    Image.fromarray(a, "RGBA").save(path_out, "PNG", optimize=True)


def main():
    ap = argparse.ArgumentParser(description="Re-theme images by luminance->gradient LUT")
    ap.add_argument("--ramp", choices=list(RAMPS), help="built-in colour ramp")
    ap.add_argument("--stops", help="custom ramp 't:r,g,b; ...' (overrides --ramp)")
    ap.add_argument("--input")
    ap.add_argument("--output")
    ap.add_argument("--glob", help="process every match in place")
    args = ap.parse_args()

    stops = parse_stops(args.stops) if args.stops else RAMPS.get(args.ramp)
    if not stops:
        sys.exit("provide --ramp <name> or --stops")
    lut = build_lut(stops)

    if args.glob:
        files = sorted(globmod.glob(args.glob))
        if not files:
            sys.exit(f"no files match {args.glob}")
        for f in files:
            recolor(f, f, lut)
        print(f"recolor_lut: re-themed {len(files)} files")
    elif args.input and args.output:
        recolor(args.input, args.output, lut)
        print(f"recolor_lut: {args.input} -> {args.output}")
    else:
        sys.exit("provide --input/--output or --glob")


if __name__ == "__main__":
    main()
