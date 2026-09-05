# Art generation workflow

Single-shot images via OpenRouter. Used for slot reels, icons, decorations, backgrounds.

## When to use

User asks for one of:

- "Generate a slot symbol / wild / scatter"
- "Make a background for the reel area"
- "Create a character portrait"
- "Make this asset transparent"
- "Give me 3 variations of X"

## Steps

1. Pick model:
   - `nano-banana-2` — default, fast, supports reference images.
   - `nano-banana-pro` — slower, better for hero assets and complex compositions.
2. Pick aspect ratio matching the target slot:
   - Square reel symbols → `1:1`
   - Background sky/banner → `16:9` or `21:9`
   - Vertical promo → `9:16`
3. Pick size:
   - `1K` — quick previews, cheapest.
   - `2K` — default for finals.
   - The configured route rejects `4K`; verify a suitable provider/model explicitly if a task requires it.
4. For sprites, request native alpha with `--transparent` or generate on a
   controlled solid background and clean it locally with `chroma_key.py` or
   `key_flood.py`.

Use the installed shared client. Unsupported options fail before spending; never
silently substitute a model or reduce the user's requested resolution/token limit.

## Examples

Quick preview of a slot wild symbol:

```bash
bun run tools/generate-image.ts \
  --prompt "Cartoon golden lion mascot, dynamic pose, neon outline, slot wild symbol" \
  --size 1K --aspect-ratio 1:1 \
  --output ./out/wild-preview.png
```

Final reel symbol generated on a controlled chroma background and keyed locally:

```bash
bun run tools/generate-image.ts \
  --prompt "Cartoon golden lion mascot, dynamic pose, neon outline, slot wild symbol, solid magenta background" \
  --size 2K --aspect-ratio 1:1 \
  --output ./out/wild-raw.png

python3 scripts/chroma_key.py \
  --input ./out/wild-raw.png \
  --output ./out/wild.png
```

Three variations of a background:

```bash
bun run tools/generate-image.ts \
  --model nano-banana-pro \
  --prompt "Ancient Egyptian temple at dusk, painterly, slot machine background" \
  --size 2K --aspect-ratio 16:9 \
  --creative-variations 3 \
  --output ./out/bg.png
```

Stand-alone full-resolution keying call:

```bash
python3 scripts/key_flood.py \
  ./uploads/user-symbol-on-black.png \
  ./out/user-symbol.png \
  --bg black
```

## Prompt tips (carried over from /art)

- Avoid hex codes (`#1A8A9B` renders as text). Use color names.
- State direction explicitly: "LEFT TO RIGHT" or "TOP TO BOTTOM".
- Specify single label position (inside OR below, not both).
- For consistent sets, reuse the exact same `--size` and `--aspect-ratio`.

## Examples from a production reskin

These examples are conditional on the brief, not a universal theme or mandatory recipe.

### Transparency / quality
- For frames, buttons, banners, and logos, generate on a **solid magenta
  `#FF00FF`** background, then use `scripts/chroma_key.py --input raw.png
  --output clean.png --resize WxH`. This preserves native resolution and clean
  edges.
- For a purple or magenta subject, generate on **solid green `#00FF00`** and
  pass `--color 00ff00`. De-spill is chroma-aware: magenta keying neutralises
  magenta spill, while green keying neutralises only green-dominant spill and
  preserves purple foreground pixels.
- For solid black or white backgrounds, use `scripts/key_flood.py` to remove
  the border-connected background while retaining the largest foreground part.
- **Never upscale.** Generate at or above target size and downscale once.

### Model / aspect ratio
- **`nano-banana-pro` rejects extreme strip ratios** (`4:1`, `8:1`, `1:4`,
  `1:8`) with HTTP 400. The tool now blocks this early — use `nano-banana-2`
  (flash) for wide/tall strips. (Pro is worth it for hero art at normal ratios.)

### Text & logos
- AI text breaks at wide aspect: at `8:1` it duplicates/misspells
  ("BOCK", "ABYDOS AYDOS"). Keep titles to **≤4:1**, one word per generation,
  and **eyeball the spelling** every time — regenerate on any defect.
- For matching word/light style across a multi-word logo, generate one word as
  the anchor, then pass it as `--reference-image` for the rest ("match this
  material and LIGHTING exactly").
- For guaranteed-correct short text where AI keeps failing, render with PIL +
  a bold font (e.g. macOS Copperplate) and a gold gradient — crisp and correct,
  if less flashy than AI 3D.

### Consistent sets (symbols, buttons, frames)
- Generate an **anchor** first, then `--reference-image` it for the rest so the
  frame/material/lighting stays identical across the set.
- If the source reference is a protected paytable or contact sheet, do not use
  it directly for new symbols whose object classes or silhouettes overlap the
  sheet. Build a style-only anchor without those target shapes, then use the
  original sheet only in the final similarity audit. Prompt-level originality
  instructions alone do not reliably prevent silhouette/facet copying.
- To make paired UI (YES/NO) symmetric AND keep the bezel from darkening on
  hover: generate ONE bezel+gem, mask the gem by colour, and build the
  hover/press/disabled states by changing **only the gem** (leave the bezel
  pixels untouched across all four state PNGs).
- Match the **original asset's exact pixel dimensions and inner opening** when
  replacing engine art (pull the original from the reference project, measure
  its border/opening, fit yours to it) — guessing breaks in-game alignment.

### Re-theming existing animations
- To recolour a frame **sequence** (or any effect) to a new theme, do NOT
  regenerate frames (no temporal coherence). Map luminance→gradient with
  `scripts/recolor_lut.py --ramp gold --glob "sphere/s_*.png"`. Motion + alpha
  preserved, only hue changes. Remember the sibling layers too — a blue glow
  often has separate `light`/`blastwave` additive PNGs that also need recolouring.
