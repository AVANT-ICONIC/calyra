# CALYRA Stage A: actual Blitz 0.3.0-beta.4 rendering evidence

**Date:** 2026-11-15. **Outcome:** restricted but promising for modern CSS paint. This is a browserless, CPU-rendered HTML screenshot experiment, not a hardware GPU, JavaScript, or interactive UI demonstration.

## Grounded evidence

- [Successful real native build and four captures, run 43671027217](https://github.com/AVANT-ICONIC/calyra/actions/runs/43671027217). Pinned upstream DioxusLabs/blitz revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` (version 0.3.0-beta.4), Rust 1.91, Ubuntu 24.04 x86_64.
- Screenshot engine is the **official upstream `examples/screenshot.rs`**, with Stylo, Taffy and Vello **CPU**. No Chromium/WebView and no native window/GPU proof.
- Four real native scenes: **controls, dashboard, visual and interaction**. Each normalized PNG is 1060x800 from a 2x upstream capture, with signed provenance, fresh output, full build and runtime logs in [artifact 14145005316](https://github.com/AVANT-ICONIC/calyra/actions/runs/43671027217/artifacts/14145005316). The artifact has a 7-day retention limit.
- The reference stylesheet's bytes were preserved **verbatim** by inlining it into an HTML style element. The canonical HTML document was patched **only to set the static active fixture and reduced-motion state**, and browser JS was removed without execution. Record `css_modified=false`, `dom_patched=true`, `js_executed=false`.
- Canonical source CSS SHA-256: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`. HTML: `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`.
- After retrieving the artifact, all eight native PNG files and the four generated snapshot HTML files **matched their recorded SHA-256 digests**.

## Local static Chromium image diagnostic

Original static HTML snapshots from the artifact were also rendered through local headless Chromium at 1060x800 (device scale 1, reduced motion), without CSS edits. Images are aligned, then compared by per-pixel absolute RGB difference. Thresholded changed pixels mean ANY color channel differs by at least 32/255. Results:

| Fixture | Mean RGB absolute difference (0–255) | Pixels over 32/255 threshold | Verified native normalized PNG SHA-256 |
| --- | ---: | ---: | --- |
| Controls | 10.885 | 7.873% | `fdf2e6da16e292dca88b2837b78f26a79697b704920c7d8bad09473abcb4bc19` |
| Dashboard | 5.302 | 4.582% | `f58ee32b7258c5ab36b5619757f3ee2ac3af29b872e2a98869023bbee616e1c3` |
| Visual | 4.767 | 3.632% | `98fd043c4fddabfe1b4a69e871e96badd920a5fd1d8e784a0c104a7c336d6b62` |
| Interaction, static only | 6.125 | 4.802% | `76d32b4b396324d6002997ae270745495f56f2f40bd6573348ce2508ed89cb61` |

These values are **not CSS property support rates**, nor performance or user-perceived quality measurements. Chromium was captured in a different Linux container than Blitz's GitHub Actions runner, so fonts, antialiasing and color management are not controlled; repeated samples and property-level isolations have not been executed.

## Visual inspection / known mismatches

- The **visual effects fixture** paints the shell, radial/linear gradient orb, clipping outlines, layered translucent glass card and foreground text in recognizably corresponding positions. Fine compositing/blur, border appearance and text metrics differ.
- The **dashboard** retains major Grid and Flex structure, SVG sparkline and sample numeric labels. This does not verify all CSS Grid semantics or mobile breakpoints.
- **Controls has material gaps:** native `<select>` control/value is absent in the captured image, the range input loses its progress fill/thumb and accent styling, and a heading wraps where Chromium fits one line. Native text inputs and buttons appear, but no actual focus or typing was tested.
- **Interaction fixture** is only a screenshot. Escape, focus order, scroll, clicks, ARIA, accessibility and JavaScript cannot be inferred from it.

## Architectural implication and next experiment

Blitz is a more credible **candidate for CALYRA's original browser-style CSS authoring model** than the separately adapted RmlUi RCSS sample. It still needs isolated `<select>` and `<input type=range>` tests, narrow/mobile viewport checks, and native Blitz `blitz-test-harness` input event validation. GPU-based window rendering is a separate gate.

Reproduce with `native/blitz/README.md`, `.github/workflows/native-blitz-proof.yml` and `native/blitz/compare_static.py`. Preserve original artifact hashes; do not turn low image differences into fictional CSS-property or GPU compliance claims.


## Durable source-backed screenshots

The source captures were subsequently copied from [successful run #43671027217](https://github.com/AVANT-ICONIC/calyra/actions/runs/43671027217) by the [one-time verification archive run #43675908339](https://github.com/AVANT-ICONIC/calyra/actions/runs/43675908339). The first archival attempt failed safely because the dashboard SHA-256 transcription was accidentally truncated; the corrected run verified all four full SHA-256 digests and pinned-source metadata before committing. The four exact native 1060x800 PNGs and eight corresponding JSON files are now permanent in [`docs/evidence/blitz/`](evidence/blitz/), with Git blob IDs checked against local original bytes. See [controls](evidence/blitz/blitz-controls-viewport.png), [dashboard](evidence/blitz/blitz-dashboard-viewport.png), [visual](evidence/blitz/blitz-visual-viewport.png), and [interaction](evidence/blitz/blitz-interaction-viewport.png). This does not alter the restricted/CPU-only assessment.


## First Blitz DOM and JavaScript behavior evidence

After the real Vello-CPU frames, actual headless Blitz `blitz-test-harness` and Boa `ScriptDocument` were separately compiled and exercised on pinned upstream 0.3.0-beta.4. Verified internal input shows typing, checkbox-label toggle and scrolling work; the select has **0×0px** despite three parsed options. Byte-identical original CALYRA JS runs without exceptions and opens the menu, but select value is empty, initial menu focus is lost, and Escape does not close it even after explicitly correcting focus. See [native input results](blitz-native-input-observations.md) and [original JS results plus timing diagnostic](blitz-original-js-observations.md). This is progress, not complete browser compatibility. OpenSpec task 4.1 remains unchecked.
