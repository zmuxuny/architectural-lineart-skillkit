---
name: campus-architectural-lineart
description: Create photo-grounded architectural line art through evidence-backed web/photo retrieval, per-building reference-image generation, conservative Agent visual audit, targeted retries, compositing and transparent SVG export. Use when a real campus or named building must not be invented or structurally misrepresented.
license: MIT
metadata:
  version: "1.1"
---


# Campus architectural line art — **Agent-first evidence + vision review**


**Produce attractive drawings without treating AI's visual plausibility as architectural fact.** This skill orchestrates tools; its Python scripts do not include an image-generation model. The Agent must use an available reference-image generation/edit tool with actual image attachments; if unavailable, stop with an evidence packet.


## Route by intended artifact (mandatory)


The user may supply only a **school/city name and a use case**. The Agent must autonomously infer the correct mode; do NOT ask the user to decide the implementation details.


| User intent | Route | Artwork goal |
| --- | --- | --- |
| One identifiable landmark | `single-building` | Photo-grounded individual drawing |
| Multiple independent drawings or an architecture catalogue | `gallery-layout` | Separate clear subjects; legacy `compose.py` |
| School/city anniversary, visual identity, tote bag, commemorative poster, merch | **`commemorative-montage`** | **One harmonious composition**, with clear anchor, overlapping supports, shared visual connectors and unified line style |


When asked for a school or city **as a commemorative visual**, prefer `commemorative-montage` instead of auto-arranging isolated building cutouts. Select 2–5 real landmarks with documented references when the user did not supply a list; prioritise correct identity over arbitrary photogenic additions. See [compositional protocol](../../docs/COMMEMORATIVE_MONTAGE.md) and [Chinese detailed guide](../../docs/COMMEMORATIVE_MONTAGE.zh-CN.md).


**Gallery and commemorative are NOT interchangeable.** A page with disjoint independent building stickers is a failure for a tote-bag or anniversary hero illustration. Do not call the legacy `compose.py` output the finished commemorative artwork. Visual composition work belongs in the Skill, not in user-supplied prompts.


## One-time workflow (with limited human intervention)


1. **Ground identity and rights**. Parse user style/reference. Search official source pages and photo repositories for each exact building. Open original photo pages, check names, known roofs/arches/entrances, locate two genuinely different viewpoints, note photographer and permission to produce derivatives. Prefer high-resolution originals to search thumbnails; don't copy unlicensed images to public GitHub. Read [photo sourcing](references/photo-sourcing.md). Agent may create *agent-attested* source records for publicly licensed images, with source/rights evidence URLs and model-call IDs; do **not** claim a human reviewed anything unless a person did. User-owned or ambiguous-license photos must be authorized by their owner. Photo/feature fields have a [schema](references/evidence-schema.md).
2. **Lock photo and shape evidence.** Run `scripts/reference_pipeline.py template` for a starter manifest; replace all placeholders with actually observed information. Record per-building `primary_view_id`, `must_match` features with photo IDs and optional per-view bboxes, forbidden inventions and unknown/unseen features. Record image-input model/call IDs for any agent-provenanced checks. Then run `scripts/reference_pipeline.py prepare`. Any rejection means return to sourcing; no synthetic attestation fields just to pass.
3. **Reference-conditioned visual generation.** For each building, **actually attach** its own original-photo pixels and style-only reference plus available feature crops to an image-capable generator. Pass [prompt contract](references/prompt-recipe.md) + `generation-brief.md`. Never pass filenames or a purely text description in lieu of photos. Preserve one camera anchor, do not mix multiple views into a fabricated facade; use a clean transparent cutout with **no generated official text**. Record the real model invocation and output SHA256 in `generation-log.json` per building. See [Agent audit protocol](references/agent-audit.md).
4. **Multi-building artwork.** For `gallery-layout` only, arrange independently reviewed cutouts with legacy `scripts/compose.py`. For `commemorative-montage` follow the new two-stage [integrated composition workflow](../../docs/COMMEMORATIVE_MONTAGE.md): use `compose_v2.py plan` and `compose_v2.py draft` to create a hierarchically organised, overlapping composition **draft**, then actually call a reference-image generation/editing model to unify the whole drawing. The draft is NOT the final image. Never pretend buildings from different campuses occupy one factual camera view.
5. **Agent automatically reviews using actual image inputs**. Run `scripts/agent_audit.py` either with an `OPENAI_API_KEY` (two structured vision calls per building through Responses API), or with `--provider agent-json` where a vision-enabled Agent separately inspects the candidate and original photos twice, saving both structured reports. Inspect each `must_match`, unsupported geometry, model-created text and viewpoint consistency. If any score is under 0.90, mismatch, missing photo ID or conflicting assessment, return `needs_review` rather than manufacturing a pass. Agent output is explicitly machine-assessed, not human-certified.
6. **Targeted repair and escalation.** Read `retry-brief.md` and correct **only the building** with mismatches using cited original/cropped photos. Update `generation-log.json` and rerun both audits. Maximum 2 image-edit/audit retries per problematic building before escalating precise unresolved points to a human. `photo-faithful` mode normally requires a human review (optional `--permit-photo-faithful-auto` opts into lower assurance). Official logos/inscriptions and legal rights are always separately sourced/licensed.
7. **Deliver only supported output.** For single-building/gallery use the documented `agent_audit.py` approval. For commemorative use **`montage_audit.py` on the actual integrated final PNG**, which audits every landmark against source photos plus the overall composition in two passes. Only pass its **final-image-bound** `approval.json` to `raster-to-layered-svg/scripts/convert.py`, then build the offline HTML editor. Preserve final evidence/agent reports, visual inputs and hash provenance. If blocked, deliver the reference packet and outstanding questions rather than calling unreviewed art accurate.


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


## Commemorative montage in one glance (v0.4)


After genuine photo-grounded cutouts exist under `workspace/artwork/cutouts/`:


~~~bash
python skills/campus-architectural-lineart/scripts/compose_v2.py plan   --manifest workspace/project.json --usage tote-bag   --anchor-id BuildingA --output workspace/artwork/montage-plan.json


python skills/campus-architectural-lineart/scripts/compose_v2.py draft   --plan workspace/artwork/montage-plan.json   --output-dir workspace/artwork/montage-draft
~~~


**Optional executable integrated redraw (when an OpenAI Image API key is available):**

~~~bash
python skills/campus-architectural-lineart/scripts/integrated_edit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --plan workspace/artwork/montage-plan.json \
  --draft workspace/artwork/montage-draft/draft-layout.png \
  --draft-evidence workspace/artwork/montage-draft/draft-evidence.json \
  --brief workspace/artwork/montage-draft/integrated-generation-brief.md \
  --output workspace/artwork/final-integrated.png \
  --generation-log workspace/artwork/integrated-generation-log.json
~~~

Requires `OPENAI_API_KEY` in the environment, uses the real Images Edit API (`gpt-image-2.5-sunburst` by default), uploads the draft/style/cutouts and each landmark's primary real photograph, and writes the real response request ID plus exact input/output hashes. This step incurs external API costs. If the credential is absent, use an already connected multimodal image-editing tool with the same genuine image inputs and record its actual call; **never fabricate a call or treat the draft as the final**.

The Agent must NOW **actually use an image-generation/editing tool** with the generated draft, real photographs, all cutouts, and a style image as **image attachments**, obtain `final-integrated.png`, and truthfully record `integrated-generation-log.json`. Run `scripts/montage_audit.py` (full CLI and provider alternatives in [guide](../../docs/COMMEMORATIVE_MONTAGE.zh-CN.md)), and ONLY THEN use `convert.py --approval`.


The draft-making code alone cannot produce a woven, unified, print-ready final image. For layouts involving different institutions, note the result is an artistic commemorative montage, not a real panorama. Tote-bag currently means **16:9 horizontal graphic placement**, not a print vendor dieline. A believable but unverified new tower, bridge, official text, or visually disjoint sticker gallery must NOT pass.


## Visual success criteria


Check the ACTUAL integrated image, not just each cutout: (1) identifiable dominant landmark; (2) purposeful supporting hierarchy and partial overlap; (3) shared visual ground/vegetation/ornamental rhythm; (4) consistent line weight, texture and contrast; (5) readable silhouette at reduced print size; and (6) recognizable grounded facades with no invented geometry. If it still looks like three separated buildings on a white page, **redo the whole-scene composition** rather than declaring success.
