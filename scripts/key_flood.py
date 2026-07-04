"""Full-res keying of a logo / text / UI part generated on a SOLID background
(white OR black), when remove.bg would downscale and magenta wasn't used.

Flood-fills the background from the image border on a "flatness" mask, then keeps
ONLY the largest connected foreground component — which drops the detached sparks /
embers the image model loves to sprinkle around a logo. Optionally erodes the alpha
a few px to thin a too-thick outline. Auto-detects white vs black bg from the corners.

    python key_flood.py in.png out.png            # auto bg, no erosion
    python key_flood.py in.png out.png --erode 9  # thin the outline by ~4px
    python key_flood.py in.png out.png --bg black

Caveat: sparks painted ON TOP of the letters cannot be removed this way (they are not
a separate component) — regenerate the asset without them instead.
"""

import argparse
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def key_flood(src, out, erode=1, bg="auto", feather=1.2):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    mn, mx = a.min(2), a.max(2)

    if bg == "auto":
        c = np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3),
                            a[-8:, :8].reshape(-1, 3), a[-8:, -8:].reshape(-1, 3)])
        bg = "white" if c.mean() > 128 else "black"
    flat = (mn > 230) & ((mx - mn) < 22) if bg == "white" else (mx < 45)

    border = np.zeros_like(flat)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    lbl, _ = ndimage.label(flat)
    bg_labels = set(np.unique(lbl[border & flat])) - {0}
    fg = ~np.isin(lbl, list(bg_labels))

    lbl2, n2 = ndimage.label(fg)
    if n2 > 1:
        sizes = ndimage.sum(np.ones_like(lbl2), lbl2, range(1, n2 + 1))
        fg = lbl2 == (int(np.argmax(sizes)) + 1)

    alpha = np.where(fg, 255, 0).astype(np.uint8)
    if erode > 1:
        alpha = ndimage.minimum_filter(alpha, size=erode if erode % 2 else erode + 1)
    alpha_im = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(feather))
    rgba = np.dstack([np.asarray(im), np.asarray(alpha_im)]).astype(np.uint8)
    res = Image.fromarray(rgba, "RGBA")

    ys, xs = np.where(np.asarray(alpha_im) > 16)
    if len(xs):
        res = res.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    res.save(out)
    print(f"WROTE {out} {res.size} bg={bg} fg_components={n2} erode={erode}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Flood-fill key a logo off a solid white/black bg")
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--erode", type=int, default=1, help="thin the outline (odd px window, e.g. 9)")
    p.add_argument("--bg", default="auto", choices=["auto", "white", "black"])
    args = p.parse_args()
    key_flood(args.src, args.out, erode=args.erode, bg=args.bg)
