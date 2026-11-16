# CALYRA Stage A: actual Tauri 2 host (macOS WKWebView)

This adapter packages the **original** HTML, CSS and JavaScript under the canonical repository `fixtures/` directory. It creates a **real Tauri 2** application using the macOS **WKWebView** system runtime, not a browserless CALYRA renderer and not a hand-written Swift substitute.

## Build on a Mac (Apple Silicon)

From `adapters/tauri-reference/`:

```sh
python3 verify_source.py
python3 prepare_macos_icon.py
npm ci --no-audit --no-fund
npm run build:macos -- --debug
```

The resulting Tauri `.app` is under `src-tauri/target/debug/bundle/macos/`. For an optimized binary omit `--debug`; do not use a debug-build launch time or RSS to rank CALYRA against a release-built candidate.

The host has **no Vite, no transformed CSS, no copy of the fixture files, no Rust IPC commands and no additional renderer widgets**. The Tauri build embeds directly from `../../../fixtures` and loads `index.html?fixture=controls&motion=off` as the initial WebView URL.

To inspect a fixture manually, click the existing in-app navigation for Dashboard, Visual or Interaction. The author-authored JavaScript still uses its original query parameters and DOM behavior.

## Verification boundaries

- `verify_source.py` checks canonical source hashes and exact build config, **not** that the native app compiles or opens.
- The GitHub `macos-15` ARM64 job attempts to build a real Tauri `.app`, verify its bundle/arm64 executable, record package size and other metadata, and perform a **best-effort** real app launch. A successful bundle is not proof of first meaningful pixels, real keyboard input, screenshot parity, accessibility, IME or tested launch-time performance.
- GitHub-hosted macOS GUI/WindowServer and automation permissions may prevent a real runtime screenshot or trusted event replay. Any such failure is recorded, never silently substituted by a Chromium screenshot.
- **Exact dependency locks are now committed:** `package-lock.json` pins Tauri CLI **2.12.4**; `src-tauri/Cargo.lock` pins Rust `tauri 2.12.6` and `tauri-build 2.7.5`. They were archived from [successful real Linux native compile #43937455301](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301) by [verified lock-preservation CI #43938227700](https://github.com/AVANT-ICONIC/calyra/actions/runs/43938227700). Use `npm ci` on subsequent builds, and fail if the Cargo lock changes unexpectedly.
- Not signed or notarized for distribution. This research branch is **not a shipped product**.

Compare **same machine, same build profile, same fonts and framebuffer** in at least five independent runs for startup/RSS/CPU. Also account for system-provided WebKit processes; comparing only the parent app to a self-contained renderer is not a fair memory benchmark.

See `openspec/changes/establish-native-css-feasibility/` task 3.1. The task remains unchecked until a real Tauri macOS WKWebView frame and original JS behavior are verified.

## Verified Linux native compile, separate from macOS

[Native Tauri/GTK CI #43937455301](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301) passed: a **real Tauri 2 Linux native executable** was compiled with Ubuntu 24.04 development libraries for WebKitGTK 4.1, CLI 2.12.4, and launched under Xvfb. Its process remained alive over the smoke-check interval. Original CALYRA asset digests were verified. [12 original logs and dependency receipts](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301/artifacts/14260796745) preserve build/runner state.

This is **actual Tauri build and process start**, not a validated first frame, WKWebView on macOS, physical input, GPU, accessibility or resource win. The dedicated Apple Silicon workflow `tauri-macos-arm64-reference.yml` is a distinct gate; its macOS runner must actually start and finish before we claim a `.app` was produced.
