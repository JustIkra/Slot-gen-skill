# Art generation workflow

Qwen-Image-2.1 generation and editing are available through fal. Other models
will move to BB generation agents after they are chosen. Do not launch the
legacy direct-provider generation scripts from this skill. Existing source
artwork can still be prepared locally with the transparency, recolor and
validation routes in `SKILL.md`.

For any generation route, retain the task brief: target dimensions, aspect
ratio, palette, layer purpose, transparent or controlled-background output,
reference images and budget. Preserve one accepted master for derivatives.

## Qwen-Image-2.1 on fal

Use this route when the user selects Qwen-Image-2.1 or wants to try its native
transparent output. The fal model IDs are `fal-ai/qwen-image-2.1` for generation
and `fal-ai/qwen-image-2.1/edit` for editing. Load `FAL_KEY` from
`~/.codex/.env` in the same shell invocation; never print the key. Send JSON to
`https://fal.run/<model-id>` with `Authorization: Key <FAL_KEY>` or use the fal
client. For edits, pass ordered reference URLs in `image_urls` (up to 10).
Preserve the requested aspect ratio and output dimensions using the model's
supported `image_size` values or custom width and height.

For a transparent subject, request `output_format: "png"` and state in the prompt:
"This is an RGBA image with transparency. The image has an alpha channel and
the background is transparent." `prompt_expander: "none"` keeps that instruction
verbatim. Native transparency does not require a separate mask or chroma key.
Inspect the saved PNG's alpha channel and composite it over light and dark
backgrounds; check faint spill and edge halos before accepting it. If the
alpha is missing or the edges are poor, revise the prompt or regenerate.

Check the current rate through fal's
[`/v1/models/pricing`](https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai%2Fqwen-image-2.1)
before a batch; both endpoints were billed per compute second when checked on
2026-09-25. See the [model card](https://huggingface.co/Qwen/Qwen-Image-2.1)
and fal [generation](https://fal.ai/models/fal-ai/qwen-image-2.1/api) and
[editing](https://fal.ai/models/fal-ai/qwen-image-2.1/edit/api) schemas.

## Prompt tips (carried over from /art)

- Avoid hex codes (`#1A8A9B` renders as text). Use color names.
- State direction explicitly: "LEFT TO RIGHT" or "TOP TO BOTTOM".
- Specify single label position (inside OR below, not both).
- For consistent sets, reuse the exact same size and aspect ratio.

## Examples from a production reskin

These examples are conditional on the brief, not a universal theme or mandatory recipe.

### Transparency / quality
- When Qwen-Image-2.1's native RGBA output fits the brief, try it first and
  verify the alpha against both light and dark backgrounds.
- For models without usable native alpha, generate frames, buttons, banners,
  and logos on a **solid magenta
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
- Check the selected BB generation model's supported ratios before asking for
  extreme strips such as `4:1` or `8:1`; preserve the requested aspect ratio.

### Text & logos
- AI text breaks at wide aspect: at `8:1` it duplicates/misspells
  ("BOCK", "ABYDOS AYDOS"). Keep titles to **≤4:1**, one word per generation,
  and **eyeball the spelling** every time — regenerate on any defect.
- For matching word/light style across a multi-word logo, generate one word as
  the anchor, then use it as a reference for the rest ("match this
  material and LIGHTING exactly").
- For guaranteed-correct short text where AI keeps failing, render with PIL +
  a bold font (e.g. macOS Copperplate) and a gold gradient — crisp and correct,
  if less flashy than AI 3D.

### Consistent sets (symbols, buttons, frames)
- Generate an **anchor** first, then use it as a reference for the rest so the
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
