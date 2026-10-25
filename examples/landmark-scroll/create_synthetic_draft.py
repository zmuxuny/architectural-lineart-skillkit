#!/usr/bin/env python3
"""Generate inspectable SYNTHETIC scroll layout, no university/architecture claims.

This is only planner QA, not a generated or verified school/city landmark.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/campus-architectural-lineart/scripts'))
import compose_v2 as planner


def draw_synthetic(building:int, target: Path):
    image=Image.new('RGBA',(470,560),(0,0,0,0))
    d=ImageDraw.Draw(image)
    gray=(214,221,230,250)
    pale=(200,209,222,230)
    mid=(135,152,171,150)
    # All structures are deliberately invented fixtures: not actual landmarks.
    if building%4==0:
        d.rectangle((170,78,304,530),outline=gray,width=7)
        d.ellipse((183,145,292,254),outline=gray,width=7)
        d.line((235,72,235,25),fill=gray,width=4)
        for y in (315,370,425):d.line((176,y,300,y),fill=mid,width=3)
    elif building%4==1:
        d.polygon([(33,280),(232,70),(437,280)],outline=gray)
        d.line((33,280,437,280),fill=gray,width=8)
        d.rectangle((45,285,425,530),outline=gray,width=6)
        for x in (102,190,280,366):d.rectangle((x,350,x+45,475),outline=pale,width=3)
    elif building%4==2:
        d.arc((85,40,390,360),180,360,fill=gray,width=8)
        d.rectangle((85,214,390,530),outline=gray,width=7)
        for x in (145,250,355): d.line((x,232,x,520),fill=mid,width=4)
    else:
        d.rectangle((34,175,437,530),outline=gray,width=7)
        d.line((20,175,450,175),fill=gray,width=7)
        for x in range(61,430,44):d.line((x,180,x,523),fill=mid,width=3)
        d.rectangle((183,350,295,527),outline=pale,width=4)
    d.line((23,533,445,533),fill=gray,width=4)
    target.parent.mkdir(parents=True,exist_ok=True)
    image.save(target)


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--out-dir',required=True,type=Path)
    a=arg.parse_args()
    root=a.out_dir
    landmarks=[]
    for i in range(9):
        key=f'Synthetic{i+1:02}'
        landmarks.append({'id':key,'name':'SYNTHETIC NOT A REAL LANDMARK'})
        draw_synthetic(i,root/'cutouts'/f'{key}.png')
    manifest={'landmarks':landmarks}
    planner.save_json(root/'synthetic-manifest.json',manifest)
    plan=planner.make_scroll_plan(manifest,'tote-bag')
    planner.save_json(root/'montage-plan.json',plan)
    planner.render(root/'montage-plan.json',root/'draft')
    print('Generated 9 synthetic architectural placeholders only; DO NOT describe as real landmark art.')

if __name__=='__main__':main()
