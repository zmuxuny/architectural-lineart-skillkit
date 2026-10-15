# Export and browser QA

1. Open HTML with `file://` in current Edge/Chrome. No external CSS, JS, image or network references should be needed.
2. Verify the embedded PNG is previewed and the original compressed SVG can decompress.
3. Test selection `#AEB0B2`, visibility 1.15, category 主线突出; numeric detail 1.65 is estimated from screenshot, not confirmed.
4. Export transparent PNG and inspect 3840×2160 size plus 0 alpha in blank top corner.
5. Export white or black background PNG and verify opaque background and legible strokes.
6. Export SVG; XML parses and contains `<path>` but **no `<image>`**; geometry should remain unchanged by color edits.
7. Export SVG with solid background and verify a `<rect data-background="true">` is present.
8. Test import of a custom SVG; imported text paths may need manual adjustment.
9. Treat SVG import as intended for user-trusted files. Basic sanitization is not a fully secure general-purpose SVG renderer.
10. Avoid calling 4K-upscaled PNG 'native 4K' when source raster is smaller.
