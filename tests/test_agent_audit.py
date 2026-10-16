"""Agent review gates use synthetic fixtures. Tests do not validate actual buildings."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'skills/campus-architectural-lineart/scripts'))
import test_photo_grounding as fixtures
import reference_pipeline as p
import agent_audit as a

class AgentAuditTests(unittest.TestCase):
    def setUp(self):
        self.fix=fixtures.PhotoGroundingTests('test_prepare_evidence_crops_and_prompt')
        self.fix.setUp()
        self.addCleanup(self.fix.tmp.cleanup)
        self.root=self.fix.root
        self.pack=self.fix.prepare()
        self.image=self.root/'drawing.png'
        Image.new('RGBA',(600,400),(0,0,0,255)).save(self.image)
        self.generation_log=self.root/'generation-log.json'
        self.record_log()

    def record_log(self):
        s=p.sha_file(self.image)
        self.log={'tool':'imaginary synthetic generation tool (QA only)',
            'image_input_confirmed':True,
            'final_image_sha256':s,
            'landmark_calls':[{'id':'BuildingA', 'tool':'synthetic fixture', 'image_input_confirmed':True,
                'reference_ids_attached':['style','BuildingA:front','BuildingA:side'], 'output_sha256':s}]}
        p.write_json(self.generation_log,self.log)

    def verdict(self, status='pass', confidence=.98, diff='none'):
        def check(fid,refs=['front']):
            return {'id':fid,'status':status,'confidence':confidence,'photo_ids':refs,
                    'observation':f'Synthetic candidate and original photo show aligned {fid} position and proportions.',
                    'difference':diff}
        return {'landmark_id':'BuildingA','features':[check('roof'),check('door')],
            'checks':[check(k,['front','side']) for k in a.REVIEW_CHECKS],
            'candidate_has_legible_text':False,
            'overall_notes':'The synthetic line drawing has been compared against both real image inputs in the test fixture.'}

    def backend(self, observations):
        call_count=[0]
        def review(*,model,prompt,pictures,max_side):
            idx=call_count[0]
            call_count[0]+=1
            self.assertEqual(len(pictures)>=3,True)
            self.assertEqual(set(i for i,_,_ in pictures[:3]),{'CANDIDATE:BuildingA','BuildingA:front','BuildingA:side'})
            return observations[min(idx,len(observations)-1)],{
                'response_id':f'mock-review-{idx}','model':model,'image_ids':[z[0] for z in pictures]}
        return review

    def run_audit(self, backend, **opts):
        return a.run(manifest_file=self.fix.manifest_file,lock_file=self.pack/'evidence-lock.json',
            image_file=self.image,output_dir=self.root/'result',generation_log_file=self.generation_log,
            model='synthetic-reviewer',backend=backend,**opts)

    def test_two_pass_consensus_approves_agent_only(self):
        r=self.run_audit(self.backend([self.verdict(),self.verdict()]))
        self.assertEqual(r['decision'],'agent_pass')
        approval=p.read_json(self.root/'result'/'approval.json')
        self.assertEqual(approval['status'],'approved')
        self.assertEqual(approval['review_mode'],'agent_vision_two_pass')
        self.assertIn('not human',approval['assurance'].lower())
        self.assertEqual(len(r['landmarks'][0]['passes']),2)

    def test_nonconsensus_low_confidence_escalates_and_creates_retry(self):
        r=self.run_audit(self.backend([self.verdict(),self.verdict(confidence=.51)]))
        self.assertEqual(r['decision'],'needs_review')
        self.assertEqual(p.read_json(self.root/'result'/'approval.json')['status'],'blocked')
        self.assertTrue((self.root/'result'/'retry-brief.md').exists())

    def test_hallucinated_geometry_escalates(self):
        r=self.run_audit(self.backend([self.verdict('fail',.98,'An extra roof and clock are unsupported'),self.verdict()]))
        self.assertEqual(r['decision'],'needs_review')
        self.assertTrue(any('roof' in q for q in r['problems']))

    def test_rejects_missing_evidence_citation_and_missing_feature(self):
        v=self.verdict()
        v['features'][0]['photo_ids']=['style']
        v['features'].pop()
        errors=a.evaluate_verdict(v,self.fix.manifest['landmarks'][0])
        self.assertTrue(any('missing/duplicate/extra' in x for x in errors))
        self.assertTrue(any('no valid photo evidence' in x for x in errors))

    def test_rejects_pass_with_reported_difference(self):
        v=self.verdict(diff='Clock on roof is invented')
        self.assertTrue(any('contradicts reported difference' in x for x in a.evaluate_verdict(v,self.fix.manifest['landmarks'][0])))

    def test_missing_generation_photo_inputs_fails_before_model_call(self):
        self.log['landmark_calls'][0]['reference_ids_attached']=['style','BuildingA:front']
        p.write_json(self.generation_log,self.log)
        called=[False]
        def none(**kwargs):called[0]=True;raise AssertionError('must not call')
        with self.assertRaisesRegex(ValueError,'generation evidence rejected'):
            self.run_audit(none)
        self.assertFalse(called[0])

    def test_photo_hash_changed_fails_before_model_call(self):
        with Image.open(self.root/'photos/b_front.png') as src:
            src.putpixel((7,9),(44,55,66))
            src.save(self.root/'photos/b_front.png')
        with self.assertRaisesRegex(ValueError,'evidence gate rejected'):
            self.run_audit(self.backend([self.verdict()]))

    def test_image_hash_changed_fails_generation_audit(self):
        Image.new('RGB',(600,400),'red').save(self.image)
        with self.assertRaisesRegex(ValueError,'generation evidence rejected'):
            self.run_audit(self.backend([self.verdict()]))

    def test_faithful_mode_escalates_unless_explicitly_allowed(self):
        self.fix.manifest['project']['mode']='photo-faithful'
        self.fix.save_manifest()
        self.pack=self.fix.prepare()
        r=self.run_audit(self.backend([self.verdict(),self.verdict()]))
        self.assertEqual(r['decision'],'needs_review')
        r=self.run_audit(self.backend([self.verdict(),self.verdict()]),allow_photo_faithful=True)
        self.assertEqual(r['decision'],'agent_pass')

    def test_candidate_composited_on_black_not_white(self):
        transparent=self.root/'transparent.png'
        img=Image.new('RGBA',(40,30),(255,255,255,0))
        img.putpixel((15,15),(255,255,255,255));img.save(transparent)
        v=a.image_blob(transparent,max_side=900,lineart=True)
        self.assertTrue(v['image_url'].startswith('data:image/jpeg;base64,'))
        self.assertEqual(v['detail'],'high')

    def test_native_agent_judgements_need_attached_image_ids(self):
        root=self.root/'verdicts';root.mkdir()
        for stage in ('feature','adversarial'):
            p.write_json(root/f'BuildingA__{stage}.json',{
                'tool_call_id':'native-vision-'+stage,'review_model':'test-vision-agent',
                'image_ids_seen':['CANDIDATE:BuildingA','BuildingA:front','BuildingA:side'],
                'input_sha256':{'CANDIDATE:BuildingA':p.sha_file(self.image),
                                'BuildingA:front':p.sha_file(self.root/'photos/b_front.png'),
                                'BuildingA:side':p.sha_file(self.root/'photos/b_side.png')},
                'report':self.verdict()})
        review=a.local_agent_backend(root)
        r=self.run_audit(review)
        self.assertEqual(r['decision'],'agent_pass')
        q=p.read_json(root/'BuildingA__adversarial.json');q['image_ids_seen']=['CANDIDATE:BuildingA']
        p.write_json(root/'BuildingA__adversarial.json',q)
        with self.assertRaisesRegex(ValueError,'did not declare seeing'):
            self.run_audit(review)

    def test_agent_json_refuses_stale_candidate_sha(self):
        d=self.root/'verdicts';d.mkdir()
        item={'tool_call_id':'native-review-call','review_model':'synthetic-vision',
              'image_ids_seen':['CANDIDATE:BuildingA','BuildingA:front','BuildingA:side'],
              'input_sha256':{'CANDIDATE:BuildingA':'0'*64,'BuildingA:front':p.sha_file(self.root/'photos/b_front.png'),
                              'BuildingA:side':p.sha_file(self.root/'photos/b_side.png')},
              'report':self.verdict()}
        p.write_json(d/'BuildingA__feature.json',item)
        with self.assertRaisesRegex(ValueError,'stale or mismatched'):
            self.run_audit(a.local_agent_backend(d))

    def test_no_key_is_not_a_fake_review(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(RuntimeError,'OPENAI_API_KEY'):
                a.openai_review(model='synthetic',prompt='test',pictures=[],max_side=1792)

    def test_real_responses_payload_contains_actual_reference_images(self):
        captured={}
        class FakeResponse:
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self):
                return json.dumps({'id':'resp-fixture-22','model':'test-vision','status':'completed',
                    'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self_verdict)}]}]}).encode()
        self_verdict=self.verdict()
        def fake_open(request,timeout):
            captured['body']=json.loads(request.data)
            captured['timeout']=timeout
            self.assertEqual(request.get_header('Authorization'),'Bearer test-fake-key')
            return FakeResponse()
        photos=[('CANDIDATE:BuildingA',self.image,True),
                ('BuildingA:front',self.root/'photos/b_front.png',False),
                ('BuildingA:side',self.root/'photos/b_side.png',False)]
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-fake-key'}),patch.object(a,'urlopen',fake_open):
            r,meta=a.openai_review(model='test-vision',prompt='Please review every feature',pictures=photos,max_side=900)
        self.assertEqual(r['landmark_id'],'BuildingA')
        self.assertEqual(meta['response_id'],'resp-fixture-22')
        items=captured['body']['input'][1]['content']
        self.assertEqual(sum(1 for x in items if x['type']=='input_image'),3)
        self.assertTrue(all(x['image_url'].startswith('data:image/jpeg;base64,') for x in items if x['type']=='input_image'))
        self.assertEqual(captured['body']['text']['format']['type'],'json_schema')
        self.assertFalse(captured['body']['store'])

    def test_agent_provenance_can_replace_human_for_public_licensed_photo(self):
        self.fix.manifest['landmarks'][0]['photos'][0]['human_confirmed_photo']=False
        photo=self.fix.manifest['landmarks'][0]['photos'][0]
        photo['source_page']='https://example.org/building-photo'
        photo['agent_confirmed_photo']=True
        photo['agent_evidence']={
            'confidence':.97,'model':'synthetic-vision-model','call_id':'synthetic-response-id',
            'source_page_checked':True,'building_identity_checked':True,'license_checked':True,
            'license_evidence_url':'https://example.org/usage-rights',
            'observation':'Compared photographed facade to named building and source record.'}
        self.fix.save_manifest()
        self.assertEqual(p.check_project(self.fix.manifest_file)['status'],'ready')
        photo['agent_evidence']['confidence']=.55
        self.fix.save_manifest()
        self.assertTrue(any('agent_evidence' in v for v in p.check_project(self.fix.manifest_file)['errors']))

    def test_agent_feature_evidence_can_replace_human_feature_review(self):
        feat=self.fix.manifest['landmarks'][0]['must_match'][0]
        feat['visible_and_human_verified']=False
        feat['visible_and_agent_verified']=True
        feat['agent_evidence']={'model':'synthetic-vis','call_id':'fixture123','confidence':.98,
            'observation':'Roof shape and placement match original photo from known front view',
            'image_input_ids':['BuildingA:front']}
        self.fix.save_manifest()
        self.assertEqual(p.check_project(self.fix.manifest_file)['status'],'ready')
        feat['agent_evidence']['image_input_ids']=['style']
        self.fix.save_manifest()
        self.assertTrue(any('agent visual evidence' in x for x in p.check_project(self.fix.manifest_file)['errors']))

if __name__=='__main__':unittest.main()
