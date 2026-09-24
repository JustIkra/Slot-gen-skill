# Art generation workflow

Image generation and editing will move to BB generation agents after the
generation models are chosen. Do not launch the legacy direct-provider
generation scripts from this skill. Existing source artwork can still be
prepared locally with the transparency, recolor and validation routes in
`SKILL.md`.

For the later BB route, retain the task brief: target dimensions, aspect
ratio, palette, layer purpose, transparent or controlled-background output,
reference images and budget. Preserve one accepted master for derivatives.

## Prompt tips (carried over from /art)

- Avoid hex codes (`#1A8A9B` renders as text). Use color names.
- State direction explicitly: "LEFT TO RIGHT" or "TOP TO BOTTOM".
- Specify single label position (inside OR below, not both).
- For consistent sets, reuse the exact same size and aspect ratio.

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
