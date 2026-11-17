# CALYRA: actual Tauri 2 desktop shell feasibility (updated 2026-11-17)

**Scope:** real Tauri 2 desktop application using the **original CALYRA HTML/CSS/JS**. A live **Linux Tauri WebKitGTK** executable and its **real X11 window screenshot** have been built and verified. **The macOS ARM64 .app build, native process launch, and a real app-owned WKWebView first frame are verified; original JS event handlers have been validated inside a genuine WKWebView, but OS-delivered keyboard/pointer and IME remain unverified.** This is a restricted Stage A feasibility result, not a production release or speed benchmark.

## Direct native WebKit helper process identities (2026-11-17)

An earlier five-run ownership census [#44007500896](https://github.com/AVANT-ICONIC/calyra/actions/runs/44007500896) **PASSED its actual native window/resource tests**, but **correctly attributed zero helper processes**. Using optional responsibility_get_pid_responsible_for_pid (private OS API), macOS returned the same CI runner responsible PID (922) for Tauri itself and new WebKit.WebContent/Networking processes. Temporal coincidences of 2/2/7/2/2 new helpers were not enough to identify individual ownership. The [original five-run raw evidence](evidence/macos-webkit-helper-attribution/) is preserved. The first attempted run [#44007387344](https://github.com/AVANT-ICONIC/calyra/actions/runs/44007387344) failed before measurement due to an absolute-path concatenation error; the corrected run is the only source for this finding.

To resolve identity directly, a **new, opt-in, macOS-only diagnostic build** uses Tauri's real with_webview handle to query WKWebView's **private _webProcessIdentifier**, WKWebsiteDataStore's **private _networkProcessIdentifier**, and optional **_gpuProcessIdentifier** using Objective-C dynamic selectors. These are genuine upstream WebKit internal selectors (used by WebKit's own MiniBrowser), NOT supported public APIs. They are **compile-time excluded** from normal CALYRA builds. The ordinary reference app and canonical authored fixture HTML/CSS/JS stay byte-for-byte unchanged; no extra privileged IPC surface is created.

**[Direct native Mac ARM64 CI #44008089167](https://github.com/AVANT-ICONIC/calyra/actions/runs/44008089167) PASSED**: the real Tauri app returned process identifiers from its own running WKWebView, and the test independently matched those exact PIDs to executing system WebKit binaries. Original [JSON/process table/libproc outputs and SHA-256 provenance](evidence/macos-wkwebview-direct-process-ids/) were committed on the research branch.

| Verified process | PID | ps RSS (bytes) | libproc resident (bytes) | libproc physical footprint (bytes) |
|---|---:|---:|---:|---:|
| Tauri UI process | 4184 | 86,114,304 | 86,130,688 | 17,041,664 |
| WKWebView-owned WebContent | 4198 | 52,740,096 | 52,740,096 | 27,625,408 |
| WKWebView-owned Networking | 4202 | 18,874,368 | 18,874,368 | 5,309,632 |

Note: 84,096 KiB ps RSS for the main process equals 86,114,304 bytes, slightly different from libproc's 86,130,688 bytes because they were sampled at different moments. This is not a data inconsistency. **UI + WebContent + Networking libproc resident values sum arithmetically to 157,745,152 bytes (150.44 MiB)**. However RSS includes shared mappings and is **not a unique application RAM footprint**. The 47.66 MiB arithmetic sum of native per-process phys_footprint is a different metric, likewise not independently validated as a unique application budget. WebKit GPU PID was **null**; do not assume there was no system GPU work.

**Evidence bounds:** one debug/research binary, one actual Tauri app window, original canonical content unmodified. A direct PID lookup identifies the WebContent and Networking processes on this machine at this moment; it does not prove identical PIDs or resource costs across runs or on other macOS versions. Private WebKit methods may disappear, change, or be disallowed and must never be required by the production library. No trusted OS keyboard/pointer, IME/a11y, matched optimized-build memory or browserless speed advantage established. OpenSpec tasks 3.1, 4.1 and 4.2 remain unchecked.
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

## Independent real Tauri-versus-system-WebKitGTK raster comparison

[Source-hash-verified comparison CI #43941143858](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941143858) **PASSED end-to-end** using the archived [actual Tauri GTK/X11 window PNG](evidence/tauri-linux-window-pixels/tauri-native-window.png) (SHA-256 `8d035f42495d2b5d0d006c37c2cba1e6124c9795768937d42e66b77b743dc6e9`) and the independently archived [real system-WebKitGTK controls baseline](evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default-initial.png) (SHA-256 `22b9bb1b3369bc3fd78773e580bcb57e306014eb9368bba1c8bbae27655cdbad`). Both are **1060×800** canonical Controls initial views, not regenerated stand-ins.

A separate lightweight PIL verifier recomputed direct absolute RGB differences. **1,692 of 848,000 pixels differ at per-channel threshold 12/255 (0.1995%)**; **99.8005%** are below that threshold. Exact matches at threshold 12 across the scoped **Select ROI (20,400 px)** and **Range ROI (31,500 px)**: zero differing pixels in each. Header ROI: 235/90,100 pixels differ; sidebar ROI: zero. The mean absolute RGB-channel difference over the full frame is **0.098917/255**. Verified [structured region report](evidence/comparisons/tauri-webkitgtk-controls/tauri-vs-webkitgtk-comparison.json), [three-panel original/diff montage](evidence/comparisons/tauri-webkitgtk-controls/tauri-vs-webkitgtk-montage.png), [raw absolute difference PNG](evidence/comparisons/tauri-webkitgtk-controls/tauri-vs-webkitgtk-raw-difference.png) and source digest manifest are archived byte-exact under [`docs/evidence/comparisons/tauri-webkitgtk-controls/`](evidence/comparisons/tauri-webkitgtk-controls/).

**Interpretation:** The actual Tauri Linux shell faithfully paints the initial Controls view very close to the standalone WebKitGTK backend under these Xvfb conditions; no visibly distinct native-control region was observed. The two screenshots are **not** binary identical; both were produced in different GitHub CI jobs and capture pipelines (Tauri X11 `xwd` versus native WebKit snapshot), without locked font/AA/color settings or pixel alignment. Do not call 99.8% CSS support, hardware-GPU parity, actual OS input coverage, macOS pixel parity, or Tauri-versus-Blitz performance. This comparison establishes a credible **actual Tauri** system-WebView visual correctness anchor for a single Linux Controls frame.

## macOS ARM64 gate remains open

[Original macOS 15 ARM64 workflow #43936544580](https://github.com/AVANT-ICONIC/calyra/actions/runs/43936544580) initially remained queued **15 minutes and was cancelled without an allocated macOS runner or any job steps**. It did not reach Checkout/Rust or attempt compilation. One targeted retry was requested (attempt 2); only report a macOS `.app` or WKWebView runtime after a run genuinely builds and records that evidence.

The [macOS bundle workflow](../.github/workflows/tauri-macos-arm64-reference.yml) would produce an unsigned debug `.app` if a runner is assigned and the build succeeds. An app bundle alone does **not** establish successful first frame, macOS `innerWidth` parity, user input, accessibility, IME, GPU behavior or comparative startup/memory performance. The actual target remains Apple Silicon WKWebView on the same hardware as eligible native engines.

## Mac compile failure and corrected reproducible retry

The original [macOS job #43936544580](https://github.com/AVANT-ICONIC/calyra/actions/runs/43936544580) was manually rerun once after the first attempt timed out while queued. The **second attempt obtained a genuine ARM64 macOS 15 runner**, verified original CALYRA source, built the macOS `.icns` icon, installed Tauri CLI, and compiled macOS dependencies up to the Tauri application proc macro. It **failed** with exact compiler error:

```
error: proc macro panicked
  --> src/main.rs:7:14
   = help: message: failed to open icon .../src-tauri/icons/icon.png: No such file or directory (os error 2)
```

This was a missing conventional **Tauri macro icon**, not a verified macOS platform blocker. `prepare_macos_icon.py` now creates deterministic default `icons/icon.png` alongside the existing `icons/icon.icns`, byte-identical to the original generated PNG. Independent [source/icon preflight #43942204867](https://github.com/AVANT-ICONIC/calyra/actions/runs/43942204867) **PASSED** actual 1024×1024 PNG header, byte equality, and original source hashes. Updated macOS CI uses pinned `npm ci` and Tauri `--locked` build, and checks both icons explicitly: [corrected macOS run #43941982471](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941982471). **Do not represent that run as a working `.app` or macOS WKWebView without verifying its final result.** Failed original logs retained.

## Actual Apple Silicon bundle success and correctly classified smoke failure (2026-11-17)

The corrected [actual Tauri macOS build #43941982471](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941982471), job `133561611527`, ran on **macOS-15 arm64**: `npm ci`, locked Tauri/Rust compilation, and native macOS `.app` bundling all **PASSED**. Tauri reported **26.82 MiB** for the debug `CALYRA Stage A Reference.app`. A separate successful inspection step read `Contents/Info.plist`, found the real executable and confirmed `arm64` with Apple's `lipo` tool. The original 18-file archive including the zipped unsigned `.app`, source/lock hashes, bundle report and launch log is at [artifact #14263945995](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941982471/artifacts/14263945995).

**The job as a whole FAILED** in the optional launch probe, not compilation: `open -a` was passed `adapters/tauri-reference/.../CALYRA Stage A Reference.app`, a relative path containing slashes, and macOS Launch Services returned `Unable to find application named ...`. The shell's inherited `-e` also prevented the intended best-effort exit-code report. This does **not** demonstrate a runtime crash or a WKWebView failure.

On the research branch, commit `778f3640dbb224f4bb139ae7fa2caef80f5f208a` changes the smoke check to resolve the `.app` absolute path, use `open -n -a`, and capture the return code and matching process names without misclassifying the separate compiled bundle. The workflow change triggers a further runner attempt; **its result is unverified at the time this report is written**.

**Acceptance boundary:** a real arm64 macOS desktop bundle is now built and archived. No on-host WKWebView pixels, Tauri-hosted original JS semantics, OS keyboard/IME/accessibility, GPU or repeatable CPU/RAM measurements have been measured. OpenSpec **3.1, 4.1 and 4.2 remain unchecked**. Preserve the raw evidence and the draft PR; do not infer a browserless rendering advantage.

## Five original Apple Silicon app-owned-window RSS observations (2026-11-17, NEWEST)

[Native macOS CI #44002257080](https://github.com/AVANT-ICONIC/calyra/actions/runs/44002257080) **PASSED end-to-end**. This reused the SHA-256-verified, unchanged normal Tauri .app from [build #43996164957](https://github.com/AVANT-ICONIC/calyra/actions/runs/43996164957) on an actual macos-15 ARM64 runner. The new harness/macos_tauri_resource_baseline.py launched the executable five separate times and required its own genuine CGWindow for each PID, using the compiled native window inspector.

At approximately **12 seconds after each distinct launch**, one macOS ps snapshot recorded the **Tauri parent-process resident set**:

| Trial | App PID | OS window ID | Parent RSS (KiB) |
|---|---:|---:|---:|
| 1 | 1690 | 23 | 79,552 |
| 2 | 1754 | 32 | 84,528 |
| 3 | 1876 | 40 | 85,056 |
| 4 | 2089 | 47 | 84,720 |
| 5 | 2239 | 54 | 86,320 |

**Parent RSS median: 84,720 KiB**, range **79,552 to 86,320 KiB**. Exact original observations, native logs for all trials, source and executable SHA-256, environment, and manifest are committed to [the permanent evidence folder](evidence/tauri-macos-resource-census/). [CI artifact #14292403562](https://github.com/AVANT-ICONIC/calyra/actions/runs/44002257080/artifacts/14292403562) is a short-term duplicate.

**Important:** ps RSS includes shared pages and is not private footprint. WKWebView WebContent, Networking and GPU helper processes are potentially not descendants of the app PID, and have **not been reliably attributed**. Therefore this is NOT total Tauri memory and NOT a matched benchmark against Blitz, Chromium or any other engine. CPU percent is instantaneous only. First window observations include inspection overhead, not first meaningful pixels or JavaScript readiness. These launches share a warmed CI host, so they are NOT controlled cold starts. OpenSpec task 4.2 remains unchecked.

**Failed attempt #44001984660:** Cross-run artifact download received an improperly escaped GitHub Actions token expression and returned Bad credentials. Fix commit c9a2e96aa1206a699dee2c8bfeb725b19d012d67 corrected that workflow wiring; the separately successful run above is the actual verified resource evidence.

## Apple Silicon OS-input permission preflight (2026-11-17)

[Mac CI #44001280702](https://github.com/AVANT-ICONIC/calyra/actions/runs/44001280702) **PASSED** a prompt-free, event-free native inspection. AXIsProcessTrusted, CGPreflightPostEventAccess, CGPreflightListenEventAccess, and CGPreflightScreenCaptureAccess each returned true for that Swift runner process. [Original permission results](evidence/macos-os-input-preflight/preflight.json) are archived. **No actual OS mouse/keyboard events were posted or observed**, so OS input, IME and accessibility acceptance remain unverified. An unexecuted OS-injection draft was removed rather than left as apparent proof.

## Verified original JavaScript inside genuine macOS Tauri WKWebView (2026-11-17, NEWEST)

[Native Apple Silicon CI #44000680977](https://github.com/AVANT-ICONIC/calyra/actions/runs/44000680977) **PASSED all steps**, including actual Rust/Tauri opt-in-feature compilation, live execution and independent strict verification of **29/29 original DOM/JavaScript handler assertions**. Tauri invoked `eval_with_callback` only from an `on_page_load(PageLoadEvent::Finished)` callback inside its own OS WKWebView; those results returned to Rust and were saved as original raw callback records. No browser automation stand-in, Chromium driver or rewritten `reference.js`.

- **Controls 15/15 PASS:** original `document.body.dataset.ready` and section state, initial input/select/range/output values, simulated slider `input` event and original listener, original Apply click status, original Reset click status, and full reset of name, select, range, output and checkbox.
- **Interaction 14/14 PASS:** the SAME Tauri window navigated to the canonical `interaction` fixture (not an artificial hidden DOM test), with menu open/ARIA/focus, synthetic document Escape, focus restoration, command click/close, focus destination and scroll offset.
- **Native WebKit origin:** `tauri://localhost/index.html?fixture=controls&motion=off` and `tauri://localhost/index.html?fixture=interaction&motion=off`; AppleWebKit/605.1.15 user agent; Mac CSS viewport **1024×653**, `devicePixelRatio=1`. This is deliberately not asserted to match 1060×800 Linux CSS viewport or prove pixel parity.
- **Isolation:** `--features stage-a-js-probe` builds `stage_a_js_probe.rs` with a **test-only** Rust WKWebView callback; default Tauri app's `main.rs` retains original bridge-free behavior. No extra privileged IPC commands. Canonical HTML, CSS and JS SHA-256 remain unchanged.
- **Archived original source-backed output:** [`docs/evidence/tauri-macos-native-js/`](evidence/tauri-macos-native-js/) contains the raw callback records, strict 29-test verifier summary, native app/build logs, runner/environment, SHA-256 source and executable digests and self-hashed archive manifest. CI wrote this to the feature branch with a non-force rebase/push after green verification. Artifact [#14291623001](https://github.com/AVANT-ICONIC/calyra/actions/runs/44000680977/artifacts/14291623001).
- **Not proved:** actual OS-delivered physical keyboard or pointer, IME composition, screen-reader accessibility, hardware GPU, cold/warm startup benchmarks, whole-process/private-resident memory or native browserless alternatives. These tests use **synthetic DOM-dispatched events inside a real OS WKWebView**, not native input events.

OpenSpec **3.1 remains unchecked** because full real OS input and source-defined reference acceptance are incomplete. **4.1/4.2 unchecked**. PR #2 remains DRAFT/UNMERGED on `feat/reference-fixtures`; `main` untouched.

## Archived live macOS WKWebView first frame (2026-11-17, NEWEST)

The prior Mac app build's absolute-path Launch Services fix was independently verified in [native ARM64 CI #43996164957](https://github.com/AVANT-ICONIC/calyra/actions/runs/43996164957): all job steps passed; `open -n -a` returned 0; genuine Tauri executable PID 3944 remained alive after 5 seconds. The unsigned debug application artifact is [#14290436244](https://github.com/AVANT-ICONIC/calyra/actions/runs/43996164957/artifacts/14290436244).

A separately implemented **prebuilt-app**, no-Rust-rebuild macOS proof then ran in [CI #43996877529](https://github.com/AVANT-ICONIC/calyra/actions/runs/43996877529), which **PASSED**. Real macOS 15.8.2 arm64 host: exact original bundle ZIP hash and unmodified fixture hashes checked, real app process **PID 1497** located, CoreGraphics found its foreground normal layer-0 window **CGWindow ID 28**, and `screencapture -x -l 28` captured **the actual on-screen Tauri WKWebView Controls UI**. Original PNG **1136×793** (display-scale screenshot of an app window listed as 1024×681 window units), SHA-256 **`fe0ba545fa469f84211ab79aebbe90d1df8d7fc6e2a940336c8292c26f110d24`**. Native AppKit pixel validation accepted 40 quantized distinct colors across 1,444 sampled interior pixels. Direct human image inspection further confirms visible CALYRA title bar, sidebar, Controls heading and original text/select/range UI. **This is real WKWebView pixels in the Tauri host**, not standalone WebKitGTK, Chrome or a mocked screenshot.

[Independent archival CI #43997275993](https://github.com/AVANT-ICONIC/calyra/actions/runs/43997275993) **PASSED** exact PNG SHA, PNG dimensions, owner PID/window ID, original source hashes and architecture verification, then committed all **10 byte-exact original screenshot/build/window evidence files** plus `provenance.json` to [permanent feature-branch archive](evidence/tauri-macos-wkwebview-first-frame/). The earlier [archival run #43997214282](https://github.com/AVANT-ICONIC/calyra/actions/runs/43997214282) passed evidence verification but failed staging because `docs/evidence` is gitignored; its corrected successor force-added **only** this evidence directory. Preserved original Git screenshot blob SHA: `8078a5780e4c98ca239c3c372980bd179c5c05c0`.

**What this proves:** an ARM64 Tauri app packages, launches and visibly paints canonical CALYRA controls in its actual macOS system WKWebView. **What it does not prove:** the original page JS event handlers executing correctly inside this Tauri host, physical OS keyboard/pointer/IME/accessibility, GPU path, quantitative CSS fidelity compared at identical viewport/font settings, repeated same-machine CPU/RAM/speed, or a browserless rendering advantage. The single 1136×793 Mac screenshot cannot be directly compared as pixel parity to the 1060×800 Linux reference without matching viewport/scale/pixel policy.

Keep existing OpenSpec **3.1, 4.1, 4.2 UNCHECKED** until their full functional/measurement acceptance is satisfied. Keep draft PR #2 unmerged and `main` untouched.

## Decision

- **Verified:** original source unchanged; pinned Tauri 2 dependencies; real native Linux Tauri compile/link/start; verified real X11 GTK/WebKitGTK window pixels; safe archival of genuine source and image evidence.
- **Not verified:** Tauri-hosted JavaScript semantics on macOS or Linux, real OS keyboard/pointer, IME/accessibility, hardware GPU, color-managed visual parity, five repeated matched memory/CPU/startup samples.
- **OpenSpec task 3.1:** **UNCHECKED**, since macOS WKWebView path is a required target and original JavaScript correctness inside actual Tauri runtime needs verification. **4.1 and 4.2:** **UNCHECKED**.
- **Next productive check:** validate original fixture JavaScript behavior inside the actual Tauri WKWebView and trusted OS input, then repeat controlled resource measurements on matched hardware. The macOS first-frame gate is complete; functional and performance gates are not. A browserless speed advantage cannot be concluded from this evidence.

**Repository constraint:** work only on `feat/reference-fixtures`, preserve existing OpenSpec `establish-native-css-feasibility` and PR #2 DRAFT/UNMERGED. Never merge to `main` as a side effect of this evidence.
