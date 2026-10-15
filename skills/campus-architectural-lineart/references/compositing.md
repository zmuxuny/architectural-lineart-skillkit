# Deterministic panorama from independently generated building cutouts

Unlike asking a generator to draw a fictitious joint skyline, deterministic compositing does not create new facade/tower pixels. It cannot alone guarantee that cutouts were accurately drawn; the final montage still needs visual audit.

The building generator should return separately inspected **RGBA PNGs with actual alpha=0 background**. Filenames must be relative to a local `layout.json` file. Keep the upper 55–65% blank for slide titles.

Example `layout.json` (generic placeholders, **not** a proven real campus):

```json
{
  "mode": "illustrative-montage",
  "canvas": [1672, 941],
  "upper_blank_fraction": 0.60,
  "background": "#000000",
  "placements": [
    {"landmark_id":"BuildingA", "image":"building-a-cutout.png", "box":[0.05,0.60,0.47,1.0]},
    {"landmark_id":"BuildingB", "image":"building-b-cutout.png", "box":[0.49,0.60,0.95,1.0]}
  ]
}
```

Run:

```bash
python skills/campus-architectural-lineart/scripts/compose.py \
  --layout workspace/artwork/layout.json \
  --output workspace/artwork/final.png
```

The compositor checks each entry has one unique landmark ID, an RGBA image with transparent corners, a valid normalized destination box, and placement restricted to the lower canvas. It preserves alpha and placement; it does **not** remove background, invent trees/water or fill unsupported facade regions. Audit against the photos **after** compositing and before SVG conversion.
