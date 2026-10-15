#!/usr/bin/env python3
"""Deterministic assembly of reviewed building cutouts. Does NOT invent architecture.

Each input must be a transparent RGBA illustration of ONE landmark. Place them
using explicit normalized boxes; visual evidence audit still required afterward.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image


def compose(layout_file: Path, output: Path) -> None:
    obj = json.loads(layout_file.read_text(encoding="utf-8"))
    if not isinstance(obj, dict): raise ValueError("layout JSON root must be an object")
    size = obj.get("canvas", [1672, 941])
    if not isinstance(size, list) or len(size) != 2 or not all(isinstance(x, int) and 100 <= x <= 7680 for x in size):
        raise ValueError("canvas must be [width, height] integers")
    if obj.get("mode") != "illustrative-montage":
        raise ValueError("layout.mode must be illustrative-montage to avoid implying a real camera view")
    placements = obj.get("placements", [])
    if not isinstance(placements, list) or not placements: raise ValueError("placements must not be empty")
    blank = obj.get("upper_blank_fraction", 0.60)
    if not isinstance(blank, (int, float)) or not 0.4 <= blank <= 0.8:
        raise ValueError("upper_blank_fraction must be 0.4..0.8")
    background = obj.get("background", "#000000")
    if background != "#000000": raise ValueError("only #000000 background accepted for this line-art workflow")
    board = Image.new("RGBA", tuple(size), (0, 0, 0, 255))
    used = set()
    root = layout_file.resolve().parent
    for p in placements:
        lid = p.get("landmark_id", "")
        if not isinstance(lid, str) or not lid or lid in used: raise ValueError("each landmark_id must occur exactly once")
        used.add(lid)
        item = Path(p.get("image", ""))
        if item.is_absolute() or ".." in item.parts: raise ValueError("input file path must be relative")
        file = (root/item).resolve()
        if not file.is_relative_to(root) or not file.is_file(): raise ValueError(f"missing cutout: {item}")
        box = p.get("box", [])
        if not isinstance(box, list) or len(box) != 4 or any(not isinstance(x, (int,float)) for x in box):
            raise ValueError(f"{lid}: box should be normalized [x0,y0,x1,y1]")
        x0,y0,x1,y1 = box
        if not (0 <= x0 < x1 <= 1 and blank <= y0 < y1 <= 1):
            raise ValueError(f"{lid}: cutout must lie in the lower {1-blank:.0%} of the canvas")
        with Image.open(file) as im:
            if im.mode != "RGBA": raise ValueError(f"{lid}: need real RGBA transparent cutout, not painted black rectangle")
            art = im.copy()
        a = art.getchannel("A")
        corners = [a.getpixel((0,0)),a.getpixel((art.width-1,0)),a.getpixel((0,art.height-1)),a.getpixel((art.width-1,art.height-1))]
        if max(corners)>16: raise ValueError(f"{lid}: edges are not transparent; mask the exact subject before composing")
        bounds = a.getbbox()
        if not bounds: raise ValueError(f"{lid}: input is fully transparent")
        art = art.crop(bounds)
        bw = round((x1-x0)*size[0]);bh = round((y1-y0)*size[1])
        art.thumbnail((bw,bh),Image.Resampling.LANCZOS)
        px = round(x0*size[0] + (bw-art.width)/2)
        py = round(y1*size[1] - art.height)
        if py < round(blank*size[1]): raise ValueError(f"{lid}: cutout overlaps reserved top blank region")
        board.alpha_composite(art,(px,py))
    output.parent.mkdir(parents=True,exist_ok=True)
    board.convert("RGB").save(output)
    print(f"Composed {len(used)} distinct grounded building cutouts: {output} ({size[0]}x{size[1]})")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layout",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    try:compose(args.layout,args.output)
    except (ValueError, OSError, KeyError) as exc:ap.error(str(exc))


if __name__=='__main__':main()
