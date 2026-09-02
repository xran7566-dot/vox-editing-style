#!/usr/bin/env python3
"""Create a validated, non-destructive fusion manifest for one talking-head video."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "vox-director"
VALID_ASPECTS = {"9:16", "16:9", "1:1", "3:4", "4:3"}
VALID_SCOPES = {"scene_solution", "visual_quality", "technical_mechanism", "system_anchor", "needs_user_decision"}
VALID_MUSIC_MODES = {"disabled", "local_track", "director_preview"}
VALID_PERSONA_FORMS = {"full_frame", "dynamic_cutout", "round_window", "square_window", "rectangle_window"}
FUSION_LAYERS = [
    "director_capabilities", "original_performance", "source_audit", "semantic_record", "visual_translation",
    "visual_system", "persona", "components", "mg", "platform", "keyframe_approval",
    "execution_audio", "qc_repair_versioning",
]

AUDIT_SPEC = importlib.util.spec_from_file_location("source_audit", Path(__file__).resolve().parent / "validate_source_audit.py")
assert AUDIT_SPEC and AUDIT_SPEC.loader
AUDIT_MODULE = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT_MODULE)


def fail(message: str) -> None:
    raise ValueError(message)


def local_file(value: object, label: str) -> str:
    path = Path(str(value)).expanduser().resolve()
    if not path.is_file():
        fail(f"{label} is missing or not a file: {path}")
    return str(path)


def local_dir(value: object, label: str) -> str:
    path = Path(str(value)).expanduser().resolve()
    if not path.is_dir():
        fail(f"{label} is missing or not a directory: {path}")
    return str(path)


def validate(doc: dict, *, require_source_audit: bool = True) -> dict:
    required = ("project_name", "aspect", "duration_seconds", "source_video", "remotion_source", "composition", "semantic_units", "references", "director_route", "watermark")
    for key in required:
        if key not in doc:
            fail(f"missing required field: {key}")
    if require_source_audit and "source_audit" not in doc:
        fail("missing required field: source_audit")
    if require_source_audit and "music" not in doc:
        fail("new v2 runs must set music; use local_track by default or disabled only after explicit opt-out")
    if require_source_audit and "sound_direction" not in doc:
        fail("new v2 runs must set sound_direction from the approved source audit")
    if doc.get("director_route") != "director_first":
        fail("director_route must be director_first; do not bypass Director with local SVG")
    if doc.get("watermark") != "disabled":
        fail("watermark must be disabled for Vox editing output")
    if doc["aspect"] not in VALID_ASPECTS:
        fail(f"unsupported aspect: {doc['aspect']}")
    if not isinstance(doc["duration_seconds"], (int, float)) or doc["duration_seconds"] <= 0:
        fail("duration_seconds must be positive")
    doc["source_video"] = local_file(doc["source_video"], "source_video")
    if doc.get("srt"):
        doc["srt"] = local_file(doc["srt"], "srt")
    if doc.get("source_audit"):
        doc["source_audit"] = local_file(doc["source_audit"], "source_audit")
        audit = AUDIT_MODULE.validate_audit(json.loads(Path(doc["source_audit"]).read_text(encoding="utf-8")))
        if audit["project_name"] != doc["project_name"]:
            fail("source audit project_name does not match fusion input")
        resolved = audit["_resolved_artifacts"]
        if resolved.get("source_video") != doc["source_video"]:
            fail("source audit source_video does not match fusion input")
        if doc.get("srt") and resolved.get("srt") != doc["srt"]:
            fail("source audit srt does not match fusion input")
        audit_units = {unit["id"]: unit["time"] for unit in audit["semantic_units"]}
        fusion_units = {unit["id"]: unit["time"] for unit in doc["semantic_units"]}
        if audit_units.keys() != fusion_units.keys():
            fail("fusion input semantic unit ids do not match source audit")
        for unit_id, span in fusion_units.items():
            if span != audit_units[unit_id]:
                fail(f"fusion input semantic unit time does not match source audit: {unit_id}")
        if doc.get("sound_direction") != audit["sound_direction"]:
            fail("fusion input sound_direction does not match source audit")
    doc["remotion_source"] = local_dir(doc["remotion_source"], "remotion_source")
    if not (Path(doc["remotion_source"]) / "package.json").is_file():
        fail("remotion_source has no package.json")
    if not isinstance(doc["semantic_units"], list) or not doc["semantic_units"]:
        fail("semantic_units must be a non-empty list")
    spans, unit_ids = [], set()
    for unit in doc["semantic_units"]:
        for key in ("id", "time", "takeaway", "visual_proposition", "director_brief", "persona_brief"):
            if key not in unit:
                fail(f"semantic unit missing {key}")
        if unit["id"] in unit_ids:
            fail(f"duplicate semantic unit id: {unit['id']}")
        visual = unit.get("visual", {})
        if visual.get("visual_source") != "director_generated":
            fail(f"semantic unit {unit['id']} must use director_generated visual_source")
        if not isinstance(visual.get("director_asset_id"), str) or not visual["director_asset_id"].strip():
            fail(f"semantic unit {unit['id']} missing director_asset_id")
        if visual.get("director_asset_approved") is not True:
            fail(f"semantic unit {unit['id']} Director asset is not approved")
        if visual.get("svg_role", "auxiliary_only") != "auxiliary_only":
            fail(f"semantic unit {unit['id']} cannot use SVG as the main visual")
        unit_ids.add(unit["id"])
        if not isinstance(unit["time"], list) or len(unit["time"]) != 2:
            fail(f"semantic unit {unit['id']} time must be [start, end]")
        start, end = unit["time"]
        if not (isinstance(start, (int, float)) and isinstance(end, (int, float)) and 0 <= start < end <= doc["duration_seconds"]):
            fail(f"semantic unit {unit['id']} has invalid time")
        brief = unit["director_brief"]
        if not isinstance(brief, dict):
            fail(f"semantic unit {unit['id']} director_brief must be an object")
        if not isinstance(brief.get("relationship_to_make_visible"), str) or not brief["relationship_to_make_visible"].strip():
            fail(f"semantic unit {unit['id']} needs a Director semantic relationship")
        for key in ("must_preserve", "must_avoid"):
            if not isinstance(brief.get(key), list):
                fail(f"semantic unit {unit['id']} director_brief.{key} must be a list")
        persona = unit["persona_brief"]
        if not isinstance(persona, dict) or not isinstance(persona.get("purpose"), str) or not persona["purpose"].strip():
            fail(f"semantic unit {unit['id']} needs a persona purpose")
        allowed_forms = persona.get("allowed_forms")
        if not isinstance(allowed_forms, list) or not allowed_forms or any(form not in VALID_PERSONA_FORMS for form in allowed_forms):
            fail(f"semantic unit {unit['id']} needs valid allowed dynamic persona forms")
        spans.append((start, end, unit["id"]))
    ordered = sorted(spans)
    for earlier, later in zip(ordered, ordered[1:]):
        if later[0] < earlier[1]:
            fail(f"semantic units overlap: {earlier[2]} and {later[2]}")
    for ref in doc["references"]:
        for key in ("id", "path", "scope", "applies_to"):
            if key not in ref:
                fail(f"reference missing {key}")
        if ref["scope"] not in VALID_SCOPES:
            fail(f"reference {ref['id']} has invalid scope")
        ref["path"] = local_file(ref["path"], f"reference {ref['id']}")
        if not isinstance(ref["applies_to"], list) or not ref["applies_to"]:
            fail(f"reference {ref['id']} needs applies_to")
        unknown = set(ref["applies_to"]) - unit_ids
        if unknown:
            fail(f"reference {ref['id']} names unknown units: {sorted(unknown)}")
    music = doc.get("music", {"mode": "disabled"})
    if not isinstance(music, dict) or music.get("mode") not in VALID_MUSIC_MODES:
        fail("music.mode must be disabled, local_track, or director_preview")
    if music["mode"] == "local_track":
        music["path"] = local_file(music.get("path"), "music.path")
    if music["mode"] == "director_preview":
        if not isinstance(music.get("prompt"), str) or not music["prompt"].strip():
            fail("director_preview needs a non-empty music.prompt")
        music["requires_user_approval"] = True
    if require_source_audit and "source_audit" in doc:
        audit_bgm_enabled = audit["sound_direction"]["bgm_enabled"]
        if audit_bgm_enabled and music["mode"] == "disabled":
            fail("source audit requires BGM, but fusion input disables it")
        if not audit_bgm_enabled and music["mode"] != "disabled":
            fail("source audit disables BGM, but fusion input enables a music track")
        if audit_bgm_enabled and audit["_resolved_artifacts"].get("bgm") != music.get("path"):
            fail("fusion input music.path does not match the fingerprinted BGM artifact")
    doc["music"] = music
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    source = Path(args.input).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    try:
        if not source.is_file():
            fail(f"input is missing: {source}")
        doc = validate(json.loads(source.read_text(encoding="utf-8")))
        if run_dir.exists() and any(run_dir.iterdir()):
            fail(f"run-dir must be new or empty: {run_dir}")
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "vox-talking-head-fusion/v2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "production_engine": "local_remotion",
            "prohibited_backends": ["tts", "image_to_video", "cloud_assembly"],
            "required_visual_backend": "vox_director",
            "permitted_optional_services": ["director_music_preview"],
            "director_vendor": str(VENDOR),
            "director_vendor_mode": "read_only",
            "reference_scope_protocol": "v1",
            "approval_frame_source": "director_asset_then_remotion_composition",
            "active_fusion_layers": FUSION_LAYERS,
            "project": doc,
            "workflow": ["source_audit_approved", "semantic_keyframes", "user_approval", "remotion_motion", "frame_qc", "segment_repair"],
        }
        target = run_dir / "fusion-run.json"
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(source, run_dir / "input.snapshot.json")
        print(f"Created: {target}")
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Fusion run not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
