#!/usr/bin/env python3
"""Validate a user-approved source audit before a Vox fusion run."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "vox-source-audit/v1"
VALID_SOURCE_MODES = {"local_files", "public_link", "mixed"}
VALID_ROLES = {"source_video", "srt", "transcript", "screen_recording", "brand_asset", "reference", "bgm"}
VALID_SCOPES = {"scene_solution", "visual_quality", "technical_mechanism", "system_anchor", "needs_user_decision"}
VALID_ISSUE_STATUS = {"resolved", "accepted", "blocking"}


def fail(message: str) -> None:
    raise ValueError(message)


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value.strip()


def local_file(value: object, label: str) -> Path:
    path = Path(text(value, label)).expanduser().resolve()
    if not path.is_file():
        fail(f"{label} is missing or not a file: {path}")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def string_list(value: object, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        fail(f"{label} must be a list of non-empty strings")
    if not allow_empty and not value:
        fail(f"{label} must not be empty")
    return value


def validate_audit(doc: dict) -> dict:
    required = (
        "schema", "project_name", "source_mode", "public_source_urls", "duration_seconds",
        "review_script", "source_artifacts", "creator_identity", "content_intent",
        "sound_direction", "semantic_units", "reference_decisions", "uncertainties", "asset_gaps", "approval",
    )
    for key in required:
        if key not in doc:
            fail(f"missing required field: {key}")
    if doc["schema"] != SCHEMA:
        fail(f"unsupported source audit schema: {doc['schema']}")
    text(doc["project_name"], "project_name")
    if doc["source_mode"] not in VALID_SOURCE_MODES:
        fail(f"source_mode must be one of {sorted(VALID_SOURCE_MODES)}")
    urls = string_list(doc["public_source_urls"], "public_source_urls")
    if doc["source_mode"] in {"public_link", "mixed"} and not urls:
        fail("public_link or mixed source_mode needs public_source_urls")
    duration = doc["duration_seconds"]
    if not isinstance(duration, (int, float)) or duration <= 0:
        fail("duration_seconds must be positive")
    review_script = local_file(doc["review_script"], "review_script")
    if review_script.stat().st_size == 0:
        fail("review_script must not be empty")

    artifacts = doc["source_artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        fail("source_artifacts must be a non-empty list")
    ids, roles = set(), set()
    resolved_artifacts = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            fail("each source artifact must be an object")
        artifact_id = text(artifact.get("id"), "source_artifact.id")
        if artifact_id in ids:
            fail(f"duplicate source artifact id: {artifact_id}")
        ids.add(artifact_id)
        role = artifact.get("role")
        if role not in VALID_ROLES:
            fail(f"source artifact {artifact_id} has invalid role: {role}")
        path = local_file(artifact.get("path"), f"source artifact {artifact_id}.path")
        expected = text(artifact.get("sha256"), f"source artifact {artifact_id}.sha256").lower()
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            fail(f"source artifact {artifact_id} has invalid sha256")
        actual = sha256(path)
        if actual != expected:
            fail(f"source artifact {artifact_id} fingerprint changed: expected {expected}, got {actual}")
        roles.add(role)
        resolved_artifacts[role] = str(path)
    if "source_video" not in roles:
        fail("source_artifacts needs a source_video")
    if not ({"srt", "transcript"} & roles):
        fail("source_artifacts needs at least one srt or transcript")

    identity = doc["creator_identity"]
    if not isinstance(identity, dict):
        fail("creator_identity must be an object")
    text(identity.get("creator_name"), "creator_identity.creator_name")
    text(identity.get("account_name"), "creator_identity.account_name")
    string_list(identity.get("must_preserve"), "creator_identity.must_preserve", allow_empty=False)
    string_list(identity.get("must_not_substitute"), "creator_identity.must_not_substitute", allow_empty=False)
    text(doc["content_intent"], "content_intent")
    sound = doc["sound_direction"]
    if not isinstance(sound, dict):
        fail("sound_direction must be an object")
    if not isinstance(sound.get("bgm_enabled"), bool):
        fail("sound_direction.bgm_enabled must be boolean")
    text(sound.get("emotion"), "sound_direction.emotion")
    text(sound.get("energy_curve"), "sound_direction.energy_curve")
    text(sound.get("selection_rule"), "sound_direction.selection_rule")
    string_list(sound.get("must_avoid"), "sound_direction.must_avoid", allow_empty=False)
    if sound["bgm_enabled"] and "bgm" not in roles:
        fail("sound_direction enables BGM but source_artifacts has no bgm")

    units = doc["semantic_units"]
    if not isinstance(units, list) or not units:
        fail("semantic_units must be a non-empty list")
    unit_ids, spans = set(), []
    for unit in units:
        if not isinstance(unit, dict):
            fail("each semantic unit must be an object")
        unit_id = text(unit.get("id"), "semantic_unit.id")
        if unit_id in unit_ids:
            fail(f"duplicate semantic unit id: {unit_id}")
        unit_ids.add(unit_id)
        span = unit.get("time")
        if not isinstance(span, list) or len(span) != 2:
            fail(f"semantic unit {unit_id} time must be [start, end]")
        start, end = span
        if not (isinstance(start, (int, float)) and isinstance(end, (int, float)) and 0 <= start < end <= duration):
            fail(f"semantic unit {unit_id} has invalid time")
        text(unit.get("transcript_exact"), f"semantic unit {unit_id}.transcript_exact")
        text(unit.get("takeaway"), f"semantic unit {unit_id}.takeaway")
        string_list(unit.get("must_preserve"), f"semantic unit {unit_id}.must_preserve")
        string_list(unit.get("must_not_invent"), f"semantic unit {unit_id}.must_not_invent")
        plan = unit.get("sound_plan")
        if not isinstance(plan, dict):
            fail(f"semantic unit {unit_id}.sound_plan must be an object")
        text(plan.get("bgm_role"), f"semantic unit {unit_id}.sound_plan.bgm_role")
        text(plan.get("emotion"), f"semantic unit {unit_id}.sound_plan.emotion")
        events = plan.get("sfx_events")
        if not isinstance(events, list):
            fail(f"semantic unit {unit_id}.sound_plan.sfx_events must be a list")
        for event in events:
            if not isinstance(event, dict):
                fail(f"semantic unit {unit_id}.sound_plan.sfx_events items must be objects")
            text(event.get("semantic_event"), f"semantic unit {unit_id}.sfx_event.semantic_event")
            text(event.get("type"), f"semantic unit {unit_id}.sfx_event.type")
            text(event.get("intensity"), f"semantic unit {unit_id}.sfx_event.intensity")
        spans.append((start, end, unit_id))
    ordered = sorted(spans)
    for earlier, later in zip(ordered, ordered[1:]):
        if later[0] < earlier[1]:
            fail(f"semantic units overlap: {earlier[2]} and {later[2]}")

    refs = doc["reference_decisions"]
    if not isinstance(refs, list):
        fail("reference_decisions must be a list")
    for ref in refs:
        ref_id = text(ref.get("id") if isinstance(ref, dict) else None, "reference_decision.id")
        if ref.get("scope") not in VALID_SCOPES:
            fail(f"reference decision {ref_id} has invalid scope")
        applies_to = string_list(ref.get("applies_to"), f"reference decision {ref_id}.applies_to", allow_empty=False)
        unknown = set(applies_to) - unit_ids
        if unknown:
            fail(f"reference decision {ref_id} names unknown units: {sorted(unknown)}")

    for field in ("uncertainties", "asset_gaps"):
        issues = doc[field]
        if not isinstance(issues, list):
            fail(f"{field} must be a list")
        for issue in issues:
            if not isinstance(issue, dict):
                fail(f"each {field} item must be an object")
            item = text(issue.get("item"), f"{field}.item")
            status = issue.get("status")
            if status not in VALID_ISSUE_STATUS:
                fail(f"{field} item '{item}' has invalid status: {status}")
            if status == "blocking":
                fail(f"{field} has blocking item: {item}")

    approval = doc["approval"]
    if not isinstance(approval, dict):
        fail("approval must be an object")
    if approval.get("status") != "approved":
        fail("approval.status must be approved")
    if approval.get("approved_by") != "user":
        fail("approval.approved_by must be user")
    text(approval.get("approved_at"), "approval.approved_at")
    doc["_resolved_artifacts"] = resolved_artifacts
    return doc


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_source_audit.py <source-audit.json>", file=sys.stderr)
        return 2
    try:
        path = Path(sys.argv[1]).expanduser().resolve()
        audit = validate_audit(json.loads(path.read_text(encoding="utf-8")))
        audit.pop("_resolved_artifacts", None)
        print(f"Source audit check passed: {path}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Source audit check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
