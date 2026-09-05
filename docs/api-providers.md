# Provider contract

The shared implementation is src/slotgen_provider/openrouter.py. Python scripts and the
Bun frontend call this one implementation. It uses OpenRouter's chat-completions endpoint.

| Alias | Configured model | Role |
|---|---|---|
| nano-banana-2 | google/gemini-3.1-flash-image | Images |
| nano-banana-pro | google/gemini-3-pro-image | Images |
| vision | openai/gpt-5.6-luna-pro | Image analysis / art direction |

These are configured routes, not a claim that every future provider supports every option.
Current guards allow the configured 1K/2K path and reject unsupported strips for Pro and
4K before credentials/spend. Do not silently reduce resolution or swap models. Verify
official capabilities before changing aliases or guards.

Image requests accept multiple --reference-image flags; Python accepts reference_images.
--dry-run returns the exact payload without a remote request. --reasoning and --provider
are passed explicitly; the Bun --reasoning-trace flag maps to Python's
--reasoning-include-trace. --creative-variations requests the stated number of outputs.

Art direction:

    python scripts/art_director_review.py --images render.png reference.png --question "Assess the candidate against the reference" --out .tmp_review/audit.json

The report includes input hashes, prompt, model, completion status, coverage and verdict.
--max-tokens is optional and passed unchanged. Truncated, refused or empty responses fail;
a local validator checks the verdict structure even when a provider ignores JSON formatting.
AI acceptance does not replace human visual acceptance.

Image generation is synchronous: an ambiguous timeout must be reconciled before another
paid request. Video uses persistent jobs in slotgen_provider.video/jobs. See the video workflow.
No keys are stored in reports or job metadata. Authenticated requests use exact origins;
CDN downloads use no Authorization, public-address validation and checked redirects.

Reference: https://openrouter.ai/docs/guides/features/structured-outputs
