#!/usr/bin/env python3
"""Local Remotion entry point. No install, download or approval fabrication."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from validate_review import fingerprint, sha, validate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, required=True)
    p.add_argument('--kind', choices=['still','sample','final'], required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frame', type=int)
    p.add_argument('--start', type=int)
    p.add_argument('--end', type=int)
    p.add_argument('--browser-executable')
    a=p.parse_args(); root=a.project_root.resolve()
    stage={'still':'compose','sample':'sample-render','final':'final-render'}[a.kind]
    errors=validate(root,stage)
    if errors:
        sys.exit('\n'.join('BLOCKED: '+e for e in errors))
    timeline=json.loads((root/'production/semantic-timeline.json').read_text())
    count=timeline['duration_frames']
    if a.kind=='still' and (a.frame is None or not 0<=a.frame<count):
        p.error('still needs an in-range --frame')
    if a.kind=='sample' and (a.start is None or a.end is None or not 0<=a.start<=a.end<count):
        p.error('sample needs an in-range --start / --end')
    output=a.output.resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    before=fingerprint(root)
    cmd=[str(root/'node_modules/.bin/remotion'), 'still' if a.kind=='still' else 'render', 'src/index.tsx', timeline['composition'], str(output)]
    if a.kind=='still': cmd+=['--frame='+str(a.frame)]
    elif a.kind=='sample': cmd+=['--frames=%s-%s'%(a.start,a.end)]
    if a.browser_executable: cmd+=['--browser-executable='+a.browser_executable]
    subprocess.run(cmd,cwd=root,check=True)
    if fingerprint(root)!=before:
        sys.exit('BLOCKED: project changed during render; no receipt issued')
    receipt={'kind':a.kind,'project_sha256':before,'composition':timeline['composition'],'artifact_sha256':sha(output),'command':cmd}
    if a.kind=='still': receipt['frame']=a.frame
    else: receipt.update(start_frame=a.start if a.kind=='sample' else 0,end_frame=a.end if a.kind=='sample' else count-1)
    Path(str(output)+'.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print('Output rendered. Run the corresponding review gate before presenting it.')

if __name__=='__main__': main()
