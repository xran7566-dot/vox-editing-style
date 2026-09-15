#!/usr/bin/env python3
"""Wire existing local project entry points; preserve unrelated package scripts."""
import argparse
import json
from pathlib import Path
import shlex


def wire(root, skill):
    package=root/'package.json'
    d=json.loads(package.read_text())
    scripts=d.setdefault('scripts',{})
    validator=shlex.quote(str(skill/'scripts/validate_review.py'))
    renderer=shlex.quote(str(skill/'scripts/render_review.py'))
    scripts['check:review']='python3 '+validator+' --project-root . --stage sample-review'
    old=scripts.get('studio','remotion studio src/index.tsx --no-open')
    if 'npm run check:review' not in old:
        scripts['studio']='npm run check:review && '+old
    scripts['render']='python3 '+renderer+' --project-root . --kind final'
    scripts['render:sample']='python3 '+renderer+' --project-root . --kind sample'
    scripts['render:still']='python3 '+renderer+' --project-root . --kind still'
    package.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    build=root/'build-preview.cjs'
    if build.exists():
        s=build.read_text()
        if '// vox-review-gate' not in s:
            guard="// vox-review-gate: standalone compilation is a dynamic preview entry\nrequire('child_process').execFileSync('python3', ["+json.dumps(str(skill/'scripts/validate_review.py'))+", '--project-root', __dirname, '--stage', 'sample-review'], {stdio:'inherit'});\n"
            build.write_text(guard+s)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,required=True)
    p.add_argument('--skill-root',type=Path,default=Path(__file__).resolve().parent.parent)
    a=p.parse_args();wire(a.project_root.resolve(),a.skill_root.resolve())
