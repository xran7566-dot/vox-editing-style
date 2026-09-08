#!/usr/bin/env python3
"""Check immutable upstream files. Record only during an authorized vendor update."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/video-shotcraft'
MANIFEST = ROOT / 'assets/shotcraft-vendor-manifest.json'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', metavar='UPSTREAM_CHECKOUT')
    args = parser.parse_args()
    actual = {p.relative_to(VENDOR).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(VENDOR.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    if args.record:
        source = Path(args.record)
        version = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        for rel, digest in actual.items():
            assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == digest, rel
        with MANIFEST.open('x', encoding='utf-8') as stream:
            json.dump({'upstream': 'https://github.com/Vincentwei1021/video-shotcraft',
                       'commit': version, 'license': 'Apache-2.0',
                       'excluded': ['.git', '.github', '*.mp3', '*.mp4', 'node_modules', '__pycache__'],
                       'files': actual}, stream, indent=2, ensure_ascii=False)
    expected = json.loads(MANIFEST.read_text())['files']
    errors = [p for p in actual.keys() | expected.keys() if actual.get(p) != expected.get(p)]
    if errors:
        raise SystemExit('FAIL vendor drift: ' + ', '.join(errors[:20]))
    print(f'PASS: {len(actual)} upstream files unchanged')

if __name__ == '__main__':
    main()
