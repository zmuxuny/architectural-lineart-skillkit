#!/usr/bin/env python3
"""Build a cohesive commemorative montage DRAFT, not a finished factual artwork.


The draft carries foreground/background hierarchy, deliberate overlap and
decorative connecting strokes. A reference-conditioned IMAGE EDIT must make the
finished artwork; passing this draft off as the finished montage is prohibited.
"""
from __future__ import annotations


import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


USAGES = ("tote-bag", "anniversary-poster", "ppt-cover", "city-poster")
MODES = ("commemorative-montage",)
ARCHETYPES = ("hero-montage", "landmark-scroll")
RESAMPLING = Image.Resampling.LANCZOS




def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()




def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")




def load_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("JSON root must be an object")
    return result




def safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("cutout path is missing")
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("cutout must be a relative path within the plan folder")
    out = (root / p).resolve()
    if not out.is_relative_to(root.resolve()):
        raise ValueError("cutout path escapes the plan directory")
    return out




def make_plan(manifest: dict, usage: str, anchor_id: str, cutouts: str = "cutouts") -> dict:
    """Choose an intentional center/side hierarchy; Agent may refine boxes."""
    if usage not in USAGES:
        raise ValueError("unknown usage: " + usage)
    landmarks = manifest.get("landmarks", [])
    ids = [b["id"] for b in landmarks]
    if not 2 <= len(ids) <= 5 or len(set(ids)) != len(ids):
        raise ValueError("commemorative montage requires 2–5 distinct landmarks")
    if anchor_id not in ids:
        raise ValueError("anchor must match a landmark ID in the manifest")


    # All layouts intentionally overlap; the old gallery compositor does not.
    # Rectangles are normalized x0,y0,x1,y1 in a 16:9 draft canvas.
    layouts = {
        "tote-bag": {
            "top": 0.18, "ground": 0.87,
            "main": [.26, .22, .75, .92],
            "sides": [[.04, .37, .46, .91], [.55, .38, .97, .92],
                      [.00, .48, .37, .86], [.66, .47, 1.00, .87]],
        },
        "anniversary-poster": {
            "top": 0.33, "ground": 0.91,
            "main": [.27, .40, .74, .96],
            "sides": [[.03, .54, .46, .95], [.55, .53, .98, .95],
                      [.00, .62, .35, .90], [.67, .63, 1.00, .91]],
        },
        "ppt-cover": {
            "top": 0.51, "ground": 0.95,
            "main": [.28, .53, .73, .99],
            "sides": [[.02, .62, .46, .97], [.55, .62, .99, .97],
                      [.00, .68, .36, .93], [.65, .69, 1.00, .94]],
        },
        "city-poster": {
            "top": 0.34, "ground": 0.92,
            "main": [.28, .39, .73, .98],
            "sides": [[.03, .53, .48, .95], [.54, .52, .98, .94],
                      [.00, .63, .36, .91], [.65, .64, 1.00, .91]],
        },
    }
    spec = layouts[usage]
    supporters = [bid for bid in ids if bid != anchor_id]
    placements = []
    for i, bid in enumerate(supporters):
        placements.append({
            "landmark_id": bid,
            "image": f"{cutouts}/{bid}.png",
            "role": "support",
            "rect": spec["sides"][i],
            "depth": i,
            "opacity": 0.85 if i < 2 else 0.72,
        })
    placements.append({
        "landmark_id": anchor_id,
        "image": f"{cutouts}/{anchor_id}.png",
        "role": "anchor",
        "rect": spec["main"],
        "depth": 10,
        "opacity": 1.0,
    })
    return {
        "schema_version": 1,
        "mode": "commemorative-montage",
        "usage": usage,
        "canvas": [1672, 941],
        "upper_blank_fraction": spec["top"],
        "ground_y": spec["ground"],
        "anchor_landmark_id": anchor_id,
        "integrated_redraw_required": True,
        "connectors": ["ornamental-ground-line", "flowing-contour-waves"],
        "placements": placements,
        "disclosure": "Artistic montage of independently grounded real buildings, not a true single-camera scene.",
    }




def make_scroll_plan(manifest: dict, usage: str, anchor_id: str | None = None,
                     cutouts: str = "cutouts") -> dict:
    """Architecture-dominant landmark scroll, rather than three buildings plus scenery.

    6–10 verified landmarks share a wide illustrative skyline; positions
    alternate in roof-height and depth. The final result still requires a
    photo-conditioned integrated redraw and visual audit.
    """
    if usage not in USAGES:
        raise ValueError("unknown usage: " + usage)
    ids = [b["id"] for b in manifest.get("landmarks", [])]
    if len(ids) < 6 or len(ids) > 10 or len(ids) != len(set(ids)):
        raise ValueError("landmark-scroll requires 6–10 distinct verified landmarks")
    if anchor_id is None:
        anchor_id = ids[len(ids) // 2]
    if anchor_id not in ids:
        raise ValueError("anchor must match a landmark ID")
    # The Agent's landmark order is the selected narrative order; reserve one
    # visible central focus without hiding the other landmarks in landscaping.
    ordered = [x for x in ids if x != anchor_id]
    ordered.insert(len(ids)//2, anchor_id)
    n = len(ordered)
    base_width = min(.27, max(.18, 1.60 / n))
    width_pattern = [.96, 1.13, .84, 1.10, .92, 1.17, .88, 1.06, .95, 1.12]
    upper = {
        "tote-bag": .12,
        "anniversary-poster": .19,
        "ppt-cover": .46,
        "city-poster": .18,
    }[usage]
    ground = .94 if usage != "ppt-cover" else .965
    raised = [0, .085, .035, .115, .015, .075, .045, .10, 0, .055]
    placements = []
    for i, bid in enumerate(ordered):
        width = min(.33, max(.155, base_width * width_pattern[i] *
                            (1.12 if bid == anchor_id else 1)))
        target_center = base_width / 2 + (1 - base_width) * i / (n - 1)
        center_x = min(1-width/2, max(width/2, target_center))
        # Different visual heights, but all buildings take substantial space;
        # avoid equally sized stickers and avoid tiny background cameos.
        if bid == anchor_id:
            top = upper + .035
        else:
            top = upper + .11 + raised[i]
        bottom = .98 - (.025 if i % 3 == 1 else 0)
        placements.append({
            "landmark_id": bid,
            "image": f"{cutouts}/{bid}.png",
            "role": "anchor" if bid == anchor_id else "support",
            "rect": [round(center_x - width / 2, 4), round(top, 4),
                     round(center_x + width / 2, 4), round(bottom, 4)],
            "depth": 20 if bid == anchor_id else 2 + (i % 4),
            "opacity": 1.0,
        })
    return {
        "schema_version": 1,
        "mode": "commemorative-montage",
        "archetype": "landmark-scroll",
        "usage": usage,
        "canvas": [1672, 941],
        "upper_blank_fraction": upper,
        "ground_y": ground,
        "anchor_landmark_id": anchor_id,
        "integrated_redraw_required": True,
        # Decor may CONNECT architecture, not fill blank space with scenery.
        "connectors": ["architectural-baseline"],
        "max_ornament_area_fraction": 0.05,
        "placements": placements,
        "disclosure": "Continuous artistic scroll of grounded landmarks, not their real geographic adjacency.",
    }


def validate_plan(plan: dict, root: Path, require_images: bool = True) -> dict[str, Path]:
    if plan.get("schema_version") != 1 or plan.get("mode") not in MODES:
        raise ValueError("expected commemorative-montage schema_version=1")
    if plan.get("usage") not in USAGES:
        raise ValueError("unsupported usage")
    canvas = plan.get("canvas", [])
    if not (isinstance(canvas, list) and len(canvas) == 2 and
            all(type(n) is int and 400 <= n <= 7680 for n in canvas) and
            abs(canvas[0] / canvas[1] - 16 / 9) < 0.04):
        raise ValueError("draft canvas must be a 16:9 image with integer dimensions")
    top = plan.get("upper_blank_fraction")
    if not isinstance(top, (int, float)) or not .1 <= top <= .7:
        raise ValueError("invalid negative-space fraction")
    ground = plan.get("ground_y")
    if not isinstance(ground, (int, float)) or not top + .2 < ground < 1:
        raise ValueError("invalid shared ground line position")
    if plan.get("integrated_redraw_required") is not True:
        raise ValueError("this is a generation DRAFT; integrated redraw cannot be skipped")
    archetype = plan.get("archetype", "hero-montage")
    if archetype not in ARCHETYPES:
        raise ValueError("unsupported composition archetype")
    placements = plan.get("placements")
    minimum, maximum = (6, 10) if archetype == "landmark-scroll" else (2, 5)
    if not isinstance(placements, list) or not minimum <= len(placements) <= maximum:
        raise ValueError(f"{archetype} requires {minimum}–{maximum} placed landmarks")
    if archetype == "landmark-scroll":
        fraction = plan.get("max_ornament_area_fraction")
        if not isinstance(fraction,(int,float)) or not 0 <= fraction <= .08:
            raise ValueError("landmark-scroll requires ornament budget <= 8%")
        if plan.get("connectors") != ["architectural-baseline"]:
            raise ValueError("scroll must not default to trees, shrubs, lakes or decorative waves")
    ids, paths, anchors = set(), {}, []
    for p in placements:
        if not isinstance(p, dict):
            raise ValueError("placement must be an object")
        bid = p.get("landmark_id", "")
        if not isinstance(bid, str) or not bid or bid in ids:
            raise ValueError("empty or repeated landmark_id")
        ids.add(bid)
        if p.get("role") == "anchor":
            anchors.append(bid)
        elif p.get("role") != "support":
            raise ValueError("role must be anchor/support")
        rect = p.get("rect")
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in rect) or
                not (0 <= rect[0] < rect[2] <= 1 and top <= rect[1] < rect[3] <= 1)):
            raise ValueError(f"{bid}: invalid rect or overlap with reserved negative space")
        if not isinstance(p.get("depth"), int) or not 0 <= p["depth"] <= 100:
            raise ValueError(f"{bid}: invalid depth")
        if not isinstance(p.get("opacity"), (int, float)) or not .4 <= p["opacity"] <= 1:
            raise ValueError(f"{bid}: invalid opacity")
        f = safe_file(root, p.get("image", ""))
        if require_images and not f.is_file():
            raise ValueError(f"{bid}: cutout not found: {f}")
        paths[bid] = f
    if anchors != [plan.get("anchor_landmark_id")]:
        raise ValueError("exactly one correct anchor is required")
    # Intentionally integrated: at least one support overlaps the anchor's box.
    anchor = next(p for p in placements if p["role"] == "anchor")["rect"]
    overlaps = sum(max(0, min(anchor[2], p["rect"][2]) - max(anchor[0], p["rect"][0])) *
                   max(0, min(anchor[3], p["rect"][3]) - max(anchor[1], p["rect"][1])) > 0
                   for p in placements if p["role"] == "support")
    if not overlaps:
        raise ValueError("gallery-like disjoint boxes are invalid in commemorative mode")
    if archetype == "landmark-scroll":
        boxes = [p["rect"] for p in placements]
        if min(r[0] for r in boxes) > .04 or max(r[2] for r in boxes) < .96:
            raise ValueError("scroll must occupy the width rather than cluster at one side")
        centers = [(.5 * (r[0]+r[2])) for r in boxes]
        if any(not any(a <= x < b for x in centers) for a,b in
               ((0,1/3),(1/3,2/3),(2/3,1.00001))):
            raise ValueError("scroll needs landmarks across left, middle and right")
    return paths




def prepared_cutout(path: Path, max_width: int, max_height: int, strength: float) -> Image.Image:
    with Image.open(path) as im:
        if im.mode != "RGBA":
            raise ValueError(f"requires true RGBA transparent building cutout: {path}")
        art = im.copy()
    alpha = art.getchannel("A")
    corners = [alpha.getpixel(pt) for pt in (
        (0, 0), (art.width - 1, 0), (0, art.height - 1), (art.width - 1, art.height - 1))]
    if max(corners) > 16:
        raise ValueError(f"black/opaque background is not a cutout: {path}")
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError(f"empty building cutout: {path}")
    art = art.crop(bbox)
    art.thumbnail((max_width, max_height), RESAMPLING)
    if strength != 1:
        alpha = art.getchannel("A").point(lambda x: round(x * strength))
        art.putalpha(alpha)
    return art




def draw_ornaments(board: Image.Image, ground: float, archetype: str = "hero-montage") -> None:
    """A scroll gets only an extremely restrained baseline: architecture is subject."""
    w, h = board.size
    d = ImageDraw.Draw(board, "RGBA")
    if archetype == "landmark-scroll":
        yy = min(h-7, round(h * ground))
        d.line([(round(.025*w), yy), (round(.975*w), yy)],
               fill=(175, 188, 198, 42), width=1)
        return
    for layer in range(4):
        y = h * (ground + layer * .017)
        pts = [(round(w * (.035 + .93 * i / 180)),
                round(y + h * .009 * math.sin(i * .11 + layer * .7)))
               for i in range(181)]
        d.line(pts, fill=(200, 208, 218, max(30, 108 - 20 * layer)), width=2)
    for x in (.08, .90):
        for k in range(4):
            r = round(w * (.035 + k * .009))
            cy = round(h * (ground - .012 - k * .008))
            d.arc((round(w*x)-r, cy-r//2, round(w*x)+r, cy+r//2),
                  start=195, end=345, fill=(190, 199, 211, 75), width=1)




def draft_brief(plan: dict, hashes: dict[str, str]) -> str:
    placements = plan["placements"]
    scroll = plan.get("archetype") == "landmark-scroll"
    lines = [
        "# Integrated image-redraw contract: commemorative montage",
        "",
        "THIS DRAFT IS NOT THE FINAL ARTWORK. Call a real image editing/generation model with actual image pixels.",
        "Attach draft-layout.png (composition), every independent landmark cutout (geometry),",
        "the verified photographic source views for each landmark (identity), and the style reference (style only).",
        "If image-input capacity is insufficient, work in smaller grounded groups or stop; NEVER silently omit sources.",
        "",
        f"Output use: {plan['usage']}; output aspect ratio: 16:9.",
        f"Anchor: {plan['anchor_landmark_id']}. Supporting buildings must be visually subordinate.",
        "Transform the disjoint silhouette edges into ONE harmonious anniversary/merchandise illustration.",
        "Preserve central hierarchy and purposeful overlapping. Integrate coherent ground, foliage/ornamental",
        "lines, flowing curves and negative space. Connector motifs are decorative and do NOT assert real geography.",
        "Uniform line density, perspective language, shading, and visual rhythm across all buildings.",
        "The architecture must be the principal visual subject; foliage and water are NOT default connectors.",
        "Do not render each building as a sticker, tile, isolated card or equally spaced gallery.",
        "Do not invent towers, wings, arches, clock faces, windows, signs or official lettering.",
        "Keep distinguishing silhouettes and verified visible architectural features from source photos.",
        "Allow partial occlusion and artistic scale only while each landmark remains identifiable.",
        "If a real geometry conflict cannot be resolved, revise layout or report the problem: never guess.",
        "",
        "After redraw: compare the ACTUAL FINAL integrated image against all original photos,",
        "not just the independent cutouts. Review both architecture and composition in two passes.",
        "Do not vectorize without an approval bound to the final redraw PNG hash.",
        "",
        "## Landmark order and locked source cutouts",
    ]
    if scroll:
        lines.extend(["", "## REQUIRED LANDMARK SCROLL ART DIRECTION",
            f"Render ALL {len(placements)} named buildings as a densely populated, continuous architectural landmark scroll.",
            "This is a school/city ARCHITECTURE IDENTIFICATION PANORAMA, not a scenic campus landscape.",
            "Architectural landmarks must dominate (>85% of visual ink/attention); ornament budget <=5%.",
            "NO default trees, shrub borders, forest, lake, water reflections, hillside or ornamental clouds.",
            "Do not create a landscaped foreground. Use only a very faint shared architectural baseline if useful.",
            "Keep multiple recognizable building silhouettes visible across left, middle and right thirds.",
            "Vary roof heights, facade density and scale with a controlled rhythm; avoid three giant landmarks.",
            "Buildings may interleave slightly but do NOT erase signature gates, domes, roofs or tower silhouettes.",
            "One connected architectural scroll is required. Avoid vertical gaps, floating cutouts, emoji/logo icons and tiles.",
            "When reference permits, alternate historic and contemporary identity landmarks; no invented structures.",
            "Do not assume a physical continuous site or fake road/water around landmarks.",
            ""])
    for p in sorted(placements, key=lambda p: p["depth"]):
        lines.append(f"- {p['landmark_id']}: {p['role']}; cutout={p['image']}; SHA256={hashes[p['landmark_id']]}; rect={p['rect']}")
    return "\n".join(lines) + "\n"




def render(plan_file: Path, out_dir: Path) -> dict:
    plan = load_json(plan_file)
    paths = validate_plan(plan, plan_file.resolve().parent)
    w, h = plan["canvas"]
    board = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw_ornaments(board, plan["ground_y"], plan.get("archetype", "hero-montage"))
    guides = board.copy()
    gd = ImageDraw.Draw(guides, "RGBA")
    hashes = {}
    for p in sorted(plan["placements"], key=lambda x: x["depth"]):
        bid = p["landmark_id"]
        path = paths[bid]
        hashes[bid] = digest(path)
        x0, y0, x1, y1 = p["rect"]
        box_w, box_h = round((x1 - x0) * w), round((y1 - y0) * h)
        art = prepared_cutout(path, box_w, box_h, p["opacity"])
        px = round(x0 * w + (box_w - art.width) / 2)
        py = round(y1 * h - art.height)
        if py < round(plan["upper_blank_fraction"] * h):
            raise ValueError(f"{bid}: cutout invades protected headline area")
        board.alpha_composite(art, (px, py))
        guides.alpha_composite(art, (px, py))
        border = tuple(round(v * dim) for v, dim in zip(p["rect"], (w, h, w, h)))
        color = (255, 171, 74, 195) if p["role"] == "anchor" else (91, 197, 250, 165)
        gd.rectangle(border, outline=color, width=3)
        gd.text((border[0]+6, border[1]+7), f"{bid} · {p['role']}", fill=color)
    out_dir.mkdir(parents=True, exist_ok=True)
    picture = out_dir / "draft-layout.png"
    guide = out_dir / "draft-guides.png"
    board.convert("RGB").save(picture)
    guides.convert("RGB").save(guide)
    (out_dir/"integrated-generation-brief.md").write_text(draft_brief(plan, hashes), encoding="utf-8")
    evidence = {"mode": "draft-only", "plan_sha256": digest(plan_file),
                "draft_sha256": digest(picture), "cutout_sha256": hashes}
    save_json(out_dir / "draft-evidence.json", evidence)
    return evidence




def cli() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="action", required=True)
    s = sub.add_parser("plan", help="create intentional overlapping visual hierarchy from building manifest")
    s.add_argument("--manifest", required=True, type=Path)
    s.add_argument("--usage", required=True, choices=USAGES)
    s.add_argument("--anchor-id", help="optional for landmark-scroll; defaults to central slot")
    s.add_argument("--archetype", choices=ARCHETYPES, default="hero-montage")
    s.add_argument("--cutouts", default="cutouts", help="path relative to plan directory")
    s.add_argument("--output", required=True, type=Path)
    r = sub.add_parser("draft", help="create composition guides for a reference-conditioned image edit")
    r.add_argument("--plan", required=True, type=Path)
    r.add_argument("--output-dir", required=True, type=Path)
    a = ap.parse_args()
    try:
        if a.action == "plan":
            manifest = load_json(a.manifest)
            if a.archetype == "landmark-scroll":
                plan = make_scroll_plan(manifest, a.usage, a.anchor_id, a.cutouts)
            else:
                if not a.anchor_id:
                    raise ValueError("hero-montage requires --anchor-id")
                plan = make_plan(manifest, a.usage, a.anchor_id, a.cutouts)
            save_json(a.output, plan)
            print(f"Created intentional montage plan: {a.output}")
        else:
            render(a.plan, a.output_dir)
            print(f"Created DRAFT only; use actual image editing for integrated redraw: {a.output_dir}")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        ap.error(str(exc))




if __name__ == "__main__":
    cli()


