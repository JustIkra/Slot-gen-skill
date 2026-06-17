# slot-gen-skill

Claude Code skill that fuses the `/art` and `/spine-animation` skills behind one
unified backend:

- **OpenRouter** for all image generation (Nano Banana 2 / Pro).
- **remove.bg** for background removal.

No direct Google Gemini calls anywhere — a single `OPENROUTER_KEY` covers both
the static-art flow and the Spine deconstruct/rig/animate pipeline.

## Quick start

```bash
# 1. API keys
echo 'OPENROUTER_KEY=sk-or-...'   >> ~/.claude/.env
echo 'REMOVEBG_API_KEY=...'        >> ~/.claude/.env

# 2. Deps
brew install oven-sh/bun/bun
pip install -r scripts/requirements.txt

# 3. Art flow
bun run tools/generate-image.ts \
  --prompt "Cartoon slot wild symbol" --size 2K --aspect-ratio 1:1 \
  --output ./out/wild.png --remove-bg

# 4. Spine flow
python3 scripts/split_character.py ./input/character.png \
  --output-dir ./work/parts --atlas-out ./work/atlas.png --remove-bg-parts
```

Read `SKILL.md` for the full routing and `docs/` for setup + provider notes.

## Status

Initial scaffold (2026-05-26):

- ✅ Unified OpenRouter + remove.bg backend (`tools/generate-image.ts` and
  `scripts/openrouter_image.py`)
- ✅ Spine scripts copied from upstream (`position_parts`, `build_spine_json`,
  `make_atlas`, `generate_spine_player`)
- ✅ `split_character.py` rewritten to use OpenRouter instead of Gemini direct
- ⏭ Next: smoke tests with real API keys, then any slot-machine specific
  workflows (reel layouts, paytable graphics, etc.)
