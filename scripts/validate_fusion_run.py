#!/usr/bin/env python3
"""Validate an existing fusion manifest without changing project or Vendor files."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("fusion_bootstrap", HERE / "create_fusion_run.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_fusion_run.py <fusion-run.json>", file=sys.stderr)
        return 2
    try:
        path = Path(sys.argv[1]).expanduser().resolve()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        schema = manifest.get("schema")
        if schema not in {"vox-talking-head-fusion/v1", "vox-talking-head-fusion/v2"}:
            raise ValueError("unsupported manifest schema")
        if manifest.get("production_engine") != "local_remotion":
            raise ValueError("fusion must use local_remotion")
        if manifest.get("director_vendor_mode") != "read_only":
            raise ValueError("Director vendor must remain read_only")
        if manifest.get("required_visual_backend") != "vox_director":
            raise ValueError("fusion must require vox_director as the visual backend")
        project = manifest.get("project", {})
        if project.get("director_route") != "director_first":
            raise ValueError("fusion project must use director_first route")
        if project.get("watermark") != "disabled":
            raise ValueError("fusion project watermark must be disabled")
        MODULE.validate(project, require_source_audit=schema == "vox-talking-head-fusion/v2")
        print(f"Fusion run check passed: {path}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Fusion run check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
