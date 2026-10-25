"""Architecture-first scroll planning and source-atlas trust tests.

Synthetic figures only. Passing this suite never certifies real landmarks.
"""
from __future__ import annotations
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'skills/campus-architectural-lineart/scripts'))
import compose_v2 as layout
import montage_audit as audit
import integrated_edit as editor
import scroll_atlas


class ScrollTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        (self.root/'cutouts').mkdir()
        (self.root/'photos').mkdir()
        self.manifest={'project':{'mode':'montage'},'style_reference':'photos/style.png','landmarks':[]}
        Image.new('RGB',(900,520),'black').save(self.root/'photos/style.png')
        for i in range(10):
            bid=f'LM{i+1:02}'
            outline=Image.new('RGBA',(300,410),(0,0,0,0))
            d=ImageDraw.Draw(outline)
            d.polygon([(20,350),(150,35+i*3),(280,350)],fill=(215,215,215,255))
            outline.save(self.root/'cutouts'/(bid+'.png'))
            original=Image.new('RGB',(1100,800),(190,205,213))
            d=ImageDraw.Draw(original)
            d.rectangle((100+i*3,200,950,710),fill=(67,73,89))
            original.save(self.root/'photos'/(bid+'.png'))
            self.manifest['landmarks'].append({'id':bid,'name':bid,'location':'synthetic test only',
                'primary_view_id':'front','photos':[{'id':'front','file':'photos/'+bid+'.png'}]})

    def plan(self,n=9):
        subset=dict(self.manifest)
        subset['landmarks']=self.manifest['landmarks'][:n]
        plan=layout.make_scroll_plan(subset,'tote-bag')
        plan_file=self.root/'plan.json';layout.save_json(plan_file,plan)
        return subset,plan,plan_file

    def test_9_landmarks_cover_breadth_and_no_forest(self):
        _,p,path=self.plan(9)
        self.assertEqual(p['archetype'],'landmark-scroll')
        self.assertEqual(len(p['placements']),9)
        self.assertEqual(p['connectors'],['architectural-baseline'])
        self.assertLessEqual(p['max_ornament_area_fraction'],.05)
        self.assertEqual(len(layout.validate_plan(p,self.root)),9)
        result=layout.render(path,self.root/'draft')
        brief=(self.root/'draft'/'integrated-generation-brief.md').read_text()
        self.assertIn('NO default trees',brief)
        self.assertIn('ALL 9',brief)
        self.assertIn('not the final',brief.lower())
        self.assertEqual(result['mode'],'draft-only')
        with Image.open(self.root/'draft'/'draft-layout.png') as im:
            self.assertEqual(im.size,(1672,941))

    def test_gallery_and_landscape_modes_cannot_disguise_three_subjects_as_scroll(self):
        with self.assertRaisesRegex(ValueError,'6–10'):
            layout.make_scroll_plan({'landmarks':self.manifest['landmarks'][:3]},'tote-bag')
        _,p,_=self.plan(8)
        p['connectors']=['ornamental-foliage']
        with self.assertRaisesRegex(ValueError,'trees, shrubs'):
            layout.validate_plan(p,self.root)
        p['connectors']=['architectural-baseline'];p['max_ornament_area_fraction']=.20
        with self.assertRaisesRegex(ValueError,'ornament budget'):
            layout.validate_plan(p,self.root)

    def test_atlases_contain_all_original_photo_and_cutout_hashes(self):
        sub,plan,plan_path=self.plan(10)
        cutouts=[('CUTOUT:'+b['id'],self.root/'cutouts'/(b['id']+'.png')) for b in sub['landmarks']]
        photos=[('PHOTO:'+b['id']+':front',self.root/'photos'/(b['id']+'.png')) for b in sub['landmarks']]
        images,records=scroll_atlas.build(cutouts,photos,self.root/'reference-atlases')
        self.assertEqual(len(images),6)
        self.assertEqual(len(records),6)
        self.assertEqual(sum(len(x['members']) for x in records),20)
        self.assertEqual({y['image_id'] for x in records for y in x['members']},
                         {x[0] for x in photos+cutouts})
        self.assertTrue(all(Path(x[1]).is_file() for x in images))

    def test_integrated_edit_log_and_audit_reject_atlas_tampering(self):
        subset,plan,plan_file=self.plan(8)
        working=self.root/'work';working.mkdir()
        layout.render(plan_file,working/'draft')
        draft=working/'draft/draft-layout.png'
        brief=working/'draft/integrated-generation-brief.md'
        final=working/'final.png';logfile=working/'integrated-generation-log.json'
        manifest=self.root/'manifest.json';layout.save_json(manifest,subset)
        lock=self.root/'lock.json';lock.write_text('{}')
        mockpic=Image.new('RGB',(1536,864),'black')
        out=io.BytesIO();mockpic.save(out,format='PNG')
        def backend(*,model,size,prompt,images):
            ids=[k for k,_ in images]
            self.assertEqual(ids[:2],['DRAFT','STYLE'])
            self.assertTrue(all(k.startswith(('CUTOUT_ATLAS:','PHOTO_ATLAS:')) for k in ids[2:]))
            self.assertIn('LANDMARK SCROLL SPECIAL RULES',prompt)
            self.assertLessEqual(len(images),16)
            return out.getvalue(),'req-unit-test',{'model':model}
        import reference_pipeline as sources
        with patch.object(editor,'input_integrity',return_value=(subset,{},plan,{})),\
             patch.object(sources,'verify_lock',return_value=[]):
            log=editor.run(manifest_file=manifest,lock_file=lock,plan_file=plan_file,
                draft_file=draft,draft_evidence_file=working/'draft/draft-evidence.json',
                brief_file=brief,output_file=final,log_file=logfile,backend=backend)
        self.assertEqual(log['input_mode'],'reference-atlas-v1')
        self.assertEqual(len(log['atlas_entries']),4)
        self.assertEqual(log['call_id'],'req-unit-test')
        kwargs=dict(manifest=subset,plan=plan,plan_path=plan_file,
            evidence=layout.load_json(working/'draft/draft-evidence.json'),draft=draft,
            final=final,log=log,cutouts=layout.validate_plan(plan,self.root),
            log_root=working,source_root=self.root)
        self.assertEqual(audit.validate_generation(**kwargs),[])
        # The declared inputs may not be silently replaced after generation.
        atlas=working/'reference-atlases'/log['atlas_entries'][0]['file']
        with atlas.open('ab') as f:f.write(b'tampered')
        problems=audit.validate_generation(**kwargs)
        self.assertTrue(any('atlas was modified' in x for x in problems),problems)

    def test_scroll_has_extra_whole_image_audit_contract(self):
        _,p,_=self.plan(8)
        ids={x['id'] for x in audit.pseudo_building(p)['must_match']}
        self.assertIn('architecture_priority',ids)
        self.assertIn('landmark_inventory',ids)
        self.assertIn('continuous_landmark_rhythm',ids)
        prompt=audit.montage_prompt(p,'adversarial')
        self.assertIn('shrubs/trees',prompt)
        self.assertIn('all 8',prompt)


if __name__=='__main__':unittest.main()
