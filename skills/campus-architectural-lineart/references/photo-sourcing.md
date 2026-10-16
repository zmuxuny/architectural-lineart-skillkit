# Collecting high-quality factual building references

## Source search in an actual Agent run

**Do actual image/web search and open the provenance pages.** Search landmark's official name with its institution, campus, and building type; search a separate view by `front / side / facade / roofline / panorama / aerial`; inspect source URLs, then open the original images, not just thumbnail cards. When a user requests a named real place, do not substitute a visually similar building from an unrelated site.

Ranking: (1) owner's authoritative institution site with openly licensed originals, (2) user photos with clear permission, (3) photographer's original high-resolution Creative Commons files with source/attribution, (4) news/photos with clarified permissions. **An official website does not automatically grant modification rights.** A picture without a clear license is not a redistributable sample.

## Before recording as accepted

1. Open the source web page and confirm caption, date/location, photo identity and publication source.
2. Open the original image, record exact image URL, photographer, declared license/rights and local filename. Do not infer an image's identity or provenance from a filename alone.
3. Manually compare recognizable architectural details with an independent photo or authoritative building description. Check building vs. neighboring similar structures and historical renovations.
4. Explicitly choose one photo as the **primary view anchor** (`primary_view_id`); alternate views must not cause the generator to merge two camera perspectives.
5. Verify that **both** shots depict the **same** structure from distinct actual camera directions (e.g. front/side); a crop, resize, recompressed image, or color variation of one shot does not count as independent.
6. Prefer originals with at least 1.5 MP, shorter side >=850px, longer side >=1400px; if not available, do not silently label them reference-grade. Ask for more photos or use a human/tracing workflow.
7. For each visible/important feature, annotate its photo ID, a truthful description, optionally a normalized bounding box for automated evidence crops, and human review. Record all hidden/contradictory/unknown regions.
8. Record derivative-use permission accurately; keep the source attribution and link in deliverables. Do not copy unlicensed images into a public GitHub repository.
9. For inscriptions and university marks, find an authoritative logo/wordmark page and its usage rules. The image model should NOT synthesize letterforms; add the permitted verified asset afterwards.

## Multi-building composition

For art montages spanning several campuses, do **not** find an aerial photo of one campus and guess adjacent buildings. Acquire two+ views **for each** depicted landmark. Generate/verify separate building cutouts; composite deterministically in a labelled *illustrative montage*. For actual single-view imagery, constrain to one camera view, maintaining scene geometry. When original facade must be exact, trace it manually/vectorize photo-guided outlines and independently review.

## Trust caveats

The CLI can verify basic pixel dimensions, content hashes, duplicate image fingerprints, allowed download hosts and the existence of human review fields. It **cannot certify** that a source-page caption is correct, that a named photographer owns the image, that `derivatives_allowed` is legally correct, or that a reviewer truly looked at the image. The agent must document uncertainty rather than fabricate this evidence.

## Agent evidence capture in v0.3

An Agent with actual web and image-reading access may supply publicly licensed photos plus a structured source-page/identity/license check and its own invocation IDs. The preflight recognizes this as **agent-attested**, never as human confirmation. Search labels, license declarations and image-model confidence remain evidence to scrutinize, not conclusive authentication.
