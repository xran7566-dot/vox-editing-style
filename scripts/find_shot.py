#!/usr/bin/env python3
"""Small filtered view; never dump the single-line full gallery index to the agent."""
import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('query')
p.add_argument('--limit', type=int, default=5)
a = p.parse_args()
cards = json.loads((root / 'vendor/video-shotcraft/gallery/api/library.json').read_text())['cards']
matches = [c for c in cards if a.query.lower() in (c['name']+' '+c.get('summary','')).lower()]
for c in matches[:max(1, min(a.limit, 10))]:
    print(json.dumps({k: c[k] for k in ('name','summary','source')}, ensure_ascii=False))
print(f'Matches: {len(matches)}; displayed: {min(len(matches), max(1,min(a.limit,10)))}')
