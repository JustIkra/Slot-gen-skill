# API providers

The slot-gen skill talks to exactly two upstream services. There is no other
provider matrix — that is the whole point of the merge.

## OpenRouter

Endpoint: `https://openrouter.ai/api/v1/chat/completions`

| Local model name | OpenRouter ID                              |
|------------------|--------------------------------------------|
| `nano-banana-2`  | `google/gemini-3.1-flash-image-preview`    |
| `nano-banana-pro`| `google/gemini-3-pro-image-preview`        |

Request shape (used by both `tools/generate-image.ts` and
`scripts/openrouter_image.py`):

```json
{
  "model": "google/gemini-3.1-flash-image-preview",
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

## remove.bg

Endpoint: `https://api.remove.bg/v1.0/removebg`

Multipart POST with `image_file` and `size` (`auto` default; `full`/`preview`
also accepted via `--remove-bg-size`). Header `X-Api-Key: $REMOVEBG_API_KEY`.
The response body is the cleaned PNG.

Used in three places:

1. `tools/generate-image.ts` — `--remove-bg` flag (art flow).
2. `scripts/openrouter_image.py remove-bg` — stand-alone Python CLI.
3. `scripts/split_character.py` — `--remove-bg-atlas` and `--remove-bg-parts`
   flags inside the Spine pipeline.

### ⚠ Resolution cap (read before using on UI assets)

On the **free / preview plan, remove.bg downscales every result to ~0.25 MP
(~578×432)** no matter what `size` you send — `size=full` returns
`402 / auth_failed` without a paid plan. This silently destroys frames, buttons,
logos and banners (you only notice when the upscaled asset looks soft in-game).

Both clients now **warn** when the output is much smaller than the input
(`tools/generate-image.ts` and `openrouter_image.py`). When you see that warning:

- **Full-res transparency without remove.bg** — generate the asset on a SOLID
  magenta (`#FF00FF`) background **without** `--remove-bg`, then key it at native
  resolution with `scripts/chroma_key.py` (key → erode → de-spill → optional
  downscale). Magenta is safe for gold/Egyptian art (nothing is magenta) and the
  keyer is tuned not to eat lapis-blue studs/panels. Then downscale to the target
  size — **never upscale past the source**.
- Subjects/characters (where remove.bg's matting is genuinely better than a flat
  key) on a paid plan: pass `--remove-bg-size full`.

## Cost / quota notes

- OpenRouter charges per image. Use `--size 1K` previews before final 2K/4K.
- remove.bg consumes one credit per call. The atlas cleanup is a single call;
  per-part cleanup multiplies by the number of body parts (typically 10–15).
- If quota is a concern, segment first, inspect, and only run remove.bg on the
  parts that need it (manual call to `openrouter_image.py remove-bg`).

## Known issues

- **`image_size: "0.5K"` is broken end-to-end.** OpenRouter advertises it as a
  supported value for `google/gemini-3.1-flash-image-preview`, but **both**
  Google providers (`google-ai-studio` AND `google-vertex/global`) reject it
  with `INVALID_ARGUMENT` from Google. Confirmed across all aspect ratios
  (1:1, 9:16, 16:9, 3:4, 4:3, 2:3) and with/without `reasoning` set.
  Not gated to a particular provider — broken at the model layer. Until Google
  ships the matching capability, `1K` is the minimum. Probed 2026-05-26.
