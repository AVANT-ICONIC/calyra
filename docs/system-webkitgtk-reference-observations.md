# CALYRA: Linux system-WebKitGTK reference and first Blitz image comparison

**Date:** 2026-11-16. **Working branch:** `feat/reference-fixtures`. **OpenSpec:** `establish-native-css-feasibility`. Scope is a reproducible Stage A compatibility/visual preflight, **not** Tauri packaging or performance testing.

## Why the system-WebView baseline matters

Tauri 2 uses the system WebKit browser engine on both macOS and Linux, but different platform wrappers: **WKWebView on macOS** and **WebKitGTK on Linux**. Official references: [Tauri WebView versions](https://tauri.app/reference/webview-versions/) and [Tauri Linux prerequisites](https://v2.tauri.app/start/prerequisites/).

The CALYRA adapter runs the **actual Linux WebKit2GTK-4.1 engine** in an undecorated GTK3/X11 window under Xvfb, **not a Tauri binary**. It serves the canonical `fixtures/index.html`, `reference.css` and `reference.js` *unmodified* via local loopback HTTP. A JavaScript harness reads native WebKit DOM-computed CSS and tests programmatic DOM actions; scripted `Element.click()` and constructed `KeyboardEvent` objects **are not real X11 user input**.

The code is `harness/run_webkitgtk_reference.py` and its independent verifier `harness/verify_webkitgtk_reference.py`. Its schema is the existing `harness/adapter-contract.schema.json` (`calyra.adapter-result.v1`), with honest `system-webview`, `restricted`, `measured_performance=false` classification.

## Successful engine backend execution

- **[Actual Ubuntu 24.04 WebKitGTK CI #43930684985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43930684985): complete SUCCESS.** OS WebKit2GTK **2.52.6** (Ubuntu package `2.52.6-0ubuntu0.24.04.1`), GTK3 **3.24.41**, X11 virtual display, explicitly software GL. This is not hardware GPU benchmarking.
- **6/6 scenarios** succeeded and independently validated: controls, dashboard, visual effects, interaction, pre-opened interaction menu (each 1060×800), plus dashboard responsive view at 390×844. **8/8 useful screenshots** passed dimensions, digest and nonblank-pixel checks. Preserved [27 exact original run files](evidence/system-webkitgtk-reference/) with screenshots, scripted-state traces, system packages, source checksums and two diagnostic failed GDK grabs.
- Original canonical HTML/CSS/JS hashes were verified at runtime: HTML `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`, CSS `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`, JavaScript `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`.
- Actual WebKit JavaScript assertions confirmed the selected fixture and nav, responsive `@media(max-width:650px)` Grid → Block behavior, absence of horizontal overflow, text/select/range/checkbox programmatic mutations and Apply status, menu open and Escape handler, focus restoration and internal scrolling. **None of this constitutes physical OS input testing or accessibility validation.**

### Why GDK screenshots initially failed

The first attempted run [#43929273980](https://github.com/AVANT-ICONIC/calyra/actions/runs/43929273980) incorrectly expected Grid at 390px; the canonical CSS explicitly switches to `display:block` at ≤650px. Corrected as a **test expectation error**, not a renderer defect.

Subsequent window-pixbuf capture attempts under Xvfb intermittently recorded a uniform pale image, notably for Visual effects, **while native DOM/CSS/JS state remained correct**. Captures are now checked for color diversity *before* being accepted. If a GDK window grab is blank, the runner preserves the failed bytes as `*-gdk-blank.png` and calls WebKit's asynchronous **native `WebView.get_snapshot` API**, then verifies the resulting real WebKit page pixels. Documentation: [WebKit2GTK get_snapshot](https://webkitgtk.org/reference/webkit2gtk/stable/method.WebView.get_snapshot.html). The successful CI archived both failed and recovered snapshots, so no silently substituted fake frame is presented. The root cause of the Xvfb/GDK blank grab itself is **not conclusively diagnosed**.

## First exploratory archived screenshot comparison

**[Comparison CI #43931943330](https://github.com/AVANT-ICONIC/calyra/actions/runs/43931943330) succeeded**, using *already archived genuine original screenshots*, without recompiling either engine:

- **Blitz** (source-pinned `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` with experimental noneditable SelectData + Vello CPU): `docs/evidence/blitz-select-typography/typography-before.png`, native producer [#43919838241](https://github.com/AVANT-ICONIC/calyra/actions/runs/43919838241).
- **WebKitGTK 2.52.6** real browser-backed reference: `docs/evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default-initial.png`, native producer [#43930684985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43930684985).
- Both represent **controls, initial state, 1060×800 CSS pixels, motion off, Balanced option** with unchanged authored HTML/CSS/JS.
- **51,944 of 848,000 pixels (6.1255%)** differ by ≥12/255 in any RGB channel, and **778,478** are exactly equal bytewise as RGB. Mean per-channel absolute difference **4.619758**. These are image diagnostics, **NOT** `93.9% browser compatibility` or any measure of performance.

### Spatial diagnostics at RGB threshold 12

| Region | Bounding box (x0,y0,x1,y1) | Pixel-change rate |
| --- | --- | ---: |
| Header | (0,0,1060,85) | 1.73% |
| Sidebar | (0,85,258,800) | 0.98% |
| Upper main content | (258,85,1060,450) | 3.72% |
| Control surface | (258,450,1060,800) | 13.42% |
| Select control | (670,465,1010,525) | **79.69%** |
| Range/slider area | (310,585,1010,630) | **24.72%** |

**Visual observation:** the shared background/structure dominates the pixel match; meaningful incompatibilities cluster in text antialiasing and especially native controls. The experimental Blitz select lacks the WebKitGTK native dropdown appearance; the range input paints like a plain bar in this CPU experiment. These are distinct Stage A compatibility findings, not mere numerical noise.

[Original pixel difference, labelled visual montage, machine-readable regions and source hashes](evidence/comparisons/webkitgtk-blitz-controls/) are permanently archived separately from the unchanged original PNGs.

**Methodology caveats:** the two engine screenshots came from **different CI jobs/runners**, not a locked common font installation, graphics profile or simultaneous capture. Fonts, antialiasing, subpixel positioning and OS environments can differ. Regions were manually selected and overlap. No image-registration alignment, feature-by-feature Chromium fidelity check, real user input, accessibility API, native packaged Tauri executable, macOS WKWebView, hardware GPU, startup/idle measurements, process-tree PSS/RSS or energy benchmark was produced.

## Practical decision

1. **Keep Blitz as a restricted promising CSS/scene renderer**, not a full native GUI toolkit. The latest successful native experiments prove a noneditable selected-label and CSS typography text shaping, but interactive control/widget semantics remain incomplete. A 6% global pixel difference does not override 80% difference in the select rectangle.
2. **Keep the system WebView reference as the correctness anchor**, not as a claimed speed winner. WebKitGTK is a Linux backend proxy only; Tauri packaging and actual **macOS WKWebView** remain **OpenSpec task 3.1 incomplete**.
3. **Next high-signal Stage A work:** package and run the canonical fixture in a real Tauri 2 desktop window on a target macOS machine, record OS input/accessibility and whole process-tree resources (including WebContent helper processes). In parallel, independently probe **Electrobun 2.x's experimental non-WebView GPU UI** rather than treating its standard WebView option as native.
4. **Performance work must wait until comparable conditions:** at least five runs per workload, same viewport/state/fonts/hardware, explicit cold/warm readiness, app and helper-process RSS/PSS, idle/active CPU, GPU classification and package bytes. Do not rank unmeasured alternatives.

The existing OpenSpec tasks 3.1, 3.4, 4.1 and 4.2 remain **unchecked**. The current PR #2 stays DRAFT/UNMERGED and `main` is not modified. Both evidence-generating workflows are now **manual-only** after the successful archived runs, to avoid unintended repeated builds.
