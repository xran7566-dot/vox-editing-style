#!/usr/bin/env python3
"""Compatibility command: old stages use the single current evidence contract."""
import argparse
from pathlib import Path
import sys
from validate_review import validate

STAGE_MAP={'stills':'compose','sample':'sample-render','review-sample':'sample-review','full':'final-render'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',required=True,type=Path)
    parser.add_argument('--stage',choices=STAGE_MAP,required=True)
    a=parser.parse_args()
    errors=validate(a.project_root,STAGE_MAP[a.stage])
    if errors:
        print('Legacy command uses production/semantic-timeline.json and production/review.json; old review-plan approval is not migrated automatically.',file=sys.stderr)
        for error in errors: print('BLOCKED: '+error,file=sys.stderr)
        return 1
    print('PASS: evidence only; human visual/listening review remains required.')
    return 0

if __name__=='__main__': sys.exit(main())
