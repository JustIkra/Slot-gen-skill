# slot-gen-skill

Codex skill that fuses static-art, art-direction audit, image-to-video, and
Spine 4.2 animation workflows behind one unified OpenRouter backend:

- **OpenRouter** for all image generation (Nano Banana 2 / Pro).
- **GPT-5.6 Luna Pro** for every image-analysis and art-direction query.
- **Local full-resolution keying** for transparency cleanup.

A single `OPENROUTER_KEY` covers image generation, technical vision, art audit,
and the Spine deconstruct/rig/animate pipeline.

## Quick start

```bash
# 1. API key
echo 'OPENROUTER_KEY=sk-or-...'   >> ~/.codex/.env

# 2. Deps
brew install oven-sh/bun/bun
pip install -r scripts/requirements.txt

# 3. Art flow
bun run tools/generate-image.ts \
  --prompt "Cartoon slot wild symbol on a solid magenta background" --size 2K --aspect-ratio 1:1 \
  --output ./out/wild-raw.png

python3 scripts/chroma_key.py \
  --input ./out/wild-raw.png --output ./out/wild.png

# 4. Spine flow
python3 scripts/split_character.py ./input/character.png \
  --output-dir ./work/parts --atlas-out ./work/atlas.png
```

Read `SKILL.md` for the full routing and `docs/` for setup + provider notes.

For production Urso/Zephyr integration, the default profile is
`@zephyr/slot-base 0.11.2`, Pixi 8, Spine 4.2, and exact
`@esotericsoftware/spine-pixi-v8 4.2.119`. Confirm the target game's
`package.json` and `package-lock.json` before using it, then pack runtime images
through the Urso Texture Builder.

## Current contract

- OpenRouter image generation with reproducible TypeScript and Python clients.
- GPT-5.6 Luna Pro for art audit and technical image analysis.
- Local full-resolution chroma and flood-fill keying.
- Spine 4.2 deconstruction, positioning, skeleton generation, atlas packing,
  animation presets, and standalone preview.
- Urso/Zephyr runtime guidance and production promo-composition workflows.
