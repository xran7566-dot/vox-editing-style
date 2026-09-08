#!/usr/bin/env python3
"""Revalidate exported runtime props immediately before Remotion preview/render."""
import argparse
import json
from pathlib import Path
from create_fusion_run import validate

def main():
    p=argparse.ArgumentParser()
    p.add_argument('manifest'); p.add_argument('props')
    a=p.parse_args()
    manifest=json.loads(Path(a.manifest).read_text())
    if manifest.get('schema')!='vox-talking-head-fusion/v3':
        raise ValueError('recreate a v3 run to use approved execution props')
    doc=validate(manifest['project'],require_execution=True)
    props=json.loads(Path(a.props).read_text())
    if props.get('execution')!=doc['execution']:
        raise ValueError('runtime props differ from approved execution')
    print('PASS: runtime props match approved source, cuts and captions')

if __name__=='__main__': main()
