#!/usr/bin/env python3
"""Generate only an optional Director BGM preview. It never touches narration or video."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_SCRIPTS = ROOT / "vendor" / "vox-director" / "scripts"
MUSIC_MODEL = "minimax/music-2.6"


def load_provider():
    spec = importlib.util.spec_from_file_location("director_provider", VENDOR_SCRIPTS / "provider.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: generate_bgm_preview.py <fusion-run.json> <output.mp3>", file=sys.stderr)
        return 2
    manifest_path, output = Path(sys.argv[1]).expanduser().resolve(), Path(sys.argv[2]).expanduser().resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        music = manifest["project"]["music"]
        if music.get("mode") != "director_preview" or not music.get("requires_user_approval"):
            raise ValueError("manifest does not request a user-approved Director music preview")
        if not os.environ.get("ATLASCLOUD_API_KEY"):
            raise ValueError("ATLASCLOUD_API_KEY is required for the optional Director music preview")
        provider_module = load_provider()
        provider = provider_module.get_provider("atlas_cloud")
        jobs = {"bgm": lambda: provider.submit_audio(MUSIC_MODEL, prompt=music["prompt"], is_instrumental=True, format="mp3")}
        result = provider_module.run_jobs(provider, jobs, poll_s=4, stall_s=150, max_retries=2, deadline_s=600)
        url = result.get("bgm")
        if not url:
            raise ValueError("Director music service returned no preview")
        output.parent.mkdir(parents=True, exist_ok=True)
        provider.download(url, str(output))
        print(f"BGM preview created: {output}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"BGM preview not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
