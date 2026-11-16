# CALYRA Stage A: actual Tauri 2 host (macOS WKWebView)

This adapter packages the **original** HTML, CSS and JavaScript under the canonical repository `fixtures/` directory. It creates a **real Tauri 2** application using the macOS **WKWebView** system runtime, not a browserless CALYRA renderer and not a hand-written Swift substitute.

## Build on a Mac (Apple Silicon)

From `adapters/tauri-reference/`:

```sh
python3 verify_source.py
python3 prepare_macos_icon.py
npm install --no-audit --no-fund
npm run build:macos -- --debug
```

The resulting Tauri `.app` is under `src-tauri/target/debug/bundle/macos/`. For an optimized binary omit `--debug`; do not use a debug-build launch time or RSS to rank CALYRA against a release-built candidate.

The host has **no Vite, no transformed CSS, no copy of the fixture files, no Rust IPC commands and no additional renderer widgets**. The Tauri build embeds directly from `../../../fixtures` and loads `index.html?fixture=controls&motion=off` as the initial WebView URL.

To inspect a fixture manually, click the existing in-app navigation for Dashboard, Visual or Interaction. The author-authored JavaScript still uses its original query parameters and DOM behavior.

## Verification boundaries

- `verify_source.py` checks canonical source hashes and exact build config, **not** that the native app compiles or opens.
- The GitHub `macos-15` ARM64 job attempts to build a real Tauri `.app`, verify its bundle/arm64 executable, record package size and other metadata, and perform a **best-effort** real app launch. A successful bundle is not proof of first meaningful pixels, real keyboard input, screenshot parity, accessibility, IME or tested launch-time performance.
- GitHub-hosted macOS GUI/WindowServer and automation permissions may prevent a real runtime screenshot or trusted event replay. Any such failure is recorded, never silently substituted by a Chromium screenshot.
- `npm install` creates `package-lock.json` and `src-tauri/Cargo.lock` during first build. The CI archives dependency lockfiles/hashes for reproducibility. The Tauri CLI is pinned to version **2.12.4**, while the Rust Tauri 2 dependency is pinned by the generated `Cargo.lock`; future releases should commit the lockfiles and use `npm ci` / `cargo --locked`.
- Not signed or notarized for distribution. This research branch is **not a shipped product**.

Compare **same machine, same build profile, same fonts and framebuffer** in at least five independent runs for startup/RSS/CPU. Also account for system-provided WebKit processes; comparing only the parent app to a self-contained renderer is not a fair memory benchmark.

See `openspec/changes/establish-native-css-feasibility/` task 3.1. The task remains unchecked until a real Tauri macOS WKWebView frame and original JS behavior are verified.
