#!/usr/bin/env python3
"""Synthetic fixtures only. These approvals never authorize a real project."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from validate_review import fingerprint, sha, validate

class ReviewGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='vox-gate-')
        cls.base = Path(cls.temp.name)/'base'
        r=cls.base
        for p in ('src','public','production/evidence','production/mg'):
            (r/p).mkdir(parents=True)
        def ff(*args):
            subprocess.run(['ffmpeg','-v','error','-y',*args],check=True)
        ff('-f','lavfi','-i','color=c=blue:s=160x90','-frames:v','1',str(r/'public/layer.png'))
        ff('-f','lavfi','-i','aevalsrc=0.2*sin(2*PI*(220*t+95*t*t)):s=8000:d=2',str(r/'public/voice.wav'))
        ff('-loop','1','-i',str(r/'public/layer.png'),'-i',str(r/'public/voice.wav'),'-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(r/'production/evidence/sample.mp4'))
        ff('-loop','1','-i',str(r/'public/layer.png'),'-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(r/'production/evidence/silent.mp4'))
        ff('-loop','1','-i',str(r/'public/layer.png'),'-f','lavfi','-i','anullsrc=r=8000:cl=mono','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(r/'production/evidence/zero.mp4'))
        ff('-loop','1','-i',str(r/'public/layer.png'),'-f','lavfi','-i','sine=frequency=900:duration=2','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(r/'production/evidence/wrong.mp4'))
        (r/'src/index.tsx').write_text('// Synthetic fixture, not a production composition\n')
        (r/'production/mg/scene.md').write_text('Synthetic relation test')
        (r/'production/evidence/qc.md').write_text('Synthetic report; not a real visual or listening review.')
        (r/'production/evidence/message.txt').write_text('SYNTHETIC USER: approve these fixture frames and sample')
        shutil.copy2(r/'public/layer.png',r/'production/evidence/frame.png')
        def ref(p): return {'path':p,'sha256':sha(r/p)}
        def save(p,d): (r/p).write_text(json.dumps(d))
        (r/'public/approved.srt').write_text('1\n00:00:00,000 --> 00:00:02,000\nsynthetic cue\n')
        save('public/captions.json',[{'id':1,'text':'synthetic cue','start_frame':0,'end_frame':60}])
        layers=[{'id':str(i),'role':role,'source_kind':'image','source':'public/'+str(i)+'.png','semantic_function':'fixture role','entry':'enter','relation':'relate','settle':'settle','exit':'leave'} for i,role in enumerate(('background','subject','foreground'))]
        for l in layers: shutil.copy2(r/'public/layer.png',r/l['source'])
        save('production/layer-manifest.json',{'version':1,'approval':{'status':'approved'},'scenes':[{'id':'test','timecode':'0-2','base_mode':'collage_main_with_presenter','mg_task_file':'production/mg/scene.md','remotion_component':'src/index.tsx','layers':layers}]})
        save('production/semantic-timeline.json',{'scope':'full','approved_srt':ref('public/approved.srt'),'scenes':[{'id':'test','range':[0,60],'new_information':'fixture','relationship':'attach','handoff':'end'}],'composition':'Fixture','fps':30,'duration_frames':60,'original_audio':ref('public/voice.wav'),'captions':ref('public/captions.json'),'events':[{'id':'cue','scene_id':'test','cue_id':1,'quote':'synthetic cue','frame':30,'before':'separate','after':'connected','information':'connection','text_role':'label','relation':'attach','sfx':{'mode':'none','reason':'fixture'}}]})
        save('production/asset-plan.json',{'assets':[{'id':'a','file':ref('public/layer.png'),'origin':'local','purpose':'fixture','composition':'center','states':'apart then connected','occlusion':'front','text_role':'label','inspection':{'decision':'usable','observations':'synthetic only','report':ref('production/evidence/qc.md'),'images':[ref('public/layer.png')]}}]})
        asset_plan=json.loads((r/'production/asset-plan.json').read_text())
        base_asset=asset_plan['assets'][0]
        for i,l in enumerate(layers):
            a=copy.deepcopy(base_asset);a['id']='layer-'+str(i);a['file']=ref(l['source']);asset_plan['assets'].append(a)
        save('production/asset-plan.json',asset_plan)
        cls.seal(r)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    @staticmethod
    def seal(r, movie='sample.mp4'):
        def ref(p): return {'path':p,'sha256':sha(r/p)}
        fp=fingerprint(r)
        for name,kind in [('frame.png','still'),(movie,'sample')]:
            receipt={'project_sha256':fp,'artifact_sha256':sha(r/'production/evidence'/name),'kind':kind,'composition':'Fixture'}
            if kind=='still': receipt['frame']=30
            else: receipt.update(start_frame=0,end_frame=59)
            (r/('production/evidence/'+name+'.receipt.json')).write_text(json.dumps(receipt))
        k=ref('production/evidence/frame.png'); k.update(receipt=ref('production/evidence/frame.png.receipt.json'),frame=30,event_id='cue',quote='synthetic cue',focus='fixture focus',expected_action='fixture action')
        sample=ref('production/evidence/'+movie);sample['receipt']=ref('production/evidence/'+movie+'.receipt.json')
        def approval(items): return {'by':'user','decision':'approved','project_sha256':fp,'artifact_sha256s':[i['sha256'] for i in items],'message':ref('production/evidence/message.txt'),'quote':'approve these fixture frames and sample','source_reference':'SYNTHETIC fixture only'}
        d={'project_sha256':fp,'keyframes':[k],'required_event_ids':['cue'],'internal_visual_review':{'project_sha256':fp,'decision':'ready_for_user','observations':'fixture observation','report':ref('production/evidence/qc.md')},'keyframe_approval':approval([k]),'sample':sample,'sample_approval':approval([sample]),'internal_audio_review':{'project_sha256':fp,'sample_sha256':sample['sha256'],'decision':'ready_for_user','voice_only':'fixture','voice_with_sfx':'fixture','observations':'fixture','report':ref('production/evidence/qc.md')}}
        (r/'production/review.json').write_text(json.dumps(d))

    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='vox-case-');self.r=Path(self.t.name)/'project';shutil.copytree(self.base,self.r)
    def tearDown(self):self.t.cleanup()
    def edit(self,name,fn):
        p=self.r/'production'/name;d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d))
    def blocked(self,stage,word):
        errors=validate(self.r,stage);self.assertTrue(errors);self.assertIn(word,'\n'.join(errors))
    def test_positive_stages(self):
        for stage in ('compose','keyframes','sample-render','sample-review','final-render'):
            self.assertEqual(validate(self.r,stage),[],stage)
    def test_positive_final_review(self):
        receipt=self.r/'production/evidence/final.receipt.json'
        receipt.write_text(json.dumps({'project_sha256':fingerprint(self.r),'artifact_sha256':sha(self.r/'production/evidence/sample.mp4'),'kind':'final','composition':'Fixture','start_frame':0,'end_frame':59}))
        def add(d):
            d['final']=copy.deepcopy(d['sample'])
            d['final']['receipt']={'path':'production/evidence/final.receipt.json','sha256':sha(receipt)}
        self.edit('review.json',add)
        self.assertEqual(validate(self.r,'final-review'),[])
    def test_no_listening_review_blocks_final(self):
        self.edit('review.json',lambda d:d.pop('internal_audio_review'))
        self.blocked('final-render','listening review')
    def test_static_does_not_need_user_approval(self):
        self.edit('review.json',lambda d:d.pop('keyframe_approval'))
        self.assertEqual(validate(self.r,'keyframes'),[])
        self.blocked('sample-render','keyframe_approval')
    def test_static_can_inspect_pending_assets(self):
        self.edit('asset-plan.json',lambda d:d['assets'][0].update(inspection={'decision':'pending'}))
        self.assertEqual(validate(self.r,'compose'),[])
        self.blocked('keyframes','asset not inspected')
    def test_source_subtitle_text_cannot_change(self):
        (self.r/'public/approved.srt').write_text('1\n00:00:00,000 --> 00:00:02,000\ndifferent text\n')
        self.edit('semantic-timeline.json',lambda d:d['approved_srt'].update(sha256=sha(self.r/'public/approved.srt')))
        self.blocked('compose','differs from approved')
    def test_full_scope_needs_full_coverage(self):
        self.edit('semantic-timeline.json',lambda d:d['scenes'][0].update(range=[0,50]))
        self.blocked('compose','full scope')
    def test_empty_evidence_cannot_pass(self):
        (self.r/'production/semantic-timeline.json').write_text('{}')
        self.blocked('compose','nonempty')
    def test_missing_used_asset(self):
        self.edit('asset-plan.json',lambda d:d['assets'].pop())
        self.blocked('compose','does not cover')
    def test_bool_approval_not_enough(self):
        self.edit('review.json',lambda d:d.update(keyframe_approval={'status':'approved'}))
        self.blocked('sample-render','approval')
    def test_agent_cannot_approve_keyframes(self):
        self.edit('review.json',lambda d:d['keyframe_approval'].update(by='agent'))
        self.blocked('sample-render','user approval')
    def test_changed_source_invalidates_approval(self):
        (self.r/'src/index.tsx').write_text('// changed')
        self.blocked('sample-render','stale')
    def test_changed_keyframe_invalidates_receipt(self):
        (self.r/'production/evidence/frame.png').write_bytes(b'changed')
        self.blocked('sample-render','changed artifact')
    def test_keyframe_must_match_event_frame(self):
        self.edit('semantic-timeline.json',lambda d:d['events'][0].update(frame=31))
        self.seal(self.r)
        self.blocked('keyframes','semantic event frame')
    def test_missing_keyframe(self):
        self.edit('review.json',lambda d:d.update(keyframes=[]))
        self.blocked('sample-render','no actual')
    def test_missing_original_voice(self):
        (self.r/'public/voice.wav').unlink()
        self.blocked('sample-render','voice.wav')
    def test_rejected_asset(self):
        self.edit('asset-plan.json',lambda d:d['assets'][0]['inspection'].update(decision='rejected'))
        self.blocked('keyframes','rejected')
    def test_unmapped_event(self):
        self.edit('semantic-timeline.json',lambda d:d['events'][0].update(frame=90))
        self.blocked('compose','outside')
    def test_no_information_change(self):
        self.edit('semantic-timeline.json',lambda d:d['events'][0].update(after='separate'))
        self.blocked('compose','unchanged')
    def test_sound_not_shared_event(self):
        self.edit('semantic-timeline.json',lambda d:d['events'][0].update(sfx={'mode':'file','frame':0,'asset':d['original_audio']}))
        self.blocked('compose','share')
    def test_output_without_audio(self):
        self.seal(self.r,'silent.mp4');self.blocked('sample-review','no audio')
    def test_silent_audio_track(self):
        self.seal(self.r,'zero.mp4');self.blocked('sample-review','silent')
    def test_wrong_audio(self):
        self.seal(self.r,'wrong.mp4');self.blocked('sample-review','absent or misaligned')
    def test_segment_cannot_render_full(self):
        self.edit('semantic-timeline.json',lambda d:d.update(scope='segment'))
        self.blocked('final-render','only a segment')
    def test_presenter_anchor_without_decorative_layers(self):
        self.edit('layer-manifest.json',lambda d:d['scenes'][0].update(base_mode='presenter_anchor',layers=[],anchor_reason='approved presenter expression',outline_evidence='fixture approved outline',source_video='production/evidence/sample.mp4'))
        self.assertEqual(validate(self.r,'compose'),[])
    def test_wired_entrypoints_block_before_execution(self):
        from wire_review_gate import wire
        marker=self.r/'should-not-exist'
        (self.r/'package.json').write_text(json.dumps({'scripts':{'studio':'node -e "require(\\\"fs\\\").writeFileSync(\\\"should-not-exist\\\",\\\"bad\\\")"'}}))
        (self.r/'build-preview.cjs').write_text("require('fs').writeFileSync('should-not-exist','bad');")
        wire(self.r,Path(__file__).resolve().parent.parent)
        wire(self.r,Path(__file__).resolve().parent.parent)
        self.seal(self.r)
        self.edit('review.json',lambda d:d.pop('keyframe_approval'))
        for command in (['npm','run','studio'],['node','build-preview.cjs']):
            result=subprocess.run(command,cwd=self.r,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse(marker.exists())
        self.seal(self.r)
        result=subprocess.run(['node','build-preview.cjs'],cwd=self.r,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(marker.exists())

    def test_wiring_upgrades_legacy_preview_guard(self):
        from wire_review_gate import wire
        (self.r/'package.json').write_text('{"scripts":{}}')
        build=self.r/'build-preview.cjs'
        build.write_text("// vox-review-gate: standalone compilation is a dynamic preview entry\nrequire('child_process').execFileSync('python3', ['old-validator', '--stage', 'sample-render']);\nconsole.log('existing body');\n")
        wire(self.r,Path(__file__).resolve().parent.parent)
        self.assertNotIn('sample-render',build.read_text())
        self.assertIn('sample-review',build.read_text())
        self.assertIn("console.log('existing body')",build.read_text())
        first=build.read_bytes()
        wire(self.r,Path(__file__).resolve().parent.parent)
        self.assertEqual(build.read_bytes(),first)

    def test_collage_still_requires_layers(self):
        self.edit('layer-manifest.json',lambda d:d['scenes'][0].update(layers=[]))
        self.blocked('compose','structure')

if __name__=='__main__': unittest.main(verbosity=2)
