#!/usr/bin/env python3
"""chroma_key.py — full-resolution background removal via solid-colour keying.

Why this exists
---------------
UI assets such as frames, buttons, logos, and banners must preserve their
generated source resolution. The reliable full-resolution path is:

  1. Generate the asset on a SOLID CHROMA background (magenta #FF00FF works best
     because nothing in gold/Egyptian art is magenta).
  2. Key the chroma out here at full native resolution.

This keeps every pixel the model produced, then you downscale to the target
size yourself (never upscale past the source — see the skill notes).

Pipeline: colour key -> alpha erosion (kills the fringe) -> de-spill (neutralises
the colour halo left on kept edge pixels) -> optional bbox trim.

Usage
-----
  python3 chroma_key.py --input raw.png --output clean.png
  python3 chroma_key.py --input raw.png --output clean.png \
      --color ff00ff --erode 3 --no-trim --resize 1364x994

Notes
-----
- `--color` is the chroma to remove (hex, default magenta ff00ff).
- The keyer is tuned to NOT eat lapis-blue studs / blue panels: magenta needs
  BOTH red and blue high with green low, while blue gems have low red.
- `--resize WxH` downscales the cleaned result (LANCZOS). Do not use it to
  upscale — generate larger instead.
"""

import argparse
import sys

try:
    from PIL import Image, ImageFilter
    import numpy as np
except ImportError:
    sys.exit("chroma_key.py needs Pillow + numpy: pip install pillow numpy")


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def chroma_key(img: Image.Image, color, erode: int, despill: bool) -> Image.Image:
    a = np.array(img.convert("RGBA")).astype(np.int16)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    cr, cg, cb = color

    # Generic "close to chroma" test plus a magenta-specialised test that is
    # robust to the soft halo without touching blue studs (low red) or gold.
    dist = np.abs(R - cr) + np.abs(G - cg) + np.abs(B - cb)
    near = dist < 140
    if (cr, cg, cb) == (255, 0, 255):  # magenta fast-path
        near |= (R > 140) & (B > 110) & (G < 115) & (R - G > 55) & (B - G > 25)

    alpha = np.where(near, 0, 255).astype(np.uint8)

    if erode > 0:
        k = erode * 2 + 1
        alpha = np.array(Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(k)))

    out = np.array(img.convert("RGBA"))
    out[:, :, 3] = alpha

    if despill:
        op = alpha > 0
        o = out.astype(int)
        # pixels still tinted toward the chroma (here: magenta-style R&B > G)
        spill = op & (o[:, :, 0] - o[:, :, 1] > 35) & (o[:, :, 2] - o[:, :, 1] > 20)
        g = o[:, :, 1]
        out[:, :, 0][spill] = np.clip(g[spill] + 12, 0, 255)
        out[:, :, 2][spill] = np.clip(g[spill] + 8, 0, 255)

    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser(description="Full-res background removal by chroma keying")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--color", default="ff00ff", help="chroma hex to remove (default magenta)")
    ap.add_argument("--erode", type=int, default=3, help="alpha erosion radius px (default 3)")
    ap.add_argument("--no-despill", action="store_true")
    ap.add_argument("--no-trim", action="store_true", help="keep canvas (default trims to content bbox)")
    ap.add_argument("--resize", help="WxH to downscale cleaned result, e.g. 1364x994")
    args = ap.parse_args()

    img = Image.open(args.input).convert("RGBA")
    res = chroma_key(img, hex_to_rgb(args.color), args.erode, not args.no_despill)

    if not args.no_trim:
        al = np.array(res)[:, :, 3]
        ys, xs = np.where(al > 30)
        if len(xs):
            res = res.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

    if args.resize:
        w, h = (int(v) for v in args.resize.lower().split("x"))
        if w > res.width or h > res.height:
            print(f"warning: --resize {w}x{h} UPSCALES past source {res.size}; "
                  "generate larger instead of upscaling", file=sys.stderr)
        res = res.resize((w, h), Image.LANCZOS)

    res.save(args.output, "PNG", optimize=True)
    print(f"chroma_key: {img.size} -> {res.size} saved {args.output}")


if __name__ == "__main__":
    main()
