#!/usr/bin/env python3
"""
build_skeleton_v2.py — Spine config builder for the 21-part body schema.

Given a layout.json (from canonical_layout / detect_parts / position_parts) and
a parts directory, write a Spine config compatible with build_spine_json.py.

Bone hierarchy (Anubis 3/4 character, kilt as hip-region piece):

    root
    └── hip                     (placed at belt centre)
        ├── kilt                (attachment on hip)
        ├── belt                (attachment on hip)
        ├── torso               (bone above hip)
        │   ├── collar          (attachment)
        │   ├── neck → head     (head bone)
        │   │   ├── nemes
        │   │   ├── ear, brow, eye, nose, mouth (head sub-slots)
        │   ├── left_shoulder → left_upper_arm → left_lower_arm → left_hand
        │   └── right_shoulder → right_upper_arm → right_lower_arm → right_hand
        ├── left_thigh → left_lower_leg → left_foot
        └── right_thigh → right_lower_leg → right_foot

"thigh" bones exist only as parents for lower_leg — there is no separate
upper-leg attachment because the kilt covers the thigh region.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


HEAD_DETAILS = ["nemes", "ear", "brow", "eye", "nose", "mouth"]
TORSO_DETAILS = ["collar"]
HIP_DETAILS = ["kilt", "belt"]


def _bone(side: str | None, name: str) -> str:
    """Return the canonical hyphen-cased bone name expected by the animation
    presets in build_spine_json.py. e.g. (left, upper_arm) -> left-upper-arm."""
    if side:
        return f"{side}-{name.replace('_', '-')}"
    return name.replace("_", "-")


def _centre(part: dict) -> tuple[float, float]:
    return (part["x"] + part["width"] / 2.0, part["y"] + part["height"] / 2.0)


def build(layout_path: str, parts_dir: str, out_dir: str) -> str:
    layout = json.loads(Path(layout_path).read_text())
    parts = layout["parts"]
    cw = layout["canvas_width"]
    ch = layout["canvas_height"]

    images_dir = Path(out_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    for name, p in parts.items():
        src = Path(parts_dir) / p.get("file", f"{name}.png")
        if src.is_file():
            shutil.copyfile(src, images_dir / f"{name}.png")

    def world(name: str) -> tuple[float, float]:
        if name not in parts:
            return (0.0, 0.0)
        cx, cy = _centre(parts[name])
        return (cx - cw / 2.0, ch - cy)

    bones: list[dict] = [{"name": "root"}]
    slots: list[dict] = []
    attachments: dict[str, dict] = {}

    def add_bone(name: str, parent: str, x: float, y: float, length: float = 0.0,
                 rotation: float = 0.0) -> None:
        parent_meta = next(b for b in bones if b["name"] == parent)
        parent_world = _bone_world(parent_meta)
        bones.append({
            "name": name,
            "parent": parent,
            "x": round(x - parent_world[0], 2),
            "y": round(y - parent_world[1], 2),
            "length": round(length, 2),
            "rotation": round(rotation, 2),
        })

    def _bone_world(meta: dict) -> tuple[float, float]:
        if meta["name"] == "root":
            return (0.0, 0.0)
        parent_meta = next(b for b in bones if b["name"] == meta["parent"])
        px, py = _bone_world(parent_meta)
        return (px + meta.get("x", 0), py + meta.get("y", 0))

    def add_part(part_name: str, bone: str, slot_name: str | None = None) -> None:
        if part_name not in parts:
            return
        p = parts[part_name]
        cx, cy = _centre(p)
        wx = cx - cw / 2.0
        wy = ch - cy
        bone_meta = next(b for b in bones if b["name"] == bone)
        bw = _bone_world(bone_meta)
        att_x = wx - bw[0]
        att_y = wy - bw[1]
        slot = slot_name or part_name
        slots.append({"name": slot, "bone": bone, "attachment": part_name})
        attachments[part_name] = {
            "x": round(att_x, 2),
            "y": round(att_y, 2),
            "width": p["width"],
            "height": p["height"],
        }

    hip_w = world("belt") if "belt" in parts else world("kilt")
    add_bone("hip", "root", hip_w[0], hip_w[1], length=40)

    torso_w = world("torso") if "torso" in parts else (hip_w[0], hip_w[1] + 200)
    add_bone("torso", "hip", torso_w[0], torso_w[1], length=200)

    head_w = world("head") if "head" in parts else (torso_w[0], torso_w[1] + 200)
    add_bone("neck", "torso", torso_w[0], torso_w[1] + 80, length=60)
    add_bone("head", "neck", head_w[0], head_w[1], length=80)

    def shoulder_world(side: str) -> tuple[float, float]:
        ua_w = world(f"{side}_upper_arm")
        return ua_w if ua_w != (0.0, 0.0) else (torso_w[0] + (-150 if side == "left" else 150), torso_w[1] + 40)

    def hip_side_world(side: str) -> tuple[float, float]:
        ll_w = world(f"{side}_lower_leg")
        if ll_w == (0.0, 0.0):
            return (hip_w[0] + (-60 if side == "left" else 60), hip_w[1] - 100)
        return (hip_w[0] + (-60 if side == "left" else 60), hip_w[1] - 30)

    for side in ("left", "right"):
        sh_w = shoulder_world(side)
        add_bone(_bone(side, "shoulder"), "torso", sh_w[0], sh_w[1], length=80)
        ua_w = world(f"{side}_upper_arm") or sh_w
        add_bone(_bone(side, "upper_arm"), _bone(side, "shoulder"), ua_w[0], ua_w[1], length=150)
        la_w = world(f"{side}_lower_arm") or (ua_w[0], ua_w[1] - 150)
        add_bone(_bone(side, "lower_arm"), _bone(side, "upper_arm"), la_w[0], la_w[1], length=120)
        hand_w = world(f"{side}_hand") or (la_w[0], la_w[1] - 100)
        add_bone(_bone(side, "hand"), _bone(side, "lower_arm"), hand_w[0], hand_w[1], length=40)

    for side in ("left", "right"):
        thigh_w = hip_side_world(side)
        add_bone(_bone(side, "upper_leg"), "hip", thigh_w[0], thigh_w[1], length=180)
        ll_w = world(f"{side}_lower_leg") or (thigh_w[0], thigh_w[1] - 200)
        add_bone(_bone(side, "lower_leg"), _bone(side, "upper_leg"), ll_w[0], ll_w[1], length=180)
        foot_w = world(f"{side}_foot") or (ll_w[0], ll_w[1] - 200)
        add_bone(_bone(side, "foot"), _bone(side, "lower_leg"), foot_w[0], foot_w[1], length=60)

    for d in HIP_DETAILS:
        add_part(d, "hip")
    add_part("torso", "torso")
    for d in TORSO_DETAILS:
        add_part(d, "torso")
    add_part("head", "head")
    for d in HEAD_DETAILS:
        add_part(d, "head")

    for side in ("left", "right"):
        add_part(f"{side}_upper_arm", _bone(side, "upper_arm"))
        add_part(f"{side}_lower_arm", _bone(side, "lower_arm"))
        add_part(f"{side}_hand", _bone(side, "hand"))
        add_part(f"{side}_lower_leg", _bone(side, "lower_leg"))
        add_part(f"{side}_foot", _bone(side, "foot"))

    config = {
        "skeleton": {
            "name": "anubis",
            "width": cw,
            "height": ch,
        },
        "bones": bones,
        "slots": slots,
        "attachments": attachments,
        "animations": ["idle", "walk", "run", "wave", "jump", "attack"],
    }

    out_path = Path(out_dir) / "config.json"
    out_path.write_text(json.dumps(config, indent=2))
    print(f"Config saved: {out_path}")
    print(f"  bones: {len(bones)}, slots: {len(slots)}, attachments: {len(attachments)}")
    return str(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True)
    parser.add_argument("--parts", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    build(args.layout, args.parts, args.out_dir)


if __name__ == "__main__":
    main()
