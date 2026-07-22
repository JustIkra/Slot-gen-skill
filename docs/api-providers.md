# API providers

The slot-gen skill uses OpenRouter as its only upstream API provider.

## OpenRouter

Endpoint: `https://openrouter.ai/api/v1/chat/completions`

| Local model name | OpenRouter ID                       | Purpose |
|------------------|-------------------------------------|---------|
| `nano-banana-2`  | `google/gemini-3.1-flash-image`     | Image generation |
| `nano-banana-pro`| `google/gemini-3-pro-image`         | Image generation |
| `vision`         | `openai/gpt-5.6-luna-pro`           | All image analysis and critique |

Request shape (used by both `tools/generate-image.ts` and
`scripts/openrouter_image.py`):

```json
{
  "model": "google/gemini-3.1-flash-image",
  "messages": [{ "role": "user", "content": [
    { "type": "image_url", "image_url": { "url": "data:image/png;base64,..." } },
    { "type": "text", "text": "<prompt>" }
  ]}],
  "modalities": ["image", "text"],
  "stream": false,
  "image_config": { "aspect_ratio": "1:1", "image_size": "2K" }
}
```

Auth header: `Authorization: Bearer $OPENROUTER_KEY`.

The result image lives at `choices[0].message.images[0].image_url.url` as a
`data:image/png;base64,...` URI. The clients handle both that shape and the
fallback where the image is delivered inside `message.content[].image_url.url`.

### Reasoning (Gemini thinking) via OpenRouter

`reasoning.effort` IS pass-through-supported by OpenRouter on both Google
providers (`google-ai-studio` and `google-vertex/global`) — confirmed by
endpoint metadata (`reasoning, include_reasoning` in `supported_parameters`)
and by live calls returning non-zero `usage.completion_tokens_details.reasoning_tokens`.

Levels: `minimal | low | medium | high | xhigh | none` (OpenAI-style ladder),
mapped to Gemini's native `thinkingConfig.thinkingLevel`.

Both clients expose this:

```bash
bun run tools/generate-image.ts \
  --prompt "..." --size 2K --reasoning high \
  --output ./out/image.png
```

```python
from openrouter_image import generate_image
generate_image(prompt="...", output="image.png",
               size="2K", reasoning_effort="high")
```

Cost: each step on the effort ladder adds reasoning_tokens to billing. In our
measurements `high` added ~1500 tokens (~$0.005) on top of a 2K NB2 image.

### Trade-offs vs direct Google Gemini

Lost vs the original `/art` skill:

- `--grounded` (web search grounding) — Google-only feature, OpenRouter does
  not expose it. Kept dropped.

Kept:

- Reference image input.
- Aspect ratio + size selection.
- Creative variations (`-v1`, `-v2`, ...).
- Transparency prompt prefix.
- **Reasoning / thinking** (added back after verification).
- **Provider routing** — `provider: { only: [...] }` to pin Vertex vs AI Studio.

### Art-direction audit

`scripts/art_director_review.py` sends one or more images and an optional
assembler script to GPT-5.6 Luna Pro. Every image-analysis path, including
technical body-part detection, is fixed to `openai/gpt-5.6-luna-pro`; the CLIs
do not expose a vision-model override. Gemini models are used only for image
generation.

### Local transparency cleanup

Transparency post-processing stays at source resolution and does not call a
remote cleanup provider:

- `scripts/chroma_key.py` removes a controlled solid chroma background with
  erosion, de-spill, optional trimming, and optional downscaling.
- `scripts/key_flood.py` flood-fills solid black or white backgrounds and keeps
  the largest connected foreground component.
- Native alpha can be used directly when the generator returns clean edges.

## Cost / quota notes

- OpenRouter charges per image. Use `--size 1K` previews before final 2K/4K.
- GPT-5.6 Luna Pro art audit is token-billed. Review a labelled contact sheet
  instead of many individual images when auditing a large promo set.

## Known issues

- **`image_size: "0.5K"` is broken end-to-end.** OpenRouter advertises it as a
  supported value for `google/gemini-3.1-flash-image-preview`, but **both**
  Google providers (`google-ai-studio` AND `google-vertex/global`) reject it
  with `INVALID_ARGUMENT` from Google. Confirmed across all aspect ratios
  (1:1, 9:16, 16:9, 3:4, 4:3, 2:3) and with/without `reasoning` set.
  Not gated to a particular provider — broken at the model layer. Until Google
  ships the matching capability, `1K` is the minimum. Probed 2026-05-26.
