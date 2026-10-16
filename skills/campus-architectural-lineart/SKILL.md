---
name: campus-architectural-lineart
description: Create photo-grounded architectural line art through evidence-backed web/photo retrieval, per-building reference-image generation, conservative Agent visual audit, targeted retries, compositing and transparent SVG export. Use when a real campus or named building must not be invented or structurally misrepresented.
license: MIT
metadata:
  version: "1.1"
---

# Campus architectural line art — **Agent-first evidence + vision review**

**Produce attractive drawings without treating AI's visual plausibility as architectural fact.** This skill orchestrates tools; its Python scripts do not include an image-generation model. The Agent must use an available reference-image generation/edit tool with actual image attachments; if unavailable, stop with an evidence packet.

## One-time workflow (with limited human intervention)

1. **Ground identity and rights**. Parse user style/reference. Search official source pages and photo repositories for each exact building. Open original photo pages, check names, known roofs/arches/entrances, locate two genuinely different viewpoints, note photographer and permission to produce derivatives. Prefer high-resolution originals to search thumbnails; don't copy unlicensed images to public GitHub. Read [photo sourcing](references/photo-sourcing.md). Agent may create *agent-attested* source records for publicly licensed images, with source/rights evidence URLs and model-call IDs; do **not** claim a human reviewed anything unless a person did. User-owned or ambiguous-license photos must be authorized by their owner. Photo/feature fields have a [schema](references/evidence-schema.md).
2. **Lock photo and shape evidence.** Run `scripts/reference_pipeline.py template` for a starter manifest; replace all placeholders with actually observed information. Record per-building `primary_view_id`, `must_match` features with photo IDs and optional per-view bboxes, forbidden inventions and unknown/unseen features. Record image-input model/call IDs for any agent-provenanced checks. Then run `scripts/reference_pipeline.py prepare`. Any rejection means return to sourcing; no synthetic attestation fields just to pass.
3. **Reference-conditioned visual generation.** For each building, **actually attach** its own original-photo pixels and style-only reference plus available feature crops to an image-capable generator. Pass [prompt contract](references/prompt-recipe.md) + `generation-brief.md`. Never pass filenames or a purely text description in lieu of photos. Preserve one camera anchor, do not mix multiple views into a fabricated facade; use a clean transparent cutout with **no generated official text**. Record the real model invocation and output SHA256 in `generation-log.json` per building. See [Agent audit protocol](references/agent-audit.md).
4. **Optional multi-building composition.** After per-building first visual checks, arrange approved cutouts using `scripts/compose.py` and an explicit [layout](references/compositing.md). This is alpha compositing only; it never adds invented towers or new facades. If buildings are on different campuses, label artwork as an *illustrative montage*, not a factual site photograph.
5. **Agent automatically reviews using actual image inputs**. Run `scripts/agent_audit.py` either with an `OPENAI_API_KEY` (two structured vision calls per building through Responses API), or with `--provider agent-json` where a vision-enabled Agent separately inspects the candidate and original photos twice, saving both structured reports. Inspect each `must_match`, unsupported geometry, model-created text and viewpoint consistency. If any score is under 0.90, mismatch, missing photo ID or conflicting assessment, return `needs_review` rather than manufacturing a pass. Agent output is explicitly machine-assessed, not human-certified.
6. **Targeted repair and escalation.** Read `retry-brief.md` and correct **only the building** with mismatches using cited original/cropped photos. Update `generation-log.json` and rerun both audits. Maximum 2 image-edit/audit retries per problematic building before escalating precise unresolved points to a human. `photo-faithful` mode normally requires a human review (optional `--permit-photo-faithful-auto` opts into lower assurance). Official logos/inscriptions and legal rights are always separately sourced/licensed.
7. **Deliver only supported output.** If `agent-review.json` says `agent_pass` and `approval.json` says `approved`, pass `--approval` to `raster-to-layered-svg/scripts/convert.py`, then build the offline HTML editor. Preserve final evidence/agent reports, visual inputs and hash provenance. If blocked, deliver the reference packet and outstanding questions rather than calling unreviewed art accurate.

## Commands

```bash
python skills/campus-architectural-lineart/scripts/reference_pipeline.py template --output workspace/project.json
python skills/campus-architectural-lineart/scripts/reference_pipeline.py prepare \
  --manifest workspace/project.json --out-dir workspace/grounding

# Agent actually calls image-generation tool using source photo pixels,
# saves workspace/artwork/final.png & actual workspace/artwork/generation-log.json.
# For multi-building art also save workspace/artwork/cutouts/<building-id>.png.

python skills/campus-architectural-lineart/scripts/agent_audit.py \
  --provider openai --model gpt-4.1 \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --generation-log workspace/artwork/generation-log.json \
  --image workspace/artwork/final.png \
  --feature-crops-dir workspace/grounding/feature-crops \
  --output-dir workspace/artwork/agent-audit

python skills/raster-to-layered-svg/scripts/convert.py \
  --input workspace/artwork/final.png \
  --approval workspace/artwork/agent-audit/approval.json \
  --out-dir workspace/dist --size 3840x2160
```

Provide `--cutouts-dir workspace/artwork/cutouts` to `agent_audit.py` if >1 landmark. See [complete automatic and native Agent review commands](references/agent-audit.md) and [source checking guide](references/reference-checklist.md).

## Truthfulness / assurance boundary

Source-page, copyright and geometric identity cannot be cryptographically proven by prompt text, a hash or a model confidence score. An agent-generated verification declaration is **not a human review**. Two VLM passes can make correlated errors. Built-in checks enforce *evidence presence, consistency and fail-closed workflow*, not a guarantee that the artwork depicts real architecture exactly. The existing Zhejiang University example predates this protocol and remains an **unverified artistic montage**; do not create fake approvals for it.
