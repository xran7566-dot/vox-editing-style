#!/usr/bin/env python3
"""Local ASR and approved, non-destructive rough-cut timeline utilities."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess


def fingerprint(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def transcribe(args):
    from faster_whisper import WhisperModel
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'draft.srt').exists() or (output / 'asr.json').exists():
        raise ValueError('输出已存在；请复用或选择新目录')
    model = WhisperModel(args.model, device='cpu', compute_type='int8',
                         download_root=args.model_cache, local_files_only=not args.allow_download)
    segments, info = model.transcribe(args.source, language=args.language,
                                      word_timestamps=True, vad_filter=True)
    rows = []
    for s in segments:
        rows.append({'start': s.start, 'end': s.end, 'text': s.text,
                     'words': [{'start': w.start, 'end': w.end, 'text': w.word,
                                'probability': w.probability} for w in (s.words or [])]})
    with (output / 'draft.srt').open('x', encoding='utf-8') as stream:
        for i, row in enumerate(rows, 1):
            stream.write(f"{i}\n{stamp(row['start'])} --> {stamp(row['end'])}\n{row['text'].strip()}\n\n")
    save(output / 'asr.json', {'source': str(Path(args.source).resolve()),
         'sha256': fingerprint(args.source), 'model': args.model, 'language': info.language,
         'approval': 'pending_user', 'segments': rows})
    print(json.dumps({'segments': len(rows), 'draft': str(output / 'draft.srt'),
                      'status': 'pending_user'}, ensure_ascii=False))


def build_timeline(doc):
    if doc.get('schema') != 'vox-rough-cut-candidates/v1':
        raise ValueError('候选格式错误')
    if doc.get('semantic_review') != 'complete':
        raise ValueError('语义/气口试听检查尚未完成')
    if doc.get('approval', {}).get('status') != 'approved' or doc['approval'].get('approved_by') != 'user':
        raise ValueError('粗剪尚未由用户批准')
    if not doc['approval'].get('approved_at'):
        raise ValueError('缺少审批时间')
    source = Path(doc['source_video']).resolve()
    if fingerprint(source) != doc.get('source_sha256'):
        raise ValueError('原片指纹变化')
    duration = doc['duration_seconds']
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError('时长无效')
    cuts = []
    for item in doc['items']:
        if item['status'] not in ('delete', 'keep'):
            raise ValueError('仍有未确认的候选')
        a, b = item['time']
        if not (math.isfinite(a) and math.isfinite(b) and 0 <= a < b <= duration):
            raise ValueError('候选时间越界')
        if item['status'] == 'delete':
            if item['category'] in ('small_breath', 'natural_pause', 'emotional_pause'):
                raise ValueError('受保护停顿不能自动删除')
            cuts.append((a, b))
    cuts.sort()
    if any(b > c for (a, b), (c, d) in zip(cuts, cuts[1:])):
        raise ValueError('删除区间重叠')
    keep, cursor, target = [], 0.0, 0.0
    for a, b in cuts + [(duration, duration)]:
        if a > cursor:
            keep.append({'source_start': cursor, 'source_end': a,
                         'output_start': target, 'output_end': target + a - cursor})
            target += a - cursor
        cursor = b
    if not keep:
        raise ValueError('不可删除全部原片')
    return {'schema': 'vox-cut-timeline/v1', 'source_video': str(source),
            'source_sha256': doc['source_sha256'], 'segments': keep,
            'duration_seconds': target}


def remap_srt(content, timeline):
    """Keep approved words unchanged; partial-cue cuts require corrected boundaries."""
    def seconds(value):
        h, m, s = value.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    output = []
    for block in re.split(r'\n\s*\n', content.strip().replace('\r\n', '\n')):
        if not block.strip():
            continue
        lines = block.splitlines()
        if len(lines) < 3 or ' --> ' not in lines[1]:
            raise ValueError('SRT 格式不正确')
        a, b = map(seconds, lines[1].split(' --> '))
        if not 0 <= a < b:
            raise ValueError('字幕时间无效')
        overlaps = [s for s in timeline['segments'] if a < s['source_end'] and b > s['source_start']]
        if not overlaps:
            continue
        if len(overlaps) != 1 or a < overlaps[0]['source_start'] - 0.001 or b > overlaps[0]['source_end'] + 0.001:
            raise ValueError('切点穿过字幕句子，先按原声校正切点或拆分字幕并重新确认')
        s = overlaps[0]
        start = a - s['source_start'] + s['output_start']
        end = b - s['source_start'] + s['output_start']
        output.append(f'{len(output)+1}\n{stamp(start)} --> {stamp(end)}\n' + '\n'.join(lines[2:]))
    return '\n\n'.join(output) + ('\n' if output else '')


def detect_silence(args):
    if not (0 < args.threshold < 1 and args.min_silence > 0 and args.padding >= 0):
        raise ValueError('静音参数无效')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'json', args.source], check=True, capture_output=True, text=True)
    duration = float(json.loads(probe.stdout)['format']['duration'])
    result = subprocess.run([args.auto_editor, 'levels', args.source, '--edit', 'audio',
                             '--timebase', '30'], check=True, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if '@start' not in lines:
        raise ValueError('Auto-Editor levels 输出格式不匹配')
    levels = [float(s) for s in lines[lines.index('@start') + 1:] if s.strip()]
    if abs(len(levels) / 30 - duration) > 0.15:
        raise ValueError('音频长度与原片不一致，需检查时间基准')
    items, beginning = [], None
    for index, value in enumerate(levels + [1.0]):
        if value < args.threshold and beginning is None:
            beginning = index
        if value >= args.threshold and beginning is not None:
            start, end = beginning / 30, min(index / 30, duration)
            if end - start >= args.min_silence and end - start > 2 * args.padding:
                items.append({'id': f'silence-{len(items)+1}',
                    'time': [round(start + args.padding, 6), round(end - args.padding, 6)],
                    'detected_time': [start, end], 'category': 'long_silence',
                    'reason': 'Auto-Editor 音量低于阈值且超过最小时长，已保留两端留白；待试听',
                    'confidence': 'candidate_only', 'status': 'pending'})
            beginning = None
    save(args.output, {'schema': 'vox-rough-cut-candidates/v1',
        'source_video': str(Path(args.source).resolve()), 'source_sha256': fingerprint(args.source),
        'duration_seconds': duration, 'items': items,
        'detector': {'tool': 'auto-editor', 'timebase': 30, 'threshold': args.threshold,
                     'min_silence': args.min_silence, 'padding': args.padding},
        'semantic_review': 'pending', 'protected_categories': ['small_breath', 'natural_pause', 'emotional_pause'],
        'approval': {'status': 'draft', 'approved_by': '', 'approved_at': ''}})
    print(json.dumps({'silence_candidates': len(items), 'output': args.output,
                      'semantic_review': 'pending'}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('transcribe')
    p.add_argument('source'); p.add_argument('--output', required=True)
    p.add_argument('--model', default='base'); p.add_argument('--language', default='zh')
    p.add_argument('--model-cache', required=True)
    p.add_argument('--allow-download', action='store_true')
    p = sub.add_parser('silence')
    p.add_argument('source'); p.add_argument('--output', required=True)
    p.add_argument('--auto-editor', default='auto-editor')
    p.add_argument('--threshold', type=float, default=0.02)
    p.add_argument('--min-silence', type=float, default=0.8)
    p.add_argument('--padding', type=float, default=0.15)
    p = sub.add_parser('timeline')
    p.add_argument('candidates'); p.add_argument('--output', required=True)
    p = sub.add_parser('captions')
    p.add_argument('candidates'); p.add_argument('--srt', required=True)
    p.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'transcribe':
        transcribe(args)
    elif args.command == 'silence':
        detect_silence(args)
    else:
        doc = json.loads(Path(args.candidates).read_text(encoding='utf-8'))
        timeline = build_timeline(doc)
        if args.command == 'captions':
            mapped = remap_srt(Path(args.srt).read_text(encoding='utf-8-sig'), timeline)
            with Path(args.output).open('x', encoding='utf-8') as stream:
                stream.write(mapped)
            print('PASS: 字幕按批准时间轴映射，原字幕未覆盖')
            return
        timeline['approval_record'] = str(Path(args.candidates).resolve())
        timeline['approval_sha256'] = fingerprint(args.candidates)
        save(args.output, timeline)
        print(f'PASS: {len(timeline["segments"])} 个保留段 → {args.output}')


if __name__ == '__main__':
    main()
