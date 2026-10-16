#!/usr/bin/env python3
"""Evidence-gated photo-to-lineart orchestration; DOES NOT claim to generate images.


Commands:
  template   Create an explicitly incomplete project manifest
  fetch      Download *declared original* photographs from allowlisted HTTPS hosts
  prepare    Validate evidence and construct contact sheets + grounded generation packet
  audit      Validate human review and bind its approval to the generated image hash


Design boundary: source provenance and photo-to-artwork structural fidelity require
human verification. Automated gates check that evidence/review exist, not that
human assertions are true. No hidden CoT, image model, or OCR is used here.
"""
from __future__ import annotations


import argparse
import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import sys
import tempfile
from urllib.parse import urlparse, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from pathlib import Path
from typing import Any


from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


VERSION = "2.0"
MIN_PIXELS = 1_500_000
MIN_SHORT_SIDE = 850
MIN_LONG_SIDE = 1400
MAX_BYTES = 24 * 1024 * 1024
PHOTO_TYPES = {"JPEG", "PNG", "WEBP", "TIFF"}
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,63}$")
REVIEW_STATUSES = {"pass", "fail", "unknown"}




def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()




def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()




def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")




def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")




def read_json(path: Path) -> dict:
    v = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v, dict):
        raise ValueError("JSON root must be an object")
    return v




def safe_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name:
        raise ValueError("missing relative file path")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path must be relative and within manifest directory: {name}")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"file escapes manifest root: {name}")
    return result




def valid_https(url: str) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None




def load_photo(path: Path) -> tuple[Image.Image, dict]:
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        if im.format not in PHOTO_TYPES:
            raise ValueError(f"unsupported format: {im.format}")
        im.load()
        rgb = im.convert("RGB")
        info = {"width": im.width, "height": im.height, "format": im.format, "bytes": path.stat().st_size}
        return rgb, info




def dhash(img: Image.Image) -> int:
    thumb = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    px = list(thumb.get_flattened_data() if hasattr(thumb, "get_flattened_data") else thumb.getdata())
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | int(px[y * 9 + x] > px[y * 9 + x + 1])
    return bits




def error(errors: list[str], message: str) -> None:
    errors.append(message)




def agent_attestation_valid(record: dict, *, kind: str, required_ids: set[str] | None = None) -> bool:
    """Validate existence of a structured AGENT report, not its objective truth.

    Never set human_* booleans on the basis of an AI review. Permission and
    attribution claims remain user/account responsibility when publishing.
    """
    att = record.get("agent_evidence")
    if not isinstance(att, dict):
        return False
    confidence = att.get("confidence")
    if (isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or
        not 0.92 <= confidence <= 1):
        return False
    if (not str(att.get("model", "")).strip() or not str(att.get("call_id", "")).strip() or
            not isinstance(att.get("observation"), str) or len(att["observation"].strip()) < 30):
        return False
    if kind == "photo":
        if record.get("source_page") == "user-owned":
            return False  # Only the user can license their own private original.
        if not all(att.get(k) is True for k in
                   ("source_page_checked", "building_identity_checked", "license_checked")):
            return False
        if not valid_https(att.get("license_evidence_url", "")):
            return False
    if kind == "feature":
        inputs = att.get("image_input_ids") or []
        if not isinstance(inputs, list) or not required_ids or not required_ids.intersection(inputs):
            return False
    return True


def check_project(manifest_file: Path) -> dict:
    root = manifest_file.resolve().parent
    project = read_json(manifest_file)
    problems: list[str] = []
    warnings: list[str] = []
    photos = []
    features = []
    photo_keys: set[str] = set()
    landmark_ids: set[str] = set()
    evidence_phash: dict[str, int] = {}
    global_photo_shas: dict[str, str] = {}


    if project.get("schema_version") != 1:
        error(problems, "schema_version must equal 1")
    meta = project.get("project", {})
    if not isinstance(meta, dict) or not str(meta.get("title", "")).strip():
        error(problems, "project.title is required")
        meta = {}
    if meta.get("mode") not in ("montage", "photo-faithful"):
        error(problems, "project.mode must be montage or photo-faithful")
    if meta.get("aspect_ratio") != "16:9":
        error(problems, "project.aspect_ratio must be '16:9' for this release")
    if not (isinstance(meta.get("upper_blank_fraction"), (float, int)) and 0.45 <= meta["upper_blank_fraction"] <= 0.8):
        error(problems, "project.upper_blank_fraction must be 0.45..0.8")


    style = project.get("style_reference", "")
    if not style:
        error(problems, "style_reference path is required")
    else:
        try:
            image_path = safe_path(root, style)
            if not image_path.is_file():
                error(problems, f"style reference missing: {style}")
            else:
                _, info = load_photo(image_path)
                if info["width"] < 600 or info["height"] < 300:
                    error(problems, f"style reference too small: {style}")
                photos.append({"kind": "style", "id": "style", "relative_path": style, "sha256": sha_file(image_path), **info})
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            error(problems, f"style reference invalid: {exc}")


    landmarks = project.get("landmarks", [])
    if not isinstance(landmarks, list) or not landmarks:
        error(problems, "landmarks must be a non-empty list")
        landmarks = []
    if meta.get("mode") == "photo-faithful" and len(landmarks) != 1:
        error(problems, "photo-faithful mode permits exactly one landmark; do not invent a single viewpoint from distant sites")
    for building in landmarks:
        if not isinstance(building, dict):
            error(problems, "landmark entry must be an object")
            continue
        bid = building.get("id", "")
        if not isinstance(bid, str) or not SAFE_ID.fullmatch(bid) or bid in landmark_ids:
            error(problems, f"invalid or duplicate landmark id: {bid!r}")
            continue
        landmark_ids.add(bid)
        if not str(building.get("name", "")).strip() or not str(building.get("location", "")).strip():
            error(problems, f"{bid}: name and location must be verified")
        views = building.get("photos", [])
        if not isinstance(views, list) or len(views) < 2:
            error(problems, f"{bid}: at least two distinct original photo views are required")
            views = views if isinstance(views, list) else []
        accepted_angles = set()
        accepted_photo_hashes = []
        primary = building.get("primary_view_id", "")
        if not primary or primary not in {v.get("id") for v in views if isinstance(v, dict)}:
            error(problems, f"{bid}: primary_view_id must identify the exact main camera/view anchor")
        for photo in views:
            if not isinstance(photo, dict):
                error(problems, f"{bid}: each photo must be an object")
                continue
            pid = photo.get("id", "")
            key = f"{bid}:{pid}"
            if not isinstance(pid, str) or not SAFE_ID.fullmatch(pid) or key in photo_keys:
                error(problems, f"{bid}: invalid/duplicate photo id {pid!r}")
                continue
            photo_keys.add(key)
            path_name = photo.get("file", "")
            for k in ("photographer", "license", "source_verified_by", "view_angle"):
                if not str(photo.get(k, "")).strip():
                    error(problems, f"{key}: missing {k}")
            if photo.get("derivatives_allowed") is not True:
                error(problems, f"{key}: derivatives_allowed must be justified by license evidence")
            agent_photo = photo.get("agent_confirmed_photo") is True and agent_attestation_valid(photo, kind="photo")
            human_photo = photo.get("human_confirmed_photo") is True
            if not (human_photo or agent_photo):
                error(problems, f"{key}: require human_confirmed_photo or supported agent_evidence with original-source and license checks")
            attestation_mode = "human" if human_photo else "agent" if agent_photo else "unverified"
            page = photo.get("source_page", "")
            if page != "user-owned" and not valid_https(page):
                error(problems, f"{key}: source_page must be HTTPS or 'user-owned'")
            if page == "user-owned" and photo.get("license") != "user-owned":
                error(problems, f"{key}: user-owned photo should have license='user-owned'")
            original = photo.get("original_url", "")
            if original and not valid_https(original):
                error(problems, f"{key}: original_url must be HTTPS")
            try:
                path = safe_path(root, path_name)
                if not path.is_file():
                    error(problems, f"{key}: original image missing: {path_name}; use fetch or supply a local file")
                    continue
                img, info = load_photo(path)
                if min(img.size) < MIN_SHORT_SIDE or max(img.size) < MIN_LONG_SIDE or img.width * img.height < MIN_PIXELS:
                    error(problems, f"{key}: insufficient native resolution {img.width}x{img.height}; need >=1.5MP and sides >=850/1400")
                digest = sha_file(path)
                if digest in accepted_photo_hashes:
                    error(problems, f"{bid}: same photo content reused as multiple views")
                accepted_photo_hashes.append(digest)
                if digest in global_photo_shas and global_photo_shas[digest] != key:
                    error(problems, f"{key}: identical original photo already claimed as {global_photo_shas[digest]}")
                global_photo_shas[digest] = key
                p_hash = dhash(img)
                for other_id, old_hash in evidence_phash.items():
                    if other_id.startswith(bid + ":") and (p_hash ^ old_hash).bit_count() <= 3:
                        error(problems, f"{key}: perceptually near-identical to {other_id}; supply genuinely different camera view")
                evidence_phash[key] = p_hash
                photos.append({"kind": "landmark", "id": key, "relative_path": path_name, "sha256": digest, "phash": f"{p_hash:016x}", "attestation_mode": attestation_mode, **info})
                accepted_angles.add(str(photo.get("view_angle", "")).strip().lower())
            except (OSError, ValueError, UnidentifiedImageError) as exc:
                error(problems, f"{key}: cannot read photo: {exc}")
        if len(accepted_angles - {""}) < 2:
            error(problems, f"{bid}: two genuinely distinct labeled camera angles required")


        claims = building.get("must_match", [])
        if not isinstance(claims, list) or len(claims) < 2:
            error(problems, f"{bid}: provide at least two evidence-backed visible structural features")
            claims = claims if isinstance(claims, list) else []
        used = set()
        for f in claims:
            if not isinstance(f, dict):
                error(problems, f"{bid}: invalid feature")
                continue
            fid = f.get("id", "")
            if not isinstance(fid, str) or not SAFE_ID.fullmatch(fid) or fid in used:
                error(problems, f"{bid}: invalid/duplicate feature id {fid!r}")
                continue
            used.add(fid)
            refs = f.get("photo_ids", [])
            known = {p.get("id") for p in views if isinstance(p, dict)}
            if not isinstance(refs, list) or not refs or set(refs) - known:
                error(problems, f"{bid}:{fid}: photo_ids must cite available photo ids")
            human_feature = f.get("visible_and_human_verified") is True
            agent_feature = (f.get("visible_and_agent_verified") is True and
                             agent_attestation_valid(f, kind="feature", required_ids={f"{bid}:{x}" for x in refs} if isinstance(refs, list) else set()))
            if not str(f.get("description", "")).strip() or not (human_feature or agent_feature):
                error(problems, f"{bid}:{fid}: need a visible feature and human or structured agent visual evidence")
            boxes = f.get("bboxes")
            if boxes is not None and (not isinstance(boxes, dict) or set(boxes.keys()) - set(refs if isinstance(refs,list) else [])):
                error(problems, f"{bid}:{fid}: bboxes keys must name evidence photo IDs")
                boxes = {}
            # `bbox` is supported for a SINGLE cited photo only. The same
            # pixel rectangle means something different in another viewpoint.
            if f.get("bbox") is not None and (not isinstance(refs,list) or len(refs) != 1):
                error(problems, f"{bid}:{fid}: use bboxes per-photo instead of reusing one bbox across camera angles")
            candidate_boxes = dict(boxes or {})
            if f.get("bbox") is not None and isinstance(refs,list) and len(refs)==1:
                candidate_boxes[refs[0]] = f["bbox"]
            for view, region in candidate_boxes.items():
                if not isinstance(region, list) or len(region) != 4 or any(not isinstance(v, (float, int)) for v in region) or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1):
                    error(problems, f"{bid}:{fid}:{view}: bbox must be normalized [x0,y0,x1,y1]")
            features.append({"landmark_id": bid, "id": fid, "description": f.get("description", ""), "photos": refs})
        forbidden = building.get("forbidden_inventions", [])
        if not isinstance(forbidden, list) or not forbidden or any(not isinstance(x, str) or not x.strip() for x in forbidden):
            error(problems, f"{bid}: set explicit forbidden_inventions based on reference photos")
        if not isinstance(building.get("unknowns"), list):
            error(problems, f"{bid}: unknowns must list obscured or unverifiable architecture (possibly [])")
        if building.get("signage_policy") != "no_generated_letters_use_verified_overlay":
            error(problems, f"{bid}: signage_policy must be no_generated_letters_use_verified_overlay")
        marks = building.get("official_marks", [])
        if not isinstance(marks, list):
            error(problems, f"{bid}: official_marks must be a list")
        else:
            for m in marks:
                if not isinstance(m, dict) or not str(m.get("label", "")).strip() or not valid_https(m.get("authority_page", "")) or not str(m.get("verified_by", "")).strip():
                    error(problems, f"{bid}: official mark requires label, authority_page (HTTPS), verified_by")
    return {"version": VERSION, "status": "blocked" if problems else "ready", "manifest": str(manifest_file), "manifest_sha256": sha_file(manifest_file), "errors": problems, "warnings": warnings, "photos": photos, "features": features, "landmarks": sorted(landmark_ids)}




def font(size: int):
    for path in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()




def photo_board(manifest: dict, root: Path, out: Path) -> dict[str, str]:
    landmarks = manifest["landmarks"]
    rows = [(b, p) for b in landmarks for p in b["photos"]]
    width, cell_w, cell_h, margin = 1440, 680, 390, 22
    cell_img_w, cell_img_h = cell_w - 24, 308
    board = Image.new("RGB", (width, 90 + ((len(rows) + 1) // 2) * cell_h), "#eef1f4")
    draw = ImageDraw.Draw(board)
    draw.text((24, 20), "Evidence contact sheet | photos are NOT generated artwork", fill="#18304b", font=font(27))
    crops = {}
    for i, (b, p) in enumerate(rows):
        x, y = 24 + (i % 2) * (cell_w + margin), 78 + (i // 2) * cell_h
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h - 8), radius=12, fill="white", outline="#ccd6df", width=2)
        image, _ = load_photo(safe_path(root, p["file"]))
        small = image.copy()
        small.thumbnail((cell_img_w, cell_img_h), Image.Resampling.LANCZOS)
        board.paste(small, (x + 12 + (cell_img_w - small.width) // 2, y + 10 + (cell_img_h - small.height) // 2))
        info = f"{b['id']}:{p['id']} | angle: {p['view_angle']} | {image.width}x{image.height}"
        draw.text((x + 12, y + 323), info[:82], fill="#18304b", font=font(17))
        draw.text((x + 12, y + 354), f"source verified by: {p['source_verified_by']}"[:84], fill="#637385", font=font(15))
        for feat in b["must_match"]:
            if p["id"] not in feat["photo_ids"]:
                continue
            coords = (feat.get("bboxes") or {}).get(p["id"])
            if coords is None and len(feat["photo_ids"])==1:
                coords = feat.get("bbox")
            if coords is None:
                continue
            crop_dir = out / "feature-crops" / b["id"]
            crop_dir.mkdir(parents=True, exist_ok=True)
            rect = tuple(round(v * dim) for v, dim in zip(coords, (image.width, image.height, image.width, image.height)))
            crop = image.crop(rect)
            file = crop_dir / f"{feat['id']}__{p['id']}.png"
            crop.save(file)
            crops[f"{b['id']}:{feat['id']}:{p['id']}"] = str(file.relative_to(out))
    board.save(out / "reference-board.png")
    return crops




def generation_packet(manifest: dict, report: dict, crops: dict[str, str]) -> str:
    meta = manifest["project"]
    out = [
        "# IMAGE GENERATION PACKET — photo-grounded architecture",
        "",
        f"Project: {meta['title']}", f"Mode: {meta['mode']}",
        f"Layout: 16:9, leave upper {meta['upper_blank_fraction']:.0%} empty; architectural drawing lower band only.",
        "STYLE IMAGE: " + manifest["style_reference"],
        "",
        "## Image input contract (MANDATORY)",
        "Provide the actual source photo pixels as separate image attachments to a model with image-input support. The style reference MUST also be attached. A text description or filenames alone do not count as image grounding.",
        "When image attachments are unavailable: STOP; deliver this packet for manual use instead of claiming generation has occurred.",
        "Do not derive building geometry from generic architectural style priors. Preserve only identifiable features proven by provided views. No guesses for unseen facades, hidden window counts, towers, stairs, arch counts or roof forms.",
        "For a montage, FIRST render/review each isolated landmark from its photos, preferably with transparent background; then use deterministic compositing. Do not ask a generator to hallucinate the connections into a single continuous real-world complex.",
        "NO LEGIBLE OR OFFICIAL TEXT should be generated by the model; keep sign panels unlettered, and optionally add independently licensed and verified branding as separate overlays.",
        "Aim for hand-drawn gray/white architectural line art on black: selective windows, natural line-weight hierarchy, visible architectural joints, editorial line textures. DO NOT run Canny/photo-outline as a substitute for drawing.",
        "",
        "## Evidence locked images",
    ]
    for p in report["photos"]:
        out.append(f"- `{p['id']}`: `{p['relative_path']}`; SHA256 `{p['sha256']}`; native {p['width']}x{p['height']}")
    out.extend(["", "## Per-landmark immutable constraints"])
    for b in manifest["landmarks"]:
        out.extend(["", f"### {b['id']} — {b['name']} ({b['location']})", ""]) 
        out.append(f"CAMERA ANCHOR (must preserve this viewpoint, do not merge views): {b['id']}:{b['primary_view_id']}")
        out.append("Actual photos: " + ", ".join(f"{b['id']}:{p['id']} ({p['view_angle']})" for p in b["photos"]))
        out.append("REQUIRED structural facts:")
        for f in b["must_match"]:
            linked = ", ".join(f"{b['id']}:{r}" for r in f["photo_ids"])
            examples = [crops[f"{b['id']}:{f['id']}:{r}"] for r in f["photo_ids"] if f"{b['id']}:{f['id']}:{r}" in crops]
            out.append(f"- `{f['id']}`: {f['description']} | evidence: {linked}" + (" | close-ups: " + ", ".join(examples) if examples else ""))
        out.append("FORBIDDEN inventions: " + "; ".join(b["forbidden_inventions"]))
        out.append("UNOBSERVED — do not guess: " + ("; ".join(b["unknowns"]) or "none declared; still never fill hidden geometry without evidence"))
        for m in b.get("official_marks", []):
            out.append(f"Verified overlay asset only: {m['label']} | authority: {m['authority_page']}")
    out.extend(["", "## Art direction and review", "The line-art style reference constrains stroke quality and placement, not building geometry. Preserve the designated primary camera viewpoint; use alternate photo views only to resolve/verify details.", "If a structural feature is distorted, do not repair by giving the model more descriptive fantasy architecture; feed cropped reference evidence again or switch to photo-grounded manual vector redraw.", "Label a multi-campus montage as *illustrative composite*, never a single real viewpoint.", "For every proposed output, complete `review-template.json`, independently compare every required feature against its cited original photograph, and call `audit` before vectorization."])
    return "\n".join(out) + "\n"




def review_template(manifest: dict, evidence_digest: str) -> dict:
    return {
        "reviewer": "REPLACE_WITH_HUMAN_REVIEWER",
        "evidence_sha256": evidence_digest,
        "model_invocation": {
            "tool": "REPLACE_WITH_ACTUAL_IMAGE_TOOL",
            "image_input_confirmed": False,
            "reference_ids_attached": [],
            "landmark_calls": [{"id": b["id"], "tool": "REPLACE_WITH_ACTUAL_IMAGE_TOOL", "image_input_confirmed": False,
                                "reference_ids_attached": [], "notes": "Record actual per-building tool call and output."}
                               for b in manifest["landmarks"]],
            "notes": "Record actual tool invocations, not a proposed prompt or tool name."
        },
        "global_checks": {k: "unknown" for k in ("no_unlisted_buildings", "no_invented_text", "viewpoint_or_montage_labeled", "style_and_layout_accepted")},
        "landmark_reviews": [
            {"id": b["id"], "features": {f["id"]: "unknown" for f in b["must_match"]}, "no_new_geometry": "unknown", "source_comparison_note": ""}
            for b in manifest["landmarks"]
        ],
    }




def run_prepare(manifest_path: Path, output: Path) -> int:
    report = check_project(manifest_path)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "preflight-report.json", report)
    if report["status"] != "ready":
        print("PREFLIGHT BLOCKED; see preflight-report.json\n- " + "\n- ".join(report["errors"]), file=sys.stderr)
        return 2
    manifest = read_json(manifest_path)
    crops = photo_board(manifest, manifest_path.parent, output)
    evidence = {"schema_version": 1, "project_manifest_sha256": report["manifest_sha256"], "photos": report["photos"], "features": report["features"]}
    evidence_hash = sha_bytes(canonical_json(evidence))
    evidence["evidence_sha256"] = evidence_hash
    write_json(output / "evidence-lock.json", evidence)
    write_json(output / "review-template.json", review_template(manifest, evidence_hash))
    (output / "generation-brief.md").write_text(generation_packet(manifest, report, crops), encoding="utf-8")
    print(f"READY. Evidence locked: {evidence_hash}\nBoard: {output/'reference-board.png'}\nBrief: {output/'generation-brief.md'}")
    return 0




def verify_lock(manifest_path: Path, lock: dict) -> list[str]:
    report = check_project(manifest_path)
    failures = report["errors"][:]
    if report["status"] != "ready":
        return failures
    if lock.get("project_manifest_sha256") != report["manifest_sha256"]:
        failures.append("manifest changed after preparation")
    expected = {p["id"]: p["sha256"] for p in lock.get("photos", [])}
    current = {p["id"]: p["sha256"] for p in report["photos"]}
    if expected != current:
        failures.append("reference images changed since locked evidence packet")
    digest = sha_bytes(canonical_json({"schema_version": 1, "project_manifest_sha256": report["manifest_sha256"], "photos": report["photos"], "features": report["features"]}))
    if lock.get("evidence_sha256") != digest:
        failures.append("evidence-lock hash invalid or stale")
    return failures




def run_audit(manifest_path: Path, evidence_path: Path, image_path: Path, review_path: Path, output: Path) -> int:
    problems: list[str] = []
    evidence = read_json(evidence_path)
    review = read_json(review_path)
    manifest = read_json(manifest_path)
    problems.extend(verify_lock(manifest_path, evidence))
    if not image_path.is_file():
        problems.append("generated image missing")
    else:
        try:
            load_photo(image_path)
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            problems.append(f"invalid generated illustration: {exc}")
    if review.get("evidence_sha256") != evidence.get("evidence_sha256"):
        problems.append("review is not tied to locked evidence packet")
    reviewer = str(review.get("reviewer", ""))
    if not reviewer.strip() or reviewer.startswith("REPLACE_"):
        problems.append("a named independent human reviewer is required")
    invocation = review.get("model_invocation", {})
    if not isinstance(invocation, dict):
        invocation = {}
    if not str(invocation.get("tool", "")).strip() or str(invocation.get("tool", "")).startswith("REPLACE_"):
        problems.append("model image-generation tool name missing")
    if invocation.get("image_input_confirmed") is not True:
        problems.append("explicit confirmation that actual reference IMAGE pixels were provided to model is mandatory")
    attached = set(invocation.get("reference_ids_attached") or [])
    expected = {p["id"] for p in evidence.get("photos", [])}
    if not expected.issubset(attached):
        problems.append("image model input is missing one or more required photo/style ids: " + ", ".join(sorted(expected - attached)))
    # A union of refs is not enough: every individually rendered building must
    # actually receive its own photographs, not merely the general prompt.
    calls = invocation.get("landmark_calls", [])
    call_by_id = {c.get("id"): c for c in calls if isinstance(c, dict)}
    for b in manifest.get("landmarks", []):
        bid = b["id"]
        required = {"style", *(bid + ":" + p["id"] for p in b.get("photos", []))}
        call = call_by_id.get(bid, {})
        refs = set(call.get("reference_ids_attached") or [])
        if call.get("image_input_confirmed") is not True or not str(call.get("tool", "")).strip() or str(call.get("tool", "")).startswith("REPLACE_"):
            problems.append(f"{bid}: actual image-enabled tool call must be recorded for this building")
        if required - refs:
            problems.append(f"{bid}: direct per-building image input omitted {sorted(required - refs)}")


    checks = review.get("global_checks", {})
    for key in ("no_unlisted_buildings", "no_invented_text", "viewpoint_or_montage_labeled", "style_and_layout_accepted"):
        if not isinstance(checks, dict) or checks.get(key) != "pass":
            problems.append(f"global visual check not passed: {key}")
    reviews = review.get("landmark_reviews", [])
    by_id = {r.get("id"): r for r in reviews if isinstance(r, dict)}
    for landmark in manifest.get("landmarks", []):
        bid = landmark["id"]
        r = by_id.get(bid, {})
        if r.get("no_new_geometry") != "pass":
            problems.append(f"{bid}: hallucinated / unobserved geometry check not passed")
        if len(str(r.get("source_comparison_note", "")).strip()) < 15:
            problems.append(f"{bid}: missing substantial source/photo comparison note")
        for feat in landmark.get("must_match", []):
            fid = feat["id"]
            if not isinstance(r.get("features"), dict) or r["features"].get(fid) != "pass":
                problems.append(f"{bid}:{fid}: not explicitly reviewed as pass against cited original photos")
    result = {"status": "blocked" if problems else "approved", "problems": problems, "reviewer": reviewer, "image_sha256": sha_file(image_path) if image_path.is_file() else None, "evidence_sha256": evidence.get("evidence_sha256"), "review_sha256": sha_file(review_path), "manifest_sha256": sha_file(manifest_path)}
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    if problems:
        print("AUDIT BLOCKED\n- " + "\n- ".join(problems), file=sys.stderr)
        return 3
    print("AUDIT APPROVED (human-attested, not a mathematical proof): " + str(output))
    return 0




class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None




def host_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    return bool(infos) and all(ipaddress.ip_address(info[4][0]).is_global for info in infos)




def fetch_original(url: str, allowed: set[str], max_bytes: int = MAX_BYTES) -> bytes:
    opener = build_opener(NoRedirect)
    for _ in range(5):
        if not valid_https(url):
            raise ValueError("only HTTPS original-image URLs allowed")
        host = urlparse(url).hostname.lower()
        if host not in allowed:
            raise ValueError(f"host {host} is not explicitly allowlisted")
        if not host_public(host):
            raise ValueError(f"host {host} does not resolve only to publicly routed addresses")
        try:
            res = opener.open(Request(url, headers={"User-Agent": "ArchitecturalLineartSkillkit/2.0"}), timeout=20)
        except Exception as exc:
            if getattr(exc, "code", None) in (301, 302, 303, 307, 308):
                url = urljoin(url, exc.headers.get("Location", ""))
                continue
            raise
        with res:
            typ = res.headers.get("Content-Type", "")
            if not typ.lower().startswith("image/") and typ.lower() != "application/octet-stream":
                raise ValueError(f"non-image content type: {typ}")
            chunks = []; amount = 0
            while True:
                part = res.read(64 * 1024)
                if not part: break
                amount += len(part)
                if amount > max_bytes:
                    raise ValueError(f"download exceeds {max_bytes} bytes")
                chunks.append(part)
            return b"".join(chunks)
    raise ValueError("too many redirects")




def run_fetch(manifest_path: Path, allowed: list[str], dry_run: bool, overwrite: bool) -> int:
    manifest = read_json(manifest_path)
    root = manifest_path.resolve().parent
    whitelist = {h.lower() for h in allowed}
    if not whitelist:
        print("FETCH BLOCKED: supply --allow-host for each trusted image host", file=sys.stderr)
        return 2
    for b in manifest.get("landmarks", []):
        for p in b.get("photos", []):
            if not p.get("original_url"):
                continue
            dest = safe_path(root, p["file"])
            if dest.exists() and not overwrite:
                print("exists, skipping: " + str(dest))
                continue
            if dry_run:
                print(f"would fetch {p['original_url']} => {dest}")
                continue
            data = fetch_original(p["original_url"], whitelist)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dest.parent, suffix=dest.suffix or ".img", delete=False) as tmp:
                temp_path = Path(tmp.name)
                tmp.write(data)
            try:
                load_photo(temp_path)
                temp_path.replace(dest)
            finally:
                temp_path.unlink(missing_ok=True)
            print(f"saved {dest} ({len(data)} bytes, sha256={sha_file(dest)})")
    return 0




def template(path: Path) -> None:
    data = {
        "schema_version": 1,
        "project": {"title": "REPLACE: real campus/landmark", "mode": "montage", "aspect_ratio": "16:9", "upper_blank_fraction": 0.62},
        "style_reference": "photos/style-reference.png",
        "landmarks": [
            {"id": "BuildingA", "name": "REPLACE verified building name", "location": "REPLACE exact campus/location",
             "primary_view_id": "front",
             "photos": [
                 {"id": "front", "file": "photos/BuildingA-front.jpg", "source_page": "https://REPLACE-SOURCE-PAGE", "original_url": "https://REPLACE-ORIGINAL-IMAGE", "photographer": "REPLACE", "license": "REPLACE", "derivatives_allowed": False, "human_confirmed_photo": False, "source_verified_by": "", "view_angle": "front"},
                 {"id": "side", "file": "photos/BuildingA-side.jpg", "source_page": "https://REPLACE-SECOND-SOURCE", "original_url": "https://REPLACE-SECOND-ORIGINAL", "photographer": "REPLACE", "license": "REPLACE", "derivatives_allowed": False, "human_confirmed_photo": False, "source_verified_by": "", "view_angle": "side"}
             ],
             "must_match": [
                 {"id": "roof", "description": "REPLACE with exact roof silhouette seen in original photograph", "photo_ids": ["front", "side"], "visible_and_human_verified": False, "bbox": [0.1, 0.1, 0.9, 0.5]},
                 {"id": "entrance", "description": "REPLACE with actual entrance/column count visible in original photograph", "photo_ids": ["front"], "visible_and_human_verified": False, "bbox": [0.2, 0.35, 0.8, 0.9]}
             ],
             "forbidden_inventions": ["Do not create unseen clock towers, wings, arches or readable signage"],
             "unknowns": ["REPLACE with facade/sections not seen in photos; keep hidden"],
             "signage_policy": "no_generated_letters_use_verified_overlay",
             "official_marks": []}
        ]
    }
    write_json(path, data)




def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    t = sub.add_parser("template", help="create manifest with explicitly unverified placeholders")
    t.add_argument("--output", required=True, type=Path)
    f = sub.add_parser("fetch", help="download declared original photos from allowlisted HTTPS hosts")
    f.add_argument("--manifest", required=True, type=Path)
    f.add_argument("--allow-host", action="append", default=[])
    f.add_argument("--dry-run", action="store_true")
    f.add_argument("--overwrite", action="store_true")
    p = sub.add_parser("prepare", help="validate all reference evidence then create generation pack")
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    a = sub.add_parser("audit", help="refuse approval unless all human-reviewed features pass")
    a.add_argument("--manifest", required=True, type=Path)
    a.add_argument("--evidence-lock", required=True, type=Path)
    a.add_argument("--image", required=True, type=Path)
    a.add_argument("--review", required=True, type=Path)
    a.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "template":
            template(args.output); print(f"Created intentionally incomplete template: {args.output}"); return 0
        if args.command == "prepare": return run_prepare(args.manifest, args.out_dir)
        if args.command == "audit": return run_audit(args.manifest, args.evidence_lock, args.image, args.review, args.output)
        if args.command == "fetch": return run_fetch(args.manifest, args.allow_host, args.dry_run, args.overwrite)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1




if __name__ == "__main__":
    raise SystemExit(main())


