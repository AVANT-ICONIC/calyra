# CALYRA

**CSS-authored interfaces, native execution.**

CALYRA is a research-first project exploring whether developers can use familiar CSS to build interactive, visually sophisticated native interfaces without requiring a Chromium-based application runtime.

The project is a **feasibility lab**, not a production GUI framework. Experimental native rendering and limited JavaScript behavior have been demonstrated on the [active research branch](../../tree/feat/reference-fixtures), while broad CSS parity, OS input, accessibility, cross-platform compatibility, and any performance advantage remain **unproven**.

## Thesis

The strongest product may be a portable CSS-compatible authoring and compilation layer over native GPU UI backends, rather than another full browser or complete app framework.

Key hypotheses to test:

- A useful subset of real CSS can render natively with sufficient visual fidelity.
- The resulting applications can offer measurable practical benefits over a system-WebView baseline for selected workloads.
- A future **material grammar** could separate layout, visible surfaces, and physical/material behavior rather than treating every layout container as a visual box.
- A neutral UI representation and C ABI may eventually allow multiple language and framework integrations.

**All four are hypotheses, not commitments or proven properties.**

## Current experimental evidence (research branch)

On [`feat/reference-fixtures`](../../tree/feat/reference-fixtures), the existing [draft PR #2](../../pull/2) documents source-pinned experiments against the original CSS/JS fixture:

- **Blitz + Vello CPU:** real native raster captures for four static CALYRA scenes. Browser JavaScript is absent from those *static* captures, and explicit DOM adaptation is recorded.
- **Blitz + Boa:** nine native Rust/JavaScript integration tests passed for restricted programmatic select state, and a single live document repainted a selected-option label on the same native node. [CI evidence](../../actions/runs/43778999121) and [archived evidence](docs/evidence/blitz-select-live/) report **732 changed pixels**; these pixels are *CPU-rendered*, not a hardware GPU or OS input demonstration.
- **RmlUi:** real restricted native captures exist, but direct modern-CSS compatibility is visibly incomplete.

The select-label prototype currently uses a temporary editable text buffer as a paint workaround. The next task is a **noneditable native `SelectData`** with one authoritative selection state; keyboard/pointer input, popup, IME, accessibility, CSS parity, and a production-ready runtime are not established. Read [the live branch handoff](HANDOFF.md), [evidence notes](docs/blitz-select-live-observations.md), and the existing OpenSpec change before proposing or implementing changes. These links resolve on the research branch, not necessarily on `main` until the stacked PRs are merged.

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

**Active experimental feasibility work on the research branch; unmerged.** The public default branch is not an implementation release. No comparative performance win, native OS input stack, complete CSS coverage, or supported cross-platform product has been verified. Published evidence is experimental, not a claim of a deployable SDK.
