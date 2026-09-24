# Animation loop review

Use this route when a slot Hero, Collector, symbol or FX idle needs motion critique.
It is an advisory visual review, not a Spine validator or production approval.

## Evidence package

- Keep the candidate and production comparison at matched scale, duration, playback speed
  and background. Show the candidate at its actual game size; a 64-px stress crop may be
  additional evidence, but its enlarged pixels are not the game-size design.
- Supply at least one full idle cycle and a view across the actual wrap. If the recording
  stops at the cycle end, provide the last and first frames plus a local frame-difference
  measurement; similarity between two sampled phases does not prove a duplicate or pause.
- Add lossless frames from the same runtime render when assessing banding, alpha, halo or
  flatness. Keep source/video compression and nearest-neighbor enlargement separate from
  asset defects. Record source paths, SHA-256 hashes, FPS, duration and sampled times.
- Keep idle separate from activation, win flashes and popups. Compare Hero and Collector
  as one material family while judging the miniature at native size.

## Qwen3.8 request

Use `qwen/qwen3.8-omni-flash` via OpenRouter chat completions and `OPENROUTER_KEY`.
Use the shared `slotgen_provider.http.request_bytes` client with the exact OpenRouter
origin. Put the fixed criteria in a text part first, then each labeled local MP4 as a
`video_url` Base64 data URL and each lossless PNG as an `image_url` Base64 data URL.
Request text output and stream usage. Set `max_completion_tokens` only when the user
specifies a limit; do not silently lower it or change the model/reference set.

Ask for observed surface flow, independent plasma/rim motion, brightness/contrast,
edge and glow, Hero–Collector consistency, native-size readability, and any visible
seam. Require a time, severity, visual evidence and minimal adjustment for each issue.
If the exact wrap or alpha source is not shown, the answer must say `not proven`, not
infer a defect from a similar composition or a dark montage panel.

Save the raw stream before parsing it. A valid report needs a nonempty answer, the
terminal `[DONE]`, `finish_reason: stop`, and no provider error/refusal. Preserve the
prompt, input hashes, returned model and usage in the task-local report. A 502,
truncated stream or partial answer is not a verdict; do not resubmit unchanged work
solely to obtain `APPROVED`.

Qwen3.8 missed a deliberately inserted two-second freeze in a controlled 256-px
Collector video. Therefore use local adjacent-frame and wrap metrics plus human
playback to decide whether the loop is seamless; the model can suggest what to inspect,
not certify continuity. Keep accepted source masters unchanged until the user chooses
an art direction.

API references: [OpenRouter Qwen3.8](https://openrouter.ai/qwen/qwen3.8-omni-flash/),
[video inputs](https://openrouter.ai/docs/guides/overview/multimodal/videos),
[chat completions](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion).
