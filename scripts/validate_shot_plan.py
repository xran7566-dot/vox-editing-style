#!/usr/bin/env python3
"""Check required directing handoff, not whether its creative choices are good."""
import json
from pathlib import Path

PERSONA_MODES = {'full', 'circle', 'rectangle', 'collage', 'brief_cameo', 'voice_only'}

def validate_shot_plan(root, timeline, manifest, stage, artifact, probe):
    root=Path(root)
    def need(ok, message):
        if not ok: raise ValueError(message)
    plan=json.loads((root/'production/shot-plan.json').read_text())
    need(plan.get('version')==1, 'shot-plan version must be 1')
    # Reports are real files; the checker cannot authenticate author observations.
    for key in ('directing_report','source_observation'):
        p=artifact(root,plan[key]);need(bool(p.read_text().strip()), 'empty '+key)
    need(plan['source_audio']==timeline['original_audio'], 'shot plan uses different original source')
    shots=plan['shots']; scenes=timeline['scenes']; layers=manifest['scenes']
    need(bool(shots) and len(shots)==len(scenes), 'shot coverage differs from timeline')
    ids=[s['id'] for s in shots]
    need(len(ids)==len(set(ids)) and ids==[s['id'] for s in scenes], 'shot IDs/order differ from timeline')
    need(set(ids)=={s['id'] for s in layers}, 'shot coverage differs from layer manifest')
    captions=json.loads(artifact(root,timeline['captions']).read_text())
    for shot,scene in zip(shots,scenes):
        need(shot['range']==scene['range'], 'shot duration differs from implemented scene')
        need(shot['persona_mode'] in PERSONA_MODES, 'missing/invalid persona_mode')
        for key in ('purpose','persona_reason','framing','main_action','new_information','handoff','visual_family'):
            need(isinstance(shot.get(key),str) and bool(shot[key].strip()), 'shot missing '+key)
        expected=[c['id'] for c in captions if c['start_frame']<shot['range'][1] and c['end_frame']>shot['range'][0]]
        need(shot['source_cue_ids']==expected, 'shot does not cover its exact source cues')
        layer=next(s for s in layers if s['id']==shot['id'])
        component=artifact(root,shot['implementation'])
        need(component.resolve()==(root/layer['remotion_component']).resolve(), 'shot implementation differs from layer manifest')
        if layer['base_mode']=='presenter_anchor':
            need(shot['persona_mode']=='full', 'presenter anchor requires full persona mode')
        if shot['persona_mode']!='voice_only':
            info=probe(artifact(root,shot['presenter_source']))
            need(any(s['codec_type']=='video' for s in info['streams']), 'presenter source is not video')
    # Repetition is flagged as a review obligation, not an automatic aesthetic failure.
    runs=[]
    for s in shots:
        if runs and runs[-1]['family']==s['visual_family']:
            runs[-1]['end']=s['range'][1];runs[-1]['ids'].append(s['id'])
        else:runs.append(dict(family=s['visual_family'],start=s['range'][0],end=s['range'][1],ids=[s['id']]))
    long_runs=[r for r in runs if (r['end']-r['start'])/timeline['fps']>8]
    if long_runs:
        record=plan.get('continuity_review',{})
        report=artifact(root,record)
        need(bool(report.read_text().strip()), 'long same-family run needs continuity review')
        need(record.get('shot_ids')==[s for r in long_runs for s in r['ids']], 'continuity review does not identify long repeated shots')
    if stage!='compose':
        review=json.loads((root/'production/evidence/sequence-review.json').read_text())
        need(review['decision']=='ready_for_user', 'sequence review needs revision')
        report=artifact(root,review['report']);need(bool(report.read_text().strip()), 'empty sequence report')
        need(review['shot_ids']==ids, 'sequence review misses shots')
        need(bool(review['contact_sheets']), 'sequence review missing actual composite contact sheet')
        for image in review['contact_sheets']:
            info=probe(artifact(root,image));need(any(s['codec_type']=='video' for s in info['streams']), 'invalid sequence contact sheet')
    return plan
