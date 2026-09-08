"""Offline validation fixtures, not downloaded/licensed production assets."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class PublicSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.asset=self.root/'fixture.bin'
        self.asset.write_bytes(b'synthetic fixture only')
        self.doc={'schema':'vox-public-asset-record/v1','status':'qualified','provider':'pexels_web',
          'provider_page_url':'https://www.pexels.com/photo/test-1/',
          'download_url':'https://images.pexels.com/test.jpg','asset_path':str(self.asset),
          'sha256':hashlib.sha256(self.asset.read_bytes()).hexdigest(),'material_type':'image',
          'creator':'synthetic creator','layer_role':'test','semantic_reason':'test','timecode':'0-1',
          'license_note':'test fixture only','licence_checked':True,'adaptation':'test',
          'rejected_risks':[],'downloaded_at':'synthetic-test'}
    def check(self):
        record=self.root/'record.json'
        record.write_text(json.dumps(self.doc))
        return subprocess.run([sys.executable,str(Path(__file__).with_name('validate_public_asset_record.py')),str(record)],capture_output=True).returncode
    def test_pexels(self): self.assertEqual(self.check(),0)
    def test_pixabay(self):
        self.doc.update(provider='pixabay_web',provider_page_url='https://pixabay.com/photos/test-1/')
        self.assertEqual(self.check(),0)
    def test_wrong_host(self):
        self.doc['provider_page_url']='https://www.pexels.com.evil.invalid/test'
        self.assertNotEqual(self.check(),0)
    def test_rejected_asset(self):
        self.doc['status']='rejected'
        self.assertNotEqual(self.check(),0)
    def test_missing_creator(self):
        self.doc.pop('creator')
        self.assertNotEqual(self.check(),0)
    def test_wrong_fingerprint(self):
        self.asset.write_bytes(b'changed')
        self.assertNotEqual(self.check(),0)
    def test_pexels_not_music(self):
        self.doc['material_type']='audio'
        self.assertNotEqual(self.check(),0)

if __name__=='__main__': unittest.main()
