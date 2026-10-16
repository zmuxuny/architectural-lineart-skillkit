# Evidence manifest and generation review schema (v1)

**The JSON is an explicit record of a person's checks. It does not prove that checks actually happened.** Running `template` creates an intentionally blocked placeholder file. Fill it only after reviewing source pages, original pictures, people/rights and geometry.

## Inputs — `project.json`

```json
{
  "schema_version": 1,
  "project": {
    "title": "My verified campus illustration",
    "mode": "montage",
    "aspect_ratio": "16:9",
    "upper_blank_fraction": 0.62
  },
  "style_reference": "photos/style-reference.png",
  "landmarks": [
    {
      "id": "BuildingA",
      "name": "REPLACE with checked exact building name",
      "location": "REPLACE with checked campus/city",
      "primary_view_id": "front",
      "photos": [
        {
          "id": "front",
          "file": "photos/building-front.jpg",
          "source_page": "https://SOURCE_OWNER/original-photo-page",
          "original_url": "https://LICENSED_HOST/path/to/full-resolution.jpg",
          "photographer": "REPLACE with identified photographer",
          "license": "REPLACE with checked license",
          "derivatives_allowed": false,
          "human_confirmed_photo": false,
          "source_verified_by": "",
          "view_angle": "front"
        },
        {
          "id": "side",
          "file": "photos/building-side.jpg",
          "source_page": "https://ANOTHER_SOURCE/independent-view",
          "original_url": "https://LICENSED_HOST/side-original.jpg",
          "photographer": "REPLACE with identified photographer",
          "license": "REPLACE with checked license",
          "derivatives_allowed": false,
          "human_confirmed_photo": false,
          "source_verified_by": "",
          "view_angle": "side"
        }
      ],
      "must_match": [
        {"id":"roof","description":"REPLACE: actual roof silhouette in front/side photos","photo_ids":["front","side"],"visible_and_human_verified":false,"bboxes":{"front":[0.1,0.05,0.9,0.4],"side":[0.2,0.03,0.95,0.5]}},
        {"id":"main_door","description":"REPLACE: door count in facade photo","photo_ids":["front"],"visible_and_human_verified":false,"bbox":[0.25,0.35,0.75,0.98]}
      ],
      "forbidden_inventions": ["No towers not visible in reference photos"],
      "unknowns": ["Do not infer hidden rear facade"],
      "signage_policy": "no_generated_letters_use_verified_overlay",
      "official_marks": []
    }
  ]
}
```

The above example is **not a real source or legal declaration**. It must not pass until real records and human evidence are supplied. Mark `derivatives_allowed`, `human_confirmed_photo`, and `visible_and_human_verified` true **only after real checks**. The strings describing sources/identities, the actual file bytes and angles must correspond to reality.

Photos owned by a user may use `"source_page":"user-owned"`, `"license":"user-owned"`, `"original_url":""` and a clear author plus named reviewer. Do not publish private/user-owned photos without permission.

`bbox=[x0,y0,x1,y1]` is normalized 0..1 for a feature referencing **one photo only**. For multiple camera angles, use `bboxes={"front":[...],"side":[...]}`; never reuse a single rectangle for different photos. Crops are optional but strongly recommended for structural details. A feature with conflicting viewpoints must be described as unresolved rather than human-verified. For inscriptions/official marks, use independently authorized overlays with `official_marks` objects containing `{label,authority_page,verified_by}`; **do not** have the generator render text.

## Evidence gate

- At least two original photographs of the same landmark from **different independently checked viewpoints**, short side >= 850 px, long side >= 1400 px, and >= 1.5 megapixels each.
- A style-only reference image >= 600×300; one or more landmarks with exact names and locations.
- Photo source page/photographer/rights/derived-use and actual image input files, distinct hash and non-near-duplicate perception hashes.
- At least two human-verified building features per landmark, with photo evidence IDs, plus explicit forbidden inventions and hidden/unobserved regions.
- Approval cannot be inferred from validation alone: preflight `ready` only means source metadata and bytes satisfy the evidence *format and quality* gate.

## Generation review — `review.json`

`prepare` outputs `review-template.json` with all statuses `unknown` and image-input confirmations false. Copy it, then fill after you have *actually* provided source images to the generator and looked at the result side by side with its real photo evidence.

```json
{
  "reviewer": "actual human reviewer",
  "evidence_sha256": "COPY_UNCHANGED_FROM_TEMPLATE",
  "model_invocation": {
    "tool": "the actual image editing/generation tool used",
    "image_input_confirmed": true,
    "reference_ids_attached": ["style", "BuildingA:front", "BuildingA:side"],
    "landmark_calls": [{
      "id": "BuildingA",
      "tool": "the actual image editing/generation tool used",
      "image_input_confirmed": true,
      "reference_ids_attached": ["style", "BuildingA:front", "BuildingA:side"],
      "notes": "Record actual invocation, not intended plan"
    }]
  },
  "global_checks": {
    "no_unlisted_buildings": "pass",
    "no_invented_text": "pass",
    "viewpoint_or_montage_labeled": "pass",
    "style_and_layout_accepted": "pass"
  },
  "landmark_reviews": [{
    "id": "BuildingA",
    "features": {"roof":"pass","main_door":"pass"},
    "no_new_geometry":"pass",
    "source_comparison_note": "Explain what roof/door areas were checked and on which actual source photo."
  }]
}
```

The example above illustrates **field syntax only** and does not attest to any real visual review. Each status has an intended meaning: `pass` = independently examined against specific source images and found consistent; `fail` = inconsistency; `unknown` = not inspected or insufficient data. Do not automatically fill pass flags or infer them from a visual model's positive response. `audit` refuses any missing, fail or unknown checks. It also re-hashes the original sources and links approval to the exact output PNG hash.

## Limits

- Evidence integrity / validation is partly **mechanical** (SHA, size, duplicate candidates, metadata completeness), whereas building identity, camera angle, copyright, feature presence and generated fidelity are **human assertions**.
- Even a reviewer can miss subtle geometry errors. For use requiring legally or architecturally authoritative fidelity, use permissioned camera assets and professional manual vector illustration with a separate expert review.

## v0.3: explicit Agent attestation (not fake human verification)

Instead of `human_confirmed_photo`, a public, clearly licensed photo may use `agent_confirmed_photo: true` with `agent_evidence` fields: actual model and call ID, confidence >= 0.92, concrete observation, `source_page_checked`, `building_identity_checked`, `license_checked`, and an HTTPS `license_evidence_url`. Keep `derivatives_allowed` tied to real license evidence. User-owned pictures still need owner authorization.

Instead of `visible_and_human_verified`, a feature may use `visible_and_agent_verified: true` with `agent_evidence` fields `model`, `call_id`, confidence >= 0.92, visual observation and actual `image_input_ids` citing the building's photo(s). Such assertions are not automatically proven true by the CLI.

After image generation, create a generation log recording every building's real image-input IDs, generated cutout SHA256 and final composite SHA256; use `agent_audit.py`. The native `agent-json` reviewer also requires SHA256 for every image reportedly viewed. See [automated protocol](agent-audit.md).
