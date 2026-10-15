# Reference-conditioned image-generation prompt contract

This is a **template for a tool call that includes actual image attachments**. Do not treat a descriptive prompt containing a building name as evidence the generator saw its real photographs. If the image model does not accept image attachments, stop and deliver the packet for manual use.

### Inputs required for each individual building

- **Source photo A**: independently verified full-resolution front/general view.
- **Source photo B**: independently verified different angle of the **same** building.
- **Feature crops**: roof/profile, windows/arches, side tower, monument inscriptions; the precise features present depend on that particular building.
- **Style-only reference image**: desired hand-drawn graphite/white-on-black artwork. The style image is NOT architecture evidence.
- **Approved feature inventory**: exact observable geometry; allowed artistic stylization; areas outside the sources; explicit forbidden inventions.

### Example per-building image prompt

> Transform the building present in the attached SOURCE PHOTOS into a detailed hand-drawn architectural line-art **cutout**. Preserve the roof outline, facade proportions, locations and count of visible doors, arches, towers and other important architectural features as shown in the real photos. Where the source views do not show a feature, omit or conceal it rather than invent it. Use the STYLE IMAGE only for thin/medium gray-white engraving strokes, natural shading and fine facade details. No photofilter edge detection. No additional buildings, bridges or clocks. No believable but new facade features. Leave signage blank: do not draw any legible letters or official marks. Transparent background, no shadowing that changes building silhouette. Output a PNG at the tool's actual native resolution. This is an art adaptation, not a structure design task.

Append the **actual** `generation-brief.md` section for this landmark, including positive structural constraints, forbidden inventions, and all source photo IDs. Attach the matching pixels.

### Compose stage

Prefer independent cutout PNGs + `scripts/compose.py` to a second all-scene generation call. Put lower architectural skyline within the prescribed bottom band; preserve upper negative space; no additional invented bridges, schools or adjacent structures. Natural hills/waterline may be clearly stylized decoration, but must not be misrepresented as real geography.

### Post-generation review questions (each has an evidence photo ID)

- Does the roof/cornice shape match? Is any tower added or removed?
- Are front facade and windows/arcs actually consistent with the photo?
- Did the model swap an architectural detail from another landmark?
- Did it invent a campus monument, exact inscription, church, spire or extra wing?
- Is any model-generated text present? If so, remove and use independently verified branding.
- Is the output explicitly an *illustrative montage*, not claimed to be a real single-camera view?

### Refusal and retry

If a needed face of the building isn't visible or references conflict, do NOT "fill in reasonably". Request another photo, adjust composition to hide unsupported parts, or switch to manual photo-grounded vector drawing. Do not mark a prompt, model output or an automated semantic image critique as definitive visual verification. `audit` accepts recorded **human** per-feature review only.
