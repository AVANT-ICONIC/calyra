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
