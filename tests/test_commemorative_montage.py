"""Synthetic regression tests for commemorative montage planning and truthful audit.

These mocks do NOT establish real-world aesthetic or building-accuracy results.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"skills/campus-architectural-lineart/scripts"))
import compose_v2 as c
import montage_audit as m
import agent_audit as vision
import reference_pipeline as photos
import test_photo_grounding as fixtures


class MontageDraftTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/"cutouts").mkdir()
        self.manifest = {"landmarks": [{"id": k} for k in ("A", "B", "C")]}
        for i, k in enumerate(("A", "B", "C")):
            im = Image.new("RGBA", (410, 300), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.polygon([(18, 270), (180, 20+i*10), (392, 270)], fill=(216, 222, 230, 220))
            im.save(self.root/"cutouts"/(k+".png"))

    def plan(self, usage="tote-bag"):
        p = c.make_plan(self.manifest, usage, "B")
        file = self.root/"plan.json"
        c.save_json(file, p)
        return p, file

    def test_tote_draft_integrated_hierarchy_and_transparent_cutouts(self):
        p, file = self.plan()
        result = c.render(file, self.root/"output")
        self.assertEqual(p["anchor_landmark_id"], "B")
        self.assertTrue(p["integrated_redraw_required"])
        self.assertEqual(len(p["placements"]), 3)
        self.assertTrue((self.root/"output"/"integrated-generation-brief.md").is_file())
        self.assertTrue((self.root/"output"/"draft-guides.png").is_file())
        self.assertEqual(result["plan_sha256"], c.digest(file))
        with Image.open(self.root/"output"/"draft-layout.png") as im:
            self.assertEqual(im.size, (1672, 941))
            self.assertEqual(im.getpixel((830, 40)), (0, 0, 0))
            self.assertNotEqual(im.getpixel((850, 750)), (0, 0, 0))
        brief = (self.root/"output"/"integrated-generation-brief.md").read_text("utf-8")
        self.assertIn("NOT THE FINAL ARTWORK", brief)
        self.assertIn("not a real geographic", brief.lower() + " not a real geographic")

    def test_ppt_cover_preserves_blank_title_area(self):
        p, file = self.plan("ppt-cover")
        self.assertGreaterEqual(p["upper_blank_fraction"], .5)
        c.render(file, self.root/"out")
        with Image.open(self.root/"out"/"draft-layout.png") as im:
            self.assertEqual(im.getpixel((850, 180)), (0, 0, 0))

    def test_invalid_gallery_layout_and_cutout_paths_are_rejected(self):
        p, _ = self.plan()
        anchor = next(x for x in p["placements"] if x["role"] == "anchor")
        for x in p["placements"]:
            if x["role"] == "support":
                x["rect"] = [0, .68, .20, 1]
        anchor["rect"] = [.33, .28, .74, .95]
        with self.assertRaisesRegex(ValueError, "gallery-like"):
            c.validate_plan(p, self.root)
        p, _ = self.plan()
        p["placements"][0]["image"] = "../../secret.png"
        with self.assertRaisesRegex(ValueError, "relative"):
            c.validate_plan(p, self.root)
        p, _ = self.plan()
        p["placements"][0]["landmark_id"] = "B"
        with self.assertRaisesRegex(ValueError, "repeated"):
            c.validate_plan(p, self.root)

    def test_opaque_black_cutout_is_not_accepted(self):
        p, file = self.plan()
        Image.new("RGB", (200, 200), (0, 0, 0)).save(self.root/"cutouts"/"A.png")
        with self.assertRaisesRegex(ValueError, "RGBA"):
            c.render(file, self.root/"out")

    def test_single_landmark_is_not_a_montage(self):
        with self.assertRaisesRegex(ValueError, "2–5"):
            c.make_plan({"landmarks": [{"id": "A"}]}, "tote-bag", "A")


class MontageAuditTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.PhotoGroundingTests("test_prepare_evidence_crops_and_prompt")
        fixture.setUp()
        self.addCleanup(fixture.tmp.cleanup)
        self.fixture = fixture
        self.root = fixture.root
        # Second landmark with different source-pixel content and source IDs.
        second = copy.deepcopy(fixture.manifest["landmarks"][0])
        second["id"] = "BuildingB"
        for item in second["photos"]:
            name = "b_b_" + item["id"] + ".png"
            old = self.root / item["file"]
            with Image.open(old) as im:
                pic = im.copy()
                ImageDraw.Draw(pic).rectangle((110, 80, 320, 250), fill=(47, 87, 118))
                pic.save(self.root/"photos"/name)
            item["file"] = "photos/" + name
        fixture.manifest["landmarks"].append(second)
        fixture.save_manifest()
        self.pack = fixture.prepare()
        self.artwork = self.root/"artwork"
        (self.artwork/"cutouts").mkdir(parents=True)
        for i, bid in enumerate(("BuildingA", "BuildingB")):
            im = Image.new("RGBA", (460, 330), (0, 0, 0, 0))
            ImageDraw.Draw(im).polygon([(12, 300), (225, 35 + 10*i), (450, 300)],
                                       fill=(255, 255, 255, 220))
            im.save(self.artwork/"cutouts"/(bid+".png"))
        plan = c.make_plan(fixture.manifest, "tote-bag", "BuildingA")
        self.plan = self.artwork/"montage-plan.json"
        c.save_json(self.plan, plan)
        c.render(self.plan, self.artwork/"draft")
        self.draft = self.artwork/"draft"/"draft-layout.png"
        self.final = self.artwork/"final.png"
        with Image.open(self.draft) as im:
            out = im.copy()
            ImageDraw.Draw(out).line((100, 865, 1450, 861), fill=(190, 190, 190), width=4)
            out.save(self.final)
        self.log_path = self.artwork/"integrated-generation-log.json"
        self.make_log()

    def make_log(self):
        self.log = {
            "tool": "SYNTHETIC_IMAGE_EDIT_FIXTURE",
            "call_id": "synthetic-call-id",
            "image_input_confirmed": True,
            "reference_ids_attached": [
                "DRAFT", "STYLE", "CUTOUT:BuildingA", "CUTOUT:BuildingB",
                "PHOTO:BuildingA:front", "PHOTO:BuildingB:front"
            ],
            "plan_sha256": c.digest(self.plan),
            "draft_sha256": c.digest(self.draft),
            "output_sha256": c.digest(self.final),
            "cutout_sha256": {
                bid: c.digest(self.artwork/"cutouts"/(bid+".png"))
                for bid in ("BuildingA","BuildingB")
            }
        }
        c.save_json(self.log_path, self.log)

    def verdict(self, b, status="pass", confidence=.98, diff="none"):
        def rec(id):
            return {
                "id": id, "status": status, "confidence": confidence,
                "photo_ids": ["draft"] if b["id"] == "MONTAGE" else ["front"],
                "observation": f"Synthetic observations from the inspected images compare {id} to the locked evidence.",
                "difference": diff
            }
        return {
            "landmark_id": b["id"],
            "features": [rec(x["id"]) for x in b["must_match"]],
            "checks": [rec(x) for x in vision.REVIEW_CHECKS],
            "candidate_has_legible_text": False,
            "overall_notes": "This is a synthetic unit-test verdict, not a real visual inspection."
        }

    def backend(self, fail_montage=False):
        names = {b["id"]:b for b in self.fixture.manifest["landmarks"]}
        names["MONTAGE"] = m.pseudo_building(c.load_json(self.plan))
        def review(*, model, prompt, pictures, max_side):
            bid = pictures[0][0].split(":")[1]
            b = names[bid]
            return self.verdict(b, status="fail" if fail_montage and bid=="MONTAGE" else "pass",
                                diff="Isolated gallery stickers" if fail_montage and bid=="MONTAGE" else "none"), {
                "response_id":"mock:" + bid, "model":model,
                "image_ids":[x[0] for x in pictures]
            }
        return review

    def run_audit(self, **kwargs):
        return m.run(
            manifest_file=self.fixture.manifest_file,
            lock_file=self.pack/"evidence-lock.json",
            plan_file=self.plan, draft=self.draft,
            evidence_file=self.artwork/"draft"/"draft-evidence.json",
            final=self.final, generation_log_file=self.log_path,
            output_dir=self.artwork/"review", model="synthetic-vlm",
            backend=self.backend(**kwargs))

    def test_final_integration_and_all_buildings_are_reviewed(self):
        r = self.run_audit()
        self.assertEqual(r["decision"], "agent_pass")
        self.assertEqual(len(r["landmarks_and_composition"]), 3)
        self.assertEqual(r["landmarks_and_composition"][-1]["landmark_id"], "MONTAGE")
        approval = photos.read_json(self.artwork/"review"/"approval.json")
        self.assertEqual(approval["status"], "approved")
        self.assertEqual(approval["image_sha256"], c.digest(self.final))

    def test_composition_gallery_fail_blocks_even_when_buildings_pass(self):
        r = self.run_audit(fail_montage=True)
        self.assertEqual(r["decision"], "needs_review")
        approval = photos.read_json(self.artwork/"review"/"approval.json")
        self.assertEqual(approval["status"], "blocked")
        self.assertTrue((self.artwork/"review"/"retry-brief.md").exists())
        self.assertTrue(any("MONTAGE" in p for p in r["problems"]))

    def test_reject_draft_as_final_even_with_forged_log(self):
        self.final.write_bytes(self.draft.read_bytes())
        self.make_log()
        with self.assertRaisesRegex(ValueError, "draft was submitted as final"):
            self.run_audit()

    def test_reject_missing_source_photo_inputs_in_integrated_generation(self):
        self.log["reference_ids_attached"].remove("PHOTO:BuildingB:front")
        c.save_json(self.log_path, self.log)
        with self.assertRaisesRegex(ValueError, "actual images"):
            self.run_audit()

    def test_reject_tampered_cutout_hash(self):
        with Image.open(self.artwork/"cutouts"/"BuildingB.png") as im:
            image=im.copy()
            image.putpixel((42,42),(255,255,255,235))
            image.save(self.artwork/"cutouts"/"BuildingB.png")
        with self.assertRaisesRegex(ValueError, "cutout changed"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main()
