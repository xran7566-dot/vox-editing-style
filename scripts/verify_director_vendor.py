#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "vox-director"

REQUIRED = [
    "LICENSE",
    "SKILL.md",
    "SKILL.zh.md",
    "package.json",
    "references/beat-layer.md",
    "references/prompt-guide.md",
    "references/local-engine.md",
    "references/models-and-gotchas.md",
    "scripts/styles.py",
    "scripts/style_bakeoff.py",
    "scripts/keyframes.py",
    "scripts/clips.py",
    "scripts/aroll_clips.py",
    "scripts/aroll_assemble.py",
    "scripts/croll_keyframes.py",
    "scripts/extract_elements.py",
    "scripts/motion.py",
    "scripts/mg_scrapbook.py",
    "scripts/audio.py",
    "scripts/assemble.py",
    "scripts/provider.py",
]


def main() -> int:
    missing = [rel for rel in REQUIRED if not (VENDOR / rel).is_file()]
    if missing:
        print("Director vendor is incomplete:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    license_text = (VENDOR / "LICENSE").read_text(encoding="utf-8")
    if "MIT License" not in license_text or "Alisa Qian" not in license_text:
        print("Director license attribution is missing or changed")
        return 1

    styles_text = (VENDOR / "scripts" / "styles.py").read_text(encoding="utf-8")
    if "THEME_PRESETS" not in styles_text:
        print("Director theme preset entry point is missing")
        return 1

    file_count = sum(1 for path in VENDOR.rglob("*") if path.is_file())
    print(f"Director vendor check passed: {file_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
