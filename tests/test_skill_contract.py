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
            path
            for path in root.rglob("*")
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
        offenders = [
            str(path.relative_to(ROOT))
            for path in active_text_files()
            if "3.8" in path.read_text(errors="ignore")
        ]
        self.assertEqual(offenders, [])
        for suffix in ("json", "atlas", "png"):
            self.assertFalse(
                (ROOT / "reference" / f"characters_nick.{suffix}").exists()
            )

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
