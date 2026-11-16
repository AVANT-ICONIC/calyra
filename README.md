# CALYRA

**CSS-authored interfaces, native execution.**

CALYRA is a research-first project exploring whether developers can use familiar CSS to build interactive, visually sophisticated native interfaces without requiring a Chromium-based application runtime.

The project is a **feasibility lab**, not a production GUI framework. Experimental native rendering and limited JavaScript behavior have been demonstrated on the [active research branch](https://github.com/AVANT-ICONIC/calyra/tree/feat/reference-fixtures), while broad CSS parity, OS input, accessibility, cross-platform compatibility, and any performance advantage remain **unproven**.

## Thesis

The strongest product may be a portable CSS-compatible authoring and compilation layer over native GPU UI backends, rather than another full browser or complete app framework.

Key hypotheses to test:

- A useful subset of real CSS can render natively with sufficient visual fidelity.
- The resulting applications can offer measurable practical benefits over a system-WebView baseline for selected workloads.
- A future **material grammar** could separate layout, visible surfaces, and physical/material behavior rather than treating every layout container as a visual box.
- A neutral UI representation and C ABI may eventually allow multiple language and framework integrations.

**All four are hypotheses, not commitments or proven properties.**

## Current experimental evidence (research branch)

On [`feat/reference-fixtures`](https://github.com/AVANT-ICONIC/calyra/tree/feat/reference-fixtures), the existing [draft PR #2](https://github.com/AVANT-ICONIC/calyra/pull/2) documents source-pinned experiments against the original CSS/JS fixture:

- **Blitz + Vello CPU:** real native raster captures for four static CALYRA scenes. Browser JavaScript is absent from those *static* captures, and explicit DOM adaptation is recorded.
- **Blitz + Boa (read-only native `SelectData`):** original JavaScript runs through an experimental pinned upstream adapter without creating a `PlainEditor` for the select. Programmatic selection updates, idempotent JS setters and selected-option text mutation passed actual Rust/Boa tests and separate same-document Vello CPU pixel proofs. [Read-only native evidence](docs/evidence/blitz-select-readonly/) records **731 changed pixels** when selection changes; [option text evidence](docs/evidence/blitz-select-option-text/) records **381 changed pixels** with selection unchanged.
- **Computed CSS typography:** [native CI #43919838241](https://github.com/AVANT-ICONIC/calyra/actions/runs/43919838241) passed **12/12 native Rust/Boa tests** and verified **1,639 real Vello CPU pixels** changing within a single 1060×800 document after a CSS-only `font-size` update; selected value/text remain identical. [Original screenshots, hashes, logs and adapter diff](docs/evidence/blitz-select-typography/) were committed in the successful run.
- **Linux system WebKitGTK 2.52.6 reference:** [actual GUI CI #43930684985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43930684985) validated **6/6 live canonical fixture scenarios** and **8/8 nonblank screenshots**, including responsive/mobile layout, controls and menu interactions via explicitly synthetic DOM events. [27 original archived artifacts](docs/evidence/system-webkitgtk-reference/). This is the Linux **system WebKit browser backend**, NOT a packaged Tauri desktop app or macOS WKWebView.
- **First direct native/Chrome-independent visual diagnostic:** [CI #43931943330](https://github.com/AVANT-ICONIC/calyra/actions/runs/43931943330) compared archived initial Controls PNGs (same 1060×800 viewport and original HTML/CSS/JS) from WebKitGTK and native Blitz/Vello. **51,944/848,000 RGB pixels** differed at threshold 12/255 (**6.13%**), but localized mismatch was **79.69%** in the select region and **24.72%** in the range-slider region. This is [a visual diagnostic with a montage and source hashes](docs/evidence/comparisons/webkitgtk-blitz-controls/), **not a CSS parity score**; CI environments/fonts differ.
- **Actual Tauri 2 shell (new reference host):** [Linux native Tauri compile and process test #43937455301](https://github.com/AVANT-ICONIC/calyra/actions/runs/43937455301) PASSED, with canonical assets embedded into a genuine Tauri/WebKitGTK executable rather than a standalone GTK-only harness. [Verified source/dependency-lock archive #43938227700](https://github.com/AVANT-ICONIC/calyra/actions/runs/43938227700) pins `tauri 2.12.6` and CLI `2.12.4`. The new [Tauri host source](adapters/tauri-reference/) targets **macOS WKWebView** as its next actual desktop gate. The initial Xvfb pixel capture [#43938799768](https://github.com/AVANT-ICONIC/calyra/actions/runs/43938799768) correctly failed on a blank compositor. A focused [real Tauri native X11 paint CI #43939757930](https://github.com/AVANT-ICONIC/calyra/actions/runs/43939757930) **then PASSED** and archived a [genuine 1060×800 window PNG](docs/evidence/tauri-linux-window-pixels/tauri-native-window.png), containing 759 sampled colors and source-checked original image evidence. This is not verified macOS WKWebView/JS/input parity. The first attempt of [macOS ARM64 CI #43936544580](https://github.com/AVANT-ICONIC/calyra/actions/runs/43936544580) was cancelled while queued; **attempt 2 reached a real Mac runner** and compiled to the Tauri proc macro but failed because our generator omitted its required conventional `icon.png`. That omission was fixed and [independent icon/source CI #43942204867](https://github.com/AVANT-ICONIC/calyra/actions/runs/43942204867) PASSED. The [corrected locked macOS `.app` run #43941982471](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941982471) has not yet reported a successful macOS bundle. **No macOS `.app`, macOS WKWebView paint, or performance win has been verified.**
- **Actual Tauri vs WebKitGTK original pixels:** [comparison CI #43941143858](https://github.com/AVANT-ICONIC/calyra/actions/runs/43941143858) independently verified **1,692 of 848,000 pixels** differ between the **actual Tauri Linux native window** and standalone WebKitGTK Controls screenshot at RGB threshold 12/255 (**0.1995%**). Both original native Control ROIs for **Select and Range differ by zero thresholded pixels**. [Verified original-vs-original montage/report](docs/evidence/comparisons/tauri-webkitgtk-controls/). This strong **Linux visual baseline** is not a CSS-compatibility percentage, macOS WKWebView runtime result, input parity, or performance measurement.
- **RmlUi:** real restricted native captures exist, but direct modern-CSS compatibility is visibly incomplete.

These are **restricted native CPU and JavaScript integration experiments**, not browser-level compatibility or proven performance wins. The CSS typography adapter performs an unmeasured computed-property fingerprint scan during resolution, and class/inheritance/font-loading paths are not yet verified. Working user dropdowns, physical OS input, IME, accessibility, full CSS parity, hardware GPU and a production-ready runtime remain open. The next worthwhile milestone is a **real packaged Tauri reference on macOS Apple Silicon**, an independent **Electrobun non-WebView GPU UI probe** and **comparable system-process resource measurements**, not unlimited experimental select patching. Read [the live branch handoff](HANDOFF.md), [Linux system-WebView findings](docs/system-webkitgtk-reference-observations.md), and the existing OpenSpec change before further implementation. These links resolve on the research branch, not necessarily on `main` until the stacked PRs are merged.

## First milestone: engine feasibility

Evaluate at least Blitz, RmlUi, and Electrobun's experimental GPU UI path against a Tauri/system-WebView reference, subject to platform/API availability and license review.

Measure compatibility, visual fidelity, interactivity, accessibility, CPU/RAM/GPU behavior, launch time, package size, and implementation complexity. Report unsupported capabilities honestly. Do not claim a winner before collecting comparable evidence.

## Engineering boundaries

- **CSS first.** Do not invent a replacement language merely for syntactic novelty.
- **Reuse before reinventing.** No bespoke layout engine or GPU renderer until experiments demonstrate a specific unmet requirement.
- **No false portability.** Platform-specific binaries and graphics APIs are expected.
- **Native means explicit.** Distinguish browserless GPU rendering from OS-supplied WebViews and bundled browser engines.
- **Performance must be measured.** No made-up speedups or binary-size claims.
- **Materialism is optional.** Explore material semantics after the baseline; do not make them prerequisites for ordinary CSS.
- **Research work should be reproducible.** Preserve test fixtures, hardware metadata, methodology, and failures.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) for evidence-first pull requests. A proposed [MIT license](LICENSE) is present on the active research branch; third-party dependencies, imported components and upstream Blitz patches retain their own obligations. Public release requires review of attribution and distributability.

## Specifications

The project's canonical planning and change workflow is [OpenSpec](https://github.com/Fission-AI/OpenSpec).

The first change is `openspec/changes/establish-native-css-feasibility/`: proposal, observable requirements, technical design, and implementation tasks. Product development starts only after the spec has been reviewed.

## Status

**Active experimental feasibility work on the research branch; unmerged.** The public default branch is not an implementation release. No comparative performance win, native OS input stack, complete CSS coverage, or supported cross-platform product has been verified. Published evidence is experimental, not a claim of a deployable SDK.
