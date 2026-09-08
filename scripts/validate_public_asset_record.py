#!/usr/bin/env python3
"""Validate provenance for one optional public material used by Vox."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


def fail(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 Vox 公共素材来源记录")
    parser.add_argument("record")
    args = parser.parse_args()
    try:
        record_path = Path(args.record).expanduser().resolve()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        required = ("schema", "status", "provider", "provider_page_url", "download_url", "asset_path", "sha256", "material_type", "layer_role", "semantic_reason", "timecode", "license_note", "licence_checked", "adaptation", "rejected_risks", "downloaded_at")
        missing = [key for key in required if key not in record]
        if missing:
            fail(f"缺少字段: {', '.join(missing)}")
        if record["schema"] != "vox-public-asset-record/v1":
            fail("schema 必须为 vox-public-asset-record/v1")
        if record["status"] != "qualified":
            fail("只有 qualified 公共素材可以进入分层清单")
        provider = str(record["provider"])
        page_url = str(record["provider_page_url"])
        hosts = {"pixabay_web": {"pixabay.com", "www.pixabay.com"},
                 "pexels_web": {"pexels.com", "www.pexels.com"}}
        if provider not in hosts:
            fail("当前网站来源必须为 pixabay_web 或 pexels_web；API 需另行接通")
        parsed = urlparse(page_url)
        if parsed.scheme != "https" or parsed.hostname not in hosts[provider] or parsed.username or parsed.password:
            fail("来源页必须为对应素材网站的 HTTPS 页面")
        if provider == "pexels_web":
            if record["material_type"] not in {"image", "video", "texture", "cutout"}:
                fail("Pexels 网站仅用于图片或视频类素材")
            if not isinstance(record.get("creator"), str) or not record["creator"].strip():
                fail("Pexels 素材须记录创作者")
        if not str(record["download_url"]).startswith("https://"):
            fail("download_url 必须为 HTTPS URL")
        asset = Path(str(record["asset_path"])).expanduser().resolve()
        if not asset.is_file():
            fail(f"素材文件不存在: {asset}")
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        if digest != str(record["sha256"]).lower():
            fail("素材 SHA-256 与来源记录不一致")
        if record["material_type"] not in {"image", "video", "audio", "sound_effect", "texture", "cutout"}:
            fail("material_type 无效")
        if not isinstance(record["rejected_risks"], list) or not record["licence_checked"]:
            fail("必须完成许可核对并记录风险筛查")
        for key in ("layer_role", "semantic_reason", "timecode", "license_note", "adaptation", "downloaded_at"):
            if not isinstance(record[key], str) or not record[key].strip():
                fail(f"{key} 必须为非空文字")
        print(f"PASS: 公共素材来源记录有效: {record_path}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
