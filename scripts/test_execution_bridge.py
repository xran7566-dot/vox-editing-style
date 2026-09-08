"""Synthetic integration fixtures only; never approvals for user media."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from create_fusion_run import validate
from local_preprocess import fingerprint

ROOT=Path(__file__).resolve().parents[1]

class BridgeTests(unittest.TestCase):
    def put(self,name,data):
        p=self.root/name
        p.write_text(data if isinstance(data,str) else json.dumps(data),encoding='utf-8')
        return str(p)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        source=self.put('source.bin','synthetic media bytes')
        srt=self.put('approved.srt','1\n00:00:00,000 --> 00:00:00,800\n原话\n\n2\n00:00:02,000 --> 00:00:03,900\n继续\n')
        self.put('package.json',{})
        approval={'status':'approved','approved_by':'user','approved_at':'SYNTHETIC TEST ONLY'}
        self.candidates={'schema':'vox-rough-cut-candidates/v1','source_video':source,
          'source_sha256':fingerprint(source),'duration_seconds':4,'semantic_review':'complete',
          'approval':approval,'items':[{'time':[1,2],'category':'long_silence','status':'delete'}]}
        candidate=self.put('candidates.json',self.candidates)
        sound={'bgm_enabled':False,'emotion':'test','energy_curve':'test','must_avoid':['invent'], 'selection_rule':'test'}
        audit={'schema':'vox-source-audit/v1','project_name':'test','source_mode':'local_files',
          'public_source_urls':[],'duration_seconds':4,'review_script':self.put('review.md','test'),
          'source_artifacts':[{'id':'media','role':'source_video','path':source,'sha256':fingerprint(source)},
                              {'id':'srt','role':'srt','path':srt,'sha256':fingerprint(srt)}],
          'caption_confirmation':{'source':'user_srt','approved_srt_path':srt,'approved_by':'user','approved_at':'test'},
          'rough_cut_review':{'candidate_path':candidate,'candidate_sha256':fingerprint(candidate),**approval,
            'protected_categories':['small_breath','natural_pause','emotional_pause']},
          'creator_identity':{'creator_name':'test','account_name':'test','must_preserve':['voice'],'must_not_substitute':['identity']},
          'content_intent':'test','sound_direction':sound,
          'semantic_units':[{'id':'one','time':[0,4],'transcript_exact':'原话继续','takeaway':'test',
            'must_preserve':[],'must_not_invent':[],'sound_plan':{'bgm_role':'none','emotion':'test','sfx_events':[]}}],
          'reference_decisions':[],'uncertainties':[],'asset_gaps':[],'approval':approval}
        self.audit=audit
        self.doc={'project_name':'test','aspect':'9:16','duration_seconds':4,'source_video':source,'srt':srt,
          'source_audit':self.put('audit.json',audit),'remotion_source':str(self.root),'composition':'Test',
          'director_route':'director_first','watermark':'disabled','music':{'mode':'disabled'},'sound_direction':sound,
          'references':[],'semantic_units':[{'id':'one','time':[0,4],'takeaway':'test','visual_proposition':'test',
            'director_brief':{'relationship_to_make_visible':'test','must_preserve':[],'must_avoid':[]},
            'persona_brief':{'purpose':'test','allowed_forms':['round_window']},
            'visual':{'visual_source':'director_generated','director_asset_id':'fixture','director_asset_approved':True}}]}
    def run_validate(self): return validate(copy.deepcopy(self.doc),require_execution=True)
    def test_video_timeline_connected(self):
        result=self.run_validate()['execution']
        self.assertEqual(result['duration_seconds'],3)
        self.assertEqual(result['semantic_units'][0]['retained_spans'][1]['output_time'],[1,3])
        self.assertIn('00:00:01,000 --> 00:00:02,900',result['edited_srt'])
    def test_audio_path(self):
        self.doc['source_audio']=self.doc.pop('source_video')
        self.doc['semantic_units'][0]['persona_brief']['allowed_forms']=['voice_only']
        self.audit['source_artifacts'][0]['role']='source_audio'
        self.put('audit.json',self.audit)
        self.assertEqual(self.run_validate()['execution']['media_type'],'audio')
    def test_stale_runtime_rejected(self):
        self.doc=self.run_validate()
        self.doc['execution']['duration_seconds']=4
        with self.assertRaises(ValueError): self.run_validate()
    def test_unapproved_cut_rejected(self):
        self.candidates['approval']['status']='draft'
        self.put('candidates.json',self.candidates)
        self.audit['rough_cut_review']['candidate_sha256']=fingerprint(self.root/'candidates.json')
        self.put('audit.json',self.audit)
        with self.assertRaises(ValueError): self.run_validate()
    def template(self):
        scene=self.put('Scene.tsx','export const Scene = () => null; // synthetic')
        return {'visual_source':'shotcraft_template','approved':True,'selection_reason':'test',
          'recipe':'template/TEMPLATE.md','scene_path':scene,'scene_sha256':fingerprint(scene)}
    def test_template_route(self):
        self.doc['semantic_units'][0]['visual']=self.template()
        self.run_validate()
    def test_missing_template_rejected(self):
        v=self.template();v['recipe']='missing.md'
        self.doc['semantic_units'][0]['visual']=v
        with self.assertRaises(ValueError): self.run_validate()
    def test_broll_route(self):
        v=self.template();v['visual_source']='public_broll'
        asset=self.put('asset.bin','synthetic image')
        record={'schema':'vox-public-asset-record/v1','status':'qualified','provider':'pexels_web',
          'provider_page_url':'https://www.pexels.com/photo/test-1/','download_url':'https://images.pexels.com/test.png',
          'asset_path':asset,'sha256':fingerprint(asset),'material_type':'image','creator':'test',
          'layer_role':'test','semantic_reason':'test','timecode':'0-4','license_note':'synthetic only',
          'licence_checked':True,'adaptation':'test','rejected_risks':[],'downloaded_at':'test'}
        v['public_asset_record']=self.put('asset-record.json',record)
        self.doc['semantic_units'][0]['visual']=v
        self.run_validate()
        record['status']='rejected';self.put('asset-record.json',record)
        with self.assertRaises(ValueError): self.run_validate()
    def test_cli_exports_and_checks_props(self):
        inp=self.put('input.json',self.doc);run=self.root/'run'
        subprocess.run([sys.executable,str(ROOT/'scripts/create_fusion_run.py'),'--input',inp,'--run-dir',str(run)],check=True,capture_output=True)
        self.assertTrue((run/'edited.srt').is_file())
        for script,args in [('validate_fusion_run.py',[str(run/'fusion-run.json')]),
                            ('check_execution_props.py',[str(run/'fusion-run.json'),str(run/'execution.props.json')])]:
            subprocess.run([sys.executable,str(ROOT/'scripts'/script),*args],check=True,capture_output=True)

if __name__=='__main__': unittest.main()
