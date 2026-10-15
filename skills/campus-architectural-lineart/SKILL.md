---
name: campus-architectural-lineart
description: Build photo-grounded architectural line-art from independently checked real building photographs, with evidence manifests, reference sheets, image-conditioned generation, per-feature human review and hash-bound approval. Use when a school/landmark illustration must minimize invented structures before SVG conversion.
license: MIT
metadata:
  version: "2.0"
---

# Photo-grounded architectural line art · evidence-first generation

**Do not equate beautiful AI line art with actual architecture.** This Skill has **fail-closed reference and review gates**. Code validates evidence completeness and tampering; **only a real reviewer comparing images** can judge the architecture. It is not an architectural authenticity oracle or a native image-generation engine.

## Mission and non-negotiable constraints

- Preserve a real landmark's visible roof form, geometry, door/arch count, facade and tower placement **as shown in licensed source photos**. Do not fill unseen geometry based on model priors.
- Require **at least two genuine photos of each landmark from different angles**. Each reference needs a real source page/ownership, an original image, copyright/derivative-use review, human attestation and enough pixels. No scraped thumbnails, model-generated "photos," or cropping the same shot twice to manufacture independent views.
- Text is special: do **not** ask the image model to spell university/landmark names. Keep sign panels empty and use a separately sourced, verified and permitted official mark or add text in the presentation tool after generation.
- A multi-location composition is an **illustrative montage**; it must not be presented as a real campus viewpoint. For geometry faithful to one photo, prefer **manual/photo-traced vector design** instead of unconstrained generative recreation.
- The source photo pixels AND a separate style reference must actually be attached to an image-capable generator. Merely passing photo names or textual summaries **does not ground a model**.
- If evidence, image input access, or subsequent feature-level human review is missing, **stop rather than assert success**.

## 0. Source collection and verification

Read [photo selection protocol](references/photo-sourcing.md), [human checklist](references/reference-checklist.md) and [image-tool prompt contract](references/prompt-recipe.md). Search official school pages, original licensed photographs and users' own photos. Match **building identity and viewpoint**, not visual resemblance. Set a single `primary_view_id` as the camera anchor for each building; the second angle is evidence for verifying details, not permission to mix viewpoints. Check source attribution, license, photographer, location, zoomable original, structure, and any potential photo manipulations; record every original page URL and local source file in a manifest. Source-page authenticity and camera viewpoint are not reliably machine-provable; ask the human to verify.

```bash
python skills/campus-architectural-lineart/scripts/reference_pipeline.py template \
    --output workspace/project.json
```

Fill `project.json`; the initial template is **deliberately NOT approved**. It uses `photos/*.jpg` and `style_reference`. The precise schema is in [working example and guide](references/evidence-schema.md). Obtain original photo files yourself or use the allowlisted HTTPS download helper:

```bash
python skills/campus-architectural-lineart/scripts/reference_pipeline.py fetch \
    --manifest workspace/project.json \
    --allow-host upload.wikimedia.org \
    --allow-host www.zju.edu.cn
```

`fetch` validates image bytes but **does not assert that a website's caption or license is true**. Do not flip `human_confirmed_photo`, `derivatives_allowed`, `source_verified_by`, or `visible_and_human_verified` to `true` until an actual person checked those claims against the original sources.

## 1. Lock reference evidence before generation

```bash
python skills/campus-architectural-lineart/scripts/reference_pipeline.py prepare \
    --manifest workspace/project.json --out-dir workspace/grounding
```

If rejected, inspect `workspace/grounding/preflight-report.json`, obtain better photos or clarify architecture, and retry. Never weaken thresholds or fabricate records to make the gate pass.

Passing results produce:

- `reference-board.png`: actual original-photo montage with source IDs and camera angles.
- `feature-crops/<building>/<feature>__<view>.png`: *evidence* crop(s) for locked architectural features.
- `evidence-lock.json`: hashes of the manifest, source photos and style image.
- `generation-brief.md`: actual model-input contract plus proven/not-visible/forbidden features.
- `review-template.json`: initially all `unknown`, forcing an explicit post-generation review.

## 2. Generate, with **actual reference image input**

1. Give the image model the **raw source photo images**, not just the board or textual descriptions. Include the style image as a distinct style-only conditioning reference. Use photo IDs from `generation-brief.md` when recording attachments.
2. **Render one identifiable building at a time** using that building's two or more photo angles plus style reference. Request a clean transparent cutout with preserved visible geometry, no additional building elements or lettering. Where tool input limits apply, do not silently drop images: reduce the scope to one building or stop.
3. Inspect the output against the attached photos. If a real feature deviates, supply feature close-ups and revise **that building**, or use manual photo-based tracing. Do not invent a backside, new arch count or upper tower to fill a nice composition.
4. Only after individual buildings pass a preliminary human inspection, arrange them by explicit placement using `scripts/compose.py` (see [montage guide](references/compositing.md)). This is deterministic alpha compositing, not generative stitching. One-camera `photo-faithful` mode skips montage and uses the actual single building viewpoint.
5. Save the exact generated PNG; record which reference photos the tool actually received **per building**. Record its native resolution and avoid calling upsampling "native 4K".

The Skill intentionally has no fake `generate_image()` Python function; the **Agent must invoke its available multimodal generation/editing tool and inspect the returned artwork**. If none exists, deliver the generation packet and stop. This is different from `raster-to-layered-svg`, which is fully deterministic.

## 3. Mandatory post-generation truthfulness audit

Copy `review-template.json` to a new `review.json`. An independent human reviewer must compare output against each referenced **actual photo** and mark each feature `pass`/`fail`/`unknown`. Document meaningful observations. Record a real image model/tool call, global attached source image IDs, and **per-building model call image IDs**. Passing merely because the illustration "looks like a campus" is prohibited.

```bash
python skills/campus-architectural-lineart/scripts/reference_pipeline.py audit \
    --manifest workspace/project.json \
    --evidence-lock workspace/grounding/evidence-lock.json \
    --image workspace/artwork/final.png \
    --review workspace/artwork/review.json \
    --output workspace/artwork/approval.json
```

Any `unknown`/`fail`, missing source photo image-input evidence, incorrect text, invented geometry, missing source comparison note or changed photo bytes cause **blocked** status. Keep rejection results visible, revise artwork and repeat review. Passing produces `approval.json` bound to the **exact PNG SHA-256** and reference evidence. Human attestations are not algorithmic guarantees of visual fidelity.

## 4. Only then vectorize and deliver HTML

```bash
python skills/raster-to-layered-svg/scripts/convert.py \
  --input workspace/artwork/final.png \
  --approval workspace/artwork/approval.json \
  --out-dir workspace/dist --size 3840x2160

python skills/offline-svg-color-workbench/scripts/build.py \
  --svg workspace/dist/lineart.svg \
  --png workspace/dist/lineart-transparent.png \
  --output workspace/dist/workbench.html
```

The `--approval` option checks the exact artwork hash and required human evidence. Generic raster-to-SVG users may omit it, but **do not omit it within this photo-grounded workflow**.

## Failures that must block a "verified" claim

- Reference images come only from thumbnails, a different building, one reused image, a 1024px screenshot, unclear rights, or no independent second viewpoint.
- The model was prompted with landmark names rather than actually given original photograph pixels; a total reference list does not substitute for evidence **per rendered landmark**.
- Additional towers, bridges, unreadable/incorrect official inscriptions, new wings, a different roof/arch count, or invented surrounding buildings appear.
- Reference views disagree and the ambiguity is hidden instead of reported; the model fills behind-the-camera space not visible in photos.
- A user demands exact geometry and image generation cannot preserve it. **Return to photo-guided manual tracing** with direct side-by-side human verification.

## Existing demo is not architecture-certified

The Zhejiang University example in this repository is an older **AI-generated illustrative composite**. It predates the evidence gate and does **not** have a compliant photo packet, per-building model input logs and feature-level approval. Do not retrofit or invent approvals for it. The new skill will reject that case as "unverified" if treated as an accuracy-critical image.
