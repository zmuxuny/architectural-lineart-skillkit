---
name: campus-architectural-lineart
description: Create detailed hand-drawn architectural line-art panoramas from real reference photos and a user visual example. Use for campuses or real landmarks in slide covers/posters when structure fidelity, negative space and editorial style matter.
license: MIT
metadata:
  version: "1.0"
---

# Campus architectural line art

Turn verified building references into expressive architectural line-art. **A beautiful generative illustration is not evidence of accurate architecture.**

## Workflow

1. Ask for—or infer from the request—medium, 16:9 layout, desired blank area for a title, target image, line hierarchy and realism requirement.
2. Collect primary references (official websites, licensed original photography, user-owned photos). Record source URL, building name, location, building details, license and view angle in [the reference checklist](references/reference-checklist.md).
3. Set a strict feature inventory: roof profiles, tower/arch structure, landmark inscriptions and sign placement. If mixing buildings from unrelated campuses, explicitly label the montage as illustrative rather than a single realistic view.
4. Give image/drawing tools the user reference example, photos and design constraints from [the prompt recipe](references/prompt-recipe.md). Put architecture in the lower 30–45% and preserve ample blank space above. Use varied line weight, selective facade detail, controlled wave strokes and natural foliage instead of Canny-like noisy outlines.
5. Compare the draft with real reference photos. Catch hallucinated towers, doors/arches, distorted characters and changed roofs. **Use an independently verified official school wordmark where exact spelling is required; do not trust model-rendered lettering.**
6. Revise until the aesthetic is accepted. Save the selected raster and report its actual native resolution and whether the result is a stylized montage or photo-faithful rendering.
7. Hand off raster to `raster-to-layered-svg`, then `offline-svg-color-workbench` to get 4K PNG, real SVG paths and a self-contained HTML editor.

## Deliverable and factuality gate

Provide the selected illustration, source/reference table, and one-sentence disclosure of verified vs artistic elements. **Never claim architectural accuracy without a separate visual audit** or imply the resulting SVG paths are human-drawn Bézier strokes.
