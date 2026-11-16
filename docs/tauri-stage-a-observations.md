# CALYRA: actual Tauri 2 desktop shell feasibility (2026-11-16)

**Scope:** real Tauri 2 desktop application using the **original CALYRA HTML/CSS/JS**. A live **Linux Tauri WebKitGTK** executable and its **real X11 window screenshot** have been built and verified. **macOS WKWebView and macOS .app are not yet verified.** This is a restricted Stage A feasibility result, not a production release or speed benchmark.

## Source and trust boundary

The standalone [`adapters/tauri-reference/`](../adapters/tauri-reference/) implements a minimal system-WebView desktop host using `tauri::Builder::default().run(tauri::generate_context!())`, one native window, and direct `frontendDist="../../../fixtures"`. No Vite, HTML/CSS conversion, privileged Rust commands or replacement fixture sources.

- Original `index.html` SHA-256: `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`
- Original `reference.css` SHA-256: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`
- Original `reference.js` SHA-256: `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`
- Exact original dependency locks committed from the successful actual build via [CI #43938227700](https://github.com/AVANT-ICONIC/calyra/actions/runs/43938227700): CLI `@tauri-apps/cli 2.12.4`, Rust `tauri 2.12.6`, `tauri-build 2.7.5`.

## Actual executable and live window evidence

1. [Static adapter and dependency preflight #43936844079](https://github.com/AVANT-ICONIC/calyra/actions/runs/43936844079): **PASSED** source-hash checks, Python syntax, Rust formatting/Cargo manifest and exact npm CLI resolution. Static checks alone are not native evidence.
2. [Actual Tauri Linux compile/launch #43937455301](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301): **PASSED** full native Rust/Tauri compile and WebKitGTK 4.1 link, produced the real desktop executable and launched it under Ubuntu 24.04/Xvfb; application process remained alive. [Original 12-file logs/locks artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301/artifacts/14260796745).
3. [Initial native X11 pixel experiment #43938799768](https://github.com/AVANT-ICONIC/calyra/actions/runs/43938799768): **FAILED accurately**, not a fake pass. An actual native window XID was discoverable, but the generated PNG compressed to 2 KB or less, consistent with blank WebKitGTK compositing under Xvfb. The failed capture was rejected and preserved.
4. [Corrected real Tauri Linux screenshot CI #43939757930](https://github.com/AVANT-ICONIC/calyra/actions/runs/43939757930): **PASSED completely**, including deterministic source/lockfile compile and permanent screenshot archival. The corrected Xvfb environment starts Openbox and sets `WEBKIT_DISABLE_COMPOSITING_MODE=1` and `WEBKIT_DISABLE_DMABUF_RENDERER=1` alongside software graphics. The test captures via `xwd -id 4194307` directly from the running **Tauri native GTK/X11 window**, converts original X11 image to PNG, rejects a blank or undersized image, verifies SHA-256, and commits the real image with diagnostic metadata.
5. [Original captured Tauri window PNG](evidence/tauri-linux-window-pixels/tauri-native-window.png): genuine **1060×800**, **64,585 bytes**, **759 sampled distinct colors**, **SHA-256 `8d035f42495d2b5d0d006c37c2cba1e6124c9795768937d42e66b77b743dc6e9`**. [Verified capture metadata](evidence/tauri-linux-window-pixels/native-window-result.json) confirms the image's X11 window ID `4194307`, original app PID `9132`, true frame dimensions and experimental boundaries. Five exact generated evidence files are permanently committed under [`docs/evidence/tauri-linux-window-pixels/`](evidence/tauri-linux-window-pixels/).

This proves **real native Tauri desktop window creation and nonblank pixels** on Linux, not merely a Rust binary that stays alive. It does **not** independently assert that the rendered image matches all canonical CALYRA CSS/JS behaviors; the capture does not inspect the WebView DOM or simulate trusted OS input. Prior standalone Linux WebKitGTK reference CI validated original page semantics but is not a substitute for runtime introspection *inside the Tauri host*.

## macOS ARM64 gate remains open

[Actual macOS 15 ARM64 workflow #43936544580](https://github.com/AVANT-ICONIC/calyra/actions/runs/43936544580) initially remained queued **15 minutes and was cancelled without an allocated macOS runner or any job steps**. It did not reach Checkout/Rust or attempt compilation. One targeted retry was requested (attempt 2); only report a macOS `.app` or WKWebView runtime after a run genuinely builds and records that evidence.

The [macOS bundle workflow](../.github/workflows/tauri-macos-arm64-reference.yml) would produce an unsigned debug `.app` if a runner is assigned and the build succeeds. An app bundle alone does **not** establish successful first frame, macOS `innerWidth` parity, user input, accessibility, IME, GPU behavior or comparative startup/memory performance. The actual target remains Apple Silicon WKWebView on the same hardware as eligible native engines.

## Decision

- **Verified:** original source unchanged; pinned Tauri 2 dependencies; real native Linux Tauri compile/link/start; verified real X11 GTK/WebKitGTK window pixels; safe archival of genuine source and image evidence.
- **Not verified:** actual macOS Tauri build and `.app`, WKWebView first frame on macOS, Tauri-hosted JavaScript semantics on Linux, real OS keyboard/pointer, IME/accessibility, hardware GPU, color-managed visual parity, five repeated matched memory/CPU/startup samples.
- **OpenSpec task 3.1:** **UNCHECKED**, since macOS WKWebView path is a required target and original JavaScript correctness inside actual Tauri runtime needs verification. **4.1 and 4.2:** **UNCHECKED**.
- **Next productive check:** acquire a working macOS ARM64 runner or authorized local macOS execution; only then test real `.app` / WKWebView frame, behavior, and performance. A browserless speed advantage cannot be concluded from this evidence.

**Repository constraint:** work only on `feat/reference-fixtures`, preserve existing OpenSpec `establish-native-css-feasibility` and PR #2 DRAFT/UNMERGED. Never merge to `main` as a side effect of this evidence.
