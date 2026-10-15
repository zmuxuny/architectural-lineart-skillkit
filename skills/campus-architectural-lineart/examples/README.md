# Evidence template (intentionally BLOCKED)

`project.UNVERIFIED.template.json` is a **fill-in template**, not real Zhejiang University building evidence and not a truthfulness certificate. It deliberately uses missing files, placeholder URLs and unapproved human checks.

Run `reference_pipeline.py prepare --manifest ... --out-dir ...` on this template: it should fail. That is an intentional safety gate. To use it, supply properly licensed original photos from the exact building, confirm two distinct actual viewpoints, add your own style reference, and record truthful source review and structural features. Follow [`docs/PHOTO_GROUNDING.zh-CN.md`](../../../docs/PHOTO_GROUNDING.zh-CN.md).

Do not fabricate image-model input logs or fill pass flags without comparison; the previous `examples/zju/` demo is illustrative, not evidence-verified.
