#!/usr/bin/env python3
"""Fill source artifact SHA-256 values without changing review or approval fields."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="draft source-audit.json")
    parser.add_argument("output", help="fingerprinted source-audit.json")
    args = parser.parse_args()
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    doc = json.loads(source.read_text(encoding="utf-8"))
    for artifact in doc.get("source_artifacts", []):
        path = Path(str(artifact.get("path", ""))).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"artifact path is missing: {path}")
        artifact["path"] = str(path)
        artifact["sha256"] = digest(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fingerprinted source audit: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
