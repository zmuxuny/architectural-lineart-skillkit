---
name: raster-to-layered-svg
description: Turn selected black-background/light-line raster illustrations into transparent and black-background 4K PNG plus multi-threshold real SVG contours. Use for vectorization, transparent slide overlays and downstream color workbench output.
license: MIT
metadata:
  version: "1.0"
---

# Raster → 4K PNG + layered SVG

Converts an **already accepted** raster illustration into transparent/opaque images and paths. These are **contours of raster regions**, not the original hand-drawn strokes.

## Run

Install `pip install -r requirements.txt` from the repository root, then:

```bash
python skills/raster-to-layered-svg/scripts/convert.py \
  --input examples/zju/source-ai-illustration.png \
  --out-dir dist/zju --size 3840x2160 --title 'Campus line art'
```

The skill's own `scripts/convert.py` works after copying just this skill directory, provided Pillow, NumPy and OpenCV are installed. Outputs:

- `lineart-transparent.png`: RGBA, RGB white, alpha derived from pixel luminance.
- `lineart-black.png`: opaque composite.
- `lineart.svg`: 11 tonal path layers (`fill-rule="evenodd"`), no `<image>` bitmap.

## Steps

1. Convert input RGB to grayscale; optionally `--mode dark-on-light` inverts it.
2. Map dark background to alpha 0, bright lines to alpha 1, and Lanczos resize alpha to target canvas.
3. For each original raster threshold `[6,14,26,42,62,85,112,142,174,207,237]`, use `cv2.findContours(RETR_TREE)` and `approxPolyDP` with 2× pre-scaling by default.
4. Compose 11 opacity layers with corrected cumulative alpha. Keep paths even-odd to preserve holes.
5. Check dimensions, transparent corner, parse SVG, inspect at full size and compare with source.

## Critical limitations

4K describes the **output canvas**, not native source fidelity. Image upsampling does not recover detail. Extremely dense foliage creates large polygon paths; reduce tracing `--zoom` or increase `--epsilon` only after reviewing the visual change. Do not claim photo-faithful building geometry just because the SVG has valid paths.

## Evidence-gated integration for factual landmarks

When operating as the downstream stage of `campus-architectural-lineart`, do **not** accept unreviewed artwork. Add `--approval <reviewed-approval.json>` to the conversion command; the script rejects missing/blocked approvals or if the input image's SHA-256 no longer matches the human-audited artifact. The full photo-grounded process is documented in [`docs/PHOTO_GROUNDING.zh-CN.md`](../../docs/PHOTO_GROUNDING.zh-CN.md). Generic already-licensed artwork can still be vectorized without `--approval` when no factual building claim is being made.
