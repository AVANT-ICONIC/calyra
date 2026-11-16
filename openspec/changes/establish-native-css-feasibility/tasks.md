# Tasks: native CSS feasibility

A checked task requires executable evidence. Chromium reference fixtures were verified locally; RmlUi 6.3 has now been compiled and executed on a Linux OpenGL software renderer and produced real, restricted Stage A captures. No hardware-GPU, CSS parity, accessibility, or performance result is verified.

## 1. Candidate and contract validation

- [ ] 1.1 Verify and pin current revisions, redistribution licenses, build paths, platform support, and exact rendering modes for Tauri, Blitz, RmlUi, and Electrobun (initial source research in design.md is not execution verification).
- [ ] 1.2 Run Stage A minimal CSS/input preflight and classify each as full, restricted, or blocked with source and actual evidence; explicitly probe RmlUi Grid and Electrobun font/privilege limitations.
- [ ] 1.3 Define the adapter contract for fixture selection, viewport/scale, interaction replay, screenshots, logs, and metrics; isolate and version every CSS translation.
- [ ] 1.4 Record baseline macOS environment, framebuffer scaling/font policy, process-accounting rules, cold/warm launch definitions, readiness markers, and measurement tools.

## 2. Canonical fixture construction

- [x] 2.1 Implement a compact component and control fixture with keyboard/focus/input expectations.
- [x] 2.2 Implement responsive dashboard and visual challenge fixtures using versioned CSS/assets.
- [x] 2.3 Implement and document deterministic interaction traces and visual capture checkpoints.

## 3. Engine adapters

- [ ] 3.1 Run the Tauri/system-WebView reference and confirm fixture behavior.
- [x] 3.2 Attempt Blitz adapter, preserving unsupported features and integration notes. [Run #43671027217](https://github.com/AVANT-ICONIC/calyra/actions/runs/43671027217) verified 4 native Blitz Vello-CPU captures at 1060x800, exact original CSS text with static HTML state adaptation; input/JS/GPU and feature-level CSS parity remain untested. See `docs/blitz-stage-a-observations.md`.
- [x] 3.3 Attempt RmlUi adapter with explicit CSS-subset accounting. Real RmlUi 6.3 GLFW_GL3 execution, synthetic click, computed RCSS color, and both 1060x740 captured frames: [run #43665651869](https://github.com/AVANT-ICONIC/calyra/actions/runs/43665651869). Direct CSS is visibly incompatible; engine is restricted, hardware GPU unverified.
- [ ] 3.4 Attempt Electrobun experimental GPU adapter while verifying its rendering path is not a WebView.
- [ ] 3.5 For blocked candidates, record reproducible failure and version; do not invent results.

## 4. Evidence and validation

- [ ] 4.1 Capture matching visual states and compute/record meaningful discrepancies; verify actual focus, keyboard, scroll, and text-input behavior. **Partial evidence only, NOT gate completion:** original CALYRA JavaScript executes under real Blitz/Boa without modification, experimental patches restore synthetic document Escape and button focus, live single-select property semantics pass **9/9** native tests ([run 43699535417](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535417)), and **same-document Vello CPU** `select.value` update genuinely changes **732 pixels** ([run 43778999121](https://github.com/AVANT-ICONIC/calyra/actions/runs/43778999121), [permanent evidence](../../../docs/evidence/blitz-select-live/)). These results depend on patched upstream and a temporary editor-as-label workaround. **Physical OS pointer/keyboard, IME safety, accessibility, actual dropdown, CSS parity, hardware GPU, matching mobile screenshots and complete focus/scroll input acceptance are NOT demonstrated.**
- [ ] 4.2 Run at least five repeated comparable measurements per eligible workload, preserving raw results and environment metadata.
- [ ] 4.3 Build the CSS coverage and adaptation matrix, accessibility findings, license review, and operational-cost comparison.
- [ ] 4.4 Verify report reproducibility from recorded assets/commands on at least the first target device.

## 5. Feasibility decision

- [ ] 5.1 Publish an evidence-backed recommendation: existing-engine integration, narrowly scoped compiler/adapter follow-up, targeted second experiment, or stop.
- [ ] 5.2 Record the next OpenSpec change only if a concrete gap is demonstrated; explicitly keep Material Grammar, universal UI-IR, and SDK design out of this change.
