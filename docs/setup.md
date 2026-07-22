# Setup

## 1. API key

All remote flows use `OPENROUTER_KEY`: Gemini image generation, GPT-5.6 Luna
Pro image analysis and art audit, and video generation.

Put them in `~/.codex/.env` so both the TypeScript CLI and the Python scripts
pick them up automatically:

```
OPENROUTER_KEY=sk-or-...
```

The shell environment overrides the file. Get the key at:

- OpenRouter — https://openrouter.ai/keys

## 2. TypeScript runtime (art flow + CLI)

Bun is the only required runtime — no `npm install` needed because the script
only uses built-in `fetch` and `node:fs`.

```bash
# Install bun once (macOS):
brew install oven-sh/bun/bun
```

Verify:

```bash
bun --version
bun run tools/generate-image.ts --help
```

## 3. Python deps (Spine and local keying flows)

```bash
pip install -r scripts/requirements.txt
```

Verify:

```bash
python3 scripts/openrouter_image.py generate --help
```

## 4. Smoke test

```bash
# Art flow
bun run tools/generate-image.ts \
  --prompt "Tiny test icon, isolated, transparent" \
  --size 1K --output /tmp/test.png

# Python flow
python3 scripts/openrouter_image.py generate \
  --prompt "Tiny test icon" \
  --output /tmp/test-py.png --size 1K
```

If both files appear and are non-empty, the merge is wired up correctly.

For full-resolution transparency cleanup, generate on a controlled solid
background and use `scripts/chroma_key.py` or `scripts/key_flood.py` locally.
