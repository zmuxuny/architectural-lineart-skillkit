#!/usr/bin/env python3
"""Synthetic, intentionally fictional buildings for composer smoke testing.

Creates only a layout DRAFT. Not a real campus, not AI-generated artwork,
not verified against photographs, not approved for SVG factual claims.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "campus-architectural-lineart" / "scripts"))
import compose_v2 as montage


def building(kind: int, out: Path):
    w, h = 620, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stroke = (235, 238, 244, 255)
    faint = (166, 174, 187, 210)
    if kind == 0:
        # Fictional roofed academic hall.
        d.polygon([(55, 265), (300, 75), (567, 265)], outline=stroke, width=5)
        d.rectangle((83, 265, 540, 493), outline=stroke, width=5)
        d.line([(70, 287), (554, 287)], fill=faint, width=3)
        for x in range(122, 530, 93):
            d.rectangle((x, 335, x+50, 438), outline=faint, width=4)
    elif kind == 1:
        # Fictional rounded tower, not an actual university landmark.
        d.ellipse((173, 50, 472, 145), outline=stroke, width=4)
        d.arc((173, 15, 472, 166), 180, 360, fill=stroke, width=4)
        d.rectangle((201, 143, 444, 500), outline=stroke, width=5)
        for yy in range(180, 462, 86):
            for xx in (220, 295, 370):
                d.rectangle((xx, yy, xx+45, yy+65), outline=faint, width=4)
    else:
        # Fictional small pavilion.
        d.arc((55, 180, 570, 330), 190, 355, fill=stroke, width=6)
        d.polygon([(38, 278), (295, 178), (578, 278)], outline=stroke, width=4)
        for x in (125, 300, 470):
            d.line((x, 281, x, 474), fill=stroke, width=5)
        d.line((65, 481, 552, 481), fill=stroke, width=5)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("dist/synthetic-montage-draft"))
    a = ap.parse_args()
    out = a.out_dir.resolve()
    for i, bid in enumerate(("SyntheticA", "SyntheticB", "SyntheticC")):
        building(i, out / "cutouts" / (bid+".png"))
    manifest = {"landmarks": [{"id": bid} for bid in ("SyntheticA","SyntheticB","SyntheticC")]}
    plan = montage.make_plan(manifest, "tote-bag", "SyntheticB")
    file = out / "montage-plan.json"
    montage.save_json(file, plan)
    evidence = montage.render(file, out / "draft")
    print("SYNTHETIC DRAFT ONLY:", out / "draft" / "draft-layout.png")
    print("NOT a real building photo audit; NOT a final integrated artwork.")
    print("Plan / draft SHA:", evidence["plan_sha256"], evidence["draft_sha256"])


if __name__ == "__main__":
    main()
