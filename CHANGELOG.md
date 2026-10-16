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
