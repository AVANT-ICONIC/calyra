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
