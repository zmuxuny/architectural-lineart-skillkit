"""Mocked image-edits tests; does NOT make paid API calls or prove realism.

Checks the image generation gap that v0.4's planning/audit scripts leave for an
external image tool: genuine raw image attachments + hash-bound call records.
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'skills/campus-architectural-lineart/scripts'))
import integrated_edit as editor
import montage_audit
import compose_v2
import test_commemorative_montage as fixtures


class IntegratedEditTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.MontageAuditTests('test_final_integration_and_all_buildings_are_reviewed')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture=fixture
        self.root=fixture.root
        self.plan=fixture.plan
        self.brief=fixture.artwork/'draft'/'integrated-generation-brief.md'
        self.final=fixture.artwork/'new-integrated.png'
        self.log_file=fixture.artwork/'new-integrated-generation-log.json'

    def run_edit(self, backend):
        return editor.run(
            manifest_file=self.fixture.fixture.manifest_file,
            lock_file=self.fixture.pack/'evidence-lock.json',
            plan_file=self.plan,
            draft_file=self.fixture.draft,
            draft_evidence_file=self.fixture.artwork/'draft'/'draft-evidence.json',
            brief_file=self.brief,
            output_file=self.final,
            log_file=self.log_file,
            backend=backend,
        )

    def output_bytes(self):
        im=Image.new('RGB',(1536,864),'black')
        ImageDraw.Draw(im).ellipse((150,400,1350,750),outline='#bbbbbb',width=7)
        f=io.BytesIO();im.save(f,format='PNG')
        return f.getvalue()

    def test_real_inputs_and_log_feed_existing_final_audit(self):
        seen={}
        def mock_generator(*,model,size,prompt,images):
            seen['ids']=[label for label,_ in images]
            seen['prompt']=prompt
            self.assertEqual(len(images),6)
            self.assertEqual(seen['ids'][:2],['DRAFT','STYLE'])
            self.assertIn('PHOTO:BuildingA:front',seen['ids'])
            self.assertIn('PHOTO:BuildingB:front',seen['ids'])
            return self.output_bytes(),'req-real-from-mock-fixture',{'api_model':model,'size':[1536,864]}
        log=self.run_edit(mock_generator)
        self.assertIn('ONE',seen['prompt'])
        self.assertTrue(self.final.is_file())
        self.assertEqual(log['call_id'],'req-real-from-mock-fixture')
        self.assertEqual(log['reference_ids_attached'],seen['ids'])
        self.assertEqual(len(log['reference_image_sha256']),6)
        issues=montage_audit.validate_generation(
            manifest=self.fixture.fixture.manifest,
            plan=compose_v2.load_json(self.plan),
            plan_path=self.plan,
            evidence=compose_v2.load_json(self.fixture.artwork/'draft'/'draft-evidence.json'),
            draft=self.fixture.draft,
            final=self.final,
            log=log,
            cutouts=compose_v2.validate_plan(compose_v2.load_json(self.plan),self.plan.parent)
        )
        self.assertEqual(issues,[])

    def test_real_api_request_uploads_each_input_image(self):
        samples=[('DRAFT',self.fixture.draft),('CUTOUT:BuildingA',self.fixture.artwork/'cutouts'/'BuildingA.png')]
        data=self.output_bytes()
        captured={}
        class Reply:
            headers={'x-request-id':'req-from-images-api'}
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self):return json.dumps({'data':[{'b64_json':base64.b64encode(data).decode()}]}).encode()
        def fake_open(request,timeout):
            captured['body']=request.data
            captured['content_type']=request.get_header('Content-type')
            captured['auth']=request.get_header('Authorization')
            return Reply()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST-FAKE-KEY'}):
            generated,request_id,meta=editor.request_edit(
                model=editor.DEFAULT_MODEL,size='1536x864',prompt='Merge the buildings',
                images=samples,open_request=fake_open)
        self.assertEqual(generated,data)
        self.assertEqual(request_id,'req-from-images-api')
        self.assertEqual(meta['request_image_count'],2)
        self.assertEqual(captured['auth'],'Bearer TEST-FAKE-KEY')
        self.assertIn('multipart/form-data',captured['content_type'])
        self.assertEqual(captured['body'].count(b'name="image[]"'),2)
        self.assertIn(self.fixture.draft.read_bytes(),captured['body'])
        self.assertIn(samples[1][1].read_bytes(),captured['body'])
        self.assertNotIn(b'TEST-FAKE-KEY',captured['body'])

    def test_missing_key_refuses_to_make_up_a_generated_image(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(RuntimeError,'OPENAI_API_KEY missing'):
                editor.request_edit(model=editor.DEFAULT_MODEL,size='1536x864',
                                    prompt='test',images=[])

    def test_stale_cutout_refuses_before_model_call(self):
        altered=self.fixture.artwork/'cutouts'/'BuildingB.png'
        with Image.open(altered) as im:
            pic=im.copy();pic.putpixel((100,200),(230,230,230,210));pic.save(altered)
        called=[]
        def backend(**kwargs):
            called.append(True)
            return self.output_bytes(),'req',{}
        with self.assertRaisesRegex(ValueError,'cutout changed'):
            self.run_edit(backend)
        self.assertFalse(called)

    def test_identity_missing_cannot_write_unverifiable_log(self):
        with self.assertRaisesRegex(ValueError,'real API call identity'):
            self.run_edit(lambda **kwargs:(self.output_bytes(),'',{}))
        self.assertFalse(self.log_file.exists())
        self.assertFalse(self.final.exists())

    def test_draft_as_final_is_rejected(self):
        b=self.fixture.draft.read_bytes()
        with self.assertRaisesRegex(ValueError,'no integrated redraw'):
            self.run_edit(lambda **kwargs:(b,'req-from-test',{}))
        self.assertFalse(self.log_file.exists())


if __name__=='__main__':unittest.main()
