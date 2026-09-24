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

## BB Qwen3.8 review

Use the installed BB `qwen-review` provider with model
`qwen/qwen3.8-omni-flash`. Put the fixed criteria, media labels, native
display size, FPS, duration and source hashes in a task-local prompt file.
Attach the complete local MP4 with `--file` and lossless PNGs with `--image`.
Keep the final and first frames plus a local wrap metric in the evidence set.

```bash
bb thread spawn --project "$BB_PROJECT_ID" --environment "$BB_ENVIRONMENT_ID" \
  --parent-self --visibility hidden --provider qwen-review \
  --model qwen/qwen3.8-omni-flash --permission-mode accept-edits \
  --title "Animation loop review" --prompt-file /absolute/path/review-prompt.md \
  --file /absolute/path/cycle.mp4 --image /absolute/path/wrap-last.png \
  --image /absolute/path/wrap-first.png
```

Ask for observed surface flow, independent plasma/rim motion, brightness/contrast,
edge and glow, Hero–Collector consistency, native-size readability, and any visible
seam. Require a time, severity, visual evidence and minimal adjustment for each issue.
If the exact wrap or alpha source is not shown, the answer must say `not proven`.

Wait for `bb thread wait <id> --status idle` and inspect
`bb thread log <id> --all --json`. A successful BB turn with an inaccessible
video claim or partial frame coverage is an incomplete review. Save the thread ID,
prompt, source hashes, observed coverage and findings in the task-local report.
Do not resubmit unchanged work solely to obtain an approval.

Qwen3.8 missed a deliberately inserted two-second freeze in a controlled 256-px
Collector video. Therefore use local adjacent-frame and wrap metrics plus human
playback to decide whether the loop is seamless; the model can suggest what to inspect,
not certify continuity. Keep accepted source masters unchanged until the user chooses
an art direction.

Provider reference: [Qwen3.8 Omni Flash](https://openrouter.ai/qwen/qwen3.8-omni-flash/).
