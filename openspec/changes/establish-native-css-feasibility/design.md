# Design: Feasibility first, engine second

## Architectural decision

CALYRA starts as a **CSS-native feasibility lab**, not an SDK or new renderer. Build the smallest repeatable interface and measurement harness that can answer whether a CSS-authored browserless runtime is worth developing. Defer compiler and material-system architecture until after real engine constraints are observed.

## Execution classes and candidates

| Candidate | Role | Class to verify | Main risk |
| --- | --- | --- | --- |
| Tauri using OS WebView | Baseline | Browser-backed via system WebView | Resource accounting differs from bundled engines |
| Blitz (Dioxus) | Candidate | Browserless HTML/CSS path | Beta coverage, dependency/API stability |
| RmlUi | Candidate | Native C++ UI with CSS subset | CSS subset and text/a11y integration |
| Electrobun experimental GPU UI | Candidate | GPU path explicitly distinct from its WebView option | Experimental APIs; ensure no hidden browser fallback |

Treat all versions, build feasibility, GPU paths, and license constraints as facts to verify at execution time, not settled by this document. If one candidate is blocked, preserve the failed attempt and compare remaining options; do not secretly replace a candidate with an untracked one.

## Proposed experimental boundaries

**Input:** one canonical source set: fixtures, styles, assets, font files, interaction traces, and viewport variants. Use real CSS on the reference path.

**Adapters:** an engine-specific entry point that exposes fixture selection, viewport changes, event replay hooks, and capture/measurement hooks. Translation is allowed only when declared and accounted for.

**Output:** structured per-run records plus raw logs and images. Reports distinguish direct CSS support, translation work, and missing features.

Proposed implementation directories for the apply phase (none created by this planning PR):

```text
fixtures/                 canonical authored UI and assets
adapters/                 one isolated adapter per engine
harness/                  repeatable orchestration and capture
results/                  generated raw records (do not commit large artifacts)
reports/                  generated comparison summaries
```

## Candidate research checkpoint (2026-11-14)

This section records **documentation evidence**, not CALYRA benchmark results or successful local builds. Re-check exact versions before each implementation attempt.

| Engine | Verified direction | Documented constraints | Evidence |
| --- | --- | --- | --- |
| Blitz | Modular Rust HTML/CSS stack, Stylo + Taffy, optional rendering and AccessKit integration | Official README calls it beta with missing features; no assumption of production-safe text/input behavior | [Blitz README](https://github.com/DioxusLabs/blitz) |
| RmlUi | Native C++ application/game UI with CSS-like RCSS and pluggable rendering | Its property index lists Flexbox but **no CSS Grid**; CSS compatibility is intentionally limited; rendering backend choice must be specified | [RmlUi README](https://github.com/mikke89/RmlUi) · [RCSS index](https://mikke89.github.io/RmlUiDoc/pages/rcss/property_index.html) |
| Electrobun GPU UI | Experimental Zig UI core with native Dawn/WebGPU drawing, distinct from bundled or system WebViews | Main-process privileged UI should handle trusted content only; no downloadable web fonts or network images; sticky/table/3D layout gaps; accessibility and text support vary by platform | [GPU UI guide](https://docs.electrobun.dev/electrobun/guides/electrobun-ui/) · [2.0.6 release](https://docs.electrobun.dev/electrobun/guides/changelog/v2-0-6/) |
| Tauri 2 | Uses OS WebViews (WKWebView on macOS) as browser-backed reference | Binary size excludes system web-renderer resources; browser process accounting differs from native candidates | [Tauri architecture](https://v2.tauri.app/concept/webview/) |

**Important:** RmlUi's missing Grid is a compatibility gap, not automatically a reason to exclude it from performance or adapter research. Never silently transform Grid into Flexbox and report direct compatibility. Electrobun's webview anchoring is not proof that its experimental GPU path itself runs in a webview.

## macOS native form-control audit and experimental SelectData port (2026-11-17)

The pinned Blitz winit/Vello window has now been verified to open on real macOS ARM64, but its canonical Controls snapshot visibly **omits the rendered select option label** and paints a range track with no recognizable thumb. The original WKWebView counterpart exposes macOS AX roles/values for the same fields. These visual and semantic gaps are **blocking full Stage A acceptance**, notwithstanding successful native window startup.

**Next measured vertical slice (experimental, not an engine-selection commit):** On an exact pinned disposable Blitz 0.3.0-beta.4 checkout, replay the *already Linux-tested* six baseline select fixes and isolated read-only `SelectData` implementation, without touching original CALYRA authored HTML/CSS/JS. Build the same `blitz::launch_static_html` macOS arm64 example. Capture an actual app-owned CGWindow screenshot, compare the new select region with previously archived original Mac Blitz baseline (same fixture, renderer class, Mac runner family; different run caveat), and inspect macOS Accessibility role/title/value inventory from **the real Blitz PID**, read-only. Retain upstream patch diff and the exact original snapshot manifest. Do not fabricate a native select popup, pointer selection, IME, or keyboard behavior. Native AX exposure, if absent, is a measured failure rather than a CI wiring failure.

**Acceptance scope:** A changed select area with a visually rendered label, an otherwise working native process/window, and complete machine-readable evidence count as a **restricted incremental paint fix**, not a full select component. The AX inventory and independently archived Tauri AX baseline must be compared without confusing WebView's standard AX roles with Blitz's internal DOM/Stylo data. The range input remains explicitly open; a genuine thumb must be separately implemented and visually/semantically tested. Prior experimental patches are not production candidates until integration, tests and licenses pass; all production/benchmark gates 3.1/4.1/4.2 remain unchecked.
## Blitz macOS live native-window follow-up (research gate, 2026-11-17)

Pinned upstream Blitz 0.3.0-beta.4 already has `blitz::launch_static_html(html: &str)`, using `blitz_shell::BlitzApplication` with `anyrender_vello::VelloWindowRenderer` and a winit-based event loop. Unlike `examples/screenshot.rs` (which uses `VelloCpuImageRenderer`), this launches a real native window. This is an **upstream source reading**, not proof of successful CALYRA macOS execution or hardware GPU.

After Mac static CPU screenshot build is independently verified, create an **isolated upstream example** in the temporary pinned Git checkout that reads the deterministic `prepare_static.py` snapshot and calls `blitz::launch_static_html`. Do not modify tracked upstream engine source or canonical HTML/CSS/JS; disclose the same static DOM active-state adaptation, inline original stylesheet and omitted JS. Try an actual macOS arm64 native process, verify a CGWindow owned by the exact PID, capture the **real window** with `screencapture -l`, validate nonblank pixels and preserve exact runtime/build output. A working native window alone does not establish `GPU hardware accelerated`; device/adapter details require separate evidence. Absence of a window or a failed build is an explicit blocked result, not a substituted webview screenshot.

Native accessibility/input semantics remain a separate gate: neither the static HTML fixture nor Blitz's `launch_static_html` implies original JS handlers run. Compare OS-owned window geometries only after matching viewport, pixel scale, font and content. **Never rank** a static Blender-free Blitz window against Tauri WKWebView in a single CPU/RAM/functional headline when capabilities or readiness states differ.

## Apple Silicon Blitz Vello-CPU compatibility slice (2026-11-17)

Before measuring a putative native-renderer performance advantage, verify whether the exact pinned Blitz 0.3.0-beta.4 upstream `examples/screenshot.rs` compiles and renders CALYRA on the **same macOS ARM64 runner family** as the verified Tauri WKWebView baseline. Reuse `native/blitz/run_stage_a.py` and `prepare_static.py` with unchanged authored CSS and honest static-HTML adaptations (explicit JS omission and active fixture). Keep native Blitz executable headless Vello **CPU**, not a windowed/GPU/text-input backend. Verify the actual executable revision, original fixture digests, nonblank 1060×800 normalized screenshot and raw provenance; archive success or real native build blocker.

**Acceptance boundary:** This only closes the cross-OS Blitz build/paint feasibility slice when a native Mac executable actually produces pixels. It MUST NOT be compared in a single speed/RAM headline with Tauri's persistent interactive WKWebView. A one-shot screenshot renderer that exits has different lifespan, readiness, capabilities, and memory scope than the interactive Tauri app (with WebKit helpers). Full OpenSpec 4.2 needs functionality-equivalent, same-machine, repeated runs, matched optimized configurations, defined readiness and whole-process accounting. No hidden JS substitutions or invented GPU parity.
## Two-stage experiment

### Stage A — compatibility preflight (cheap, documented)

1. Pin a candidate revision, license, OS support and executable render path.
2. Try a **minimal capability probe**: element tree, direct CSS cascade, Flexbox, Grid, variable, external font, SVG, text input, keyboard/focus, scrolling, and animation. Distinguish direct, adapted, partial, unsupported, blocked, and untested.
3. Record one native screenshot and functional trace where executable, or exact blocker and source when not.
4. Classify the candidate: **full benchmark eligible**, **restricted benchmark only**, or **blocked**. Keep all three categories in the report.

**Stage A does not allow cherry-picking a better looking engine-specific design.** Use one canonical markup and stylesheet first, then declare any adapter-specific translations in an isolated layer.

### Stage B — measured workloads (only where useful)

Benchmark the baseline and Stage A eligible candidates on shared fixture states, preserving failed features, differences and warm/cold launch methods. Restricted engines may be benchmarked on a named shared subset but SHALL NOT be included in an all-features headline ranking.

**Decision order:** evaluate correctness, text/input/accessibility, real CSS support, and integration risk before speed. A candidate with a spectacular animation but broken focus or IME is not a production foundation for general-purpose UI.

## Fidelity and asset policy

- Primary reference: browser HTML/CSS fixture using the system font stack available on all tested macOS implementations.
- Secondary typography test: explicit font-face/fallback/weight probes, recorded separately. Never present fonts drawn from different assets as a fair pixel comparison.
- The same CSS files and content are the primary comparison. Required translations are versioned patches/adapters, not modifications of source fixture.
- Record CSS pixels, scale factor, physical framebuffer dimensions, color space, and screenshots before computing visual deltas.
- Screenshot diffs need annotated regions and human review; antialiasing variance alone is not a broken layout.
- Record deliberately difficult CSS features even when only browser-backed baseline supports them.
- Trusted/local fixture content only in the initial evaluation. Do not treat privileged experimental UI as a sandbox for untrusted remote HTML.

## Measurement interpretation and publication

A performance report SHALL distinguish **app process RSS, process-tree RSS, GPU allocations when available, system WebView dependencies, and package-on-disk size**. Operating-system caches and memory sharing mean these numbers cannot be trivially added into a single universal RAM claim.

Timing data must use clear readiness markers: window created, first meaningful frame, and first working input. No demo video substitutes for instrumented or independently checked events. Record failed runs, not merely the successful subset. If instrumentation cannot be made comparable, mark the metric unranked.

Record the source revision and license for every linked framework. Verify build/download instructions without piping unreviewed remote scripts into a shell.

## Reference fixtures

1. **Controls:** buttons, dropdown, input, focus indicator, disabled states; verify pointer and keyboard behavior.
2. **Responsive dashboard:** nested Flexbox/Grid, text overflow, sidebar collapse, variable lengths, resizing.
3. **Visual challenge:** complex gradients, SVG, clipping, transitions, transforms, animated effects, shadow and optional backdrop blur. Explicitly mark feature failures; do not fake parity.
4. **Interaction:** scroll, keyboard traversal, text editing including composition/IME where testable, focus restore, resizing and UI state transitions.

Include both baseline behavior and visual capture checkpoints. The source should be inspectable and not depend on an inaccessible hosted demo.

## Benchmark methodology

- **First target:** locally available macOS Apple Silicon. Windows/Linux are subsequent validation questions.
- **Baseline:** package one fixture through Tauri/system WebView and record whether memory costs reside outside the app process.
- **Candidate runs:** use release/optimized builds where practical. Record build flags, versions, OS, machine, monitor/scale, energy profile and external load.
- **Repetition:** at least five measured runs per eligible workload/mode with raw individual values and an explicit warm/cold-launch distinction; increase samples when noise is high.
- **Metrics:** process resident memory (plus relevant child processes), CPU idle/animation load, cold/warm startup to interactive, package disk footprint and dependencies, frame-time distribution where instrumentable, input/focus correctness, visual screenshots, and adaptation effort. GPU memory/input latency are optional with explicit availability flags.
- **Comparison:** use similar windows, fonts, resolutions, content and states. Keep the system WebView cost visible; do not compare bundled-byte sizes as though system dependencies were free.
- **Quality:** attach platform-accessibility results and known limitations separately from screenshot parity.

Do not turn visual resemblance or one machine's median into proof of a broad speedup. Do not claim 60 FPS merely because an animation looked smooth.

## Candidate selection

Use a two-axis decision instead of a simplistic speed ranking:

1. **Functional fidelity and maintainability:** required controls/input/a11y, realistic CSS support, integration effort, licenses, and ability to diagnose rendering issues.
2. **Operational cost:** startup/idle/active resources, distributions, runtime dependencies and stability.

Reject a candidate for the current production hypothesis if essential input or accessibility semantics are impossible without major additional engines, regardless of attractive RAM figures. An experimental visual demo may still be valuable evidence.

## Open research questions

- Is a useful CSS subset enough for developer adoption, or would high-quality desktop UI require browser-level cascading/text complexity?
- Can existing style/layout stacks be reused without importing a heavyweight browser ecosystem?
- Do GPU material effects have stable degradation paths on integrated and low-power hardware?
- Will native framework adapters be more valuable than a standalone renderer?
- Where should future CSS-to-UI-IR compilation stop and host-native widget semantics begin?

Do not settle these by assertion.

## Explicitly deferred architecture

- **Portable UI-IR / CSS compiler** may follow once two backends demonstrate shared semantics.
- **Material Grammar** may model layout nodes, visible surface nodes, physical/material nodes, attachments and budgeted GPU effects. It is not a dependency of the current feasibility tests.
- **C ABI and third-party SDK** require a stable runtime and integration evidence.
- **Cross-platform portability** requires separate testing for every target/architecture.

## Safety, licenses and costs

Do not import proprietary code, copyrighted assets, licensed shaders, or an engine with incompatible redistribution terms. Review each dependency and its license before adoption. Keep CI disabled unless there is a specific local-testing gap; do not spend GitHub Actions minutes on empty scaffolding.

## Review gate

This OpenSpec change is **proposed, not implemented**. Implementation must not begin automatically from the existence of these files. Complete review of scope and test fixtures first; then apply as a separate activity with evidence.


## Blitz select semantics and reactive painting (targeted Stage A probe, 2026-11-15)

**Problem demonstrated:** Authored HTML/CSS/JS renders the initial label with six isolated upstream patches, but Blitz's headless select implementation has no live selection state or repaint contract. The existing \`TextInputData\` workaround is paint evidence only, not a safe select widget.

**Minimum reference contract (single-select, three direct options):**

1. Default selection is the first enabled option if no option is explicitly selected: \`selectedIndex=0\`, \`value="balanced"\`, visual label "Balanced". An explicit selected option wins on initial load.
2. Assigning \`select.value="quality"\` or \`select.selectedIndex=1\` updates selectedness and its label to "Visual fidelity" in the **same document**, without rebuilding the DOM or editing canonical assets. The identity of the select's node must remain unchanged. An unmatched value yields no selection (\`selectedIndex=-1\`, empty string), subject to Chromium baseline verification.
3. Assigning \`option.selected=true\` updates its owning select. Getter and visual label must agree. \`option.defaultSelected\` remains distinct from *current selectedness* when that model exists; an attribute-reflection approximation must be labeled restricted.
4. **Programmatic** selection changes must not generate \`input\` or \`change\` events. A **user-initiated** committed selection should dispatch \`input\` then \`change\`, each with consistent selectedness, but this is a separate physical/input simulation gate, not a requirement for the property-setter probe to masquerade as interaction.
5. Selected-label raster paint should update from a live model, not from a fresh static HTML snapshot. After a mutation and style/layout resolve, a genuine Vello CPU capture should show the change in localized pixels. Framebuffer dimensions, fonts, engine patch list and source SHA must be recorded.
6. A production solution needs noneditable select-specific state and a text-shaping/painting path that cannot receive ordinary text edits, cut/paste or IME. A temporary editor-buffer repaint experiment **may** be used to establish the state/invalidation path but cannot satisfy the production architecture gate.

**Measurement:** Record an untouched Chromium baseline on identical minimal HTML, then run native Rust/Boa behavior tests on clean pinned Blitz plus explicit patch set. Preserve failures, actual results, and both DOM and bitmap evidence. Do not claim UI popup, keyboard navigation, accessibility or OS-device input from these headless checks.

**Scope:** This probe stays within the current candidate evaluation. It does not authorize building a general HTMLSelectElement implementation or merging experimental Blitz source patches into CALYRA's main or upstream repository.


## Verified live selectedness and pixel transition (2026-11-16)

**Evidence, not release approval:** [native Rust/Boa CI #43699535417](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535417) passed 9/9 tests for seven in-place select states. [Native Vello CPU CI #43778999121](https://github.com/AVANT-ICONIC/calyra/actions/runs/43778999121) passed 9/9 tests, built a release screenshot example, and painted two 1060×800 frames from **one ScriptDocument** before/after a live `select.value='quality'` mutation. Exactly **732** pixels differed by >=12 in any RGB channel within bbox **[687, 490, 794, 505]**. The original 18 evidence files are permanently archived by [#43780409985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43780409985) under `docs/evidence/blitz-select-live/`, with independent SHA-256/pixel verification. CSS and JS original hashes remain unchanged.

This verifies **live reactive pixels** for the restricted direct-option case, not `HTMLSelectElement` compatibility. The still-used `TextInputData`/Parley editor buffer is not a safe read-only select widget. The follow-up architecture and explicit acceptance gates are recorded in `docs/blitz-select-data-architecture.md`: separate noneditable `SelectData`, single native selected-option authority, shared Parley shaping without an editor, no IME or caret, no duplicate browser DOM state, and a separate same-document test. Task 4.1 remains unchecked until the broader input/accessibility criteria hold. No hardware GPU, native OS input or general CSS parity is implied.


## Scoped Stage A system-WebView baseline: Linux WebKitGTK (2026-11-16)

**Decision:** establish a Linux WebKitGTK 4.1 reference using a minimal GTK3 host, loading the **unaltered canonical CALYRA HTML, CSS and JavaScript assets**. This is a **system-WebView engine smoke test**, **not a Tauri build** and **not a macOS WKWebView result**. Linux Tauri v2 uses WebKitGTK 4.1, while macOS Tauri v2 uses WKWebView. A successful WebKitGTK result alone cannot complete task 3.1.

**Inputs and evidence contract:**

- All four original fixtures, 1060×800 CSS-pixel viewport, motion off, same real relative CSS/JS paths via file URL, no CSS or JavaScript substitutions.
- Each scene uses a real WebKitGTK widget under a recorded Xvfb session on Ubuntu 24.04. PNG output must come from the WebKitGTK snapshot API rather than a prerendered image.
- Record exact original SHA-256 hashes, GTK/WebKit version, image dimensions and SHA-256 hashes, ready and active DOM state, CSS values, programmatic interaction traces, errors and process memory samples.
- The control interaction checks the original apply/reset handlers and select value. The menu probe tests the original toggle/Escape handler and focus. These are **synthetic DOM events**, not trusted physical keyboard or mouse input.
- Separate engine/process evidence from user-facing Tauri shell overhead. WebKitGTK 4.1 smoke results establish Linux engine behavior, not macOS WKWebView or actual Tauri app behavior.
- No claims of comparable CPU/RAM/GPU performance from a single Linux run. Load elapsed values and child-process RSS snapshots are diagnostics only, especially because shared memory may be double counted.

**Fail-closed gate:** all four states must load the unchanged source, execute canonical JavaScript, pass state assertions and save real 1060×800 screenshots. If a package, Wayland/X11 display, file URI, API or rendering path is unavailable, archive its exact failure and label this candidate restricted/blocked. Never call a Chromium fallback WebKitGTK.

**Follow-up:** actual Tauri 2 shell and WKWebView on a Mac, trusted OS input, repeatable memory/process measurements, and comparative differences to Blitz/RmlUi. Keep tasks 3.1, 4.1 and 4.2 unchecked until those distinct gates really pass.


## Stage A Tauri 2 macOS ARM64 packaged reference (2026-11-16)

**Authorized scope:** implement a minimal **Tauri 2 desktop host** in `adapters/tauri-reference/` on the existing research branch, using the **original** `fixtures/index.html`, `fixtures/reference.css` and `fixtures/reference.js` as its `frontendDist`. No Vite compiler, transpilation, rewritten CSS or parallel fixture source. This adds a real system **WKWebView-based** app packaging path, not a new CALYRA rendering engine.

**Gate method:** GitHub's `macos-15` Apple Silicon runner generates a Tauri `.app` with `tauri build --bundles app` (debug build permitted for Stage A), checks its executable and `Info.plist`, validates the direct asset path and SHA-256 before building, and archives manifest/bundle evidence. Runner OS, Apple target, Rust, Tauri CLI/Core versions, checksum, code-signing identity and app-bundle size must be recorded. Do not present an unsigned CI bundle as notarized software.

**Window contract:** initial window requests 1060×800 **logical window dimensions**, default `controls` fixture with `motion=off` query; the actual WKWebView `innerWidth`/`innerHeight` are an independent runtime acceptance gate, not inferred from config. Further fixture URLs remain exact canonical links. No native Rust commands or privileged API bridges are needed. The `app` must only load trusted embedded local UI; avoid remote networking and avoid introducing extra WebView processes for no reason.

**Evidence boundaries:** packaging and an executable existing are **build verification**, not first real frame, working native keyboard, accessibility or resource measurement. The runner may lack a logged-in macOS WindowServer. If runtime launch/screenshot tests are unavailable, explicitly record **not verified** rather than infer success from a bundle. macOS ARM64 CI success is distinct from testing on Marc's M1 Max. OpenSpec task 3.1 remains pending until at least the app actually executes original JavaScript and renders first meaningful frame under macOS WKWebView. Real OS input and the five-run matched resource protocol are separate gates.

**Failure protocol:** preserve exact compiler and bundler logs; do not silently replace the Tauri shell with Swift WKWebView/Chromium or a web-only screenshot. Avoid costly reruns after evidence is archived. This is the next contained unit of the existing `establish-native-css-feasibility` change, not a new OpenSpec project.

## Native macOS AccessKit lazy-activation diagnostic (2026-11-17)

**Question, not assumed failure:** real pinned Blitz ARM64 native window painted the selected label, yet a trusted read-only Apple Accessibility census returned 50 mostly chrome/menu nodes and 0/6 canonical fields. Pinned upstream includes `blitz-shell/accessibility` by default, builds a DOM AccessKit tree with ComboBox/Slider role mappings, and `accesskit_xplat` uses a macOS NSView subclassing adapter. It processes `InitialTreeRequested` asynchronously, and `update_if_active` can defer building a tree until an external assistive client activates the adapter. Therefore a one-shot AXChildren enumeration alone cannot conclude the application has no AX implementation.

**Controlled experiment:** start from exact pinned 0.3.0-beta.4 upstream and its previously source-verified read-only SelectData patches in a disposable checkout, compile the same native ARM64 Winit/VelloWindowRenderer GUI. Add **log-only** probes at the upstream `accesskit` event receiver, `InitialTreeRequested` handler and `update_if_active` closure. No behavior code patches, no new AX synthetic nodes and no manually forced tree. Use a separate read-only Swift client with TCC trust to record the app/window AX tree before any content hit test, probe a bounded grid of screen positions inside the **verified app-owned CGWindow** with `AXUIElementCopyElementAtPosition` and attribute reads (no focus, actions, keyboard or pointer events), then record the second live tree. Preserve return codes, position, hit roles and native process log events. Inspect observed `InitialTreeRequested` and `AX_TREE_BUILT` markers to distinguish (a) no activation, (b) active tree produced but not surfaced, and (c) exposed elements or genuine control roles.

**Bounded acceptance:** a read-only hit test must not be described as trusted OS pointer/keyboard input, VoiceOver exercise, user accessibility compliance, or a changed control implementation. If an AX backend lazily activates and emits a tree, **the exact macOS AX role/title/value** of every canonical field must still be checked. Any missing semantics remain failures even if a tree appears. Avoid adding AX stubs or transforming authored CSS/JS. Preserve original fixture hashes, prior baseline AX result, full source patch diff and native diagnostic logs. Keep OpenSpec 3.1/4.1/4.2 unchecked, PR draft and main untouched.
