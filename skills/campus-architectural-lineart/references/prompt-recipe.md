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




## Commemorative integrated redraw (after per-building reference-grounded cutouts)


If the user wants a school/city anniversary, tote-bag, commemorative poster, or one artistic visual identity piece, use the [new montage protocol](../../../docs/COMMEMORATIVE_MONTAGE.md), NOT the legacy gallery compositor as final output.


Inputs must be **actual image pixels**:
- output of `compose_v2.py draft` as the **compositional guide** (not final artwork);
- each independently photo-grounded transparent building cutout;
- a verified primary-view photo of **each** depicted landmark, with feature inventory and forbidden inventions;
- an independent illustration STYLE reference.


Integrated edit prompt:


> Transform the supplied draft and factual cutouts into ONE cohesive commemorative architectural engraving, not multiple isolated stickers. Keep one dominant anchor landmark and arrange secondary buildings into a shared silhouette with purposeful depth and partial occlusion. Use the buildings’ own facades and a restrained shared architectural baseline as the connection; never automatically add ink waves, rows of shrubs, lakes, or forests to fill empty space. Preserve verified roof shapes, door/arch counts and landmark identity; if architectural detail is hidden, don't invent it. Use one consistent fine-line artistic language, deliberate negative space and print-readable weight. Do not create new real landmark architecture, official signage, college names or spurious physical geography. Relative building placement is artistic, not a real campus view.


Run the final montage-specific two-pass vision review. **Judge the final unified artwork** for compositional cohesion AS WELL AS comparing each visible landmark to its real photo. Any equal-spaced gallery-like layout fails; a final image identical to the draft cannot be approved by `montage_audit.py`. Do not mark the final result factual/official after merely inspecting cutouts.




### Architecture-first landmark scroll (six to ten buildings)

When the request is a school/city **architectural landmark scroll**, do not use the scenic-school prompt above. Select the `landmark-scroll` subtype instead of sparse hero montage. Give every landmark an original photo identity; distribute buildings continuously across the width with varied roofline rhythm and architectural silhouette detail. **No default trees, hedges, lake, landscape reflections, foreground forests, or decorative waves.** Architectural subject ink should visually dominate (>85% design target), scenery <5%. Do not pad sparse inputs with fabricated landmarks. Use the generated `integrated-generation-brief.md`, source-labeled atlases and mandatory final whole-image audit. The result must look like a well-populated campus/city architectural illustrated scroll, never three buildings placed into a landscaped poster.
