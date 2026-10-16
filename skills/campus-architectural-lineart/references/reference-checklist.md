# Human reference and generated-art verification checklist

This checklist complements the executable `reference_pipeline.py` gate. Checkboxes are meaningful **only when a person actually inspected the underlying images/sources**.

## Reference acceptance

- [ ] Real building's official name, campus/location and reference-photo subject were verified at source page.
- [ ] Full original image was downloaded rather than a low-resolution search preview; image size meets quality gate.
- [ ] At least two actual different angles of the **same** building; not two crops of one shot.
- [ ] Photographer/rights/license/source-page/derivative-use information is recorded and understood.
- [ ] Visible roof structure, facade shapes, window count, entrances and towers have a bounded evidence photo/crop.
- [ ] Unseen surfaces and facts are explicitly unknown; avoid inference.
- [ ] A separate user-chosen **style** reference is labeled style only, not as building evidence.
- [ ] For institutional text/marks: separate authoritative source and permitted overlay asset; no generated lettering.

## Real generation tool call

- [ ] Original photo A, original photo B and style image were **actually attached to the image-input tool**.
- [ ] Per-landmark call record exists, naming model/tool and attached photo IDs. No text-only "reference" substitution.
- [ ] The model created/edited only the specified building or the layout was deterministically composed from individually reviewed cutouts.
- [ ] Actual native PNG resolution, filenames and output are recorded.

## Artwork approval

- [ ] Each required feature was compared against cited source photos and marked `pass`/`fail`/`unknown`.
- [ ] No additional towers, bridges, inaccessible facade geometry or new buildings were invented.
- [ ] Campus labels aren't synthesized and all official marks use a separate vetted overlay.
- [ ] Montage vs. photo-faithful view is truthful and stated.
- [ ] An independent human completed the comparison; remaining unknowns are **not** silently marked pass.
- [ ] `audit` generated an `approved` JSON bound to the **exact PNG image hash**.
- [ ] Downstream SVG conversion included `--approval` (mandatory for this workflow).

The old Zhejiang University repo demo is illustrative art with **no verified compliance record**. It must not be relabeled as architecturally verified.

## v0.3: Agent-first low-touch review

For ordinary illustrations, let an image-capable Agent examine original photos and record evidence and call IDs without pretending a human signed off. After creation, run two actual image-aware architectural comparisons using [agent_audit.py](../scripts/agent_audit.py): every feature must cite photo IDs, notes and high confidence; any conflict or missing pixels escalates. Human review is reserved for unresolved/high-risk claims, official wordmarks or unclear licenses. See [Agent audit documentation](agent-audit.md).
