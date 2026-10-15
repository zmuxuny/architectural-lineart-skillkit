# Contributing

Please keep changes narrowly scoped and provide before/after images for renderer changes. PRs should include tests for converter/build steps and document any artistic vs factual limitations. For visual changes, do not silently change the user's selected default `#AEB0B2`, `1.15×` and the clearly identified *approximate* detail default (`1.65`).

Test: `python -m unittest discover -s tests -v`; `node --check skills/offline-svg-color-workbench/assets/editor.js`.

PRs are welcomed as **Ready for review** when the implementation is complete; draft PRs should be finished locally before submission. Never commit private user materials or copyrighted photos without rights verification.
