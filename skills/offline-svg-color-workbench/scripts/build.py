#!/usr/bin/env python3
"""Build a standalone, self-contained offline HTML color editor for SVG + PNG."""
from __future__ import annotations
import argparse
import base64
from pathlib import Path
import gzip
import re
import html
import json
import sys

HERE=Path(__file__).resolve().parent.parent
ASSETS=HERE/'assets'

def build_editor(svg: Path,png:Path,out:Path,title:str='Architectural line art',filename:str='lineart'):
    if not svg.is_file() or not png.is_file():
        raise FileNotFoundError('Both --svg and --png must exist')
    svg_bytes=svg.read_bytes()
    low=svg_bytes[:10000].lower()
    if b'<svg' not in low: raise ValueError('Input SVG must contain a valid <svg> root')
    if b'<image' in svg_bytes.lower():
        raise ValueError('SVG contains embedded raster <image>; vector output must use paths. Vectorize before building.')
    if len(svg_bytes)>35*1024*1024:
        raise ValueError('SVG is >35MB; optimize contours before building.')
    if png.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError('--png must be a PNG file')
    template=(ASSETS/'template.html').read_text(encoding='utf-8')
    script=(ASSETS/'editor.js').read_text(encoding='utf-8')
    stem=re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5-]+','-',filename).strip('-') or 'lineart'
    script=script.replace('__ARTWORK_TITLE__',title.replace('\\','\\\\').replace("'","\\'"))
    script=script.replace('__FILE_STEM__',stem)
    result=template.replace('__EMBED_SVG_GZIP_BASE64__',base64.b64encode(gzip.compress(svg_bytes,compresslevel=9,mtime=0)).decode('ascii'))
    result=result.replace('__EMBED_PNG_BASE64__',base64.b64encode(png.read_bytes()).decode('ascii'))
    result=result.replace('__ARTWORK_TITLE__',html.escape(title,quote=True))
    result=result.replace('__EDITOR_JS__',script)
    for placeholder in ('__EMBED_SVG_GZIP_BASE64__','__EMBED_PNG_BASE64__','__EDITOR_JS__','__FILE_STEM__'):
        if placeholder in result:raise RuntimeError('unresolved placeholder: '+placeholder)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(result,encoding='utf-8')
    return out.stat().st_size

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--svg',type=Path,required=True)
    p.add_argument('--png',type=Path,required=True,help='Transparent PNG used for fast Canvas preview')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--title',default='建筑线稿 · 精细版')
    p.add_argument('--filename',default='建筑线稿')
    a=p.parse_args()
    try:n=build_editor(a.svg,a.png,a.output,a.title,a.filename)
    except (ValueError, FileNotFoundError, RuntimeError) as e:p.error(str(e))
    print(f'Created offline tool: {a.output} ({n:,} bytes)')
    print('Open with current Chrome or Edge; SVG export needs browser DecompressionStream.')
if __name__=='__main__':main()
