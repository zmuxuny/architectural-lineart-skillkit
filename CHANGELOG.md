## [0.5.0] - 2026-10-25

- Respond to visual test feedback: architecture-first landmark scroll, not three landmarks buried in foliage or an isolated sticker gallery.
- Add `compose_v2.py plan --archetype landmark-scroll` for 6–10 verified landmarks, even left/middle/right coverage, varied roofline rhythm, and near-zero default ornamental lines.
- Add `scroll_atlas.py` for labeled, source-hash-bound 2×2 reference boards, keeping every real primary photo and cutout represented within the image editing input budget.
- Extend integrated generation and final montage audit to verify all included landmark sources and reject missing identities or scenic/tree dominance.
- Add regression tests and a practical Chinese process document; no unverified claim that real image generation already meets artistic or factual targets.

## [0.4.1] - 2026-10-24


- Add optional runnable `integrated_edit.py` backed by OpenAI's multi-reference Images Edit API; accepts the draft, style image, each grounded building cutout and its primary real photo, then records authentic request ID and exact hashes for `montage_audit.py`.
- Guard against missing API keys, stale evidence/cutouts, image substitution, malformed model responses and faux draft-as-final outputs. Six new mock-API tests exercise the payload and generation-to-audit contract; no paid inference is performed in CI.
- Document native Codex/API-backed integration and the remaining visual/rights/print accuracy limitations. Preserve native Agent tools as an alternative.


## [0.4.0] - 2026-10-24




- Distinguish single-building, gallery-layout and commemorative-montage; anniversaries, canvas tote prints and city identity work must not silently use separated gallery tiles.
- Add executable `compose_v2.py` to create hierarchically overlapped composition plans, visually connected draft PNGs, layouts/guides and genuine image-model redraw briefs. Draft ≠ finished artwork.
- Add `montage_audit.py` to check actual integrated image edit call provenance, source/draft/cutout hashes and real photo plus composition in two visual passes per landmark and two for the entire montage.
- Require integrated final-image-bound approval for SVG/HTML; block sticker galleries and stale draft-for-final substitutions.
- Add montage plan JSON Schema, bilingual implementation guides and synthetic regression tests. Real model and physical-print effectiveness remain unverified.




## [0.3.0] - 2026-10-16




- Agent-first sourcing records distinguish model findings from human signoff and require traceable original-photo/license evidence.
- Added `agent_audit.py` for genuine image-input VLM calls or native multimodal Agent verdicts, two review passes, exact per-input SHA256, fail-closed approval and targeted repair brief.
- Added agent vision examples, a full Chinese walkthrough and synthetic regression tests. No live VLM factual-accuracy benchmark has been performed.
- Low-risk automated reviews are labelled Agent-reviewed; high-risk photo-faithful work escalates by default.




## [0.2.0] - 2026-10-16




- Add `campus-architectural-lineart` photo-evidence CLI: original-photo provenance, minimum native resolution, distinct viewpoints and perceptual duplicate checks, feature crops, locked image hashes, grounded generation packet, and fail-closed human review.
- Add deterministic multi-landmark transparent cutout compositor; explicitly label unrelated campuses as illustrative montages.
- Add mandatory `convert.py --approval` option for evidence-gated factual landmark conversion, preserving generic opt-in compatibility.
- Publish detailed sourcing / schema / prompting / compositing guides, an intentionally unverified template, and offline synthetic QA tests.
- **No change** to the older illustrative Zhejiang University demo's fact status: it remains not architecture-certified.




# Changelog




## 0.1.0 — 2026-10-15




- Three portable Agent Skills for architectural illustration, raster vectorization and standalone recolor workbench.
- Python/OpenCV multi-threshold 11-layer real SVG path tracing and transparent 4K PNG pipeline.
- Offline HTML/CSS/JS workbench with user's color `#AEB0B2` and 1.15× visibility defaults.
- Self-contained Zhejiang University illustrative demo (not official), English/Chinese docs, test suite and CI.
- Verified PNG/SVG browser downloads with Chromium/Playwright on sample data.


