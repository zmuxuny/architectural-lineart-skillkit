"""Synthetic fixtures only. They test evidence gates, NOT real-life architectural truth."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent


def load_script(relative):
    file=ROOT/relative
    spec=importlib.util.spec_from_file_location(file.stem,file)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


p=load_script('skills/campus-architectural-lineart/scripts/reference_pipeline.py')
c=load_script('skills/campus-architectural-lineart/scripts/compose.py')
v=load_script('skills/raster-to-layered-svg/scripts/convert.py')


class PhotoGroundingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'photos').mkdir()
        im=Image.new('RGB',(1000,600),'black')
        ImageDraw.Draw(im).rectangle((20,330,950,570),fill=(180,180,180))
        im.save(self.root/'photos/style.png')
        for i, angle in enumerate(['front', 'side']):
            im=Image.new('RGB',(1700,1100),(198+5*i,216+2*i,226))
            d=ImageDraw.Draw(im)
            if i==0:
                d.polygon([(140,550),(850,220),(1500,550)],fill=(120,58,38))
                d.rectangle((150,550,1520,1080),fill=(151,75,50))
                d.rectangle((680,750,1040,1080),fill=(40,26,24))
            else:
                d.polygon([(200,350),(1470,520),(1450,580),(150,480)],fill=(110,69,50))
                d.rectangle((230,500,1530,1060),fill=(158,65,55))
                for x in range(250,1350,180):
                    d.rectangle((x,650,x+80,920),fill=(45,23,20))
            im.save(self.root/f'photos/b_{angle}.png')
        self.manifest={
            'schema_version':1,
            'project':{'title':'SYNTHETIC QA FIXTURE - NOT A REAL BUILDING', 'mode':'montage','aspect_ratio':'16:9','upper_blank_fraction':.6},
            'style_reference':'photos/style.png',
            'landmarks':[{'id':'BuildingA','name':'SYNTHETIC STRUCTURE','location':'TEST FIXTURE ONLY',
                          'primary_view_id':'front', 'photos':[self.make_view('front'),self.make_view('side')],
                          'must_match':[
                              {'id':'roof','description':'Synthetic triangular roof in fixture', 'photo_ids':['front'], 'visible_and_human_verified':True,'bbox':[.1,.2,.9,.6]},
                              {'id':'door','description':'Synthetic central doorway in fixture', 'photo_ids':['front'], 'visible_and_human_verified':True,'bbox':[.3,.6,.7,.98]}
                          ],
                          'forbidden_inventions':['No extra towers or windows'],
                          'unknowns':['rear wall not visible'],
                          'signage_policy':'no_generated_letters_use_verified_overlay',
                          'official_marks':[]}]}
        self.save_manifest()


    def make_view(self,angle):
        return {'id':angle,'file':f'photos/b_{angle}.png','source_page':'user-owned','original_url':'',
                'photographer':'synthetic test script','license':'user-owned','derivatives_allowed':True,
                'human_confirmed_photo':True,'source_verified_by':'TEST SIMULATION ONLY','view_angle':angle}


    def save_manifest(self):
        self.manifest_file=self.root/'project.json'
        p.write_json(self.manifest_file,self.manifest)


    def prepare(self):
        dest=self.root/'pack'
        ret=p.run_prepare(self.manifest_file,dest)
        self.assertEqual(ret,0)
        return dest


    def approved_review(self,pack):
        r=p.read_json(pack/'review-template.json')
        r['reviewer']='Human QA example - simulated test data'
        r['model_invocation']={'tool':'synthetic test tool', 'image_input_confirmed':True, 'reference_ids_attached':['style','BuildingA:front','BuildingA:side'], 'landmark_calls':[{'id':'BuildingA','tool':'synthetic test tool','image_input_confirmed':True,'reference_ids_attached':['style','BuildingA:front','BuildingA:side']}]}
        for k in r['global_checks']:r['global_checks'][k]='pass'
        r['landmark_reviews'][0]['no_new_geometry']='pass'
        r['landmark_reviews'][0]['source_comparison_note']='Synthetic fixture: manually mocked source review for unit testing only'
        r['landmark_reviews'][0]['features']={'roof':'pass','door':'pass'}
        review=self.root/'review.json'
        p.write_json(review,r)
        return review


    def test_template_is_fail_closed(self):
        dest=self.root/'template.json'
        p.template(dest)
        result=p.check_project(dest)
        self.assertEqual(result['status'],'blocked')
        self.assertTrue(any('source_verified_by' in s for s in result['errors']))


    def test_prepare_evidence_crops_and_prompt(self):
        pack=self.prepare()
        report=p.read_json(pack/'preflight-report.json')
        self.assertEqual(report['status'],'ready')
        self.assertEqual(len(report['photos']),3)
        self.assertTrue((pack/'reference-board.png').is_file())
        self.assertTrue((pack/'feature-crops/BuildingA/roof__front.png').is_file())
        txt=(pack/'generation-brief.md').read_text('utf8')
        self.assertIn('actual source photo pixels',txt)
        self.assertIn('NO LEGIBLE OR OFFICIAL TEXT',txt)
        self.assertEqual(p.read_json(pack/'review-template.json')['global_checks']['no_invented_text'],'unknown')


    def test_identical_photo_and_angle_blocked(self):
        b=self.manifest['landmarks'][0]
        b['photos'][1]['file']=b['photos'][0]['file']
        b['photos'][1]['view_angle']='front'
        self.save_manifest()
        r=p.check_project(self.manifest_file)
        self.assertEqual(r['status'],'blocked')
        self.assertTrue(any('same photo content' in x for x in r['errors']))
        self.assertTrue(any('camera angles' in x for x in r['errors']))


    def test_low_res_and_missing_rights_blocked(self):
        Image.new('RGB',(400,200),'blue').save(self.root/'photos/b_front.png')
        self.manifest['landmarks'][0]['photos'][0]['derivatives_allowed']=False
        self.save_manifest()
        r=p.check_project(self.manifest_file)
        self.assertTrue(any('insufficient native resolution' in x for x in r['errors']))
        self.assertTrue(any('derivatives_allowed' in x for x in r['errors']))


    def test_no_attached_real_pixels_audit_fails(self):
        pack=self.prepare()
        illustration=self.root/'generated.png'
        Image.new('RGB',(1672,941),'black').save(illustration)
        review=pack/'review-template.json'
        self.assertEqual(p.run_audit(self.manifest_file,pack/'evidence-lock.json',illustration,review,self.root/'approval.json'),3)
        self.assertEqual(p.read_json(self.root/'approval.json')['status'],'blocked')


    def test_approved_then_tampered_image_rejected(self):
        pack=self.prepare()
        image=self.root/'generated.png'
        Image.new('RGB',(1672,941),(20,20,20)).save(image)
        review=self.approved_review(pack)
        approval=self.root/'approval.json'
        self.assertEqual(p.run_audit(self.manifest_file,pack/'evidence-lock.json',image,review,approval),0)
        v.assert_approved_image(image,approval)
        Image.new('RGB',(1672,941),(30,30,30)).save(image)
        with self.assertRaisesRegex(ValueError,'changed after review'):
            v.assert_approved_image(image,approval)


    def test_tampered_evidence_blocks_audit(self):
        pack=self.prepare()
        image=self.root/'generated.png'
        Image.new('RGB',(1672,941),'black').save(image)
        review=self.approved_review(pack)
        # update pixels on disk, not just in memory
        im=Image.open(self.root/'photos/b_front.png')
        im.putpixel((0,0),(0,0,0));im.save(self.root/'photos/b_front.png')
        self.assertEqual(p.run_audit(self.manifest_file,pack/'evidence-lock.json',image,review,self.root/'approval.json'),3)
        self.assertTrue(any('changed' in x or 'invalid' in x for x in p.read_json(self.root/'approval.json')['problems']))


    def test_per_landmark_image_inputs_required_even_if_global_union_present(self):
        pack=self.prepare()
        image=self.root/'generated.png'
        Image.new('RGB',(1672,941),'black').save(image)
        review=self.approved_review(pack)
        r=p.read_json(review)
        # Tool's global list is full, but one building did not receive side view.
        r['model_invocation']['landmark_calls'][0]['reference_ids_attached']=['style','BuildingA:front']
        p.write_json(review,r)
        approval=self.root/'approval.json'
        self.assertEqual(p.run_audit(self.manifest_file,pack/'evidence-lock.json',image,review,approval),3)
        self.assertTrue(any('per-building image input omitted' in x for x in p.read_json(approval)['problems']))


    def test_multi_angle_feature_bounding_boxes_must_be_per_photo(self):
        f=self.manifest['landmarks'][0]['must_match'][0]
        f['photo_ids']=['front','side']
        f['bbox']=[.1,.2,.9,.8]
        self.save_manifest()
        self.assertTrue(any('bboxes per-photo' in x for x in p.check_project(self.manifest_file)['errors']))
        f.pop('bbox')
        f['bboxes']={'front':[.1,.1,.8,.5],'side':[.2,.1,.85,.6]}
        self.save_manifest()
        self.assertEqual(p.check_project(self.manifest_file)['status'],'ready')
        pack=self.prepare()
        self.assertTrue((pack/'feature-crops/BuildingA/roof__front.png').is_file())
        self.assertTrue((pack/'feature-crops/BuildingA/roof__side.png').is_file())


    def test_primary_view_is_mandatory(self):
        self.manifest['landmarks'][0].pop('primary_view_id')
        self.save_manifest()
        self.assertTrue(any('primary_view_id' in x for x in p.check_project(self.manifest_file)['errors']))


    def test_needs_https_and_allowlist_for_fetch(self):
        with self.assertRaises(ValueError):
            p.fetch_original('http://127.0.0.1/photo.jpg',set())
        with self.assertRaises(ValueError):
            p.fetch_original('https://example.com/photo.jpg',{'othersite.net'})
        self.assertEqual(p.run_fetch(self.manifest_file,[],True,False),2)


    def test_compositor_strict_cutouts(self):
        cut=Image.new('RGBA',(350,240),(0,0,0,0))
        ImageDraw.Draw(cut).polygon([(10,220),(160,40),(330,220)],fill=(240,240,240,255))
        cut.save(self.root/'cut.png')
        data={'mode':'illustrative-montage','canvas':[1672,941],'upper_blank_fraction':.6,
              'placements':[{'landmark_id':'BuildingA','image':'cut.png','box':[.2,.6,.8,1]}]}
        lay=self.root/'layout.json';p.write_json(lay,data)
        out=self.root/'montage.png'
        c.compose(lay,out)
        self.assertTrue(out.exists())
        with Image.open(out) as im:
            self.assertEqual(im.getpixel((400,100)),(0,0,0))
        data['placements'][0]['box']=[.2,.4,.8,1]
        p.write_json(lay,data)
        with self.assertRaises(ValueError):c.compose(lay,out)


if __name__=='__main__':unittest.main()


