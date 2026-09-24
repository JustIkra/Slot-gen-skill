---
name: slot-gen
description: >
  Use when generating or editing slot source artwork, symbols, backgrounds or video
  masters; preparing raster layers/transparency; or requesting AI visual-asset review.
  Promo composition/delivery belongs to slot-promo, source-based reel blur to
  slot-reel-blur, and Spine rigging/runtime integration to slot-spine-skin.
---

# Slot art and source assets

Prepare source artwork and review artifacts. Choose only the route needed by the request;
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
The BB review provider reads its credential on the host; never expose its value.

## Routes

| Request | Entry point | Result |
|---|---|---|
| Image, edit, variants | BB generation agent to be configured later | Bitmap master |
| Image-to-video | BB generation agent to be configured later | Video master |
| Opaque chroma subject | scripts/chroma_key.py | RGBA retaining original alpha |
| Soft light on black | scripts/key_light.py | Straight-alpha additive layer; canvas/particles retained |
| Solid-background logo | scripts/key_flood.py | Cropped largest-component cutout; not suitable for halos/particles |
| Color variants of coherent frames | scripts/recolor_lut.py | Consistent mapped palette |
| Generate separated character parts | BB generation agent to be configured later | Source parts for the Spine owner |
| Art-direction review | BB `qwen-review` agent with candidate and reference images | Saved BB thread plus task-local findings |
| Animation loop review | [animation loop review](references/animation-loop-review.md) | Qwen3.8 video/PNG critique with independent seam proof |

For art-direction review, read [art-direction review](references/art-direction-review.md).
For idle or miniature animation reviews, read the animation-loop reference before
sending media; still images do not prove temporal motion.

For a promo package, use `slot-promo` as workflow owner and return generated source
layers to it. For spin textures derived from existing symbols, use `slot-reel-blur`;
that local process does not require this skill, provider credentials or generation.

Generation models will be configured as BB agents in a later stage. The old direct-provider
generation clients remain in the repository for migration and existing job reconciliation,
but this skill does not launch new requests through them. When the user explicitly requests
Codex-native image generation/editing, use the imagegen skill/tool. Do not silently change
a requested model, resolution, reference set or token limit.

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

Preserve existing video job records for migration. An ambiguous legacy submission
requires reconciliation, not an automatic new paid task. Report provider errors
without credentials.
