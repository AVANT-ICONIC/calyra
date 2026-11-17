# CALYRA: Verified native Blitz 0.3.0-beta.4 macOS ARM64 Vello CPU preflight

**Verified:** 2026-11-17 · [Actual GitHub Actions CI #44014447677](https://github.com/AVANT-ICONIC/calyra/actions/runs/44014447677) **PASS** on macOS 15.8.2 ARM64, Xcode 16.4, Rust 1.91.0 (pinned during workflow). **Immutable pinned upstream Git revision:** `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`. The original Blitz upstream `examples/screenshot.rs` executable was compiled and independently verified to be **arm64**. Native renderer: Blitz Stylo/Taffy and AnyRender **Vello CPU**.

## Four real Mac native pixels, independently source-checked

| Original CALYRA fixture | Validated native PNG | Captured image size | Runtime wall-time, diagnostic only |
|---|---|---|---:|
| Controls | [Mac CPU PNG](evidence/blitz-macos-arm64-cpu/blitz-controls-viewport.png) | 1060 × 800 | 0.627 s |
| Dashboard | [Mac CPU PNG](evidence/blitz-macos-arm64-cpu/blitz-dashboard-viewport.png) | 1060 × 800 | 0.183 s |
| Visual effects | [Mac CPU PNG](evidence/blitz-macos-arm64-cpu/blitz-visual-viewport.png) | 1060 × 800 | separately logged |
| Interaction | [Mac CPU PNG](evidence/blitz-macos-arm64-cpu/blitz-interaction-viewport.png) | 1060 × 800 | separately logged |

All **4/4** canonical style fixtures produced nonblank, validated native image output on real macOS ARM64; evidence contains both original 2× raw PNGs and normalized captures, four separate JSON results, original runtime/build logs and SHA-256 checks. [42 original verification files plus a separate hash manifest](evidence/blitz-macos-arm64-cpu/) were archived from the fully green actual runner.

The PNGs validate actual native rendering, not completeness of CSS support or visual parity. In each case:

- Canonical authored HTML hash: `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`
- Canonical authored CSS hash: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`
- Canonical authored JavaScript hash: `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`
- CSS **byte-for-byte unchanged** but inlined into a native HTML snapshot; DOM intentionally marks exactly one section active and disables motion; canonical browser JS intentionally omitted and not run.
- Each screenshot is the same declared **restricted static HTML workload** as the earlier Linux test, not a full CALYRA application.

## Why the runtime numbers are not a speed comparison

The diagnostic runtime recorded by the screenshot helper includes file reading, HTML parsing, layout, raster paint and PNG writing for one **headless, one-shot CPU** process, not a persistent native desktop application or first interactive frame. Tauri instead maintains a running WKWebView, native window, working original JavaScript, AX controls and out-of-tree WebKit WebContent/Networking processes. Their memory and readiness scopes differ. **Do not compare Blitz's short command execution with Tauri's startup, application RSS, FPS or native GPU without a matched workload and equivalent behavior.**

## Next bounded experiment: actual native window

Upstream pinned `packages/blitz/src/lib.rs` exposes `blitz::launch_static_html(&str)` which uses BlitzShell, a native window event loop and `VelloWindowRenderer`; this is distinct from the headless Vello CPU path. The isolated source `native/blitz/experiments/calyra_native_window.rs` loads the *same static CALYRA snapshot* and invokes that upstream API. [macOS native-window CI](https://github.com/AVANT-ICONIC/calyra/actions/workflows/blitz-macos-native-window-proof.yml) separately attempts to compile this as an untracked example in a clean pinned checkout, inspect a genuine app-owned CoreGraphics window and validate a native screencapture. The CI result, not the mere existence of the source file, determines whether this works.

A real window still would not imply working original JS, keyboard/IME, macOS accessibility semantics, hardware GPU acceleration or superior performance. OpenSpec 3.1/4.1/4.2 remain unchecked. Source branch `feat/reference-fixtures`, draft PR #2, main unchanged.
