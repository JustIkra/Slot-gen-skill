"""
openrouter_image.py — OpenRouter image generation client for Python.

Shared by the Spine pipeline (`split_character.py`) so that Python and the
TypeScript CLI (`tools/generate-image.ts`) target the exact same backend.

Reads OPENROUTER_KEY from the environment, falling back to ~/.codex/.env if it
is not already set in the shell. Full-resolution transparency cleanup uses
local chroma-key tools (`chroma_key.py`, `key_flood.py`).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_MODELS = {
    "nano-banana-2": "google/gemini-3.1-flash-image",
    "nano-banana-pro": "google/gemini-3-pro-image",
}

VISION_MODELS = {
    "vision": "openai/gpt-5.6-luna-pro",
}

SIZE_MAP = {
    "1K": "1K",
    "2K": "2K",
    "4K": "4K",
}

VALID_ASPECT_RATIOS = {
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
    "4:1", "4:3", "4:5", "5:4", "8:1",
    "9:16", "16:9", "21:9",
}

VALID_REASONING_EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "none"}


class OpenRouterError(RuntimeError):
    pass


def _load_dotenv() -> None:
    env_path = Path.home() / ".codex" / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _require_env(name: str) -> str:
    _load_dotenv()
    value = os.environ.get(name)
    if not value:
        raise OpenRouterError(
            f"Missing environment variable: {name}. "
            f"Set it in your shell or in ~/.codex/.env"
        )
    return value


def _encode_reference(path: str) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(path)
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise OpenRouterError(f"Unsupported reference image type: {mime} ({path})")
    data = Path(path).read_bytes()
    return mime, base64.b64encode(data).decode("ascii")


def generate_image(
    prompt: str,
    output: str,
    *,
    model: str = "nano-banana-2",
    size: str = "2K",
    aspect_ratio: str = "1:1",
    reference_image: Optional[str] = None,
    reference_images: Optional[list[str]] = None,
    transparent: bool = False,
    reasoning_effort: Optional[str] = None,
    reasoning_exclude: bool = True,
    provider_only: Optional[list[str]] = None,
    dry_run: bool = False,
) -> str:
    """Call OpenRouter and write the resulting PNG to *output*. Returns the path.

    reasoning_effort — passes through to Gemini's thinkingConfig via OpenRouter
                       (one of minimal/low/medium/high/xhigh/none). None means
                       no reasoning param sent.
    reasoning_exclude — when True (default) the reasoning text trace is not
                        returned in the response, but reasoning_tokens are still
                        billed. Set False to surface the trace for debugging.
    provider_only    — optional list of OpenRouter provider tags to force, e.g.
                       ["google-vertex/global"] or ["google-ai-studio"].
    """

    if model not in OPENROUTER_MODELS:
        raise OpenRouterError(f"Unknown model '{model}'. Valid: {list(OPENROUTER_MODELS)}")
    if size not in SIZE_MAP:
        raise OpenRouterError(f"Unknown size '{size}'. Valid: {list(SIZE_MAP)}")
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise OpenRouterError(
            f"Unknown aspect_ratio '{aspect_ratio}'. "
            f"Valid: {sorted(VALID_ASPECT_RATIOS)}"
        )
    if reasoning_effort and reasoning_effort not in VALID_REASONING_EFFORTS:
        raise OpenRouterError(
            f"Unknown reasoning_effort '{reasoning_effort}'. "
            f"Valid: {sorted(VALID_REASONING_EFFORTS)}"
        )
    if model == "nano-banana-pro" and aspect_ratio in {"4:1", "8:1", "1:4", "1:8"}:
        raise OpenRouterError("nano-banana-pro does not support this strip aspect; choose a model explicitly")
    if size == "4K":
        raise OpenRouterError("The configured stable image models support up to 2K; no automatic model/size substitution")

    if transparent:
        prompt = (
            "CRITICAL: Transparent background (PNG with alpha channel) — NO "
            "background color, pure transparency. Subject floating in "
            "transparent space. " + prompt
        )

    content: list[dict] = []
    refs = list(reference_images) if reference_images else []
    if reference_image:
        refs.insert(0, reference_image)
    for ref in refs:
        mime, b64 = _encode_reference(ref)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        })
    content.append({"type": "text", "text": prompt})

    payload: dict = {
        "model": OPENROUTER_MODELS[model],
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
        "stream": False,
        "image_config": {
            "aspect_ratio": aspect_ratio,
            "image_size": SIZE_MAP[size],
        },
    }
    if reasoning_effort and reasoning_effort != "none":
        payload["reasoning"] = {
            "effort": reasoning_effort,
            "exclude": reasoning_exclude,
        }
    if provider_only:
        payload["provider"] = {"only": list(provider_only)}
    if dry_run:
        return payload
    from slotgen_provider.http import request_json
    data = request_json("POST", OPENROUTER_ENDPOINT, token=_require_env("OPENROUTER_KEY"),
                        allowed_origins={"https://openrouter.ai"}, body=payload, timeout=180)
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError("Malformed OpenRouter image response") from exc

    image_b64 = _extract_image(message)
    if not image_b64:
        raise OpenRouterError("OpenRouter response contained no image data")

    usage = data.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    reasoning_tokens = details.get("reasoning_tokens")
    if reasoning_tokens:
        print(f"[openrouter] reasoning_tokens={reasoning_tokens}")

    from slotgen_provider.artifacts import save_png
    return save_png(base64.b64decode(image_b64, validate=True), output)


def _extract_image(message: dict) -> Optional[str]:
    images = message.get("images")
    if isinstance(images, list) and images:
        url = images[0].get("image_url", {}).get("url")
        if isinstance(url, str) and url.startswith("data:image/"):
            return url.split(",", 1)[1]

    content = message.get("content")
    if isinstance(content, list):
        for part in content:
            if part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url")
                if isinstance(url, str) and url.startswith("data:image/"):
                    return url.split(",", 1)[1]
    return None


def query_image(
    prompt: str,
    images: list[str],
    *,
    response_format: Optional[dict] = None,
    max_tokens: Optional[int] = None,
    result_out: Optional[str] = None,
    structured_review: bool = False,
) -> str:
    """Send *images* + *prompt* to a vision model via OpenRouter and
    return the raw text response. Use *response_format* to request JSON output.
    """
    try:
        from slotgen_provider.http import request_json
        from slotgen_provider.review import response_text, parse_review_response, input_fingerprints
    except ImportError as error:
        raise OpenRouterError("Install slotgen-provider in this Python environment: pip install -e .") from error
    api_key = _require_env("OPENROUTER_KEY")

    content: list[dict] = [{"type": "text", "text": prompt}]
    for img_path in images:
        mime, b64 = _encode_reference(img_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        })

    payload: dict = {
        "model": VISION_MODELS["vision"],
        "messages": [{"role": "user", "content": content}],
    }
    if response_format:
        payload["response_format"] = response_format
    if structured_review:
        payload["response_format"] = {"type": "json_object"}
    if max_tokens is not None:
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise OpenRouterError("max_tokens must be a positive integer")
        payload["max_tokens"] = max_tokens

    data = request_json("POST", OPENROUTER_ENDPOINT, token=api_key, allowed_origins={"https://openrouter.ai"}, body=payload, timeout=180)
    text = response_text(data)
    result = parse_review_response(data) if structured_review else text
    if result_out:
        report = {"inputs": input_fingerprints(images), "prompt": prompt, "requested_model": payload["model"], "max_tokens": max_tokens,
                  "returned_model": data.get("model"), "usage": data.get("usage"), "finish_reason": data["choices"][0].get("finish_reason"), "result": result}
        Path(result_out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return json.dumps(result, ensure_ascii=False) if structured_review else text


# Magenta-background generation pairs with scripts/chroma_key.py for UI parts;
# solid white/black backgrounds pair with scripts/key_flood.py for logos and text.


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OpenRouter image generation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate an image via OpenRouter")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--output", default="out.png")
    gen.add_argument("--model", default="nano-banana-2",
                     choices=list(OPENROUTER_MODELS))
    gen.add_argument("--size", default="2K", choices=list(SIZE_MAP))
    gen.add_argument("--aspect-ratio", default="1:1",
                     choices=sorted(VALID_ASPECT_RATIOS))
    gen.add_argument("--reference-image", action="append", default=[])
    gen.add_argument("--dry-run", action="store_true", help="Print request payload without credentials or remote calls")
    gen.add_argument("--creative-variations", type=int, choices=range(1, 11), default=1)
    gen.add_argument("--transparent", action="store_true")
    gen.add_argument("--reasoning", default=None,
                     choices=sorted(VALID_REASONING_EFFORTS),
                     help="Gemini thinking level via OpenRouter (default: off)")
    gen.add_argument("--reasoning-include-trace", action="store_true",
                     help="Surface the reasoning text in response (still billed)")
    gen.add_argument("--provider", default=None,
                     choices=["google-vertex/global", "google-ai-studio"],
                     help="Force OpenRouter to route through a specific Google provider tag")

    args = parser.parse_args()

    try:
        if args.cmd == "generate":
            for variant in range(1, args.creative_variations + 1):
                output = args.output if args.creative_variations == 1 else str(Path(args.output).with_suffix("")) + f"-v{variant}.png"
                path = generate_image(
                prompt=args.prompt,
                output=output,
                model=args.model,
                size=args.size,
                aspect_ratio=args.aspect_ratio,
                reference_images=args.reference_image,
                transparent=args.transparent,
                reasoning_effort=args.reasoning,
                reasoning_exclude=not args.reasoning_include_trace,
                provider_only=[args.provider] if args.provider else None,
                dry_run=args.dry_run,
            )
                print(json.dumps(path) if args.dry_run else f"saved: {path}")
    except OpenRouterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
