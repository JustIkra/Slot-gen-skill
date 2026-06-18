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
user-invocable: true
---

# Slot-Gen Skill

Single skill that ties together two flows:

| Flow             | Entry point                  | What it does                                                            |
|------------------|------------------------------|--------------------------------------------------------------------------|
| **Art**          | `workflows/art-generation.md` | Generate one-shot images (characters, icons, backgrounds, decorations). |
| **Spine**        | `workflows/spine-pipeline.md` | Take a character → deconstruct → rig → animate → preview.               |

Both flows share the same backend:

- **Image generation** — OpenRouter (`google/gemini-3.1-flash-image-preview` for
  Nano Banana 2, `google/gemini-3-pro-image-preview` for Pro). No direct Google API.
- **Background removal** — remove.bg (`https://api.remove.bg/v1.0/removebg`), or
  full-res `scripts/chroma_key.py` for UI assets (see gotchas).

## Gotchas (save yourself hours)

Battle-tested in a full production reskin — details in
`workflows/art-generation.md` → "Lessons from a full production reskin":

- **remove.bg free plan caps output to ~578×432** → blurry UI. For frames/
  buttons/logos generate on solid magenta `#FF00FF` (no `--remove-bg`) then
  `scripts/chroma_key.py`. Both clients now warn on the downscale. Never upscale.
- **`nano-banana-pro` rejects `4:1`/`8:1`/`1:4`/`1:8`** — use `nano-banana-2`
  for strips (the tool blocks this early with a clear error).
- **The GA image models dropped 4K.** `google/gemini-3-pro-image` /
  `gemini-3.1-flash-image` (the current GA aliases, best quality) max out at `--size 2K`;
  only the older `…-preview` snapshots accept `--size 4K` (live: HTTP 400 "image_size '4K'
  is not supported … Only …-preview… support 4K"). Use GA for the best 2K render; switch the
  alias to `-preview` only when you specifically need 4K.
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

## Temp working folder

Put all scratch (generated candidates, isolated parts, keyed frames, test renders, helper scripts) in
`./.tmp_<name>/` in the CURRENT/project directory — **never `/tmp`**. Repo-relative, reviewable, diffable
alongside the assets; `/tmp` is opaque and wiped.

## Required environment

API keys live in `~/.claude/.env` (or the shell environment):

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
│   ├── openrouter_image.py      # OpenRouter + remove.bg client used by Python
│   ├── chroma_key.py            # full-res bg removal via magenta key (beats remove.bg for UI)
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
