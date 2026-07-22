# Slot-Gen Spine 4.2 and Luna Art Audit Cleanup

## Goal

Make `slot-gen` internally consistent with the current production stack:

- Spine 4.2 is the only supported Spine format.
- Background removal uses local full-resolution keying only.
- Art-direction audits use OpenAI GPT-5.6 Luna Pro through OpenRouter.

## Scope

### Spine 4.2 only

Delete the legacy `reference/characters_nick.json`, `.atlas`, and `.png` assets because the JSON targets Spine 3.8. Remove every remaining 3.8 reference from executable code and active documentation. Preserve and clarify the existing Spine 4.2 runtime contract for Urso/Zephyr.

### Remove remove.bg completely

Delete the remove.bg HTTP client, CLI flags, API-key loading, Python imports, examples, setup instructions, provider documentation, and workflow guidance. Remove `REMOVEBG_API_KEY` from the skill contract.

Use these local replacements:

- `scripts/chroma_key.py` for opaque assets generated on a controlled solid chroma background.
- `scripts/key_flood.py` for assets generated on solid black or white backgrounds.
- Native alpha from the image generator when it is reliable and preserves source resolution.

`detect_parts.py` and `split_character.py` must start successfully and expose truthful `--help` output after the cleanup.

### GPT-5.6 Luna Pro art audit

Route art-direction review through the existing OpenRouter client using model ID `openai/gpt-5.6-luna-pro` and `OPENROUTER_KEY`. Update `scripts/art_director_review.py`, the vision-model registry, `SKILL.md`, workflows, and provider documentation so GPT-5.6 Luna Pro is the named art-audit model.

Gemini vision models may remain only for non-audit technical operations such as body-part detection. No direct OpenAI client or `OPENAI_API_KEY` is introduced.

## Compatibility and error handling

- Keep the existing OpenRouter chat-completions transport and base64 image payload format.
- Keep image generation on the existing Nano Banana model path; this change affects art critique, not art generation.
- Validate model aliases before network calls and fail with the existing `OpenRouterError` style.
- Do not perform a paid live API request as part of automated verification.

## Documentation contract

Synchronize `SKILL.md`, `README.md`, `docs/setup.md`, `docs/api-providers.md`, and all affected workflows with the executable behavior. The documented repository tree must include the active video workflow and relevant Spine utilities.

## Verification

Add an offline contract test that verifies:

- active skill files contain no `3.8` runtime references;
- the repository contains no `remove.bg` or `REMOVEBG_API_KEY` references;
- the legacy `characters_nick` reference files are absent;
- the art-audit default resolves to `openai/gpt-5.6-luna-pro`;
- `openrouter_image.py --help`, `split_character.py --help`, and `detect_parts.py --help` exit successfully;
- the skill validator passes.

## Out of scope

- Reworking the broader Spine skeleton-generation architecture.
- Replacing Gemini in non-audit technical vision tasks.
- Changing image-generation models.
- Adding a direct OpenAI API integration.
- Running paid image or vision generations during verification.
