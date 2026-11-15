# Blitz HTML/CSS Stage A proof

**Goal:** test the *actual* Blitz `0.3.0-beta.4` HTML/CSS engine against the CALYRA reference. This is intentionally a **static browserless CPU-rendering test** first, not a GPU, JavaScript, native input, accessibility or performance claim.

## Source provenance

- Official source: https://github.com/DioxusLabs/blitz
- Pinned commit: `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` (November 15, 2026)
- Upstream example: `examples/screenshot.rs` (`cargo build --locked --release --example screenshot`)
- Upstream documented Rust version: 1.91.0; renderer stack in this path: Stylo + Taffy + Vello CPU (AnyRender)
- Upstream LICENSE: MIT OR Apache-2.0, with separate dependency obligations that must be reviewed before any distribution.
- No code is copied from Blitz, no custom renderer is substituted, no upstream source patch is applied.

## Why static HTML snapshots are required

The CALYRA browser reference uses JavaScript (`reference.js`) to choose one of four scenes via `.case.active`. Blitz's upstream *HTML screenshot* frontend does **not** execute the browser JS file. Loading `index.html` unchanged would therefore leave all sections hidden by CSS and mislabel a JavaScript omission as CSS incompatibility.

`prepare_static.py` deterministically generates one snapshot per fixture from **the original HTML and original CSS**. It only:

1. Removes the browser script tag, since JavaScript is not executed.
2. Marks exactly one `.case` active, sets `data-fixture`, `data-motion=off`, `data-ready=true` and selected navigation.
3. Inlines the **exact unchanged CSS text** in a `<style>` element (avoids unrelated network/file loading). The CSS's SHA-256 is preserved and checked.

The output records **`dom_patched=true`**, **`css_modified=false`**, **`js_executed=false`**, and an explicit asset-delivery adaptation. This is not full unchanged-page rendering. The original HTML source file is never overwritten.

## Reproduce without CI

Prerequisites: Rust 1.91.0+, cargo, Git, Python 3 with Pillow and jsonschema, Linux dependencies needed by Blitz's screenshot example (see upstream `AGENTS.md`).

```bash
git clone https://github.com/DioxusLabs/blitz.git /tmp/calyra-blitz
git -C /tmp/calyra-blitz checkout --detach 4f61cffacee50fe4f944ebe9d0470d9a5d3997e0
git -C /tmp/calyra-blitz rev-parse HEAD
python3 -m pip install Pillow jsonschema
python3 native/blitz/run_stage_a.py --source /tmp/calyra-blitz --build --fixture controls
python3 native/blitz/run_stage_a.py --source /tmp/calyra-blitz --fixture dashboard
python3 native/blitz/run_stage_a.py --source /tmp/calyra-blitz --fixture visual
python3 native/blitz/run_stage_a.py --source /tmp/calyra-blitz --fixture interaction
```

The script builds and runs the **unmodified upstream `screenshot` binary**. It saves the authentic full-size 2x PNG and a separately cropped/resampled 1060×800 comparison viewport, preserving hashes and explicit pixel-scale metadata. The native capture only succeeds when the executable exits zero, the expected newly generated upstream PNG exists, and pixel geometry/content checks pass. Every blocked attempt records JSON and leaves no stale capture.

`native/blitz/capture_reference.py` can optionally generate Chromium **static snapshot** references for the same adapted DOM. That is a separate *browser* baseline, never counted as a Blitz rendering result.

## Source audit and limitations

- Success means **Blitz actually produced rasterized HTML/CSS pixels**, not CSS parity.
- A nonblank image does **not** prove that every CSS selector/property was honored; inspect the image and compare the same static snapshot in Chromium.
- `examples/screenshot.rs` uses Vello CPU (`VelloCpuImageRenderer`). Do not call this a GPU proof.
- The screenshot API sets scale `2.0`, CSS-px height `800`, and uses a full-content screenshot with min-height. The normalized viewport is a separately derived crop/downsample for visual evaluation. This is not a timed benchmark.
- Browser JavaScript, form state changes, keyboard focus, pointer input, IME, accessibility APIs, native windowing, hardware GPU and production size/memory/startup remain unverified.
- CSS source hash is canonical, DOM adaptations are explicit, and third-party code remains in a pinned external checkout.

## State

The canonical CALYRA OpenSpec change is `openspec/changes/establish-native-css-feasibility/`. Do not check off task 3.2 until actual upstream Blitz execution (or a reproducible blocked build) is backed by logs. Keep the feature PR stacked on draft PR #1; do not silently turn this experiment into a production renderer.
