# CALYRA

**CSS-authored interfaces, native execution.**

CALYRA is a research-first project exploring whether developers can use familiar CSS to build interactive, visually sophisticated native interfaces without requiring a Chromium-based application runtime.

The project is **in the specification and feasibility phase**. No renderer, performance advantage, CSS coverage, or cross-platform compatibility has been demonstrated yet.

## Thesis

The strongest product may be a portable CSS-compatible authoring and compilation layer over native GPU UI backends, rather than another full browser or complete app framework.

Key hypotheses to test:

- A useful subset of real CSS can render natively with sufficient visual fidelity.
- The resulting applications can offer measurable practical benefits over a system-WebView baseline for selected workloads.
- A future **material grammar** could separate layout, visible surfaces, and physical/material behavior rather than treating every layout container as a visual box.
- A neutral UI representation and C ABI may eventually allow multiple language and framework integrations.

**All four are hypotheses, not commitments or proven properties.**

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

## Specifications

The project's canonical planning and change workflow is [OpenSpec](https://github.com/Fission-AI/OpenSpec).

The first change is `openspec/changes/establish-native-css-feasibility/`: proposal, observable requirements, technical design, and implementation tasks. Product development starts only after the spec has been reviewed.

## Status

**Planning only.** No benchmark results, implementation, or verified performance claims yet.
