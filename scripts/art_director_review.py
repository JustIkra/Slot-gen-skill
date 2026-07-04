"""Send a render (+ its cut layers, + competitor/own-studio refs, + optionally the
assembler SCRIPT text) to a vision model for an art-director critique.

    python art_director_review.py \
        --images out/master.jpg refs/lobby_grid.png refs/our_studio_promo.jpg \
        --question "Does our promo (image 1) reach our own studio bar (image 3)?" \
        [--script assemble.py] [--model gemini-pro]

Two hard-won caveats (the prompt nudges around them, but YOU must too):
  * The score is FRAME-OF-REFERENCE dependent and noisy — the same file scored 9.5
    judged inside a real lobby grid and 4 judged against hand-painted tier-1 refs, in
    one session. Pin the comparison set deliberately; say which bar to use.
  * Compare against YOUR OWN studio's released promo, not just Pragmatic top-3 — it
    makes the critique concrete and separates "needs better ASSETS / overpaint" from
    "needs better COMPOSITING" (compositing has a ceiling).
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openrouter_image import query_image, _load_dotenv


def main():
    p = argparse.ArgumentParser(description="Vision-model art-director review")
    p.add_argument("--images", nargs="+", required=True,
                   help="image paths; reference them as 'image 1', 'image 2', ... in --question")
    p.add_argument("--question", required=True, help="what to assess (mention image numbers)")
    p.add_argument("--script", default=None,
                   help="optional assembler .py to embed for a technical compositing critique")
    p.add_argument("--model", default="gemini-pro", choices=["gemini-pro", "gemini-flash"])
    p.add_argument("--lang", default="ru", help="response language (default ru)")
    args = p.parse_args()

    _load_dotenv()
    parts = [
        "Ты арт-директор/композитор студии слотов. Дай жёсткую конкретную критику, без воды.",
        args.question,
    ]
    if args.script:
        code = open(args.script, encoding="utf-8").read()
        parts.append(
            "Ниже — РЕАЛЬНЫЙ скрипт-сборщик композита (numpy/PIL). Прочитай как код и укажи "
            "КОНКРЕТНЫЕ ошибки подхода (порядок слоёв, режимы блендинга, плоские тени, "
            "screen-глоу замыливающий контраст, отсутствие cast-теней/light-wrap/rim):\n\n"
            "```python\n" + code + "\n```"
        )
    parts.append(
        "Поставь оценку по 10-балльной шкале относительно указанного эталона и дай короткий "
        "приоритетный список правок. Отметь, что решается КОМПОЗИТОМ, а что требует лучших "
        f"АССЕТОВ/оверпейнта. Отвечай на языке: {args.lang}."
    )
    print(query_image("\n\n".join(parts), args.images, model=args.model))


if __name__ == "__main__":
    main()
