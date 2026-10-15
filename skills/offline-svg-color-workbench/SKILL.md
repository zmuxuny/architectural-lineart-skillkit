---
name: offline-svg-color-workbench
description: Make a single offline HTML app that interactively recolors dense SVG line-art, tunes opacity/detail, previews transparent white and black backgrounds, and exports 4K PNG or genuine vector SVG. Use to hand an editable artwork workbench to a nontechnical end user.
license: MIT
metadata:
  version: "1.0"
---

# SVG color workbench · offline single-file editor

Pair a real vector SVG with a transparent 4K PNG for fast browser preview, then package an independent HTML app. It runs with **no server or network requests** in current Edge/Chrome.

## Build command

```bash
python skills/offline-svg-color-workbench/scripts/build.py \
  --svg dist/zju/lineart.svg \
  --png dist/zju/lineart-transparent.png \
  --output dist/zju/color-workbench.html \
  --title 'Campus line art' --filename 'campus-lineart'
```

It embeds Gzip-compressed SVG paths + base64 PNG preview inside a standalone HTML file. User controls line HEX color, 0.25–15.00× visibility, 0.5–1.8 detail dominance, background transparency/black/white, zoom and four exports. Transparent SVG export preserves vector paths, not a raster `<image>`.

## Reproducing the user's selected final appearance

Screenshot clearly displays `#AEB0B2`, visibility `1.15×`, and the detail category `主线突出`. The exact last slider numeric value is **not visible**. This template starts at `detail=1.65` as a visual approximation; show the user how to adjust it and do not falsely claim it was their exact saved number.

## Verification

Read [export QA](references/export-qa.md). Ensure Chrome/Edge supports `DecompressionStream`. Open the HTML offline and verify SVG with no embedded images; check 3840×2160 PNG and true-alpha background; compare preview with exported results. The PNG and SVG alpha blending algorithms are related but not pixel identical in ultra-fine regions.
