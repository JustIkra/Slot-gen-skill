# Video generation (image-to-video) via OpenRouter

For REAL coherent motion of a flat asset (a book opening, pages leafing, a lid lifting, a morph),
still-image generation fails — there is no temporal coherence between independent gens. Use OpenRouter's
video API to render a short clip, then (for slot work) slice it into a Spine attachment sequence
(see the `slot-spine-skin` skill → `references/video-to-sequence.md`).

## Endpoint

OpenRouter has a dedicated video API, separate from chat/images:

- `GET  https://openrouter.ai/api/v1/videos/models` — list video models + supported aspect ratios + pricing.
- `POST https://openrouter.ai/api/v1/videos` — submit a job → returns `{id, polling_url, status}`.
- Poll `polling_url` (Bearer `OPENROUTER_KEY`) until `status=="completed"` → download `unsigned_urls[0]`
  (Bearer auth for openrouter.ai URLs).

## Model choice

- **Square 1:1 symbols → `kwaivgi/kling-v3.0-std`** (also `-pro`), native 1:1, 720p, image-to-video, cheap
  (~$0.08/s). Seedance 2.0 and Wan 2.7 also do 1:1.
- **Google `google/veo-3.1`** is high quality but only `16:9` / `9:16` (no square) — you'd have to crop.
- Check `videos/models` for the current list before assuming.

## Request

```python
import base64, json, urllib.request
def durl(p): return "data:image/jpeg;base64," + base64.b64encode(open(p,"rb").read()).decode()
body = {
  "model": "kwaivgi/kling-v3.0-std",
  "prompt": "<describe the motion AND forbid the failure mode, e.g. 'pages flip, all stay ATTACHED, "
            "no flying leaves, STATIC camera, centered'>",
  "duration": 5, "resolution": "720p", "aspect_ratio": "1:1", "generate_audio": False,
  "frame_images": [
    {"type":"image_url","image_url":{"url":durl("first.jpg")},"frame_type":"first_frame"},
    {"type":"image_url","image_url":{"url":durl("last.jpg")},"frame_type":"last_frame"},  # optional, anchors the end
  ],
}
req = urllib.request.Request("https://openrouter.ai/api/v1/videos", data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+KEY, "Content-Type":"application/json"})
```

## Gotchas

- **Frame images = base64 data-URL.** OpenRouter docs: base64 is required for local/non-public files.
  Do NOT upload proprietary art to public file hosts (catbox/transfer.sh/0x0) — it's a data leak and the
  sandbox classifier blocks it. The data-URL goes only to OpenRouter (same trust boundary as image gen).
- **first_frame + last_frame** anchor start/end → controllable interpolation (closed book → chosen open pose).
- Prompt must forbid the failure mode (camera drift, parts flying off, flattening) or the model will do it.
- Generate the subject on flat **magenta** so the frames can be keyed afterwards. To keep baked glow/beams,
  chroma-key (magenta); for soft/paper subjects key extracted frames with **remove.bg** (chroma tears paper).
- Cost ~$0.4 for a 5 s 720p clip. It's a paid, outward generation — only run when the user asked for motion.
- `ffmpeg -i clip.mp4 f_%03d.png` numbers frames from 1. Sample by VISIBLE change, not raw pixel-diff.

Keys: `OPENROUTER_KEY` (video + images), `REMOVEBG_API_KEY` (frame keying) in `~/.codex/.env`.
