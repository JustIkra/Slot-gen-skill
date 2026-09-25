# Provider routing

Art-direction and animation review use the installed BB `qwen-review` provider
with `qwen/qwen3.8-omni-flash`. Read the
[art-direction](../references/art-direction-review.md) or
[animation-loop](../references/animation-loop-review.md) route for the evidence
package and review criteria. The model's verdict is advisory; local checks and
the user's visual acceptance remain separate.

Qwen-Image-2.1 generation and editing use the [fal route](../workflows/art-generation.md#qwen-image-21-on-fal),
including native transparent PNG output. Other image and video generation
agents will be configured in a later stage. Legacy generation clients and job
records remain for migration and reconciliation; do not launch them for new
requests.
