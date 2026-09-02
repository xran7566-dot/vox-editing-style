#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

VISUAL_ROLES = {
    "background", "structure", "midground", "subject", "information",
    "foreground", "connector", "texture", "accent"
}
NON_COUNTING_ROLES = {"person", "subtitle", "audio", "gradient", "color_grade"}
REAL_ASSET_KINDS = {"image", "photo", "cutout", "video", "paper", "texture"}
MOTION_FIELDS = ("entry", "relation", "settle", "exit")
BASE_MODES = {
    "source_video_base_overlay",
    "collage_main_with_presenter",
    "dynamic_cutout_fusion",
    "mixed_by_scene",
}


def fail(errors):
    for error in errors:
        print(f"BLOCKED: {error}", file=sys.stderr)
    raise SystemExit(1)


def resolve(root, value):
    path = Path(value)
    return path if path.is_absolute() else root / path


def main():
    parser = argparse.ArgumentParser(description="校验 Vox 多图层场景清单")
    parser.add_argument("manifest")
    parser.add_argument("--project-root")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        fail([f"缺少分层场景清单: {manifest_path}"])
    root = Path(args.project_root).resolve() if args.project_root else manifest_path.parent.parent

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail([f"无法读取分层场景清单: {exc}"])

    errors = []
    if data.get("version") != 1:
        errors.append("layer-manifest version 必须为 1")
    if not args.allow_draft and data.get("approval", {}).get("status") != "approved":
        errors.append("分层场景清单尚未批准")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("分层场景清单没有 scenes")
        fail(errors)

    scene_ids = set()
    for index, scene in enumerate(scenes, start=1):
        scene_id = str(scene.get("id", "")).strip() or f"scene-{index}"
        prefix = f"{scene_id}: "
        base_mode = str(scene.get("base_mode", "")).strip()
        if base_mode not in BASE_MODES:
            errors.append(prefix + "缺少或使用了无效的 base_mode")
        if scene_id in scene_ids:
            errors.append(prefix + "镜头 id 重复")
        scene_ids.add(scene_id)

        for field in ("timecode", "mg_task_file", "remotion_component"):
            if not str(scene.get(field, "")).strip():
                errors.append(prefix + f"缺少 {field}")
        for field in ("mg_task_file", "remotion_component"):
            value = scene.get(field)
            if value and not resolve(root, value).exists():
                errors.append(prefix + f"引用文件不存在: {value}")

        layers = scene.get("layers")
        if not isinstance(layers, list):
            errors.append(prefix + "layers 必须是数组")
            continue

        counted = []
        seen_sources = {}
        counted_roles = set()
        has_real_asset = False
        for layer_index, layer in enumerate(layers, start=1):
            layer_id = str(layer.get("id", "")).strip() or f"layer-{layer_index}"
            role = str(layer.get("role", "")).strip()
            source = str(layer.get("source", "")).strip()
            kind = str(layer.get("source_kind", "")).strip()
            layer_prefix = prefix + layer_id + ": "

            if not role:
                errors.append(layer_prefix + "缺少 role")
            if not source:
                errors.append(layer_prefix + "缺少 source")
            if not str(layer.get("semantic_function", "")).strip():
                errors.append(layer_prefix + "缺少 semantic_function")
            for field in MOTION_FIELDS:
                if not str(layer.get(field, "")).strip():
                    errors.append(layer_prefix + f"缺少 {field}")
            if layer.get("contains_complete_composition") is True:
                errors.append(layer_prefix + "压平的完整构图不能计为独立图层")

            if source and not source.startswith(("inline:", "generated:")) and not resolve(root, source).exists():
                errors.append(layer_prefix + f"素材不存在: {source}")

            if role in VISUAL_ROLES and layer.get("contains_complete_composition") is not True:
                if source in seen_sources:
                    errors.append(layer_prefix + f"与 {seen_sources[source]} 重复使用同一源，不能冒充独立图层")
                else:
                    seen_sources[source] = layer_id
                    counted.append(layer)
                    counted_roles.add(role)
                    has_real_asset = has_real_asset or kind in REAL_ASSET_KINDS
            elif role and role not in NON_COUNTING_ROLES:
                errors.append(layer_prefix + f"未知或不可计数的视觉角色: {role}")

        if len(counted) < 3:
            errors.append(prefix + f"独立视觉层只有 {len(counted)} 个，至少需要 3 个；真人、字幕和重复图片不计入")
        if len(counted_roles) < 3:
            errors.append(prefix + "独立视觉层至少要覆盖 3 类不同职责")
        if not has_real_asset:
            errors.append(prefix + "缺少真实图片、照片、抠图、视频或纸媒资产，不能只用 CSS/SVG 抽象图形")
        if base_mode == "source_video_base_overlay":
            video_bases = [layer for layer in counted if layer.get("role") == "background" and layer.get("source_kind") == "video"]
            overlays = [layer for layer in counted if layer not in video_bases]
            if len(video_bases) != 1:
                errors.append(prefix + "原片底片叠层模式必须有且只有一个 background/video 原片底层")
            if len(overlays) < 3:
                errors.append(prefix + f"原片底片上方只有 {len(overlays)} 个独立视觉组件，至少需要 3 个")

    if errors:
        fail(errors)
    print(f"PASS: {len(scenes)} 个镜头通过 Vox 分层场景校验。")


if __name__ == "__main__":
    main()
