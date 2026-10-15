# Evidence-cited image critique (assistant only; not automatic approval)

For each `must_match` feature, an Agent with vision can prepare a **provisional** comparison to help a separate human reviewer:

1. Show the original full source photographs and their exact feature crops to the vision assistant; label `building_id`, `photo_id`, `feature_id` and one primary camera view.
2. Show the generated building artwork, ideally at the same cropped scale. Instruct the assistant to describe **observable differences** only: shape, count, relative position, visible/not visible, and whether the generated artwork appears to invent unsupported roof/wall/tower/door geometry.
3. Have it return `feature_id`, `photo_id`, `observation`, `uncertainty`, `proposed_status (pass/fail/unknown)` and screenshot/crop links. Don't permit it to invent missing photo evidence or claim unseen structural fidelity.
4. Display comparisons alongside the original reference files; let a human accept or reject each proposed status. Only a real human's review is recorded in `review.json` and accepted by `audit`.
5. All text/official marks require separate authoritative design files and human verification; multimodal OCR or a fluent-looking generated wordmark is not sufficient.

This is an **assistant** for catching errors, not a replacement for physically referenced, accountable human inspection. There is no implemented vision-model API or tested architectural classifier in this repository. The current code gates the evidence records and human decision, not the perceptual correctness of the decision.
