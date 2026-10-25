#!/usr/bin/env python3
"""Evidence-traceable image reference atlases for 6-10 building scrolls.

Do not silently drop photographic inputs to satisfy image-edit API limits.
Packing preserves every cutout AND its photographed primary view, with each
source ID, bytes SHA and atlas-file SHA recorded for downstream verification.
Atlas is a compact visual conditioning aid, not a full-resolution substitute.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

PER_PAGE = 4
BOARD_SIZE = 2048


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def atlas_font() -> ImageFont.ImageFont:
    for name in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(name).is_file():
            return ImageFont.truetype(name, 26)
    return ImageFont.load_default()


def draw_page(pairs: list[tuple[str,Path]], output: Path, *, cutouts: bool) -> None:
    """Actual pixels from originals, in stable labeled 2x2 cells."""
    if not pairs or len(pairs)>PER_PAGE:
        raise ValueError('atlas page must have 1-4 images')
    output.parent.mkdir(parents=True, exist_ok=True)
    w=BOARD_SIZE
    board=Image.new('RGB',(w,w),'#101010' if cutouts else '#f3f4f5')
    painter=ImageDraw.Draw(board)
    for i,(ident,path) in enumerate(pairs):
        col,row=i%2,i//2
        x,y=col*1024+13,row*1024+13
        inset=23
        area=(x+inset,y+inset,x+1024-inset-30,y+1024-inset-92)
        with Image.open(path) as im:
            src=ImageOps.exif_transpose(im).convert('RGBA')
            bg=Image.new('RGBA',src.size,(0,0,0,255) if cutouts else (255,255,255,255))
            bg.alpha_composite(src)
            pic=bg.convert('RGB')
            pic.thumbnail((area[2]-area[0],area[3]-area[1]),Image.Resampling.LANCZOS)
        center_x=(area[0]+area[2]-pic.width)//2
        center_y=(area[1]+area[3]-pic.height)//2
        board.paste(pic,(center_x,center_y))
        ink='#dedede' if cutouts else '#171717'
        painter.text((x+inset,y+1024-89),ident,fill=ink,font=atlas_font())
        painter.rectangle((x+2,y+2,x+1008,y+1008),outline='#555555' if cutouts else '#adb5bd',width=1)
    board.save(output,optimize=True)


def build(input_cutouts: list[tuple[str,Path]], input_photos: list[tuple[str,Path]],
          output_dir: Path) -> tuple[list[tuple[str,Path]], list[dict]]:
    """Return actual API image attachments and a content-hash source manifest."""
    if len(input_cutouts) != len(input_photos) or not 6<=len(input_cutouts)<=10:
        raise ValueError('scroll atlas requires corresponding cutouts and photos for 6-10 landmarks')
    if len(set(x[0] for x in input_cutouts+input_photos)) != len(input_cutouts+input_photos):
        raise ValueError('duplicate atlas source image ID')
    result=[];records=[]
    for kind,items in [('CUTOUT_ATLAS',input_cutouts),('PHOTO_ATLAS',input_photos)]:
        for start in range(0,len(items),PER_PAGE):
            batch=items[start:start+PER_PAGE]
            identifier=f'{kind}:{start//PER_PAGE}'
            target=output_dir/f'{kind.lower()}_{start//PER_PAGE}.png'
            draw_page(batch,target,cutouts=kind=='CUTOUT_ATLAS')
            result.append((identifier,target))
            records.append({'id':identifier,'file':target.name,'sha256':sha(target),
                'members':[{'image_id':iid,'source_sha256':sha(src)} for iid,src in batch]})
    if len(result)>14:
        raise ValueError('atlas exceeds API image-input budget')
    return result,records
