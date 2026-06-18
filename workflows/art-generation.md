# Art generation workflow

Single-shot images via OpenRouter. Used for slot reels, icons, decorations, backgrounds.

## When to use

User asks for one of:

- "Generate a slot symbol / wild / scatter"
- "Make a background for the reel area"
- "Create a character portrait"
- "Remove background from this image"
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
   - `4K` — only when print or zoom is required.
4. Add `--transparent` for sprites that must drop straight onto a reel canvas, or
   add `--remove-bg` to clean the result through remove.bg afterwards.

> Note: OpenRouter advertises `0.5K` for `google/gemini-3.1-flash-image-preview`,
> but Google AI Studio currently rejects it with `INVALID_ARGUMENT`. Until that
> ships end-to-end, `1K` is the minimum.

## Examples

Quick preview of a slot wild symbol:

```bash
bun run tools/generate-image.ts \
  --prompt "Cartoon golden lion mascot, dynamic pose, neon outline, slot wild symbol" \
  --size 1K --aspect-ratio 1:1 \
  --output ./out/wild-preview.png
```

Final reel symbol with background stripped through remove.bg:

```bash
bun run tools/generate-image.ts \
  --prompt "Cartoon golden lion mascot, dynamic pose, neon outline, slot wild symbol" \
  --size 2K --aspect-ratio 1:1 \
  --output ./out/wild.png \
  --remove-bg
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

Stand-alone remove.bg call (e.g., user uploaded an image):

```bash
python3 scripts/openrouter_image.py remove-bg \
  --input ./uploads/user-symbol.png \
  --output ./out/user-symbol.png
```

## Prompt tips (carried over from /art)

- Avoid hex codes (`#1A8A9B` renders as text). Use color names.
- State direction explicitly: "LEFT TO RIGHT" or "TOP TO BOTTOM".
- Specify single label position (inside OR below, not both).
- For consistent sets, reuse the exact same `--size` and `--aspect-ratio`.

## Lessons from a full production reskin (read these)

Hard-won during a complete Egyptian reskin of a live slot. They save hours.

### Transparency / quality
- **Don't trust `--remove-bg` for UI assets.** Free/preview remove.bg silently
  caps output to ~578×432 → soft, ruined frames/buttons/logos. For frames,
  buttons, banners, logos: generate on a **solid magenta `#FF00FF`** background
  (no `--remove-bg`), then `scripts/chroma_key.py --input raw.png --output
  clean.png --resize WxH`. Full native resolution, clean edges.
- **Never upscale.** Generate ≥ the target size and downscale. Upscaling a
  remove.bg-shrunk PNG is the #1 cause of "blurry in-game".
- remove.bg is still fine for organic **characters** (matting beats a flat key)
  — but watch the downscale warning, and use `--remove-bg-size full` on a paid
  plan.

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

### Decomposing a finished flat key-art back into editable layers (Gemini inpaint)
Battle-tested splitting a finished 1:1 promo (a single Nano-Banana-Pro render) into an
editable, layered PSD — when you only have the flat hero image and need per-layer control.

- **"Isolate ONLY element X on flat magenta" FAILS** with nano-banana-pro: fed the full scene
  as `--reference-image`, the model re-renders the WHOLE composition instead of one element.
- **What works: removal-with-inpaint.** Prompt "REMOVE ONLY <element>, INPAINT what is behind
  it, keep ABSOLUTELY EVERYTHING ELSE pixel-identical". The model is reliable at *subtracting*
  one thing and filling the hole. Run one removal per element from the SAME source
  (parallelizable, no drift), then derive each cut layer as the **diff** `|source − removed|`
  (threshold + region-gate + feather; take RGB from the source so baked light/shadows survive).
  bg-plate + diffs stacked ≈ the original, now editable.
- **Merge structurally-joined parts into ONE layer** (ring + crest + altar = one gold monument)
  — a seam between them gets rejected. One removal for the whole group, or union the diffs.
- **Strong magenta-isolation needs an explicit DO-NOT list** ("DO NOT draw the book/logo/
  background; the ring CENTRE is empty flat magenta; EVERYTHING else is flat #FF00FF"), and even
  then leaves residue inside enclosed areas → finish in PIL (fill the ring interior with a
  magenta ellipse, keeping the baked rim-glow annulus).
- **Logo isolation: feed a TIGHT CROP of just the title** as the reference, NOT the full scene.
  Given the whole tile it redraws the whole tile; given a crop of the words it reproduces only
  the lettering on magenta. AI also loves to **duplicate a word** (a third line) → magenta-fill
  the dupe, then `trim` recovers the real logo.
- **Strengthen a brand logo without changing its form**: reference the existing logo, ask to
  "keep IDENTICAL letterforms/shape, ONLY brighten/saturate the fill + crisp the stroke + raise
  contrast". Redrawing the font is usually off-limits (brand).
- **Register a glow to its object** — do NOT `trim`+normalize the glow and object independently.
  The glow's bbox is larger (rays spread out), so normalizing both to the same width shrinks the
  glow's *core* below the object. Place the object, then place the glow at the SAME centre,
  scaled LARGER so its core matches; rays extend past it.
- **"Sparks" usually live in several layers at once** — the additive FX glow (cyan spark dots),
  the atmosphere layer (warm embers) AND baked into the background plate. REGENERATE each source
  clean ("no sparks, no specks, no floating particles"); do not mask them in post.
- **Don't crush light to kill sparks.** A periphery "darken warm bright pixels" hack also crushes
  legitimate torch/wall light to black. Fix the source layer; keep the composite grade clean.
