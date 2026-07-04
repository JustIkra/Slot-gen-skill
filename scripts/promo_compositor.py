"""Reusable physical-light compositing primitives for slot promo / lobby art.

Why this exists: AI-generated layers composited with stacked `screen` glow + 2D
drop-shadows + 360 deg rim read as flat stickers "behind a film". These primitives
simulate light instead — the same refactor that took a murky 1:1 master to real
depth. See workflows/promo-composition.md -> "Compositing layers so elements DETACH".

All functions are CANVAS-SIZE AGNOSTIC (H, W derived from the input array), so the
same module drives a 2048x2048 master and a 1280x720 landscape unchanged.

Typical assembler:

    import numpy as np
    from PIL import Image
    from promo_compositor import (bake_vignette, cast_shadow_mul, light_wrap,
                                   directional_rim, radial_color, flatten, grade)

    H, W = 2048, 2048
    layers = []                                   # each: (PIL_RGBA, blend)
    bg = bake_vignette(bg_rgb)                     # vignette in the BG, not at the end
    layers.append((bg, "normal"))
    fp = place(frame, ...)                         # your own placement
    layers.append((cast_shadow_mul(fp, 0, int(H*0.006), int(H*0.006), 150), "multiply"))
    layers.append((cast_shadow_mul(fp, 0, int(H*0.022), int(H*0.026), 95),  "multiply"))
    layers.append((frame_lit, "normal"))
    layers.append((light_wrap(frame_lit, bg, int(W*0.012), int(W*0.012), 1.15), "screen"))
    layers.append((directional_rim(frame_lit, (255,226,175), 0, int(H*0.012), int(H*0.007), 1.1), "screen"))
    # book shadow masked to the pedestal so it lands on stone, not air:
    layers.append((cast_shadow_mul(book, 0, int(H*0.018), int(H*0.016), 150, mask_alpha=frame_alpha), "multiply"))
    # local title light: dark pool (multiply) + painted colour (dodge), never screen-milk:
    layers.append((radial_color(W, H, 0.5, 0.82, 0.34, 0.10, (0,0,0),     150, gamma=1.2), "multiply"))
    layers.append((radial_color(W, H, 0.5, 0.79, 0.20, 0.085,(40,120,150),150, gamma=1.5), "dodge"))
    flat = grade(flatten(layers))                  # grade = contrast/sat/gamma ONLY
"""

import numpy as np
from PIL import Image, ImageFilter


def directional_rim(rgba, color, dx, dy, blur, strength=1.0):
    """Rim light from ONE direction (shift alpha, subtract) — not a 360 deg stroke.
    Light from above/centre: positive dy lights the TOP edges. Returns a SCREEN layer."""
    a = np.asarray(rgba)[..., 3].astype(float)
    H, W = a.shape
    shifted = np.roll(np.roll(a, int(dy), axis=0), int(dx), axis=1)
    rim = np.clip(a - shifted, 0, 255)
    rim = np.asarray(Image.fromarray(rim.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(float)
    rim = np.clip(rim * strength, 0, 255) / 255.0
    out = np.zeros((H, W, 4), float)
    out[..., 0], out[..., 1], out[..., 2] = color
    out[..., :3] *= rim[..., None]
    out[..., 3] = 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def cast_shadow_mul(rgba, dx, dy, blur, opacity, mask_alpha=None):
    """Directional cast shadow as a MULTIPLY layer (real darkening, not grey overlay).
    Pass mask_alpha = the receiver's alpha (e.g. the pedestal) so the shadow lands on
    the surface instead of floating in the air. Use TWO (contact + ambient) per object."""
    a = np.asarray(rgba)[..., 3].astype(float)
    H, W = a.shape
    sh = np.roll(np.roll(a, int(dy), axis=0), int(dx), axis=1)
    sh = np.asarray(Image.fromarray(sh.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(float)
    sh = sh * (opacity / 255.0)
    if mask_alpha is not None:
        sh = sh * (np.asarray(mask_alpha).astype(float) / 255.0)
    out = np.zeros((H, W, 4), float)
    out[..., 3] = np.clip(sh, 0, 255)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def light_wrap(elem_rgba, bg_rgb, erode_k, blur, strength):
    """Bleed the BRIGHT background onto the object's edges so it sits in the scene
    instead of being a sticker. Take the inner edge band (alpha - eroded alpha),
    mask the blurred background by it, return a SCREEN layer. This REPLACES the
    (wrong) dark separation halo — never put dark mud over a backlit centre."""
    a = np.asarray(elem_rgba)[..., 3].astype(np.uint8)
    H, W = a.shape
    k = erode_k if erode_k % 2 else erode_k + 1
    er = np.asarray(Image.fromarray(a).filter(ImageFilter.MinFilter(k))).astype(float)
    band = np.clip(a.astype(float) - er, 0, 255)
    band = np.asarray(Image.fromarray(band.astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(float) / 255.0
    bgl = np.asarray(Image.fromarray(np.asarray(bg_rgb)[..., :3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(int(W * 0.02)))).astype(float)
    out = np.zeros((H, W, 4), float)
    out[..., :3] = np.clip(bgl * band[..., None] * strength, 0, 255)
    out[..., 3] = 255
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def radial_color(W, H, cx, cy, rx, ry, color, op, gamma=1.4):
    """A coloured radial gradient (fractional centre/radii). Use with blend:
    'multiply' + black color = darken a pool under the title;
    'dodge' + colour = paint magical light onto stone WITHOUT screen-milk."""
    yy, xx = np.mgrid[0:H, 0:W]
    d2 = ((xx - cx * W) ** 2) / (2 * (rx * W) ** 2) + ((yy - cy * H) ** 2) / (2 * (ry * H) ** 2)
    g = np.exp(-d2) ** gamma
    arr = np.zeros((H, W, 4), float)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., :3] *= g[..., None]
    arr[..., 3] = np.clip(g * op, 0, 255)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")


def bake_vignette(bg_rgb, strength=0.46, start=0.34, falloff=0.66, luma_mul=1.0):
    """Darken the background edges HERE (not over the final flatten — that darkens the
    logo corners and reads cheap). Do NOT lift the bg blacks: a light hero on a lifted
    light bg is flat. Returns an RGBA. Tune strength up for deeper 'tomb' edges."""
    src = bg_rgb.convert("RGB") if hasattr(bg_rgb, "convert") else bg_rgb
    a = np.asarray(src).astype(float) * luma_mul
    H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip(1.0 - strength * np.clip(rr - start, 0, 1) / falloff, 0, 1)
    a[..., :3] *= vig[..., None]
    return Image.fromarray(np.dstack([a[..., :3].clip(0, 255), np.full((H, W), 255)]).astype(np.uint8), "RGBA")


def flatten(layers):
    """Composite [(PIL_RGBA, blend), ...] bottom->top. blend in
    {normal, screen, multiply, dodge}. First layer is the opaque base.
    For PSD export map dodge -> linear_dodge (fallback screen)."""
    base = None
    for img, blend in layers:
        r = np.asarray(img.convert("RGBA")).astype(float)
        rgb = r[..., :3]
        al = r[..., 3:4] / 255.0
        if base is None:
            base = rgb.copy()
            continue
        if blend == "screen":
            base = 255.0 - (255.0 - base) * (255.0 - rgb * al) / 255.0
        elif blend == "multiply":
            base = base * ((rgb / 255.0) * al + (1.0 - al))
        elif blend == "dodge":
            base = np.clip(base / (1.0 - np.clip(rgb / 255.0 * al, 0, 0.996)), 0, 255)
        else:
            base = base * (1 - al) + rgb * al
    return Image.fromarray(base.clip(0, 255).astype(np.uint8), "RGB")


def grade(flat, sat=1.24, contrast=1.10, gamma=1.06):
    """Final colour grade: saturation + contrast + slight gamma ONLY. The vignette is
    already in the background (bake_vignette) — do not re-apply it here."""
    a = np.asarray(flat).astype(float)
    g = (a @ np.array([0.299, 0.587, 0.114]))[..., None]
    a = g + (a - g) * sat
    a = (a - 128.0) * contrast + 128.0
    a = 255.0 * np.power(np.clip(a / 255.0, 0, 1), 1.0 / gamma)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
