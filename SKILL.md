---
name: slot-gen
description: >
  Unified slot-machine character pipeline that merges the /art and /spine-animation
  skills behind a single backend — OpenRouter for image generation (Nano Banana 2 /
  Nano Banana Pro) and remove.bg for background removal. Use this skill whenever the
  user wants to (a) generate static character/icon/background art, (b) deconstruct a
  character image into separated body-part PNGs, (c) auto-position parts against a
  reference, (d) build a Spine 2D skeleton with idle/walk/run/wave/jump/attack
  animations, or (e) produce an interactive Spine Web Player preview. Triggers on
  "slot character", "generate art", "create asset", "spine animation", "rig this
  character", "make this walk", "split into body parts", "deconstruct sprite",
  "background remove", and similar phrases.
---

# Slot-Gen Skill

Single skill that ties together two flows:

| Flow             | Entry point                  | What it does                                                            |
|------------------|------------------------------|--------------------------------------------------------------------------|
| **Art**          | `workflows/art-generation.md` | Generate one-shot images (characters, icons, backgrounds, decorations). |
| **Spine**        | `workflows/spine-pipeline.md` | Take a character → deconstruct → rig → animate → preview.               |

Both flows share the same backend:

- **Image generation** — OpenRouter, GA-stable models: `google/gemini-3.1-flash-image`
  (Nano Banana 2) and `google/gemini-3-pro-image` (Pro). No direct Google API.
  GA caps at **2K**; `4K` returns HTTP 400 — only the older `…-image-preview` snapshots
  support 4K, so switch to those aliases only when you specifically need 4K.
- **Background removal** — remove.bg (`https://api.remove.bg/v1.0/removebg`), or
  full-res `scripts/chroma_key.py` for UI assets (see gotchas).

## Production runtime contract

For current Urso/Zephyr slot work, inspect the target game's `package.json`,
`package-lock.json`, and installed package source before authoring or integrating
runtime assets. The supported production profile is:

- exact direct `@zephyr/slot-base 0.11.2`;
- Pixi 8 supplied transitively by Zephyr/Urso;
- exact overridden `@esotericsoftware/spine-pixi-v8 4.2.119`;
- Spine 4.2 JSON and matching 4.2 preview/parser tooling;
- Urso Texture Builder for production PNG/WebP atlases and quality variants.

Do not add a second direct Pixi, Urso, or Spine runtime dependency. Do not copy
runtime recipes from another game: when an existing game resolves a different
tree, follow that game's packages and installed source instead of keeping a
separate old-version recipe in this skill.

The package files and installed source are the sole source of truth for runtime
APIs and build commands. Documentation is intentionally version-scoped to the
profile above; do not maintain legacy Pixi/Spine/Urso instructions here. Before
running an asset command, use the target package's `scripts` (and its installed
Texture Builder entry point) rather than assuming a command copied from another
project.

## Gotchas (save yourself hours)

Battle-tested in a full production reskin — details in
`workflows/art-generation.md` → "Lessons from a full production reskin":

- **remove.bg free plan caps output to ~578×432** → blurry UI. For frames/
  buttons/logos generate on solid magenta `#FF00FF` (no `--remove-bg`) then
  `scripts/chroma_key.py`. Both clients now warn on the downscale. Never upscale.
- **`nano-banana-pro` rejects `4:1`/`8:1`/`1:4`/`1:8`** — use `nano-banana-2`
  for strips (the tool blocks this early with a clear error).
- **`nano-banana-pro` + `--reference-image` intermittently returns "OpenRouter response contained
  no image data"** (the model "thinks" but emits no image — `reasoning_tokens>0`, exit 1). It is
  transient: **wrap the call in a 2–3× retry loop** (usually succeeds on retry 2), fall back to
  `nano-banana-2`. `--size 2K` fails this way more than `1K`; a ≤400 px cut needs only `1K`, so
  prefer `1K` for cuts/edits. Pure-text gens (no reference) rarely hit this.
- **AI text breaks past ~4:1** (dupes/misspells) — one word per gen, verify
  spelling, anchor + `--reference-image` to keep a logo's words consistent.
- **Re-theme animation frames with `scripts/recolor_lut.py`**, never regenerate
  them (no temporal coherence).
- **Pick the keying background by content LUMINANCE, not always magenta.** Magenta+chroma is right
  for opaque UI parts, but it tears soft light/glow. Rule: **light/glowing content → generate on
  pure BLACK and key by luminance** (dark→transparent, brightness→alpha; a saturation floor keeps
  the coloured solid opaque); **dark content → light background**. Otherwise the bg can't be cleanly
  separated and soft edges/glow are destroyed. (A glowing pyramid keyed off black preserved its burst
  as graded alpha; magenta would have ragged it.)
- **For a generated BACKGROUND panel:** generate via Gemini (not a flat procedural gradient) — give a
  sibling symbol's bg as a STYLE `--reference-image` but produce a FRESH image; keep it darker/uniform
  for contrast with the subject; mask to the window rounded-rect. When unsure of direction, batch 3–4
  distinct options and composite each behind the symbol for an A/B/C/D pick instead of regenerating blind.
- **Derive a "calm" variant FROM the "lit" one** (remove the glow), never generate them independently —
  identical subject+bg, only the effect differs (critical for video anchors; see slot-spine-skin).
- **Elements look like flat stickers "behind a film"? It's the COMPOSITING, not the assets.** Stop
  stacking `screen` glow + 2D drop-shadows + 360° rim. Use the physical-light recipe in
  `workflows/promo-composition.md` → "Compositing layers so elements DETACH": vignette baked into the
  bg (not over the flatten), MULTIPLY cast shadows masked to the receiver, light-wrap (bg bleeds onto
  rim) instead of a dark halo, directional rim (alpha-shift, not MaxFilter), color-DODGE local glow
  instead of screen-milk. One refactor took a murky 1:1 master to real depth.
- **`nano-banana-pro` also fails as a washed-out foggy smear** (not just "no image data") — retry;
  detect with `black_frac=(rgb.min(2)<25).mean()` (proper black-bg ≳0.5) and `rgb.mean()` (foggy ≳150).
- **Bake light onto a bg at the foreground's positions** by passing TWO refs (current bg + final promo)
  in one gen call — POST the payload with two `image_url` parts yourself (`generate_image` takes one).
- **Vision model as art director** (`query_image` with render+layers+script): the score is
  frame-of-reference dependent (same file 9.5 vs 4 in one session) — pin the comparison set and judge
  against YOUR studio's own released promo, not just tier-1 competitors. See promo-composition.md.
- **Reviewing a whole promo SET? send ONE labelled contact sheet, not N images.** ~33 separate images
  overflow the vision model → it spends the budget on reasoning and returns empty text. Tile them
  (6×6, captioned `#n WxH`) into one image; it then critiques the set as a set.
- **Paytable symbol blur for slot wrappers:** use exactly **3 visual layers** (`top > core > bottom`),
  not Gaussian blur and not many ghost copies. Proven 8/10 recipe: source `wrapper/paytable/symbols`,
  output `src/assets/images/opt/symbols/blur`; symmetric vertical motion blur radius `20`; top layer
  requested `-20px` with crop-safe offset, opacity `60%`; bottom `+20px`, opacity `60%`; core opacity
  `90%`; core center `70% original + 30% neutral-color blur`; blur color correction `color 1.00`,
  `brightness 1.00`, `contrast 1.00`. Blur the core rim by **distance to alpha edge** while preserving
  original alpha, so frames/rims soften by shape instead of leaving a hard top edge or dark bands.
  Validate against the game's own reference blur with one labelled contact sheet and Gemini/OpenRouter
  vision review; target score ≥7/10 before copying into `opt/symbols/blur`.
- **Build ALL promo sizes from ONE parametric assembler**, not a canvas per size: a `layout(ar)` that
  buckets by aspect ratio (beside ≥2.3 · centered ≈2:1 · stack portrait/square/landscape) feeding a
  canvas-agnostic `build()`. Glow radii in px from the placed monument height so circles stay round.
- **The bg vignette must NEVER dim the foreground.** Off-center monuments (beside/centered) look dim
  because `light_wrap` samples the *vignetted* bg — feed it a separate NON-vignetted bright bg copy,
  and add an isolated tight backlight bloom behind the ring. Don't move/widen the vignette to fake it.
- **Metal specular = SCREEN warm `(255,215,120)`, never DODGE white** — dodge+white+low-threshold
  blows gold to molten "lava". And the `255*power(.,1/1.06)` final gamma-lift in `flatten()` is the
  "milky/behind-a-film" culprit — delete it; carry contrast with `(base-128)*1.10`.
- **Re-skinning a magenta key asset via gen:** forbid baked radial light/glow/halo (it contaminates
  the chroma key) — "ONLY texture + flat #FF00FF"; pass the raw un-keyed master render as a 2nd ref
  so the re-skin matches scene light. See promo-composition.md.

## Temp working folder

Put all scratch (generated candidates, isolated parts, keyed frames, test renders, helper scripts) in
`./.tmp_<name>/` in the CURRENT/project directory — **never `/tmp`**. Repo-relative, reviewable, diffable
alongside the assets; `/tmp` is opaque and wiped.

## Required environment

API keys live in `~/.codex/.env` (or the shell environment):

```
OPENROUTER_KEY=sk-or-...
REMOVEBG_API_KEY=...
```

If either is missing, the skill stops with a clear error before any spend.

## Layout

```
.
├── SKILL.md
├── README.md
├── tools/
│   ├── generate-image.ts        # OpenRouter + remove.bg CLI (TypeScript, bun)
│   ├── package.json
│   └── tsconfig.json
├── scripts/                      # Python pipeline
│   ├── openrouter_image.py      # OpenRouter + remove.bg client (generate_image takes reference_images=[...] for multi-ref)
│   ├── chroma_key.py            # full-res bg removal via magenta key (beats remove.bg for UI)
│   ├── key_flood.py             # full-res key a logo off solid white/black bg (flood-fill + keep largest CC → drops sparks)
│   ├── promo_compositor.py      # physical-light compositing primitives (light_wrap, cast_shadow_mul, directional_rim, multiply/dodge flatten)
│   ├── art_director_review.py   # send render+layers(+script)+refs to a vision model for an art-director critique
│   ├── recolor_lut.py           # re-theme images/animation frames by luminance→gradient
│   ├── split_character.py       # character → deconstructed atlas → part PNGs
│   ├── position_parts.py        # SIFT + RANSAC auto-positioning
│   ├── build_spine_json.py      # Spine 4.2 skeleton + animation generator
│   ├── make_atlas.py            # Pack parts → Spine .atlas + .png
│   ├── generate_spine_player.py # Self-contained Spine Web Player HTML
│   └── requirements.txt
├── workflows/
│   ├── art-generation.md
│   ├── promo-composition.md     # numeric composition rules for promo/lobby thumbnails
│   └── spine-pipeline.md
└── docs/
    ├── setup.md
    └── api-providers.md
```

## Decision tree

```
User asks for…

├─ "Generate an image / icon / background"           → workflows/art-generation.md
├─ "Remove background from <file>"                   → tools/generate-image.ts --remove-bg
├─ "Full-res frame / button / logo (no quality loss)"→ generate on magenta bg, then scripts/chroma_key.py
├─ "Re-theme / recolor an asset or animation set"    → scripts/recolor_lut.py
├─ "Create paytable symbol blur / opt symbols blur"  → use the 3-layer paytable blur recipe in Gotchas
├─ "Split this character into body parts"            → scripts/split_character.py
├─ "Position these parts against a reference"        → scripts/position_parts.py
├─ "Build a Spine skeleton + animations"             → scripts/build_spine_json.py
├─ "Pack parts into a Spine atlas"                   → scripts/make_atlas.py
├─ "Give me an HTML preview of this Spine character" → scripts/generate_spine_player.py
├─ "Animate a symbol opening/morphing (real motion)" → workflows/video-generation.md (image-to-video)
├─ "Promo / lobby thumbnail / store icon / key art"  → workflows/promo-composition.md (composition rules)
└─ Full pipeline (image → animation)                 → workflows/spine-pipeline.md
```

## How to invoke the image generator

From any shell / Bash tool:

```bash
bun run tools/generate-image.ts \
  --prompt "Cartoon slot machine wild symbol, neon, transparent background" \
  --size 2K --aspect-ratio 1:1 \
  --output ./out/wild.png \
  --remove-bg
```

From Python (used by the Spine pipeline):

```python
from openrouter_image import generate_image, remove_background

generate_image(
    prompt="Sprite sheet of body parts …",
    output="atlas.png",
    size="2K",
    aspect_ratio="1:1",
    reference_image="character.png",
)
remove_background("atlas.png", overwrite=True)
```

## Notes on the merge

This skill intentionally **replaces** the original `/art` and `/spine-animation`
backends:

- `/art` used `@google/genai` directly. Here we drop the Google-direct path; both
  Nano Banana 2 and Pro are reached through OpenRouter only.
- `/spine-animation` used `google.genai` from Python inside `split_character.py`.
  That call is now routed through `scripts/openrouter_image.py`, so a single
  `OPENROUTER_KEY` covers both flows.
- `remove.bg` was an optional `--remove-bg` flag in `/art`. Here it is a
  first-class step exposed to both flows (TS CLI flag + Python helper).

Read `docs/setup.md` before the first run.
