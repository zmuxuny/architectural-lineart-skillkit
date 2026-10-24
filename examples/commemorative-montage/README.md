# A runnable synthetic montage draft (NOT a real campus)

Run from the repository root:

~~~bash
python examples/commemorative-montage/create_synthetic_draft.py \
  --out-dir dist/synthetic-montage-draft
~~~

The script generates three deliberately **fictional** transparent building cutouts, then uses the real new compose_v2.py planner and renderer to create:

- cutouts/*.png
- montage-plan.json
- draft/draft-layout.png
- draft/draft-guides.png
- draft/integrated-generation-brief.md
- draft/draft-evidence.json

This is a **layout-and-asset-processing smoke test**, not evidence-grounded architecture, not a real image generation model call, and not a finished harmonious photo-grounded commemorative artwork. Do not use the synthetic result to claim architectural accuracy, model performance, or approval. In a real task an Agent must source original licensed photographs, generate reference-conditioned cutouts, perform an actual integrated image redraw and run montage_audit.py on the FINAL integrated PNG.

See ../../docs/COMMEMORATIVE_MONTAGE.zh-CN.md for the real end-to-end route.
