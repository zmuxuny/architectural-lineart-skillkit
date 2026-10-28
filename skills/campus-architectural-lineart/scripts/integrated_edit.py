#!/usr/bin/env python3
"""Perform a real, reference-conditioned commemorative montage image edit.


This OPTIONAL OpenAI Images API backend connects compose_v2's DRAFT to an actual
whole-scene redraw. It never calls itself a renderer, never fabricates a tool
invocation, and never approves its own output: montage_audit.py remains mandatory.


Requires OPENAI_API_KEY. The API request sends the exact montage draft, separate
style reference, every original building cutout, and each building's primary
source photo as images (not filenames or textual references).


Current official API: POST https://api.openai.com/v1/images/edits, GPT Image
models, multiple image[] parts; see https://developers.openai.com/api/reference/resources/images/methods/edit
"""
from __future__ import annotations


import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


from PIL import Image, UnidentifiedImageError


import compose_v2 as layout
import scroll_atlas
import reference_pipeline as sources


API_ENDPOINT = "https://api.openai.com/v1/images/edits"
DEFAULT_MODEL = "gpt-image-2.5-sunburst"
DEFAULT_SIZE = "1536x864"
MAX_IMAGE_COUNT = 16
MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_PROMPT_CHARS = 32000




def named_inputs(manifest: dict, plan: dict, draft: Path, plan_path: Path,
                 manifest_path: Path) -> list[tuple[str, Path]]:
    """The same image IDs expected by montage_audit.validate_generation."""
    manifest_root = manifest_path.resolve().parent
    plan_root = plan_path.resolve().parent
    paths = layout.validate_plan(plan, plan_root)
    if {p['landmark_id'] for p in plan['placements']} != {b['id'] for b in manifest['landmarks']}:
        raise ValueError("montage plan does not match the evidence manifest's buildings")
    result = [
        ("DRAFT", draft),
        ("STYLE", sources.safe_path(manifest_root, manifest['style_reference'])),
    ]
    # Interleave cutout with its verified primary photograph: each landmark is
    # visually anchored rather than only loosely represented in text.
    for b in manifest['landmarks']:
        bid = b['id']
        matching = [p for p in b['photos'] if p['id'] == b['primary_view_id']]
        if len(matching) != 1:
            raise ValueError(f"{bid}: primary photo anchor is missing or ambiguous")
        result.append(("CUTOUT:" + bid, paths[bid]))
        result.append((f"PHOTO:{bid}:{b['primary_view_id']}",
                       sources.safe_path(manifest_root, matching[0]['file'])))
    if len(result) > MAX_IMAGE_COUNT:
        raise ValueError(f"image editing supports at most {MAX_IMAGE_COUNT} input images; "
                         "reduce landmark count or use smaller grounded batches")
    for ident, image in result:
        if not image.is_file():
            raise ValueError(f"required image input missing: {ident}: {image}")
        if image.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
            raise ValueError(f"unsupported API image type for {ident}: {image.suffix}")
        if not 0 < image.stat().st_size < MAX_IMAGE_BYTES:
            raise ValueError(f"image {ident} is empty or >=50MiB")
        with Image.open(image) as im:
            if im.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError(f"{ident}: decoded format not accepted by image edits endpoint")
            im.verify()
    return result




def input_integrity(manifest_file: Path, lock_file: Path, plan_file: Path,
                    draft_file: Path, evidence_file: Path) -> tuple[dict, dict, dict, dict]:
    manifest = sources.read_json(manifest_file)
    lock = sources.read_json(lock_file)
    errs = sources.verify_lock(manifest_file, lock)
    if errs:
        raise ValueError("photo evidence gate blocked: " + "; ".join(errs))
    plan = layout.load_json(plan_file)
    plan_paths = layout.validate_plan(plan, plan_file.resolve().parent)
    draft_evidence = layout.load_json(evidence_file)
    if manifest['project']['mode'] != 'montage':
        raise ValueError("integrated montage edit expects the photo-grounded montage mode")
    if draft_evidence.get('plan_sha256') != layout.digest(plan_file):
        raise ValueError("montage plan changed after draft generation")
    if draft_evidence.get('draft_sha256') != layout.digest(draft_file):
        raise ValueError("draft image changed after generation")
    for bid, path in plan_paths.items():
        if draft_evidence.get('cutout_sha256', {}).get(bid) != layout.digest(path):
            raise ValueError(f"{bid}: building cutout changed after draft generation")
    return manifest, lock, plan, draft_evidence




def redact_error(exc: HTTPError) -> str:
    # Never surface the request body, image base64, or API bearer token.
    return f"image edit API returned HTTP {exc.code} ({exc.reason})"




def multipart_fields(fields: list[tuple[str, str]], image_fields: list[tuple[str, Path]],
                     boundary: str) -> bytes:
    """Encode multipart data with repeated image[] keys, as documented by API."""
    body = io.BytesIO()
    delimiter = ("--" + boundary + "\r\n").encode()
    for name, value in fields:
        body.write(delimiter)
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(value.encode('utf-8'))
        body.write(b'\r\n')
    for ident, path in image_fields:
        suffix = path.suffix.lower()
        mime = 'image/png' if suffix == '.png' else 'image/webp' if suffix == '.webp' else 'image/jpeg'
        body.write(delimiter)
        body.write((f'Content-Disposition: form-data; name="image[]"; filename="{ident}{suffix}"\r\n'
                    f'Content-Type: {mime}\r\n\r\n').encode())
        with path.open('rb') as inp:
            while True:
                chunk = inp.read(1024*1024)
                if not chunk:
                    break
                body.write(chunk)
        body.write(b'\r\n')
    body.write(("--" + boundary + "--\r\n").encode())
    return body.getvalue()




def make_prompt(plan: dict, brief_file: Path) -> str:
    if not brief_file.is_file():
        raise ValueError(f"required grounded redraw brief missing: {brief_file}")
    text = brief_file.read_text(encoding='utf-8')
    role = plan['anchor_landmark_id']
    scroll = plan.get('archetype') == 'landmark-scroll'
    # The layout draft is the composition authority; the style reference controls
    # line language only. Explicitly suppress environmental motifs in style images.
    prompt = (
        "Create ONE unified, high-quality architectural landmark scroll from the supplied "
        "actual image references. The first image is the COMPOSITION DRAFT and has authority "
        "over landmark count, left-to-right order, scale hierarchy and overlap. The second "
        "image is STYLE ONLY: borrow its linework/engraving technique, never its scene, "
        "landscape, trees, shrubs, water, reflections, sky, or arrangement. The remaining "
        "labeled images are source-grounded building cutouts and primary-view photographs "
        "(or complete source-labeled 2x2 atlases). Use the photographs to preserve each "
        "building's real identity and visible geometry.\n\n"
        "COMPOSITION: this is a populated SCHOOL/CITY ARCHITECTURAL PANORAMA, not a scenic "
        "campus illustration, not a gallery, and not a row of isolated stickers. Include "
        "every named landmark in the plan. Let the architecture occupy the full horizontal "
        "span with a continuous, dense-but-readable rhythm of distinct roofs, towers, gates, "
        "historic facades and modern blocks. Vary heights and widths; use purposeful partial "
        "overlap and shared baselines so neighboring structures visually interlock into one "
        "long architectural silhouette. Keep every landmark identifiable; do not hide a "
        "whole building behind another. Avoid large empty gaps between buildings and avoid "
        "equal-sized/equal-spaced cutouts. A single anchor may be strongest, but side and "
        "middle landmarks must still be numerous and legible.\n\n"
        "ENVIRONMENT: architecture is the subject, not the park around it. Draw NO trees, "
        "tree canopies, shrubs, hedges, flowerbeds, lawns, lakes, rivers, reflections, clouds, "
        "mountains, decorative waves, street furniture, birds, or ornamental scenery. If any "
        "reference image contains those things, omit them. At most use one extremely subtle "
        "shared architectural ground stroke; connect the panorama through facade edges, roof "
        "rhythm, overlap and consistent linework, never through foliage or water.\n\n"
        "STYLE: one coherent hand-drawn architectural engraving on an opaque PURE BLACK "
        "background, using refined white/gray linework, controlled line-weight hierarchy, "
        "clean silhouettes and selective facade detail. Main structural contours must remain "
        "stronger than tiny window texture; keep contrast readable at small print size. "
        "Do not use a photofilter/edge-detection look. No invented towers, facades, arches, "
        "doors, signs, readable school names, logos, or unsupported physical adjacency. "
        "Preserve the source geometry even when it conflicts with the draft; adjust placement "
        "rather than redesigning a real building. This is an explicitly artistic montage of "
        "real landmarks, not a claim that they share one camera view.\n\n"
        f"Dominant landmark ID: {role}. Usage: {plan['usage']}. "
        + ("LANDMARK-SCROLL HARD CONSTRAINTS: render at least six distinguishable named "
           "architectural identities and all plan placements. Target 85–95% of meaningful "
           "visual attention on architecture and less than 3% on non-architectural marks; "
           "these are artistic priorities, not pixel-certified metrics. The lower 70–85% of "
           "the canvas should read as one continuous architectural band, with varied roofline "
           "heights and facades spanning left, center and right. Do not solve composition by "
           "adding trees, a park, water, or a large empty foreground. Never drop difficult "
           "landmarks or replace them with generic buildings.\n\n"
           if scroll else "")
        + text
    )
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError("generation prompt too long for image edits API")
    return prompt




def request_edit(*, model: str, size: str, prompt: str,
                 images: list[tuple[str, Path]], timeout: int = 240,
                 api_endpoint: str = API_ENDPOINT,
                 open_request: Callable[..., Any] = urlopen) -> tuple[bytes, str, dict]:
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY missing: no model image generation was performed')
    if not (model.startswith('gpt-image-2.5-') or model in ('gpt-image-1.5','gpt-image-2')):
        raise ValueError('unsupported image model; use a supported GPT Image edit model')
    try:
        w, h = (int(x) for x in size.lower().split('x'))
    except (ValueError, AttributeError) as ex:
        raise ValueError('size must be WIDTHxHEIGHT, for example 1536x864') from ex
    if min(w,h) < 512 or max(w,h) > 3840 or w%16 or h%16 or abs(w/h-16/9)>.05:
        raise ValueError('size must be a valid 16:9, divisible-by-16 image size')
    boundary = '----lineart-' + uuid4().hex
    request_data = multipart_fields([
        ('model',model),('size',size),('quality','high'),
        ('output_format','png'),('background','opaque'),('n','1'),('prompt',prompt)
    ],images,boundary)
    req = Request(api_endpoint, data=request_data, method='POST', headers={
        'Authorization':'Bearer '+key,
        'Content-Type':f'multipart/form-data; boundary={boundary}',
    })
    try:
        with open_request(req,timeout=timeout) as response:
            request_id = response.headers.get('x-request-id', '')
            raw=response.read()
    except HTTPError as exc:
        raise RuntimeError(redact_error(exc)) from None
    except URLError as exc:
        raise RuntimeError('network error while calling image edits API') from exc
    result=json.loads(raw)
    data = result.get('data')
    if not isinstance(data,list) or len(data)!=1 or not isinstance(data[0],dict):
        raise ValueError('image editing response has no single image result')
    raw_b64 = data[0].get('b64_json')
    if not isinstance(raw_b64,str) or not raw_b64:
        raise ValueError('image edit response omitted b64_json; no file was written')
    try:
        generated=base64.b64decode(raw_b64,validate=True)
    except Exception as exc:
        raise ValueError('image edit response contains invalid base64 image') from exc
    with Image.open(io.BytesIO(generated)) as im:
        if im.format!='PNG':
            raise ValueError('image edit result is not PNG')
        actual=im.size
        im.verify()
    if abs(actual[0]/actual[1]-16/9)>.06:
        raise ValueError(f'image editing result aspect ratio is not 16:9: {actual}')
    request_id=request_id or result.get('id','')
    if not request_id:
        raise ValueError('API response lacks a real request id; cannot emit a verifiable generation log')
    meta={'api_model':model,'size':list(actual),'usage':result.get('usage'),
          'request_image_count':len(images)}
    return generated,request_id,meta




def run(*, manifest_file: Path, lock_file: Path, plan_file: Path,
        draft_file: Path, draft_evidence_file: Path, brief_file: Path,
        output_file: Path, log_file: Path,
        model: str=DEFAULT_MODEL, size: str=DEFAULT_SIZE,
        backend: Callable[...,tuple[bytes,str,dict]]=request_edit) -> dict:
    if output_file.resolve() == draft_file.resolve():
        raise ValueError('final output must differ from draft input')
    manifest, lock, plan, draft_evidence = input_integrity(
        manifest_file,lock_file,plan_file,draft_file,draft_evidence_file)
    atlas_entries=[]
    if plan.get('archetype') == 'landmark-scroll':
        plan_paths=layout.validate_plan(plan,plan_file.resolve().parent)
        photos=[];cutouts=[]
        for building in manifest['landmarks']:
            bid=building['id']
            primary=next(p for p in building['photos'] if p['id']==building['primary_view_id'])
            cutouts.append(('CUTOUT:'+bid,plan_paths[bid]))
            photos.append((f"PHOTO:{bid}:{primary['id']}",
                           sources.safe_path(manifest_file.resolve().parent,primary['file'])))
        atlas_images,atlas_entries=scroll_atlas.build(cutouts,photos,log_file.parent/'reference-atlases')
        inputs=[('DRAFT',draft_file),('STYLE',sources.safe_path(manifest_file.resolve().parent,
                    manifest['style_reference']))]+atlas_images
        if len(inputs)>MAX_IMAGE_COUNT:
            raise ValueError('scroll reference atlases exceed the supported image input budget')
        original_sources=cutouts+photos
    else:
        inputs=named_inputs(manifest,plan,draft_file,plan_file,manifest_file)
        original_sources=[]
    snapshot={str(p):layout.digest(p) for _,p in inputs+original_sources}
    snapshot.update({str(p):layout.digest(p) for p in (
        manifest_file,lock_file,plan_file,draft_evidence_file,brief_file)})
    prompt=make_prompt(plan,brief_file)
    generated,call_id,meta=backend(model=model,size=size,prompt=prompt,images=inputs)
    # Even if image editing is long, its input evidence must not silently drift.
    for path,old_sha in snapshot.items():
        if layout.digest(Path(path))!=old_sha:
            raise ValueError(f'image input/evidence changed during generation: {path}')
    if sources.verify_lock(manifest_file,lock):
        raise ValueError('source evidence changed during image generation')
    if hashlib.sha256(generated).hexdigest()==layout.digest(draft_file):
        raise ValueError('generated result equals the draft; no integrated redraw occurred')
    with Image.open(io.BytesIO(generated)) as im:
        if im.format!='PNG' or abs(im.width/im.height-16/9)>.06:
            raise ValueError('backend returned invalid/incorrectly sized image')
        im.verify()
    if not isinstance(call_id,str) or not call_id.strip():
        raise ValueError('no real API call identity returned; refusing generation-log')
    output_file.parent.mkdir(parents=True,exist_ok=True)
    log_file.parent.mkdir(parents=True,exist_ok=True)
    output_file.write_bytes(generated)
    paths=layout.validate_plan(plan,plan_file.resolve().parent)
    log={
        'tool':f'OpenAI Images Edit API ({model})',
        'call_id':call_id,
        'image_input_confirmed':True,
        'reference_ids_attached':[ident for ident,_ in inputs],
        'reference_image_sha256':{ident:layout.digest(p) for ident,p in inputs},
        'input_mode':'reference-atlas-v1' if atlas_entries else 'individual',
        'atlas_entries':atlas_entries,
        'atlas_dir':'reference-atlases' if atlas_entries else None,
        'plan_sha256':layout.digest(plan_file),
        'draft_sha256':layout.digest(draft_file),
        'output_sha256':layout.digest(output_file),
        'cutout_sha256':{bid:layout.digest(p) for bid,p in paths.items()},
        'response_metadata':meta,
        'assurance':'Generation call only; requires separate photo-based montage_audit',
    }
    sources.write_json(log_file,log)
    return log




def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--evidence-lock',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--draft',type=Path,required=True)
    p.add_argument('--draft-evidence',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--generation-log',type=Path,required=True)
    p.add_argument('--model',default=DEFAULT_MODEL)
    p.add_argument('--size',default=DEFAULT_SIZE)
    a=p.parse_args()
    try:
        log=run(manifest_file=a.manifest,lock_file=a.evidence_lock,
                plan_file=a.plan,draft_file=a.draft,
                draft_evidence_file=a.draft_evidence,brief_file=a.brief,
                output_file=a.output,log_file=a.generation_log,model=a.model,size=a.size)
    except (OSError,ValueError,RuntimeError,UnidentifiedImageError) as exc:
        p.error(str(exc))
    print(f"Actual integrated image-edit output: {a.output}")
    print(f"Generation evidence recorded in {a.generation_log} (request id: {log['call_id']})")
    print("This image is NOT yet approved; run montage_audit.py on the final output")




if __name__=='__main__':
    main()


