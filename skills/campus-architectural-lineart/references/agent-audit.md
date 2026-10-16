# Agent-first photo-grounded audit (optional OpenAI Responses vision backend)

This workflow **automates visual review**, not factual certainty or legal clearance. The existing `reference_pipeline.py` **human** review (`audit`) remains for escalations and high-stakes geometry. For normal illustrative montages, the `agent_audit.py` optional vision backend can provide a lower-touch result.

## Before creating any images

1. Search architectural photo sources with browsing/search tools and open **original** photo pages. A string like `"Zhejiang University gate"` is never enough. Identify the exact structure and primary view.
2. Record independent front/side camera views of each building. Check two independent shots, license/derivative rights, known camera angles, and original pixel files.
3. Source checking and feature identification can be performed by a multimodal Agent: use explicit `agent_evidence`, with model/call ID, image IDs, source page and license evidence, observation, and conservative confidence; **do not** set human attestation flags for AI. For user-owned or ambiguous-rights files, ask their owner.
4. Produce `evidence-lock.json`, `reference-board.png`, `feature-crops/`, and `generation-brief.md` via `reference_pipeline.py prepare`.
5. Attach **the actual original photo pixels**, a distinct style-only image, and useful feature close-ups to the generation model for **each building**. Save generated per-building PNGs. Capture real model call IDs and the exact SHA256 of outputs.

## Automatic review of a generated illustration

Create `workspace/artwork/generation-log.json` after real model invocation (NOT from a planned request):

```json
{
  "tool": "actual-image-generation-tool",
  "image_input_confirmed": true,
  "final_image_sha256": "CALCULATE_REAL_SHA256_OF_FINAL_PNG",
  "landmark_calls": [
    {
      "id": "BuildingA",
      "tool": "actual-image-generation-tool",
      "image_input_confirmed": true,
      "reference_ids_attached": ["style", "BuildingA:front", "BuildingA:side"],
      "output_sha256": "CALCULATE_REAL_SHA256_OF_BUILDINGA_CUTOUT"
    }
  ]
}
```

For one building, `output_sha256` equals `final_image_sha256`. For multi-building montage, each building's output hash refers to `cutouts-dir/BuildingA.png`, etc.; the composite final PNG has its own hash.

With a vision API key (sent to OpenAI via HTTPS, not stored in the repo):

```bash
export OPENAI_API_KEY='your-own-key'  # set in your environment, never commit secrets
python skills/campus-architectural-lineart/scripts/agent_audit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --generation-log workspace/artwork/generation-log.json \
  --image workspace/artwork/final.png \
  --feature-crops-dir workspace/grounding/feature-crops \
  --output-dir workspace/artwork/agent-audit \
  --model gpt-4.1
```

If more than one building, include `--cutouts-dir workspace/artwork/cutouts` and name individual RGBA candidates `<building-id>.png`. In both passes each building is compared with **its own primary photo and secondary views**, never just the montage. Extra feature crops are attached when available.

When the coding/creative Agent has native visual image inspection but no standalone API key, the Agent must **actually inspect** candidate and photos in two separate review turns and create `workspace/artwork/agent-verdicts/BuildingA__feature.json` and `BuildingA__adversarial.json` as in the [sample](../../../examples/agent-review/BuildingA__feature.json). Do not let a text-only Agent invent image comparison outcomes. Then run:

```bash
python skills/campus-architectural-lineart/scripts/agent_audit.py \
  --provider agent-json --verdict-dir workspace/artwork/agent-verdicts \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --generation-log workspace/artwork/generation-log.json \
  --image workspace/artwork/final.png \
  --output-dir workspace/artwork/agent-audit
```

Native Agent verdicts must also supply `input_sha256` for every declared candidate, source photo and feature crop; the CLI checks all hashes against current files so a stale review cannot be replayed. These files carry self-declared call provenance, not cryptographic proof of what the vision model saw. `agent-json` does not itself call a remote API. **Never represent synthetic samples as completed audits of real campuses.**

## Decision rules (fail closed)

- Two passes per **individual building**, one feature-oriented and one adversarial/counterexample-oriented. Both pass exactly the declared `must_match` IDs and global negative geometry/text/viewpoint checks, with a cited source photo ID for every finding.
- All statuses `pass`, all confidence values ≥ **0.90** by default, specific observations and no contradictory difference descriptions. Confidence is a *model's self-report*, not a calibrated guarantee.
- An actual generation tool-call record is required per building, with full photo inputs + style ID and the correct PNG SHA256. Hash checks prevent later file substitutions but cannot authenticate the model's own visual reasoning.
- Any missing source file, changed hash, unavailable API key, `unknown`, `fail`, low confidence, missing evidence citation, or conflicting visual judgement **blocks auto approval**.
- By default, **photo-faithful** mode escalates even after unanimous model pass; `--permit-photo-faithful-auto` makes an explicit high-risk opt-in but does not imply expert certification.
- Even unanimous VLM agreement is not a mathematical or legal proof of architectural accuracy. University lettering and logos must be added from verified, authorized assets, never synthesized by the generator.

Outputs:

- `agent-review.json` — full pair of image-aware review records, source photo IDs, model invocation IDs, model observations, fail/unknown reasons, source image/candidate hashes.
- `approval.json` — `status: approved` only on supported agent pass; explicitly labeled `review_mode: agent_vision_two_pass`, **not** human-certified.
- `retry-brief.md` (only if blocked after actual model review) — specific mismatches and photo IDs; the Agent should edit just that building, update generation hashes, and review the new image again. Never recycle an approval for a modified image.

If approved:

```bash
python skills/raster-to-layered-svg/scripts/convert.py \
  --input workspace/artwork/final.png \
  --approval workspace/artwork/agent-audit/approval.json \
  --out-dir workspace/dist --size 3840x2160
```

This is an **agent-reviewed illustration**. For a building design, public institutional publication, official signage/marks or other high-stakes usage, request a qualified human review regardless of an automated pass.

## Retry and escalation policy for Agent execution

1. On `needs_review`, read `retry-brief.md`; if the specific defect is fixable using a source photo crop, edit *only* that building with the actual source images, not a text-only drawing prompt.
2. Regenerate candidate PNG, update the generation output hashes, run the full 2-pass audit again. Limit automatic loops to **two repair iterations**, then escalate unresolved structural/identity ambiguities to the user with precise photo/crop evidence rather than burning calls indefinitely.
3. `reference_pipeline.py audit` is still available for human/expert review. Never set `human_confirmed_photo`, `visible_and_human_verified`, or `reviewer: Human` based on an AI verdict.
