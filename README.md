# Slot art tools

Source-art generation, video masters, raster processing and art-direction review.
Art-direction and animation review use the BB `qwen-review` provider.
Generation agents are planned for a later stage; legacy generation clients
remain in the repository for job reconciliation.

Read [SKILL.md](SKILL.md) for routing and [setup](docs/setup.md) for installation.
Promo composition and delivery now live in `slot-promo`; deterministic three-copy
spin textures live in `slot-reel-blur`. Those skills own their scripts and tests.
Provider keys never belong in command arguments, logs or Git.

Spine implementation lives in the sibling slot-spine-skin repository. Old command paths
here are compatibility imports, not another generator.

Tests: python -m unittest discover -s tests. Install the art extra and the sibling Spine
package when testing compatibility commands. Exact tested versions: requirements.lock.
