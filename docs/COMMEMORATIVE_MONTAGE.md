# Commemorative montage — coherent school/city landmark illustration


This mode is for **university anniversaries, tote-bag art, postcards, school/city campaigns, and commemorative posters**. Unlike a gallery of transparent building stickers, it must be ONE cohesive piece with anchor/support hierarchy, intentional overlap, coherent strokes and connecting ornamentation.


## Intent routing


- Single landmark: single-building, grounded photo-to-line-art flow.
- Multiple individually readable subjects/catalog: gallery-layout with the legacy compose.py compositor.
- School/city visual identity, anniversary merchandise, tote-bag or commemorative artwork: **commemorative-montage** with compose_v2.py DRAFT -> reference-conditioned image edit -> montage_audit.py -> SVG and offline editor.


## Architectural integrity


Each landmark needs actual verified photo evidence from at least two viewpoints. Generate grounded building cutouts **individually**, inspect them, and preserve their recognizable roof/arch/tower/entrance geometry. The montage may change relative placement, visual scale and partial overlap because it is explicitly illustrative — it may NOT invent a new real structure, claim the buildings physically adjoin, or fabricate lettering or an official emblem.


## Working commands


After following campus-architectural-lineart to collect a valid project.json and generating actual RGBA cutouts in workspace/artwork/cutouts/<landmark-id>.png:


~~~bash
python skills/campus-architectural-lineart/scripts/compose_v2.py plan \
  --manifest workspace/project.json --usage tote-bag \
  --anchor-id BuildingA --output workspace/artwork/montage-plan.json


python skills/campus-architectural-lineart/scripts/compose_v2.py draft \
  --plan workspace/artwork/montage-plan.json \
  --output-dir workspace/artwork/montage-draft
~~~


Supported use profiles: tote-bag, anniversary-poster, ppt-cover, city-poster. These currently describe an illustrative **16:9 horizontal ink panel**, not a physical bag dieline or print-ready press specification.


Outputs: draft-layout.png, draft-guides.png, integrated-generation-brief.md, draft-evidence.json. A draft is never the finished art. The Agent must actually invoke an image-capable generation/editing tool, passing the draft, cutouts, style reference and primary real photo of each landmark. Save the tool call ID, input IDs and exact SHA-256 of all involved images into integrated-generation-log.json; do not invent a call if the tool is absent.


If the Agent has `OPENAI_API_KEY`, the following optional CLI performs the **actual** whole-scene image edit and writes the generation log automatically (no separate manual transcription of input hashes or call ID):

~~~bash
python skills/campus-architectural-lineart/scripts/integrated_edit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --plan workspace/artwork/montage-plan.json \
  --draft workspace/artwork/montage-draft/draft-layout.png \
  --draft-evidence workspace/artwork/montage-draft/draft-evidence.json \
  --brief workspace/artwork/montage-draft/integrated-generation-brief.md \
  --output workspace/artwork/final-integrated.png \
  --generation-log workspace/artwork/integrated-generation-log.json
~~~

Uses the official multi-image `POST /v1/images/edits` endpoint, default `gpt-image-2.5-sunburst`, a 1536×864 16:9 request and genuine JPEG/PNG/WebP image attachments. It verifies the locked draft, all cutouts, model response/request ID and source hashes, but does **not** itself verify factual architecture. API calls may incur usage charges. When an authenticated image-edit tool is already available within an Agent, it may be used instead; log real inputs/outputs in the same schema. Do not claim this API flow has undergone an end-to-end real-campus benchmark: CI uses mocked image responses.

The final regenerated, unified artwork is audited in two vision passes **per landmark** against its real photographs and cutout, and two holistic composition passes against draft/style. A gallery-like end product fails the composition checks even if individual buildings look accurate.


~~~bash
python skills/campus-architectural-lineart/scripts/montage_audit.py \
  --manifest workspace/project.json \
  --evidence-lock workspace/grounding/evidence-lock.json \
  --plan workspace/artwork/montage-plan.json \
  --draft workspace/artwork/montage-draft/draft-layout.png \
  --draft-evidence workspace/artwork/montage-draft/draft-evidence.json \
  --final workspace/artwork/final-integrated.png \
  --generation-log workspace/artwork/integrated-generation-log.json \
  --output-dir workspace/artwork/montage-audit \
  --provider openai --model gpt-4.1


python skills/raster-to-layered-svg/scripts/convert.py \
  --input workspace/artwork/final-integrated.png \
  --approval workspace/artwork/montage-audit/approval.json \
  --out-dir workspace/dist
~~~


See [full Chinese protocol](COMMEMORATIVE_MONTAGE.zh-CN.md) for the exact source/photo/input contract and generation log. The vision backend requires the caller's API key or an actually image-aware Agent using agent-json verdict files. A passed automated verdict is a model assessment, not guaranteed architectural or legal correctness.


**Current validation boundary:** The new draft planner and audit gates have synthetic offline tests. A real-world photo-grounded unified image-edit workflow has not yet been benchmarked. Do not relabel the existing ZJU illustration as newly verified.
