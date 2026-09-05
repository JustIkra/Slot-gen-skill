# Slot art tools

Source-art generation, video masters, raster processing and art-direction review.
The Python package owns the shared OpenRouter transport; the Bun CLI delegates to it.

Read [SKILL.md](SKILL.md) for routing and [setup](docs/setup.md) for installation.
Use --dry-run for an offline request check. Provider keys never belong in command
arguments, logs or Git.

Spine implementation lives in the sibling slot-spine-skin repository. Old command paths
here are compatibility imports, not another generator. Source attribution and inherited
terms are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Tests: python -m unittest discover -s tests. Install the art extra and the sibling Spine
package when testing compatibility commands. Exact tested versions: requirements.lock.
