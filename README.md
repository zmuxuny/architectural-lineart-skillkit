# Architectural Line Art Skillkit

[简体中文](README.zh-CN.md) · [Agent Skills specification](https://agentskills.io/specification)

**From referenced buildings and a hand-drawn image to transparent 4K PNG, genuine multi-layer SVG paths, and a single-file offline color workbench.**

## Case study — Zhejiang University-inspired architectural line art

Here is the **actual example included in this repository**, from the selected AI illustration to an adjustable, presentation-ready grayscale result. The buildings form an **artistic montage, not a verified depiction of the real campus** ([asset and trademark notes](ASSET_NOTICE.md)).

| Source artwork · black background | Final result · gray lines on white |
| :--: | :--: |
| ![Original black-background Zhejiang University-inspired campus line illustration](examples/zju/source-ai-illustration.png) | ![Final gray architectural line art on a white PowerPoint-style background](examples/zju/final-gray-on-white-preview.jpg) |
| AI-generated artwork, **1672 × 941** | White-slide preview, line color **`#AEB0B2`** and visibility **`1.15×`** |

### The offline color editor, in use

<img src="docs/assets/workbench-screenshot.png" alt="Actual browser screenshot of the offline SVG color workbench with a gray campus illustration, presets, line visibility/detail sliders, and export buttons" width="950">

The screenshot shows the **real browser UI**, not a mockup. Adjust HEX color, visibility and detail emphasis, preview on a white/black/transparent background, then export 4K PNG or true SVG paths. The **Main lines emphasized (主线突出)** setting is selected; its exact original slider number was not visible, so the bundled example uses an adjustable approximation (`detail=1.65`).

**Explore the exact demo files:**

| Artifact | Preview / use |
| --- | --- |
| Selected source illustration | [Source PNG](examples/zju/source-ai-illustration.png) |
| White-slide final appearance | [Full preview](examples/zju/final-gray-on-white-preview.jpg) |
| 4K transparent line art | [Transparent PNG](examples/zju/lineart-transparent.png) |
| Real multi-layer vector output | [SVG with 11 path layers](examples/zju/lineart.svg) |
| Full-featured offline editor | [Download `workbench.html`](examples/zju/workbench.html) and open in Edge/Chrome |

**End-to-end flow:** reference checks → AI illustration (creative step) → transparency extraction + 11-level contour vectorization → 3840 × 2160 exports → single-file offline HTML workbench.

## What you get

| Skill | Purpose | Output |
| --- | --- | --- |
| [`campus-architectural-lineart`](skills/campus-architectural-lineart/SKILL.md) | Architectural reference audit + image generation workflow, with explicit factuality checks | Selected artistic source PNG + reference log |
| [`raster-to-layered-svg`](skills/raster-to-layered-svg/SKILL.md) | Bright-on-dark raster → RGBA & 11-tone actual contour paths | 4K transparent/black PNG + `<path>` SVG |
| [`offline-svg-color-workbench`](skills/offline-svg-color-workbench/SKILL.md) | Build fast, network-free recolor/editor with source embedded | Self-contained HTML with 4 export choices |

These are **three individually installable Agent Skills** (`SKILL.md` + optional `scripts/`, `assets/`, `references/`). They follow the open [Agent Skills](https://agentskills.io/specification) directory convention. AI image generation is an external creative step—not pretended to be a deterministic Python script.

## Try the offline workbench immediately

Open [`examples/zju/workbench.html`](examples/zju/workbench.html) in **Edge or Chrome**. It needs no backend, build step or network connection; the original image and SVG are already embedded.

Controls: HEX picker, visibility slider, fine-vs-main-line balance, white/black/transparent preview, zoom and export as SVG paths or 3840×2160 PNG.

> Source is an **AI-generated illustrative montage**, not an official Zhejiang University rendering. The generated buildings/signage were not exhaustively audited against actual architecture; see [asset notice](ASSET_NOTICE.md).

## Run the full pipeline on your own illustration

Requirements: Python 3.10+ and modern Chrome or Edge.

```bash
python -m pip install -r requirements.txt

# Stage 1 (creative): obtain a source image according to
# skills/campus-architectural-lineart/SKILL.md (native resolution, not falsely labeled 4K)

# Stage 2: true contour SVG + 4K RGBA/black PNG
python skills/raster-to-layered-svg/scripts/convert.py \
    --input examples/zju/source-ai-illustration.png \
    --out-dir dist/zju --size 3840x2160 --title 'Campus illustration'

# Stage 3: standalone offline HTML tool
python skills/offline-svg-color-workbench/scripts/build.py \
    --svg dist/zju/lineart.svg --png dist/zju/lineart-transparent.png \
    --output dist/zju/workbench.html \
    --title 'Campus illustration' --filename 'campus-lineart'
```

Open `dist/zju/workbench.html`; choose `#AEB0B2`, `1.15×` and fine-detail preference, then export transparent SVG or 4K PNG.

## Install in an Agent Skills-compatible coding agent

Clone this repo or download the ZIP; copy each required `skills/<skill-name>/` directory into your agent's skills directory (e.g. `$HOME/.agents/skills/`). Each skill contains a self-contained `SKILL.md` and its own necessary code/resources. No prompt-only magic or proprietary model download is required.

Depending on your agent/client, you can also use a skill installer supporting remote repository URLs once this repository has been published:

```bash
npx skills add <YOUR-GITHUB-REPO-URL>
```

## Technical honesty

- SVG consists of **11 cumulative gray-threshold polygon contour layers**, not hand-placed or semantically separated pen strokes. It has editable `<path>` data and no embedded `<image>`.
- PNG is resampled to **3840×2160 output pixels**. The included AI source is **1672×941**, so output resolution is not native 4K detail.
- Recoloring is non-destructive for geometry, but the SVG and PNG alpha formulas are not guaranteed pixel-identical.
- The visual reference/factual audit remains manual. If accurate architectural representation is a hard requirement, use photo-grounded vector drawing with verification rather than freeform generation.
- Offline HTML contains embedded example assets; custom SVG import has basic sanitization but is intended for trusted user files, not adversarial web content.

## Directory structure

```text
skills/
  campus-architectural-lineart/{SKILL.md,references/}
  raster-to-layered-svg/{SKILL.md,scripts/convert.py}
  offline-svg-color-workbench/{SKILL.md,scripts/build.py,assets/,references/}
examples/zju/
  source-ai-illustration.png          # Native selected AI image
  lineart-transparent.png             # 4K RGBA
  lineart.svg                         # Genuine path SVG, ~8.7 MB
  workbench.html                      # Finished offline application
  final-gray-preview-4k.png           # Example adjusted appearance
  final-gray-on-white-preview.jpg     # README preview
.github/workflows/ci.yml
tests/
```

## Test

```bash
python -m unittest discover -s tests -v
node --check skills/offline-svg-color-workbench/assets/editor.js
```

License: MIT for code and skill text. AI demo art, university wordmarks and factual/rights caveats are discussed in [`ASSET_NOTICE.md`](ASSET_NOTICE.md); the demo is not an official university publication.
