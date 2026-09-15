#!/usr/bin/env python3
"""Evidence gate, not an aesthetic judge or an authentication service."""
import argparse
import array
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess
import sys

STAGES = ('compose', 'keyframes', 'sample-render', 'sample-review', 'final-render', 'final-review')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(root):
    # Include imported data, code, assets, masks, subtitles, plans and configuration.
    paths = set()
    for folder in ('src', 'public'):
        paths.update(p for p in (root / folder).rglob('*') if p.is_file())
    paths.update(p for p in root.glob('*') if p.is_file() and p.suffix in ('.json', '.ts', '.cjs', '.js'))
    for name in ('layer-manifest.json', 'semantic-timeline.json', 'asset-plan.json'):
        p = root / 'production' / name
        if p.exists():
            paths.add(p)
    paths.update(p for p in (root / 'production' / 'mg').rglob('*') if p.is_file())
    if not paths:
        raise ValueError('empty project')
    return hashlib.sha256(json.dumps({str(p.relative_to(root)): sha(p) for p in sorted(paths)}, sort_keys=True).encode()).hexdigest()


def subtitles(path):
    cues = {}
    pattern = r'(\d+)\s*\n(\d\d):(\d\d):(\d\d)[,.](\d{3}) --> (\d\d):(\d\d):(\d\d)[,.](\d{3})[^\n]*\n(.*?)(?=\n\s*\n|\Z)'
    for m in re.finditer(pattern, Path(path).read_text(encoding='utf-8-sig'), re.S):
        if int(m[1]) in cues:
            raise ValueError('duplicate source SRT cue')
        cues[int(m[1])] = m[10].replace('\n','').strip()
    if not cues:
        raise ValueError('no valid source SRT cues')
    return cues


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], stderr=subprocess.PIPE))


def artifact(root, record):
    if not isinstance(record, dict) or not record.get('path') or not record.get('sha256'):
        raise ValueError('missing file path / sha256')
    p = root / record['path']
    if not p.is_file() or sha(p) != record['sha256']:
        raise ValueError('missing or changed artifact: ' + str(p))
    return p


def pcm(path, start, duration):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(start), '-i', str(path), '-t', str(duration), '-vn', '-ac', '1', '-ar', '8000', '-f', 's16le', '-'], stderr=subprocess.PIPE)
    values = array.array('h', data)
    if sys.byteorder != 'little':
        values.byteswap()
    return values


def voice_match(source, output, start, duration):
    a, b = pcm(source, start, duration), pcm(output, 0, duration)
    n = min(len(a), len(b))
    if n < duration * 8000 * .95:
        raise ValueError('audio does not cover the requested duration')
    ea = sum(x*x for x in a[:n]); eb = sum(x*x for x in b[:n])
    if min(ea, eb) / n < 16:
        raise ValueError('silent audio')
    # Tolerate small codec delays; a presence/alignment check, not listening QC.
    best = 0
    for shift in range(-160, 161, 8):
        left = a[max(0, shift):n + min(0, shift):4]
        right = b[max(0, -shift):n - max(0, shift):4]
        aa = sum(x*x for x in left); bb = sum(x*x for x in right)
        if aa and bb:
            best = max(best, sum(x*y for x,y in zip(left,right)) / math.sqrt(aa*bb))
    if best < .65:
        raise ValueError('original voice absent or misaligned (correlation %.3f)' % best)
    return best


def validate(root, stage):
    root = Path(root).resolve()
    errors = []
    def check(label, fn):
        try:
            return fn()
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            errors.append(label + ': ' + str(exc))
    def need(ok, message):
        if not ok:
            raise ValueError(message)
    def read(name):
        data = json.loads((root / 'production' / name).read_text())
        if not isinstance(data, dict) or not data:
            raise ValueError('expected nonempty evidence object')
        return data
    layer = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_layer_manifest.py')), str(root/'production/layer-manifest.json'), '--project-root', str(root)], capture_output=True, text=True)
    if layer.returncode:
        errors.append('structure: ' + layer.stderr.strip())
    timeline = check('timeline', lambda: read('semantic-timeline.json'))
    plan = check('asset-plan', lambda: read('asset-plan.json'))
    if timeline:
        def timing():
            fps, duration = timeline['fps'], timeline['duration_frames']
            need(isinstance(fps,(int,float)) and math.isfinite(fps) and fps > 0 and isinstance(duration,int) and duration > 0, 'invalid duration / fps')
            audio = artifact(root, timeline['original_audio'])
            info = probe(audio)
            need(any(s['codec_type']=='audio' for s in info['streams']), 'no original audio stream')
            need(float(info['format']['duration']) + 1/fps >= duration/fps, 'original audio is too short')
            cues = json.loads(artifact(root, timeline['captions']).read_text())
            approved = subtitles(artifact(root, timeline['approved_srt']))
            for c in cues:
                need(approved[c['id']]==c['text'].replace('\n','').strip(), 'caption text differs from approved SRT')
                need(0<=c['start_frame']<c['end_frame']<=duration, 'invalid caption range')
            cue_ids = {c['id']:c for c in cues}
            need(len(cue_ids)==len(cues), 'duplicate caption IDs')
            scenes = timeline['scenes']
            manifest = read('layer-manifest.json')
            scene_ids = {c['id'] for c in scenes}
            need(bool(scenes) and len(scene_ids)==len(scenes) and scene_ids=={c['id'] for c in manifest['scenes']}, 'scene coverage differs from layer manifest')
            previous = None
            for scene in scenes:
                start,end = scene['range']
                need(0<=start<end<=duration and (previous is None or start==previous), 'scene ranges must be ordered and contiguous')
                need(all(scene.get(k) for k in ('new_information','relationship','handoff')), 'scene narrative handoff missing')
                previous=end
            if timeline['scope']=='full':
                need(scenes[0]['range'][0]==0 and scenes[-1]['range'][1]==duration, 'full scope does not cover full timeline')
            events = timeline['events']; need(bool(events), 'no semantic events')
            need({e['scene_id'] for e in events}==scene_ids, 'scene missing semantic events')
            ids = set()
            for e in events:
                need(e['id'] not in ids, 'duplicate event: '+e['id']); ids.add(e['id'])
                c = cue_ids[e['cue_id']]
                scene = next(s for s in scenes if s['id']==e['scene_id'])
                need(scene['range'][0]<=e['frame']<scene['range'][1], 'event outside scene')
                need(bool(e['quote']) and e['quote'] in c['text'], 'event quote not in locked caption')
                need(0 <= e['frame'] < duration and c['start_frame'] <= e['frame'] < c['end_frame'], 'event outside its spoken cue')
                need(e['before'] != e['after'] and all(e.get(k) for k in ('before','after','information','text_role','relation')), 'empty or unchanged event states')
                need(e['sfx']['mode'] in ('none', 'file'), 'sfx mode must be explicit')
                if e['sfx']['mode']=='none':
                    need(bool(e['sfx'].get('reason')), 'missing reason for no SFX')
                else:
                    artifact(root, e['sfx']['asset'])
                    need(e['sfx']['frame']==e['frame'], 'SFX does not share the action event')
        check('semantic/audio mapping', timing)
    if plan:
        def assets():
            need(bool(plan['assets']), 'empty asset plan')
            ids = set()
            covered_files = set()
            for a in plan['assets']:
                need(a['id'] not in ids, 'duplicate asset ID'); ids.add(a['id'])
                covered_files.add(artifact(root, a['file']).resolve())
                need(all(a.get(k) for k in ('origin','purpose','composition','states','occlusion','text_role')), 'missing generation-to-composition design')
                if a['origin']=='generated' and stage not in ('compose','keyframes'):
                    need(bool(a.get('director_asset_id')), 'missing Director ID')
                    artifact(root, a['prompt'])
                # A report with actual image evidence is required; approved=true is ignored.
                if stage=='compose':
                    continue
                qc = a['inspection']
                need(qc['decision']=='usable' and bool(qc['observations']), 'asset not inspected / rejected')
                artifact(root, qc['report'])
                need(bool(qc['images']), 'missing inspected image evidence')
                for img in qc['images']:
                    probe(artifact(root, img))
            manifest = read('layer-manifest.json')
            for scene in manifest['scenes']:
                for layer in scene.get('layers', []):
                    if layer.get('source_kind') in ('image','photo','cutout','paper','texture'):
                        for source in [layer['source']] + layer.get('variants', []):
                            need((root/source).resolve() in covered_files, 'asset plan does not cover used source: '+source)
        check('asset acceptance', assets)
    if stage=='compose' or errors:
        return errors
    if stage in ('final-render', 'final-review') and timeline.get('scope') != 'full':
        return ['full rendering blocked: only a segment has been prepared']
    current = fingerprint(root)
    review = check('review packet', lambda: read('review.json'))
    if not review:
        return errors
    def evidence(record, kind):
        p = artifact(root, record)
        receipt = json.loads(artifact(root, record['receipt']).read_text())
        need(receipt['project_sha256']==current, 'stale project receipt')
        need(receipt['artifact_sha256']==sha(p) and receipt['kind']==kind, 'receipt does not match output/type')
        need(receipt['composition']==timeline['composition'], 'wrong composition')
        info = probe(p)
        need(any(s['codec_type']=='video' for s in info['streams']), 'no decoded image/video')
        if kind=='still':
            need(p.suffix.lower()=='.png', 'keyframe must be a PNG still')
            need(receipt['frame']==record['frame'], 'wrong still frame')
        return p, receipt
    def keyframes():
        need(review['project_sha256']==current, 'stale review packet')
        need(bool(review['keyframes']), 'no actual composite keyframes')
        covered = set()
        for k in review['keyframes']:
            evidence(k, 'still')
            event = next(e for e in timeline['events'] if e['id']==k['event_id'])
            need(k['frame']==event['frame'], 'keyframe is not at its semantic event frame')
            need(k['quote']==event['quote'] and all(k.get(v) for v in ('focus','expected_action')), 'missing keyframe annotations')
            need(0<=k['frame']<timeline['duration_frames'], 'keyframe out of range')
            covered.add(k['event_id'])
        need(set(review['required_event_ids']) <= covered and bool(review['required_event_ids']), 'missing required semantic keyframes')
        need(set(e['id'] for e in timeline['events'] if e.get('review_required', True)) <= covered, 'timeline review event missing')
        qc = review['internal_visual_review']
        artifact(root, qc['report'])
        need(qc['decision']=='ready_for_user' and qc['project_sha256']==current and bool(qc['observations']), 'internal visual review incomplete/stale')
    check('composite keyframes', keyframes)
    if stage=='keyframes' or errors:
        return errors
    def approval(name, records):
        a = review[name]
        need(a['by']=='user' and a['decision']=='approved', 'explicit user approval required')
        need(a['project_sha256']==current, 'stale user approval')
        message = artifact(root, a['message']).read_text()
        need(bool(a['quote'].strip()) and a['quote'] in message and bool(a['source_reference']), 'missing original user message / source reference')
        need(a['artifact_sha256s']==[r['sha256'] for r in records], 'approval applies to different artifacts')
    check('keyframe user approval', lambda: approval('keyframe_approval', review['keyframes']))
    if stage=='sample-render' or errors:
        return errors
    def movie(name, kind):
        record = review[name]
        p, receipt = evidence(record, kind)
        start, end = receipt['start_frame'], receipt['end_frame']
        need(0<=start<=end<timeline['duration_frames'], 'invalid render range')
        if kind=='final':
            need(start==0 and end==timeline['duration_frames']-1, 'final does not cover full timeline')
        duration = (end-start+1)/timeline['fps']
        info = probe(p)
        need(any(s['codec_type']=='audio' for s in info['streams']), 'output has no audio stream')
        need(abs(float(info['format']['duration'])-duration)<.15, 'output duration mismatch')
        voice_match(artifact(root,timeline['original_audio']),p,start/timeline['fps'],duration)
    check('sample audio/output', lambda: movie('sample', 'sample'))
    if stage=='sample-review' or errors:
        return errors
    check('sample user approval', lambda: approval('sample_approval', [review['sample']]))
    def audition():
        q = review['internal_audio_review']
        artifact(root, q['report'])
        need(q['project_sha256']==current and q['sample_sha256']==review['sample']['sha256'] and q['decision']=='ready_for_user', 'stale/missing listening review')
        need(all(q.get(k) for k in ('voice_only','voice_with_sfx','observations')), 'listening observations missing')
    check('listening review', audition)
    if stage=='final-review' and not errors:
        check('final audio/output', lambda: movie('final', 'final'))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, required=True)
    p.add_argument('--stage', choices=STAGES, required=True)
    p.add_argument('--fingerprint', action='store_true')
    args = p.parse_args()
    if args.fingerprint:
        print(fingerprint(args.project_root.resolve())); return
    try:
        errors = validate(args.project_root, args.stage)
    except (KeyError, TypeError, ValueError, OSError, StopIteration) as exc:
        errors = ['malformed evidence: '+str(exc)]
    for error in errors:
        print('BLOCKED: '+error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print('PASS: '+args.stage+' evidence checks only; human visual/listening review is not replaced.')

if __name__=='__main__':
    main()
