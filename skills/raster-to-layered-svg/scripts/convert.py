#!/usr/bin/env python3
"""Convert line-art raster to transparent 4K PNG and genuine multilayer SVG paths.

No AI or geometric reconstruction takes place in this file. SVG paths are
polygonal contour tracing of raster threshold masks, NOT artist strokes.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from html import escape
import sys
import numpy as np
import cv2
from PIL import Image

DEFAULT_THRESHOLDS = [6, 14, 26, 42, 62, 85, 112, 142, 174, 207, 237]
DEFAULT_TARGETS = [11, 20, 34, 52, 74, 99, 127, 158, 191, 222, 255]

def dims(spec: str) -> tuple[int,int]:
    try: w, h = [int(x) for x in spec.lower().replace('×','x').split('x')]
    except Exception as ex: raise argparse.ArgumentTypeError('Size must be WIDTHxHEIGHT, e.g. 3840x2160') from ex
    if not 1 <= w <= 16000 or not 1 <= h <= 16000: raise argparse.ArgumentTypeError('Size out of bounds (1..16000)')
    return w,h

def load_luminance(src: Path, mode: str) -> np.ndarray:
    with Image.open(src) as im:
        raw = np.asarray(im.convert('RGB'))
    gray = cv2.cvtColor(raw, cv2.COLOR_RGB2GRAY)
    if mode == 'dark-on-light': gray = 255-gray
    return gray

def transparent_png(gray: np.ndarray, size: tuple[int,int], cutoff: float=2, gamma: float=1) -> Image.Image:
    alpha=np.clip((gray.astype(np.float32)-cutoff)/(255-cutoff),0,1)
    alpha=np.power(alpha,gamma)
    pil=Image.fromarray(np.uint8(np.round(alpha*255)),mode='L')
    pil=pil.resize(size,Image.Resampling.LANCZOS)
    rgba=Image.new('RGBA',size,(255,255,255,0))
    rgba.putalpha(pil)
    return rgba

def fill_evenodd_paths(gray: np.ndarray, threshold: int, zoom: int, epsilon:float) -> tuple[str,int]:
    height,width=gray.shape
    mask=np.uint8(gray>threshold)*255
    if zoom!=1: mask=cv2.resize(mask,(width*zoom,height*zoom),interpolation=cv2.INTER_NEAREST)
    contours,_=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    paths=[]; count=0
    for cont in contours:
        if len(cont)<3: continue
        poly=cv2.approxPolyDP(cont, epsilon, True).reshape(-1,2)
        if len(poly)<3: continue
        coord=[f'M{poly[0,0]/zoom:g},{poly[0,1]/zoom:g}']
        coord += [f'{x/zoom:g},{y/zoom:g}' for x,y in poly[1:]]
        coord.append('Z');paths.append(' '.join(coord));count+=1
    return ' '.join(paths),count

def vectorize(gray: np.ndarray, out: Path, title: str, target_size:tuple[int,int],
              thresholds=DEFAULT_THRESHOLDS, targets=DEFAULT_TARGETS, zoom:int=2,epsilon:float=0.48,
              black_bg: bool=False) -> tuple[int,int]:
    assert len(thresholds)==len(targets) and all(a<b for a,b in zip(thresholds,thresholds[1:]))
    height,width=gray.shape
    w,h=target_size
    out.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with out.open('w',encoding='utf8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                f'viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">\n')
        f.write(f'<title>{escape(title)}</title>\n')
        f.write('<desc>Generated using multilevel raster contour tracing; geometry is an approximation of source pixels.</desc>\n')
        if black_bg:f.write(f'<rect data-background="true" width="{width}" height="{height}" fill="#000"/>\n')
        prev=0
        for t,target in zip(thresholds,targets):
            d,n=fill_evenodd_paths(gray,t,zoom,epsilon)
            opacity=(target-prev)/(255-prev);prev=target
            f.write(f'<path fill="#ffffff" fill-rule="evenodd" opacity="{opacity:.5f}" d="{d}"/>\n')
            count+=n
            print(f'  threshold={t:>3}, contours={n:>7}, opacity={opacity:.4f}',file=sys.stderr)
        f.write('</svg>\n')
    return len(thresholds),count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path,help='Input PNG/JPG with pale lines on dark background')
    p.add_argument('--out-dir',required=True,type=Path)
    p.add_argument('--size',type=dims,default=(3840,2160))
    p.add_argument('--mode',choices=('light-on-dark','dark-on-light'),default='light-on-dark')
    p.add_argument('--title',default='Architectural line art')
    p.add_argument('--cutoff',type=float,default=2,help='Minimum source luminance treated as background')
    p.add_argument('--gamma',type=float,default=1,help='Alpha shaping, >1 suppresses faint lines')
    p.add_argument('--zoom',type=int,choices=(1,2,3),default=2,help='Upsampling before contour tracing')
    p.add_argument('--epsilon',type=float,default=0.48,help='Contour simplification in enlarged pixels')
    p.add_argument('--skip-svg',action='store_true')
    a=p.parse_args()
    if not a.input.is_file():p.error(f'Input does not exist: {a.input}')
    if not 0<=a.cutoff<255:p.error('--cutoff must be [0,255)')
    if a.gamma<=0:p.error('--gamma must be >0')
    if a.epsilon<=0:p.error('--epsilon must be >0')
    a.out_dir.mkdir(parents=True,exist_ok=True)
    print(f'Processing {a.input}, native raster: {Image.open(a.input).size}',file=sys.stderr)
    lum=load_luminance(a.input,a.mode)
    rgba=transparent_png(lum,a.size,a.cutoff,a.gamma)
    p_trans=a.out_dir/'lineart-transparent.png';rgba.save(p_trans,optimize=True)
    p_black=a.out_dir/'lineart-black.png';black=Image.new('RGBA',a.size,(0,0,0,255));black.alpha_composite(rgba);black.convert('RGB').save(p_black,optimize=True)
    print(f'Created {p_trans}, {p_black}',file=sys.stderr)
    if not a.skip_svg:
        p_svg=a.out_dir/'lineart.svg'
        levels,contours=vectorize(lum,p_svg,a.title,a.size,zoom=a.zoom,epsilon=a.epsilon)
        print(f'Created {p_svg}: {levels} layers, {contours} closed contours',file=sys.stderr)
    print('NOTE: output size is 4K canvas only; native source detail is not magically increased.',file=sys.stderr)
if __name__=='__main__': main()
