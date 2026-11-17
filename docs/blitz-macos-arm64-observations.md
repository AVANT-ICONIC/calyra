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

## Verified actual macOS BlitzShell / VelloWindowRenderer native window (2026-11-17)

**[Native macOS ARM64 CI #44018682112](https://github.com/AVANT-ICONIC/calyra/actions/runs/44018682112) PASSED every step**: the exact pinned original upstream Blitz repository compiled a temporary **untracked** CALYRA experiment using `blitz::launch_static_html(&html)`, creating a real **winit-based Mac window** and using upstream `VelloWindowRenderer`. The source was `native/blitz/experiments/calyra_native_window.rs`; **no tracked engine files or canonical authored HTML/CSS/JS were changed**. The HTML input was the same intentionally adapted and JavaScript-free Controls snapshot used by the headless CPU experiment.

CoreGraphics independently reported **Blitz executable PID 8893**, **layer-0 CGWindow ID 23**, native window bounds **800 × 628**. macOS `screencapture -x -l 23` captured actual 912 × 740 pixels (window including outer chrome/black margin). The compiled AppKit pixel inspector accepted the exact screenshot: **1,332/1,332 sampled interior pixels nonwhite** and **44 quantized colors**, not a blank window. Original screenshot SHA-256: `b00bb80f0b4297ab8b2e9cac69af61a7704028564698c457d14efc5dfc7a1133`; independently downloaded from the producing CI artifact and checked again.

**Original evidence**: [the actual native macOS window screenshot](evidence/blitz-macos-native-window/actual-blitz-native-window.png), [strict machine-readable native window verdict](evidence/blitz-macos-native-window/verified-native-window-result.json) and [complete original build/runtime/CSS snapshot logs with 25-file SHA-256 digest manifest](evidence/blitz-macos-native-window/). This is a legitimate native Blitz GUI window, **not** a Tauri or Chrome mock. The Winit/Vello code path was genuinely executed, but **the presence of `VelloWindowRenderer` does not prove actual hardware GPU acceleration**. An adapter/device/driver report and frame-time instrumentation would be needed for that claim.

### Resource observation: one diagnostic sample, not a benchmark

| Metric | Actual measured value |
|---|---:|
| Native process RSS (`ps`) | 117,504 KiB (114.75 MiB) |
| Native `proc_pid_rusage` resident size | 120,324,096 B (114.75 MiB) |
| Native `proc_pid_rusage` physical footprint | 215,599,552 B (205.61 MiB) |

These numbers were obtained once, during an **unoptimized debug** window build, after the window became visible. Physical footprint has different accounting than RSS and may include resources not expressed as resident mapped pages; the difference **must not be attributed to the GPU without independent instrumentation**. Neither metric is comparable as a speed/RAM winner against the earlier Tauri debug research process data (which included separately identified WKWebView child services and different content/viewport). A functionality-equivalent repeated same-host resource census remains an **OpenSpec 4.2 requirement**.

### Actual observed visual gaps versus the original Tauri reference

Visual inspection of the verified native window shows the CALYRA branding, sidebar, headings, input label and text, CSS positioning and text content. But the **Render priority select element has no visible widget/value** and the **Material intensity range appears as an unstyled white line without a visible thumb**. The exact same failings appear in the earlier 1060×800 headless Vello CPU controls render and had also been identified in Linux probes. The [original native WKWebView screenshot](evidence/tauri-macos-wkwebview-first-frame/tauri-macos-app-window.png) shows a visible `Balanced` native select and a discrete slider thumb. These two native-control gaps should be prioritized before treating Blitz as a realistic Tauri replacement. Screenshots have different native window widths/scales, so **do not compute or claim pixel parity from this comparison**.

**Still unverified:** original JavaScript/handler execution in the Blitz native window, real OS-delivered keyboard/pointer/IME, native per-control macOS Accessibility/VoiceOver, semantic form fidelity, independent WGPU/GPU hardware use, repeated matched native memory/startup/frame timing, full CSS support. This is a **restricted** but materially advanced Stage A GUI execution result; **OpenSpec 3.1/4.1/4.2 remain UNCHECKED**.
## Resolved follow-up: actual native window, source and test provenance

Upstream pinned `packages/blitz/src/lib.rs` exposes `blitz::launch_static_html(&str)` which uses BlitzShell, a native window event loop and `VelloWindowRenderer`; this is distinct from the headless Vello CPU path. The isolated source `native/blitz/experiments/calyra_native_window.rs` loads the *same static CALYRA snapshot* and invokes that upstream API. **[Actual macOS native-window CI #44018682112](https://github.com/AVANT-ICONIC/calyra/actions/runs/44018682112) succeeded**, as independently documented in the preceding section: a genuine PID-owned window and source-verified screenshot. A real window alone still cannot establish functional input, complete CSS/JavaScript parity or hardware GPU acceleration.

A real window still would not imply working original JS, keyboard/IME, macOS accessibility semantics, hardware GPU acceleration or superior performance. OpenSpec 3.1/4.1/4.2 remain unchecked. Source branch `feat/reference-fixtures`, draft PR #2, main unchanged.
