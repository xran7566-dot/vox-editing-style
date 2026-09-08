"""Validated source-time → render-time bridge. No media rewriting or network calls."""
import json
from pathlib import Path
import subprocess
import sys
from local_preprocess import build_timeline, fingerprint, remap_srt

ROOT = Path(__file__).resolve().parents[1]

def execution(doc, audit):
    candidates_path = Path(audit['rough_cut_review']['candidate_path'])
    candidates = json.loads(candidates_path.read_text(encoding='utf-8'))
    timeline = build_timeline(candidates)
    if abs(candidates['duration_seconds'] - doc['duration_seconds']) > 0.001:
        raise ValueError('source duration does not match approved cut candidates')
    captions = Path(audit['caption_confirmation']['approved_srt_path'])
    edited = remap_srt(captions.read_text(encoding='utf-8-sig'), timeline)
    units = []
    for unit in doc['semantic_units']:
        start, end = unit['time']
        spans = []
        for segment in timeline['segments']:
            a, b = max(start, segment['source_start']), min(end, segment['source_end'])
            if a < b:
                offset = segment['output_start'] - segment['source_start']
                spans.append({'source_time':[a,b], 'output_time':[a+offset,b+offset]})
        units.append({'id':unit['id'], 'retained_spans':spans})
    role = 'source_audio' if doc.get('source_audio') else 'source_video'
    return {'schema':'vox-execution/v1', 'media_type':'audio' if role=='source_audio' else 'video',
            'source':doc[role], 'source_sha256':timeline['source_sha256'],
            'approval_record':str(candidates_path.resolve()), 'approval_sha256':fingerprint(candidates_path),
            'source_srt_sha256':fingerprint(captions), 'duration_seconds':timeline['duration_seconds'],
            'segments':timeline['segments'], 'semantic_units':units, 'edited_srt':edited}

def validate_visual(unit):
    visual = unit.get('visual', {})
    source = visual.get('visual_source')
    if source == 'director_generated':
        if not visual.get('director_asset_id') or visual.get('director_asset_approved') is not True:
            raise ValueError('Director asset must be identified and approved')
    elif source in ('public_broll', 'shotcraft_template'):
        if visual.get('approved') is not True or not str(visual.get('selection_reason','')).strip():
            raise ValueError('B-roll/template needs explicit outline approval and semantic reason')
        if source == 'public_broll':
            record = Path(visual.get('public_asset_record',''))
            result = subprocess.run([sys.executable,str(ROOT/'scripts/validate_public_asset_record.py'),str(record)],capture_output=True,text=True)
            if result.returncode:
                raise ValueError('B-roll provenance failed: '+result.stdout.strip())
            provenance = json.loads(record.read_text())
            if provenance['material_type'] not in ('image','video'):
                raise ValueError('B-roll must be an image or video')
        else:
            root = (ROOT/'vendor/video-shotcraft').resolve()
            recipe = (root/visual.get('recipe','')).resolve()
            if not recipe.is_relative_to(root) or not recipe.is_file() or recipe.suffix != '.md':
                raise ValueError('shotcraft recipe is missing or outside bundled library')
        scene = Path(visual.get('scene_path',''))
        if not scene.is_file() or fingerprint(scene) != visual.get('scene_sha256'):
            raise ValueError('approved scene implementation missing or changed')
    else:
        raise ValueError('unsupported visual_source')
    if visual.get('svg_role','auxiliary_only') != 'auxiliary_only':
        raise ValueError('SVG cannot replace primary visual assets')
