#!/usr/bin/env python3
"""Audit the FINAL integrated commemorative artwork, not just building cutouts.


Requires grounded source photos, a compositional draft, a genuine image-edit call
and two vision reviews of EACH landmark plus the whole visual composition.
Agent pass is NOT expert architecture certification. Fail closed on uncertainty.
"""
from __future__ import annotations


import argparse
import hashlib
import json
from pathlib import Path


import agent_audit as vision
import compose_v2 as montage
import reference_pipeline as sources
import scroll_atlas


MONTAGE_FEATURES = (
    ("integrated_composition", "All landmarks form ONE illustration, not isolated cutout tiles, separated stickers, or equal-spaced gallery."),
    ("visual_hierarchy", "The declared anchor clearly dominates while supporting landmarks remain recognizable."),
    ("shared_connectors", "Subjects connect through architectural rooflines, facade edges, deliberate overlap and at most one faint architectural baseline; foliage, water, waves and scenery do not count as valid connectors."),
    ("consistent_style", "Building strokes, ink weight, density, texture, lighting and perspective style are coherent."),
    ("print_readability", "Unified legible silhouette suitable for the designated commemorative merchandise."),
)
SCROLL_FEATURES = (
    ("landmark_inventory", "All named buildings are independently recognizable, not replaced by trees or invented structures."),
    ("architecture_priority", "Architecture occupies nearly all meaningful visual attention; trees, canopies, shrubs, flowerbeds, lawns, water, reflections, clouds, birds and decorative waves are absent, not merely small or subordinate."),
    ("continuous_landmark_rhythm", "Every planned landmark forms one dense-but-readable architectural band across left, middle and right, with varied roof heights, intentional partial overlaps, no equal-spaced sticker rhythm and no large empty gaps."),
)




def source_photo_ids(manifest: dict) -> set[str]:
    return {f"PHOTO:{b['id']}:{b['primary_view_id']}" for b in manifest["landmarks"]}




def validate_generation(
    *, manifest: dict, plan: dict, plan_path: Path, evidence: dict, draft: Path,
    final: Path, log: dict, cutouts: dict[str, Path],
    log_root: Path | None = None, source_root: Path | None = None
) -> list[str]:
    problems = []
    source_expected = {"CUTOUT:"+bid:montage.digest(path) for bid,path in cutouts.items()}
    if source_root is not None:
        for b in manifest["landmarks"]:
            photo=next((p for p in b["photos"] if p["id"]==b["primary_view_id"]),None)
            if photo is not None:
                source_expected[f"PHOTO:{b['id']}:{photo['id']}"] = montage.digest(
                    sources.safe_path(source_root,photo["file"]))
    if plan.get("archetype") == "landmark-scroll":
        if log.get("input_mode") != "reference-atlas-v1":
            problems.append("landmark-scroll requires atlases of ALL source cutouts and primary real photos")
        entries=log.get("atlas_entries")
        if not isinstance(entries,list) or not entries:
            problems.append("missing source-verified reference atlas entries")
            entries=[]
        declared_ids=set();source_ids=set()
        for entry in entries:
            if not isinstance(entry,dict):
                problems.append("malformed atlas entry");continue
            aid=entry.get("id","")
            if not (isinstance(aid,str) and (aid.startswith("CUTOUT_ATLAS:") or aid.startswith("PHOTO_ATLAS:")) and aid not in declared_ids):
                problems.append("invalid or duplicated reference atlas ID")
            declared_ids.add(aid)
            members=entry.get("members")
            if not isinstance(members,list) or not 1<=len(members)<=scroll_atlas.PER_PAGE:
                problems.append(f"{aid}: missing or excessive atlas members")
                continue
            for member in members:
                if not isinstance(member,dict):
                    problems.append(f"{aid}: malformed source member");continue
                sid=member.get("image_id","")
                if sid in source_ids or sid not in source_expected:
                    problems.append(f"{aid}: duplicate/unexpected original source {sid}")
                source_ids.add(sid)
                if member.get("source_sha256")!=source_expected.get(sid):
                    problems.append(f"{aid}: source photo/cutout SHA changed for {sid}")
                if aid.startswith("CUTOUT_ATLAS") != sid.startswith("CUTOUT:"):
                    problems.append(f"{aid}: cutout/photo atlas source category mixed")
            if log_root is None:
                problems.append("atlas root location unavailable for evidence recheck")
            else:
                root=(log_root/"reference-atlases").resolve()
                f=entry.get("file","")
                file=(root/f).resolve() if isinstance(f,str) else root
                if not isinstance(f,str) or not f or '/' in f or '\\' in f or file.parent!=root or not file.is_file():
                    problems.append(f"{aid}: missing or unsafe source atlas image")
                elif entry.get("sha256")!=montage.digest(file) or log.get("reference_image_sha256",{}).get(aid)!=montage.digest(file):
                    problems.append(f"{aid}: source atlas was modified or not attached")
        if source_ids != set(source_expected):
            problems.append("reference atlases omit one or more real building cutouts/photographs")
        expected={"DRAFT","STYLE"}|declared_ids
    else:
        expected = {"DRAFT", "STYLE"} | {f"CUTOUT:{x}" for x in cutouts} | source_photo_ids(manifest)
    supplied = set(log.get("reference_ids_attached") or [])
    if not isinstance(log.get("tool"), str) or not log.get("tool") or not log.get("call_id"):
        problems.append("missing real integrated image-edit tool name and call ID")
    if log.get("image_input_confirmed") is not True or expected - supplied:
        problems.append(f"integrated editor did not confirm actual images: {sorted(expected - supplied)}")
    hashes = {
        "plan_sha256": montage.digest(plan_path),
        "draft_sha256": montage.digest(draft),
        "output_sha256": montage.digest(final),
    }
    for key, value in hashes.items():
        if log.get(key) != value:
            problems.append(f"stale or absent integrated generation log: {key}")
    if hashes["draft_sha256"] == hashes["output_sha256"]:
        problems.append("draft was submitted as final without actual integrated redraw")
    if evidence.get("plan_sha256") != hashes["plan_sha256"]:
        problems.append("draft evidence does not match montage plan")
    if evidence.get("draft_sha256") != hashes["draft_sha256"]:
        problems.append("draft image was changed after initial composition")
    locked_cutouts = evidence.get("cutout_sha256", {})
    reported_cutouts = log.get("cutout_sha256", {})
    for bid, p in cutouts.items():
        sha = montage.digest(p)
        if locked_cutouts.get(bid) != sha or reported_cutouts.get(bid) != sha:
            problems.append(f"{bid}: cutout changed after draft or was omitted from generation log")
    if {p["landmark_id"] for p in plan["placements"]} != {b["id"] for b in manifest["landmarks"]}:
        problems.append("montage plan does not cover the same landmarks as the source-photo manifest")
    return problems




def pseudo_building(plan: dict) -> dict:
    return {
        "id": "MONTAGE",
        "name": "Final commemorative composition",
        "location": "Illustrative montage, not a physical camera view",
        "primary_view_id": "draft",
        "photos": [{"id": "draft"}, {"id": "style"}],
        "must_match": [
            {"id": fid, "description": desc, "photo_ids": ["draft", "style"]}
            for fid, desc in (MONTAGE_FEATURES + (SCROLL_FEATURES if plan.get("archetype") == "landmark-scroll" else ()))
        ],
        "forbidden_inventions": ["invented scenery advertised as physical site", "model-created official text"],
        "unknowns": ["actual relative geographic positions intentionally unspecified"],
    }




def montage_prompt(plan: dict, stage: str) -> str:
    focus = ("First pass: methodically verify hierarchy, cohesion and print-readability."
             if stage == "feature" else
             "Second pass: find evidence that this is a gallery of isolated cutouts, not a coherent commemorative illustration. Be skeptical.")
    return (
        "Final image is a purported commemorative montage. Compare CANDIDATE:MONTAGE against "
        "MONTAGE:draft (layout draft) and MONTAGE:style (style reference). "
        "Draft is ONLY a guide; final must be an integrated image redraw, not merely a screenshot of a layout. "
        "Buildings are intentionally relocated artistically; no claim of a real geographic single viewpoint. "
        f"Usage={plan['usage']}; required anchor={plan['anchor_landmark_id']}; {focus}\n"
        "Evaluate all required features as separate reports: "
        + ", ".join(
            f"{key}: {desc}" for key, desc in (
                tuple((k, d) for k, d in MONTAGE_FEATURES if k != "shared_connectors")
                + (("shared_connectors", "For a landmark-scroll, only architectural rooflines, facade edges, deliberate overlap and at most one faint architectural baseline count as connectors; foliage, water, waves and scenery are failures.")
                   if plan.get("archetype") == "landmark-scroll" else
                   (("shared_connectors", dict(MONTAGE_FEATURES)["shared_connectors"]),))
                + (SCROLL_FEATURES if plan.get("archetype") == "landmark-scroll" else ())
            )
        )
        + ". And the four safety checks no_extra_geometry, no_invented_text, "
        "viewpoint_consistent, no_unobserved_facades. "
        "For positive assessments cite photo_ids ['draft'] or ['style'] exactly; "
        "these are only design references, not proof of building identity. "
        "Explicitly FAIL integrated_composition when buildings sit isolated at equal intervals, "
        "with white/black gaps and no blending, regardless of how individually accurate they appear. "
        "Do not pass a layout mockup as a finished commemorative artwork. "
        "Return exactly the structured JSON schema with specific visual observations and confidence. "
        "Unknown is mandatory when image detail is too small for a reliable judgment. "
        "Candidate_has_legible_text must be true for any model-generated readable lettering. "
        + (f"LANDMARK-SCROLL RULE: all {len(plan['placements'])} cited buildings must be recognizable. "
           "FAIL if only three large buildings and numerous shrubs/trees dominate. "
           "FAIL when trees, vegetation, fake lake, waves or other scenery consume substantial visual ink. "
           "FAIL if silhouettes don't create a continuous architectural scroll across left/middle/right thirds. "
           "Trees, foliage, shrubs, lawns, water, reflections, clouds, birds and decorative waves are hard failures even if they look attractive; the style reference never authorizes copying scenery. "
           if plan.get("archetype")=="landmark-scroll" else "")
    )




def landmark_prompt(b: dict, stage: str) -> str:
    return (
        "The CANDIDATE is the FINAL INTEGRATED montage, not an individual cutout. "
        f"Identify {b['name']} using the original photograph(s) and the CUTOUT:"
        f"{b['id']} artwork. Primary reference viewpoint {b['primary_view_id']}. "
        "Artistic partial occlusion is permitted only if building identity and all visible "
        "required evidence-backed features remain verifiable. "
        "If the building cannot be located unambiguously or distinguishing details are "
        "masked by other buildings, respond unknown or fail, never infer hidden features. "
        "Identify added towers, doors, clocks, roof geometry and lettering. "
        + vision.build_prompt(b, stage)
    )




def check_reviews(
    *, manifest: dict, plan: dict, draft: Path, final: Path, cutouts: dict[str, Path],
    source_root: Path, model: str, backend, min_confidence: float, max_image_side: int
) -> tuple[list[dict], list[str]]:
    findings, problems = [], []
    for b in manifest["landmarks"] + [pseudo_building(plan)]:
        bid = b["id"]
        if bid == "MONTAGE":
            pics = [
                ("CANDIDATE:MONTAGE", final, True),
                ("MONTAGE:draft", draft, True),
                ("MONTAGE:style", sources.safe_path(source_root, manifest["style_reference"]), True),
            ]
            names = {"MONTAGE:draft", "MONTAGE:style"}
        else:
            pics = [("CANDIDATE:" + bid, final, True)]
            pics.extend(
                (bid + ":" + p["id"], sources.safe_path(source_root, p["file"]), False)
                for p in b["photos"]
            )
            pics.append(("CUTOUT:" + bid, cutouts[bid], True))
            names = set()
        row = {"landmark_id": bid, "candidate_sha256": montage.digest(final), "passes": []}
        for stage in ("feature", "adversarial"):
            prompt = montage_prompt(plan, stage) if bid == "MONTAGE" else landmark_prompt(b, stage)
            result, call = backend(model=model, prompt=prompt, pictures=pics, max_side=max_image_side)
            errs = vision.evaluate_verdict(result, b, minimum_confidence=min_confidence)
            if not isinstance(call, dict) or not call.get("response_id") or not call.get("model"):
                errs.append(f"{bid}:{stage}: missing true reviewer call identity")
            elif set(call.get("image_ids", [])) != {x[0] for x in pics}:
                errs.append(f"{bid}:{stage}: input-image IDs don't match images reviewed")
            if bid == "MONTAGE" and names:
                # The draft/style are explicitly the design references; reviewer sees both.
                if not names.issubset(set(call.get("image_ids", []))):
                    errs.append("whole-image montage review omitted design references")
            row["passes"].append({"stage": stage, "output": result, "call": call, "problems": errs})
            problems.extend(errs)
        findings.append(row)
    return findings, problems




def retry_text(findings: list[dict]) -> str:
    lines = ["# Integrated artwork repair requests", "",
             "Use actual source photos and original cutouts for repairs.",
             "Do not approve or vectorize the same image after a failing review.", ""]
    for item in findings:
        errors = []
        for record in item["passes"]:
            for kind in ("features", "checks"):
                for check in record["output"].get(kind, []):
                    if check.get("status") != "pass" or check.get("confidence", 0) < .9:
                        errors.append(f"- {check.get('id')}: {check.get('difference') or check.get('observation')}")
            errors.extend(f"- {p}" for p in record["problems"])
        if errors:
            lines.append("## " + item["landmark_id"])
            lines.extend(dict.fromkeys(errors))
            lines.append("")
    if len(lines) == 4:
        lines.append("Review rejected due to provenance or global constraints; inspect JSON report.")
    return "\n".join(lines) + "\n"




def run(
    *, manifest_file: Path, lock_file: Path, plan_file: Path, draft: Path,
    evidence_file: Path, final: Path, generation_log_file: Path,
    output_dir: Path, backend, model: str, min_confidence: float = .90,
    max_image_side: int = 1792
) -> dict:
    if not .8 <= min_confidence <= .99:
        raise ValueError("minimum confidence must be between .8 and .99")
    manifest_file = manifest_file.resolve()
    manifest = sources.read_json(manifest_file)
    lock = sources.read_json(lock_file)
    problems = sources.verify_lock(manifest_file, lock)
    if problems:
        raise ValueError("source photo evidence invalid: " + "; ".join(problems))
    plan = montage.load_json(plan_file)
    paths = montage.validate_plan(plan, plan_file.resolve().parent)
    if problems:
        raise ValueError("; ".join(problems))
    for img in (draft, final):
        sources.load_photo(img)
    evidence = montage.load_json(evidence_file)
    log = montage.load_json(generation_log_file)
    issues = validate_generation(
        manifest=manifest, plan=plan, plan_path=plan_file,
        evidence=evidence, draft=draft, final=final, log=log, cutouts=paths,
        log_root=generation_log_file.parent,source_root=manifest_file.parent)
    if issues:
        raise ValueError("integrated image evidence invalid: " + "; ".join(issues))
    before = {str(p): montage.digest(p) for p in (
        manifest_file, lock_file, plan_file, draft, final, evidence_file,
        generation_log_file, *paths.values())}
    findings, problems = check_reviews(
        manifest=manifest, plan=plan, draft=draft, final=final,
        cutouts=paths, source_root=manifest_file.parent,
        model=model, backend=backend, min_confidence=min_confidence,
        max_image_side=max_image_side)
    problems.extend(sources.verify_lock(manifest_file, lock))
    for name, old in before.items():
        if montage.digest(Path(name)) != old:
            problems.append(f"file was modified during visual audit: {name}")
    report = {
        "schema_version": 1,
        "assurance": "Agent two-pass photo+composition review; NOT architectural or print certification",
        "review_mode": "agent_integrated_montage",
        "image_sha256": montage.digest(final),
        "evidence_sha256": lock["evidence_sha256"],
        "plan_sha256": montage.digest(plan_file),
        "generation_log_sha256": montage.digest(generation_log_file),
        "minimum_confidence": min_confidence,
        "landmarks_and_composition": findings,
        "problems": sorted(set(problems)),
        "decision": "agent_pass" if not problems else "needs_review",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir/"montage-review.json"
    sources.write_json(report_path, report)
    approval = {
        "status": "approved" if not problems else "blocked",
        "review_mode": "agent_integrated_montage",
        "assurance": report["assurance"],
        "reviewer": "agent_integrated_montage:" + model,
        "image_sha256": report["image_sha256"],
        "evidence_sha256": report["evidence_sha256"],
        "review_sha256": montage.digest(report_path),
        "manifest_sha256": montage.digest(manifest_file),
        "plan_sha256": report["plan_sha256"],
        "problems": report["problems"],
    }
    sources.write_json(output_dir/"approval.json", approval)
    if problems:
        (output_dir/"retry-brief.md").write_text(retry_text(findings), encoding="utf-8")
    return report




def cli() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--evidence-lock", required=True, type=Path)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--draft", required=True, type=Path)
    ap.add_argument("--draft-evidence", required=True, type=Path)
    ap.add_argument("--final", required=True, type=Path)
    ap.add_argument("--generation-log", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--provider", choices=("openai", "agent-json"), default="openai")
    ap.add_argument("--verdict-dir", type=Path)
    ap.add_argument("--model", default="gpt-4.1")
    ap.add_argument("--min-confidence", type=float, default=.9)
    a = ap.parse_args()
    if a.provider == "agent-json" and not a.verdict_dir:
        ap.error("--verdict-dir is needed for agent-json")
    reviewer = vision.openai_review if a.provider == "openai" else vision.local_agent_backend(a.verdict_dir)
    try:
        result = run(
            manifest_file=a.manifest, lock_file=a.evidence_lock, plan_file=a.plan,
            draft=a.draft, evidence_file=a.draft_evidence, final=a.final,
            generation_log_file=a.generation_log, output_dir=a.output_dir,
            backend=reviewer, model=a.model, min_confidence=a.min_confidence)
        print(f"{result['decision']}: {a.output_dir/'montage-review.json'}")
        if result["decision"] != "agent_pass":
            raise SystemExit(3)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        ap.error(str(exc))




if __name__ == "__main__":
    cli()


