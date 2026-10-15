from __future__ import annotations
import gzip, base64, importlib.util, re, sys, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
import yaml

ROOT=Path(__file__).resolve().parent.parent

def module(rel):
    path=ROOT/rel
    spec=importlib.util.spec_from_file_location('pkg_'+path.stem,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

class SkillkitSmoke(unittest.TestCase):
    def test_skill_headers(self):
        skills=list((ROOT/'skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills),3)
        for s in skills:
            contents=s.read_text(encoding='utf8')
            self.assertTrue(contents.startswith('---\n'))
            front=yaml.safe_load(contents.split('---\n',2)[1])
            self.assertEqual(front['name'],s.parent.name)
            self.assertGreater(len(front['description']),10)

    def test_png_alpha(self):
        m=module('skills/raster-to-layered-svg/scripts/convert.py')
        src=np.zeros((60,100),dtype=np.uint8)
        src[30:40,12:87]=180
        result=m.transparent_png(src,(200,120))
        self.assertEqual(result.size,(200,120))
        self.assertEqual(result.getpixel((0,0))[3],0)
        self.assertGreater(result.getpixel((100,70))[3],10)

    def test_true_svg(self):
        m=module('skills/raster-to-layered-svg/scripts/convert.py')
        src=np.zeros((80,144),dtype=np.uint8)
        src[20:65,10:130]=170
        src[30:50,45:90]=0
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out.svg'
            levels,parts=m.vectorize(src,out,'test title',(3840,2160),zoom=1)
            text=out.read_text(encoding='utf-8')
            root=ET.fromstring(text)
            paths=root.findall('{http://www.w3.org/2000/svg}path')
            self.assertEqual(levels,11)
            self.assertGreater(parts,0)
            self.assertEqual(len(paths),11)
            self.assertNotIn('<image',text)
            self.assertIn('fill-rule="evenodd"',text)
            self.assertEqual(root.attrib['width'],'3840')

    def test_builder_offline_payload_and_final_preset(self):
        m=module('skills/offline-svg-color-workbench/scripts/build.py')
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            svg=td/'a.svg';png=td/'a.png';out=td/'app.html'
            original=b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0,0 5,5" fill="#fff"/></svg>'
            svg.write_bytes(original)
            Image.new('RGBA',(32,18),(255,255,255,0)).save(png)
            sz=m.build_editor(svg,png,out,'Custom title','Example')
            html=out.read_text(encoding='utf8')
            self.assertEqual(sz,out.stat().st_size)
            self.assertNotIn('__EMBED',html)
            self.assertIn("color:'#aeb0b2',intensity:1.15,detail:1.65",html)
            self.assertIn('4K',html)
            b64=re.search(r'<script id="embeddedSvg" type="application/octet-stream">([^<]+)</script>',html).group(1)
            self.assertEqual(gzip.decompress(base64.b64decode(b64)),original)
            b64png=re.search(r'<script id="embeddedPng" type="application/octet-stream">([^<]+)</script>',html).group(1)
            self.assertTrue(base64.b64decode(b64png).startswith(b'\x89PNG'))

    def test_no_third_party_assets(self):
        doc=(ROOT/'examples/zju/workbench.html').read_text('utf8')
        self.assertNotIn('<script src=',doc)
        self.assertNotIn('<link rel="stylesheet" href=',doc)
        self.assertNotIn('__EDITOR_JS__',doc)
        self.assertGreater(len(doc),3000000)

if __name__ == '__main__':unittest.main()
