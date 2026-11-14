# Tasks: native CSS feasibility

All tasks are **pending**. Checking them off requires actual evidence, not a planning document.

## 1. Candidate and contract validation

- [ ] 1.1 Verify current revisions, licenses, build paths, platform capabilities, and exact native-versus-WebView execution mode for Tauri, Blitz, RmlUi, and Electrobun GPU UI.
- [ ] 1.2 Define the stable adapter contract for fixture selection, viewport/scale, interaction replay, screenshots, logs, and metrics; document unsupported adapter capabilities.
- [ ] 1.3 Decide and record one baseline OS/hardware/environment, process-accounting rules, cold/warm launch definitions, and measurement tools.

## 2. Canonical fixture construction

- [ ] 2.1 Implement a compact component and control fixture with keyboard/focus/input expectations.
- [ ] 2.2 Implement responsive dashboard and visual challenge fixtures using versioned CSS/assets.
- [ ] 2.3 Implement and document deterministic interaction traces and visual capture checkpoints.

## 3. Engine adapters

- [ ] 3.1 Run the Tauri/system-WebView reference and confirm fixture behavior.
- [ ] 3.2 Attempt Blitz adapter, preserving unsupported features and integration notes.
- [ ] 3.3 Attempt RmlUi adapter with explicit CSS-subset accounting.
- [ ] 3.4 Attempt Electrobun experimental GPU adapter while verifying its rendering path is not a WebView.
- [ ] 3.5 For blocked candidates, record reproducible failure and version; do not invent results.

## 4. Evidence and validation

- [ ] 4.1 Capture matching visual states and compute/record meaningful discrepancies; verify actual focus, keyboard, scroll, and text-input behavior.
- [ ] 4.2 Run at least five repeated comparable measurements per eligible workload, preserving raw results and environment metadata.
- [ ] 4.3 Build the CSS coverage and adaptation matrix, accessibility findings, license review, and operational-cost comparison.
- [ ] 4.4 Verify report reproducibility from recorded assets/commands on at least the first target device.

## 5. Feasibility decision

- [ ] 5.1 Publish an evidence-backed recommendation: existing-engine integration, narrowly scoped compiler/adapter follow-up, targeted second experiment, or stop.
- [ ] 5.2 Record the next OpenSpec change only if a concrete gap is demonstrated; explicitly keep Material Grammar, universal UI-IR, and SDK design out of this change.
