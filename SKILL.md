---
name: slot-gen
description: >
  Use when generating or editing slot artwork, symbols, backgrounds, promo images or
  video masters; preparing raster layers/transparency; or reviewing visual assets.
  Spine rigging and runtime integration belong to slot-spine-skin.
---

# Slot art and source assets

Produce source artwork and review artifacts. Choose only the route needed by the request;
an image task does not require a rig, game build, wrapper session or multi-agent team.

## Start

Read the target project's .memory-base/index.md and asset brief when present. Establish
output size, palette, intended layer use and references. Keep candidates, jobs and reviews
in ignored project-local .tmp_<task>/; do not overwrite accepted masters during exploration.

Use the Python environment where this repository is installed. From the repository:
    python -m pip install -e '.[art]'

For the shared workspace, the prepared interpreter is
/Users/maksim/MorningCat/.local/skills-venv/bin/python. Set PYTHON to that interpreter for
the Bun frontend. See [setup](docs/setup.md) when installing on another machine.
Provider credentials are environment variables or ~/.codex/.env; never expose their values.

## Routes

| Request | Entry point | Result |
|---|---|---|
| Image, edit, variants | scripts/openrouter_image.py generate; tools/generate-image.ts delegates to it | Bitmap master |
| Image-to-video | scripts/gen_video.py | Video + persistent job record |
| Opaque chroma subject | scripts/chroma_key.py | RGBA retaining original alpha |
| Soft light on black | scripts/key_light.py | Straight-alpha additive layer; canvas/particles retained |
| Solid-background logo | scripts/key_flood.py | Cropped largest-component cutout; not suitable for halos/particles |
| Color variants of coherent frames | scripts/recolor_lut.py | Consistent mapped palette |
| Generate separated character parts | scripts/split_character.py | Source parts for the Spine owner |
| Art-direction review | scripts/art_director_review.py --images ... --question ... --out <report.json> | Structured review with inputs/coverage |
| Promo composition | [promo workflow](workflows/promo-composition.md) | Composition evaluated against the brief |

Use --help for command arguments; --dry-run prints an image request without spending.
When the user requests Codex-native image generation/editing, use the imagegen skill/tool.
For the established OpenRouter route use the client, not hand-built authenticated requests.
Configured model aliases and response handling live in [provider notes](docs/api-providers.md).
Do not silently change a requested model, resolution, reference set or token limit.

## Visual decisions

- Keep the subject silhouette original: use a style-only anchor when a competitor's
  contact sheet would encourage copying its target objects. Keep the original for comparison,
  not as a direct generation target.
- Choose chroma by subject color; use green for purple/magenta subjects. Soft light needs
  its own extraction route, not the opaque-body erosion recipe.
- Preserve a common canvas for registered layers/sequences. Do not crop frames independently
  or upscale unless explicitly requested.
- Derive alternate light states from one master. Independent frame generations are not
  a temporally coherent animation.
- Compare at intended display size over actual light/dark backgrounds. Check spelling,
  contour, spill, clipped glow, missing small elements and consistency across the set.
- AI scores are advisory. Fix a reference set and criteria; an incomplete response is not
  ACCEPT. Preserve the user's max-token limit. Do not repeatedly submit unchanged work
  solely to obtain a passing verdict.

## Completion and failures

Deliver master paths, review artifacts and known limitations. Asset-only delivery does not
authorize integration. For rigging/packing, hand the accepted layers to slot-spine-skin;
for a real-game screenshot use zephyr-launcher-session.

Video jobs support submit/resume/download/auto. Resume the same job after interruption;
submission_unknown requires reconciliation, not an automatic new paid task. Report provider
errors without credentials. Validate provider API changes before updating the client.

Third-party source terms remain in THIRD_PARTY_NOTICES.md and licenses/.
