# Spine animation pipeline

Turn a single character image into a fully animated Spine character — every step
backed by OpenRouter (image gen) and optionally remove.bg.

## Prerequisites

```bash
pip install -r scripts/requirements.txt
# Set in shell or in ~/.codex/.env:
#   OPENROUTER_KEY=...
#   REMOVEBG_API_KEY=...
```

## Inputs (pick one)

| Input                                       | Start from   |
|---------------------------------------------|--------------|
| Full character image only                   | Step 1       |
| Separated body-part PNGs + reference image  | Step 2       |
| Separated body-part PNGs alone              | Step 3       |
| Existing Spine JSON                         | Step 4       |

## Step 1 — Deconstruct character into parts

```bash
python3 scripts/split_character.py character.png \
  --output-dir parts/ \
  --atlas-out atlas.png \
  --remove-bg-parts
```

- `--remove-bg-atlas` cleans the AI-generated atlas before segmentation.
- `--remove-bg-parts` cleans each segmented PNG (recommended for clean alpha).
- Uses OpenRouter (`google/gemini-3.1-flash-image-preview` by default) under the
  hood — no Google API key required.

## Step 2 — Auto-position parts against the reference

```bash
python3 scripts/position_parts.py \
  --reference character.png \
  --parts parts/ \
  --output layout.json \
  --debug debug/
```

SIFT + RANSAC similarity transform. Inspect `debug/comparison.png` to verify.

## Step 3 — Build the Spine skeleton and animations

Write a `config.json` describing bones, slots, attachments, and which animations
to generate, then run:

```bash
python3 scripts/build_spine_json.py \
  --config config.json \
  --output skeleton.json
```

Built-in presets: `idle`, `walk`, `run`, `wave`, `jump`, `attack`. Custom
animations can be embedded via `custom_animations` in the config.

The generator emits Spine 4.2 JSON. A rotate bezier has four numbers; a
translate/scale bezier has eight numbers because Spine 4.2 stores four control
values per animated channel. Validate production output with the exact installed
4.2 parser rather than accepting only a matching `skeleton.spine` string.

## Step 4 — Pack the texture atlas

```bash
python3 scripts/make_atlas.py \
  --parts parts/ \
  --output ./out \
  --name slot-character
```

Outputs `slot-character.png` + `slot-character.atlas`.

## Step 5 — Generate a stand-alone preview

```bash
python3 scripts/generate_spine_player.py \
  --skeleton ./out/skeleton.json \
  --atlas ./out/slot-character.atlas \
  --atlas-image ./out/slot-character.png \
  --output ./out/preview.html
```

Open `out/preview.html` in a browser — official Spine Web Player, fully embedded.

## Urso/Zephyr production integration

Before copying an asset into a game, inspect that game's `package.json`,
`package-lock.json`, and installed package source. The current production profile
is exact `@zephyr/slot-base 0.11.2`, transitive Pixi 8, exact overridden
`@esotericsoftware/spine-pixi-v8 4.2.119`, and Spine 4.2 JSON. Pack shared runtime
textures with the Urso Texture Builder; use a dedicated Spine atlas only when the
game's current loader contract explicitly requires one.

## Quick end-to-end recipe

```bash
# 1. Deconstruct
python3 scripts/split_character.py ./input/character.png \
  --output-dir ./work/parts --atlas-out ./work/atlas.png --remove-bg-parts

# 2. Position
python3 scripts/position_parts.py \
  --reference ./input/character.png \
  --parts ./work/parts \
  --output ./work/layout.json

# 3. Build skeleton (config.json built from layout.json — see references)
python3 scripts/build_spine_json.py --config ./work/config.json \
  --output ./out/skeleton.json

# 4. Pack atlas
python3 scripts/make_atlas.py --parts ./work/parts \
  --output ./out --name slot-character

# 5. Preview
python3 scripts/generate_spine_player.py \
  --skeleton ./out/skeleton.json \
  --atlas ./out/slot-character.atlas \
  --atlas-image ./out/slot-character.png \
  --output ./out/preview.html
```
