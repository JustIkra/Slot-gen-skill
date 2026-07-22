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
    "art-audit": "openai/gpt-5.6-luna-pro",
    "gemini-flash": "google/gemini-3.5-flash",
    "gemini-pro": "google/gemini-3.1-pro-preview",
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
    api_key = _require_env("OPENROUTER_KEY")

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

    request = urllib.request.Request(
        OPENROUTER_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterError(f"OpenRouter {exc.code}: {detail}") from exc

    data = json.loads(body)
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Malformed OpenRouter response: {body!r}") from exc

    image_b64 = _extract_image(message)
    if not image_b64:
        raise OpenRouterError("OpenRouter response contained no image data")

    usage = data.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    reasoning_tokens = details.get("reasoning_tokens")
    if reasoning_tokens:
        print(f"[openrouter] reasoning_tokens={reasoning_tokens}")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_bytes(base64.b64decode(image_b64))
    return output


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
    model: str = "gemini-flash",
    response_format: Optional[dict] = None,
) -> str:
    """Send *images* + *prompt* to a vision model via OpenRouter and
    return the raw text response. Use *response_format* to request JSON output.
    """
    if model not in VISION_MODELS:
        raise OpenRouterError(f"Unknown vision model '{model}'. Valid: {list(VISION_MODELS)}")
    api_key = _require_env("OPENROUTER_KEY")

    content: list[dict] = [{"type": "text", "text": prompt}]
    for img_path in images:
        mime, b64 = _encode_reference(img_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
        })

    payload: dict = {
        "model": VISION_MODELS[model],
        "messages": [{"role": "user", "content": content}],
    }
    if response_format:
        payload["response_format"] = response_format

    request = urllib.request.Request(
        OPENROUTER_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterError(f"OpenRouter {exc.code}: {detail}") from exc

    data = json.loads(body)
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Malformed vision response: {body!r}") from exc

    text = message.get("content")
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if part.get("type") == "text")
    if not isinstance(text, str) or not text.strip():
        raise OpenRouterError(f"Vision model returned empty text: {body!r}")
    return text


# Magenta-background generation pairs with scripts/chroma_key.py for UI parts;
# solid white/black backgrounds pair with scripts/key_flood.py for logos and text.


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenRouter image generation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate an image via OpenRouter")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--output", required=True)
    gen.add_argument("--model", default="nano-banana-2",
                     choices=list(OPENROUTER_MODELS))
    gen.add_argument("--size", default="2K", choices=list(SIZE_MAP))
    gen.add_argument("--aspect-ratio", default="1:1",
                     choices=sorted(VALID_ASPECT_RATIOS))
    gen.add_argument("--reference-image", default=None)
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
            path = generate_image(
                prompt=args.prompt,
                output=args.output,
                model=args.model,
                size=args.size,
                aspect_ratio=args.aspect_ratio,
                reference_image=args.reference_image,
                transparent=args.transparent,
                reasoning_effort=args.reasoning,
                reasoning_exclude=not args.reasoning_include_trace,
                provider_only=[args.provider] if args.provider else None,
            )
            print(f"saved: {path}")
    except OpenRouterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
