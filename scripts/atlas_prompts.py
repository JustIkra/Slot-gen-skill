"""
atlas_prompts.py — structured prompt builders for deconstructed-character atlas
generation via Nano Banana 2 / Pro on OpenRouter.

Context7 research on awesome-nanobanana-pro showed the model responds best to
structured JSON-shaped prompts with explicit rules and constraints rather than
prose. The builders below encode that pattern for the body-part atlas use case.
"""

from __future__ import annotations

import json
from typing import Iterable


DEFAULT_PARTS = [
    "head", "ear", "eye", "brow", "nose", "mouth", "nemes",
    "collar", "torso", "belt", "kilt",
    "left_upper_arm", "left_lower_arm", "left_hand",
    "right_upper_arm", "right_lower_arm", "right_hand",
    "left_lower_leg", "left_foot",
    "right_lower_leg", "right_foot",
]


def build_atlas_prompt(parts: Iterable[str] = DEFAULT_PARTS,
                       grid_cols: int = 4) -> str:
    """JSON-structured prompt that explicitly forbids duplicates and overlap."""
    parts = list(parts)
    rows = (len(parts) + grid_cols - 1) // grid_cols

    schema = {
        "task": "character_part_atlas",
        "output_image": {
            "purpose": (
                "A 2D game texture atlas for Spine 2D rigging. The atlas "
                "deconstructs the exact character shown in the reference "
                "image into separated body parts."
            ),
            "layout": {
                "type": "uniform_grid",
                "columns": grid_cols,
                "rows": rows,
                "cell_padding_px": 80,
                "min_gap_between_parts_px": 60,
                "grid_alignment": "row_major_top_left",
                "note": (
                    "Leave a thick black margin around every part so that no "
                    "two parts touch and no two parts share a connected "
                    "outline. The gap between adjacent parts must be visibly "
                    "wide (at least 60 px) and uniformly black."
                ),
            },
            "background": (
                "solid pure black RGB(0, 0, 0) everywhere outside the parts. "
                "Do NOT render the checkerboard transparency indicator. Do "
                "NOT draw grid lines between cells. Just flat black between "
                "parts and behind labels."
            ),
            "rendering_style": (
                "Identical to the reference image: same art style, same color "
                "palette, same outlines, same shading. Do NOT redesign."
            ),
        },
        "parts": [
            {
                "label": name,
                "instance_count": 1,
                "constraints": [
                    "exactly one instance",
                    "isolated in its own grid cell",
                    "no surrounding ground, shadow, or accessory",
                    "no detached cuffs, bands, jewelry, or decorations "
                    "floating away from the main silhouette — every visual "
                    "element of this part must touch and be part of the "
                    "same single connected shape",
                    "label text BELOW the part in small white sans-serif",
                ],
            }
            for name in parts
        ],
        "hard_rules": [
            "NEVER produce more than one instance of the same body part.",
            "NEVER allow two parts to overlap. Each part owns one grid cell.",
            "NEVER let two parts touch each other. A clear black margin must "
            "separate every adjacent pair, both horizontally and vertically.",
            "NEVER add the full assembled character anywhere in the atlas.",
            "NEVER add extra parts that are not in the parts[] list.",
            "NEVER add background scenery, gradients, frames, watermarks.",
            "NEVER draw detached decorations (cuffs, jewelry, eye whites) "
            "that float separately from the limb they belong to. Fuse them "
            "into the main silhouette of that part.",
            "If a part is not clearly visible in the reference, draw the most "
            "likely shape consistent with the reference style, but still only "
            "ONE instance, in its own cell.",
        ],
        "negative_prompt": (
            "duplicates, repeated limbs, multiple poses, overlapping parts, "
            "fused limbs, full body standing pose, dynamic pose, drop shadow, "
            "white background, colored background, gray checkerboard pattern, "
            "transparency indicator squares, grid lines, cell borders, "
            "scenery, props in hands, altered art style, redesigned face, "
            "missing limbs, text watermarks, signature, mismatched colors."
        ),
    }

    intro = (
        "You are generating a 2D game character body-part atlas. The image "
        "you produce must be a uniform grid of separated, isolated body "
        "parts, on a fully transparent background. Follow the JSON "
        "specification below exactly. Treat hard_rules as inviolable.\n\n"
    )
    return intro + json.dumps(schema, indent=2)


if __name__ == "__main__":
    print(build_atlas_prompt())
