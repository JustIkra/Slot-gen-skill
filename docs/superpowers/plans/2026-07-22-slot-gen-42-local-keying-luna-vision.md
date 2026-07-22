# Slot-Gen Spine 4.2, Local Keying, and Luna Vision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Spine 4.2 the sole supported format, use local full-resolution keying, and route every vision query through GPT-5.6 Luna Pro on OpenRouter.

**Architecture:** Keep the existing OpenRouter transport and separate Gemini image generation from GPT-5.6 Luna Pro image analysis. Enforce the migration with one offline contract suite that scans active skill files, checks CLI startup, and validates the sole vision-model mapping without making paid calls.

**Tech Stack:** Python 3 standard library `unittest`, Bun/TypeScript, OpenRouter chat completions, Spine 4.2 JSON.

## Global Constraints

- Spine 4.2 is the only supported Spine format.
- Background cleanup uses native alpha, `scripts/chroma_key.py`, or `scripts/key_flood.py` only.
- Every image-analysis and art-audit query uses `openai/gpt-5.6-luna-pro` through OpenRouter and `OPENROUTER_KEY`.
- Gemini remains only in the image-generation registry.
- Do not add `OPENAI_API_KEY`, a direct OpenAI client, or a second provider transport.
- Do not run paid image or vision requests during verification.
- Exclude `docs/superpowers/` from forbidden-term scans because it contains historical design and implementation records.

---

### Task 1: Add the failing migration contract

**Files:**
- Create: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: repository files and public CLI `--help` behavior.
- Produces: `ACTIVE_TEXT_ROOTS`, `active_text_files()`, and offline regression tests used by all later tasks.

- [ ] **Step 1: Write the failing contract suite**

```python
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TEXT_ROOTS = (
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "docs" / "setup.md",
    ROOT / "docs" / "api-providers.md",
    ROOT / "workflows",
    ROOT / "scripts",
    ROOT / "tools",
)


def active_text_files() -> list[Path]:
    files: list[Path] = []
    for root in ACTIVE_TEXT_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        files.extend(
            path for path in root.rglob("*")
            if path.is_file() and path.suffix in {".md", ".py", ".ts", ".json"}
        )
    return files


def run_help(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class SkillContractTests(unittest.TestCase):
    def test_only_spine_42_is_active(self) -> None:
        offenders = [str(path.relative_to(ROOT)) for path in active_text_files()
                     if "3.8" in path.read_text(errors="ignore")]
        self.assertEqual(offenders, [])
        for suffix in ("json", "atlas", "png"):
            self.assertFalse((ROOT / "reference" / f"characters_nick.{suffix}").exists())

    def test_external_background_removal_service_is_absent(self) -> None:
        forbidden = (
            "remove" + ".bg",
            "REMOVE" + "BG_API_KEY",
            "api." + "remove" + ".bg",
            "--remove" + "-bg",
        )
        offenders: dict[str, list[str]] = {}
        for path in active_text_files():
            text = path.read_text(errors="ignore")
            matches = [term for term in forbidden if term in text]
            if matches:
                offenders[str(path.relative_to(ROOT))] = matches
        self.assertEqual(offenders, {})

    def test_all_vision_queries_use_luna_pro(self) -> None:
        module_path = ROOT / "scripts" / "openrouter_image.py"
        spec = importlib.util.spec_from_file_location("openrouter_image", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        self.assertEqual(
            module.VISION_MODELS,
            {"vision": "openai/gpt-5.6-luna-pro"},
        )

        for script in (
            "scripts/art_director_review.py",
            "scripts/detect_parts.py",
        ):
            with self.subTest(script=script):
                result = run_help(sys.executable, "-B", script, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("GPT-5.6 Luna Pro", result.stdout)
                self.assertNotIn("--model", result.stdout)

    def test_python_clis_start_without_provider_keys(self) -> None:
        for script in (
            "scripts/openrouter_image.py",
            "scripts/split_character.py",
            "scripts/detect_parts.py",
        ):
            with self.subTest(script=script):
                result = run_help(sys.executable, "-B", script, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_typescript_help_has_no_external_background_service(self) -> None:
        result = run_help("bun", "run", "tools/generate-image.ts", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("remove-bg", result.stdout)
        self.assertNotIn("REMOVE" + "BG_API_KEY", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the suite and verify the baseline failures**

Run: `python3 -B -m unittest tests/test_skill_contract.py -v`

Expected: FAIL for the legacy reference, forbidden service terms, non-Luna vision mappings, and `detect_parts.py` import error. No test may make a network request.

- [ ] **Step 3: Commit the RED baseline**

```bash
git add tests/test_skill_contract.py
git commit -m "test: define slot-gen modernization contract"
```

### Task 2: Remove the Spine 3.8 reference assets

**Files:**
- Delete: `reference/characters_nick.json`
- Delete: `reference/characters_nick.atlas`
- Delete: `reference/characters_nick.png`

**Interfaces:**
- Consumes: the `test_only_spine_42_is_active` contract.
- Produces: a repository with no legacy Spine reference bundle.

- [ ] **Step 1: Run the focused test and confirm it fails**

Run: `python3 -B -m unittest tests.test_skill_contract.SkillContractTests.test_only_spine_42_is_active -v`

Expected: FAIL because `reference/characters_nick.*` exists and its JSON declares Spine 3.8.

- [ ] **Step 2: Delete exactly the legacy bundle**

```bash
rm reference/characters_nick.json
rm reference/characters_nick.atlas
rm reference/characters_nick.png
```

- [ ] **Step 3: Re-run the focused test**

Run: `python3 -B -m unittest tests.test_skill_contract.SkillContractTests.test_only_spine_42_is_active -v`

Expected: PASS.

- [ ] **Step 4: Commit the deletion**

```bash
git add reference/characters_nick.json reference/characters_nick.atlas reference/characters_nick.png
git commit -m "chore: remove Spine 3.8 reference assets"
```

### Task 3: Remove the external background-removal integration

**Files:**
- Modify: `tools/generate-image.ts`
- Modify: `scripts/openrouter_image.py`
- Modify: `scripts/detect_parts.py`
- Modify: `scripts/split_character.py`

**Interfaces:**
- Consumes: `OPENROUTER_KEY`, image generation, `chroma_key.py`, and `key_flood.py`.
- Produces: provider-free local cleanup guidance and CLIs with no removed flags or imports.

- [ ] **Step 1: Run the focused contract tests and confirm failures**

Run: `python3 -B -m unittest tests.test_skill_contract.SkillContractTests.test_external_background_removal_service_is_absent tests.test_skill_contract.SkillContractTests.test_python_clis_start_without_provider_keys tests.test_skill_contract.SkillContractTests.test_typescript_help_has_no_external_background_service -v`

Expected: FAIL because TypeScript still exposes the service flags, Python files mention the service, and `detect_parts.py` imports a removed function.

- [ ] **Step 2: Simplify the TypeScript CLI**

In `tools/generate-image.ts`:

- remove `removeBg`, `removeBgSize`, `RemoveBgSize`, and `REMOVE_BG_SIZES`;
- remove both service flags from `showHelp()` and `parseArgs()`;
- delete `pngSize()` and `removeBackground()`;
- after each `generate()` call, return without a cleanup API call;
- document only `OPENROUTER_KEY` in the file header and help output.

The variation branch must end with:

```typescript
for (let i = 1; i <= args.variations; i++) {
  const out = `${base}-v${i}.png`;
  tasks.push(generate(args, prompt, out));
}
await Promise.all(tasks);
return;
```

The single-output branch must end with:

```typescript
await generate(args, prompt, args.output);
```

- [ ] **Step 3: Repair the Python CLIs**

In `scripts/detect_parts.py`, import only:

```python
from openrouter_image import OpenRouterError, query_image  # noqa: E402
```

Delete the removed CLI flag and cleanup branch. Renumber output to two steps and finish with:

```python
print("[2/2] Cropping parts from the original image…")
img = Image.open(args.input_image)
layout = crop_parts(
    args.input_image,
    bboxes,
    args.output_dir,
    padding_px=args.padding,
)

layout_obj = {
    "reference_image": Path(args.input_image).name,
    "canvas_width": img.width,
    "canvas_height": img.height,
    "parts": layout,
}
layout_path = args.layout_out or str(Path(args.output_dir) / "layout.json")
Path(layout_path).parent.mkdir(parents=True, exist_ok=True)
Path(layout_path).write_text(json.dumps(layout_obj, indent=2))
print(f"      Layout: {layout_path}")
print(f"\nDone. {len(layout)} parts in {args.output_dir}/")
```

In `scripts/split_character.py`, describe a two-stage process: generate on a controlled solid background, then segment locally into transparent PNGs. Remove the obsolete flags and API-key statements from its docstring.

In `scripts/openrouter_image.py`, retain the local-cleanup policy but remove the retired service name from comments.

- [ ] **Step 4: Run the focused tests**

Run the command from Step 1.

Expected: Python and TypeScript help tests PASS. The forbidden-term test may still FAIL only in user documentation scheduled for Task 5.

- [ ] **Step 5: Commit the runtime cleanup**

```bash
git add tools/generate-image.ts scripts/openrouter_image.py scripts/detect_parts.py scripts/split_character.py
git commit -m "refactor: remove external background cleanup service"
```

### Task 4: Route every vision query to GPT-5.6 Luna Pro

**Files:**
- Modify: `scripts/openrouter_image.py`
- Modify: `scripts/art_director_review.py`
- Modify: `scripts/detect_parts.py`

**Interfaces:**
- Consumes: `query_image(prompt: str, images: list[str])` and `OPENROUTER_KEY`.
- Produces: `VISION_MODELS == {"vision": "openai/gpt-5.6-luna-pro"}` and fixed-model vision CLIs.

- [ ] **Step 1: Run the vision contract and confirm it fails**

Run: `python3 -B -m unittest tests.test_skill_contract.SkillContractTests.test_all_vision_queries_use_luna_pro -v`

Expected: FAIL because Gemini technical-vision aliases still exist and `detect_parts.py` exposes a model override.

- [ ] **Step 2: Add the sole vision mapping**

Set the registry in `scripts/openrouter_image.py` to:

```python
VISION_MODELS = {
    "vision": "openai/gpt-5.6-luna-pro",
}
```

Remove the `model` parameter from `query_image()` and always select `VISION_MODELS["vision"]`.

- [ ] **Step 3: Make the art-audit CLI deterministic**

In `scripts/art_director_review.py`:

- identify GPT-5.6 Luna Pro in the module docstring and parser description;
- delete the public `--model` option;
- call `query_image(...)` without a model override.

In `scripts/detect_parts.py`, remove the `model` argument and `--model` CLI option, identify GPT-5.6 Luna Pro in help output, and call `query_image(...)` without a model override.

The final call must be:

```python
print(query_image("\n\n".join(parts), args.images))
```

- [ ] **Step 4: Run the vision contract**

Run the command from Step 1.

Expected: PASS without a provider key or network request because only `--help` and registry inspection run.

- [ ] **Step 5: Commit the audit migration**

```bash
git add scripts/openrouter_image.py scripts/art_director_review.py scripts/detect_parts.py
git commit -m "refactor: use Luna Pro for all vision queries"
```

### Task 5: Synchronize active skill documentation

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `docs/setup.md`
- Modify: `docs/api-providers.md`
- Modify: `workflows/art-generation.md`
- Modify: `workflows/promo-composition.md`
- Modify: `workflows/spine-pipeline.md`
- Modify: `workflows/video-generation.md`

**Interfaces:**
- Consumes: the final runtime behavior from Tasks 2–4.
- Produces: one truthful user-facing contract for Spine 4.2, local keying, and Luna Pro audits.

- [ ] **Step 1: Run the forbidden-term contract and confirm documentation failures**

Run: `python3 -B -m unittest tests.test_skill_contract.SkillContractTests.test_external_background_removal_service_is_absent -v`

Expected: FAIL with only active documentation files listed as offenders.

- [ ] **Step 2: Update routing and setup documentation**

Apply these exact policy changes across the listed files:

- replace the retired service with native alpha, `chroma_key.py`, or `key_flood.py`;
- list only `OPENROUTER_KEY` as required environment;
- identify `openai/gpt-5.6-luna-pro` as the sole image-analysis and art-direction model;
- restrict Gemini wording and model IDs to image generation;
- state Spine 4.2 as the sole format;
- remove obsolete Python commands and flags;
- add `workflows/video-generation.md`, `scripts/segment_grid_atlas.py`, `scripts/canonical_layout.py`, `scripts/compose_layout.py`, and `scripts/build_skeleton_v2.py` to the Layout tree in `SKILL.md`;
- update README status so it no longer calls the repository an initial scaffold awaiting smoke tests.

- [ ] **Step 3: Run the full contract suite**

Run: `python3 -B -m unittest tests/test_skill_contract.py -v`

Expected: all contract tests PASS.

- [ ] **Step 4: Validate the skill package**

Run: `python3 -B /Users/maksim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .`

Expected: `Skill is valid!`

- [ ] **Step 5: Run static checks**

```bash
bun run tools/generate-image.ts --help
git diff --check
```

Expected: all commands exit 0; generated help contains only OpenRouter image-generation options.

- [ ] **Step 6: Commit the synchronized documentation**

```bash
git add SKILL.md README.md docs/setup.md docs/api-providers.md workflows tests/test_skill_contract.py
git commit -m "docs: align slot-gen with Spine 4.2 and Luna audit"
```

### Task 6: Final verification and repository audit

**Files:**
- Verify only; no planned modifications.

**Interfaces:**
- Consumes: all commits from Tasks 1–5.
- Produces: evidence that the agreed migration contract is complete.

- [ ] **Step 1: Run the complete offline verification set**

```bash
python3 -B -m unittest tests/test_skill_contract.py -v
python3 -B /Users/maksim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
bun run tools/generate-image.ts --help
git diff --check
git status --short
```

Expected: tests PASS, validator reports `Skill is valid!`, Bun help exits 0, diff check is clean, and status is empty.

- [ ] **Step 2: Inspect the final commit range**

Run: `git log --oneline d080e9a..HEAD`

Expected: separate commits for the RED contract, Spine 3.8 deletion, runtime cleanup, Luna audit migration, and synchronized documentation.

- [ ] **Step 3: Report paid verification as intentionally skipped**

State in the handoff that no OpenRouter generation or audit request was sent; verification covered payload/model selection and CLI behavior offline.
