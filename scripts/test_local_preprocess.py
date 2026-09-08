import copy
import tempfile
import unittest
from pathlib import Path
from local_preprocess import build_timeline, fingerprint, remap_srt

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'synthetic.bin'
        self.source.write_bytes(b'synthetic test only')
        self.doc = {'schema':'vox-rough-cut-candidates/v1','source_video':str(self.source),
          'source_sha256':fingerprint(self.source),'duration_seconds':4,'semantic_review':'complete',
          'approval':{'status':'approved','approved_by':'user','approved_at':'synthetic-test'},
          'items':[{'time':[1.15,2.85],'category':'long_silence','status':'delete'}]}
    def test_mapping(self):
        result=build_timeline(self.doc)
        self.assertAlmostEqual(result['duration_seconds'],2.3)
        self.assertAlmostEqual(result['segments'][1]['output_start'],1.15)
    def test_pending_rejected(self):
        self.doc['approval']['status']='draft'
        with self.assertRaises(ValueError): build_timeline(self.doc)
    def test_semantics_required(self):
        self.doc['semantic_review']='pending'
        with self.assertRaises(ValueError): build_timeline(self.doc)
    def test_changed_source(self):
        self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError): build_timeline(self.doc)
    def test_protected_pause(self):
        for category in ['small_breath','natural_pause','emotional_pause']:
            self.doc['items'][0]['category']=category
            with self.assertRaises(ValueError): build_timeline(self.doc)
    def test_overlap(self):
        self.doc['items'].append(copy.deepcopy(self.doc['items'][0]))
        with self.assertRaises(ValueError): build_timeline(self.doc)
    def test_subtitle_words_preserved(self):
        srt='1\n00:00:00,000 --> 00:00:01,000\n原话不改\n\n2\n00:00:03,000 --> 00:00:04,000\n第二句\n'
        out=remap_srt(srt,build_timeline(self.doc))
        self.assertIn('00:00:01,300 --> 00:00:02,300',out)
        self.assertIn('原话不改',out)
        self.assertIn('第二句',out)
    def test_cut_through_words_rejected(self):
        with self.assertRaises(ValueError):
            remap_srt('1\n00:00:01,000 --> 00:00:02,000\n不可吞字',build_timeline(self.doc))
    def test_no_cut(self):
        self.doc['items']=[]
        self.assertEqual(build_timeline(self.doc)['duration_seconds'],4)

if __name__=='__main__': unittest.main()
