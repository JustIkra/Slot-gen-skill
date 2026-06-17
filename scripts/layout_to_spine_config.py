#!/usr/bin/env python3
"""
layout_to_spine_config.py — turn position_parts.py output into a Spine
config.json that build_spine_json.py understands.

Heuristic: parts are labelled by their position in the reference canvas.
This is intentionally simple — it gets us to a working preview. Parts that
template-matching duplicated to the same spot are kept only once (highest
score wins per body region).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


REGIONS = [
    # name,    y_min_frac, y_max_frac, x_min_frac, x_max_frac, min_aspect_wh
    ("head",   0.00, 0.40, 0.20, 0.80, 0.0),
    ("torso",  0.30, 0.55, 0.25, 0.75, 0.45),
    ("kilt",   0.45, 0.70, 0.20, 0.80, 0.45),
    ("legs",   0.60, 0.90, 0.20, 0.80, 0.0),
    ("foot-left",  0.80, 1.00, 0.00, 0.50, 0.0),
    ("foot-right", 0.80, 1.00, 0.50, 1.00, 0.0),
]


def _priority(p: dict) -> tuple[int, float]:
    return (1 if p["method"] == "sift" else 0, p["score"])


def label_parts(layout: dict) -> dict[str, dict]:
    """Pick the best part per region. SIFT matches beat template fallback ones."""
    cw = layout["canvas_width"]
    ch = layout["canvas_height"]
    parts = layout["parts"]
    chosen: dict[str, tuple[str, dict]] = {}

    for pname, p in parts.items():
        cx = p["x"] + p["width"] / 2
        cy = p["y"] + p["height"] / 2
        fx = cx / cw
        fy = cy / ch
        aspect = p["width"] / max(1, p["height"])
        for region, y0, y1, x0, x1, min_aspect in REGIONS:
            if not (y0 <= fy <= y1 and x0 <= fx <= x1):
                continue
            if aspect < min_aspect:
                continue
            prev = chosen.get(region)
            if prev is None or _priority(p) > _priority(prev[1]):
                chosen[region] = (pname, p)
            break

    return {region: data for region, data in chosen.items()}


def build_config(layout_path: str, parts_dir: str, out_dir: str) -> str:
    layout = json.loads(Path(layout_path).read_text())
    cw = layout["canvas_width"]
    ch = layout["canvas_height"]

    labelled = label_parts(layout)
    print(f"Labelled {len(labelled)} body regions:")
    for region, (pname, p) in labelled.items():
        print(f"  {region:>10} ← {pname} (score={p['score']:.2f})")

    images_dir = Path(out_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    bones = [{"name": "root"}]
    slots: list[dict] = []
    attachments: dict[str, dict] = {}

    def add_bone(name: str, parent: str, world_x: float, world_y: float,
                 length: float = 0.0) -> None:
        bones.append({
            "name": name,
            "parent": parent,
            "x": round(world_x, 2),
            "y": round(world_y, 2),
            "length": round(length, 2),
        })

    def add_part(region: str, bone: str) -> None:
        if region not in labelled:
            return
        pname, p = labelled[region]
        center_x = p["x"] + p["width"] / 2
        center_y = p["y"] + p["height"] / 2
        spine_x = center_x - cw / 2
        spine_y = ch - center_y

        bone_meta = next(b for b in bones if b["name"] == bone)
        att_x = spine_x - bone_meta["x"]
        att_y = spine_y - bone_meta["y"]

        slot_name = region
        attach_name = region
        slots.append({"name": slot_name, "bone": bone, "attachment": attach_name})
        attachments[attach_name] = {
            "x": round(att_x, 2),
            "y": round(att_y, 2),
            "width": p["width"],
            "height": p["height"],
        }

        src = Path(parts_dir) / f"{pname}.png"
        dst = images_dir / f"{region}.png"
        shutil.copyfile(src, dst)

    hip_y = ch - (labelled["kilt"][1]["y"] + labelled["kilt"][1]["height"] / 2) if "kilt" in labelled else 200
    add_bone("hip", "root", 0, hip_y, 30)

    torso_y = ch - (labelled["torso"][1]["y"] + labelled["torso"][1]["height"] / 2) if "torso" in labelled else hip_y + 250
    add_bone("torso", "hip", 0, torso_y - hip_y, 200)

    head_y = ch - (labelled["head"][1]["y"] + labelled["head"][1]["height"] / 2) if "head" in labelled else torso_y + 400
    add_bone("head", "torso", 0, head_y - torso_y, 100)

    add_bone("kilt-bone", "hip", 0, -60, 60)

    legs_y = ch - (labelled["legs"][1]["y"] + labelled["legs"][1]["height"] / 2) if "legs" in labelled else hip_y - 300
    add_bone("legs", "hip", 0, legs_y - hip_y, 300)

    if "foot-left" in labelled:
        fp = labelled["foot-left"][1]
        fx = (fp["x"] + fp["width"] / 2) - cw / 2
        fy = ch - (fp["y"] + fp["height"] / 2)
        add_bone("left-foot", "legs", fx, fy - legs_y, 50)
    if "foot-right" in labelled:
        fp = labelled["foot-right"][1]
        fx = (fp["x"] + fp["width"] / 2) - cw / 2
        fy = ch - (fp["y"] + fp["height"] / 2)
        add_bone("right-foot", "legs", fx, fy - legs_y, 50)

    add_part("head", "head")
    add_part("torso", "torso")
    add_part("kilt", "kilt-bone")
    add_part("legs", "legs")
    add_part("foot-left", "left-foot")
    add_part("foot-right", "right-foot")

    config = {
        "skeleton": {
            "name": "anubis",
            "width": cw,
            "height": ch,
        },
        "bones": bones,
        "slots": slots,
        "attachments": attachments,
        "animations": ["idle", "walk", "wave"],
    }

    out_path = Path(out_dir) / "config.json"
    out_path.write_text(json.dumps(config, indent=2))
    print(f"\nConfig saved: {out_path}")
    print(f"Part PNGs copied to: {images_dir}")
    return str(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True)
    parser.add_argument("--parts", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    build_config(args.layout, args.parts, args.out_dir)


if __name__ == "__main__":
    main()
