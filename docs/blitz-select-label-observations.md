# Blitz selected-option label: genuine Vello CPU paint evidence

**Date:** 2026-11-15. **Status: experimentally painted, not an interactive select.**

## Verified execution

[GitHub Actions run #43692125454](https://github.com/AVANT-ICONIC/calyra/actions/runs/43692125454) completed successfully on Ubuntu x86_64, using **official pinned Blitz 0.3.0-beta.4** commit `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, Rust 1.91, Boa and Vello **CPU**. The CI job passed **9/9 real Rust tests**, built the official upstream screenshot example and captured two actual native 1060×800 images.

CALYRA's authored `fixtures/reference.css` and `fixtures/reference.js` were not edited: original CSS SHA-256 `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`; JS SHA-256 `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`.

## What visibly changed

| Native screenshot | Visible select label | SHA-256 of 1060×800 PNG |
|---|---|---|
| Default static controls HTML | **Balanced** | `b331a392a3a20594283d25cc08e5db81b12657524befcd419a4008fbbb211c1b` |
| Same static HTML, with `selected` on quality option | **Visual fidelity** | `0a9fbc495df35a779347c48cf4b754ff7bce234ad55d08b6c3a520ce6051bd27` |

The second snapshot is an **explicit test-only HTML state adaptation**: it adds a `selected` attribute to one existing `option`; it is not the original DOM and no JavaScript is executed during screenshot capture.

A per-pixel comparison (different if **any RGB channel differs by at least 12/255**) found exactly **1,012 changed pixels**. The raw RGB difference bounding box was **[685, 489, 796, 510]**, i.e. a **111×21 px** rectangle restricted to the displayed select text. The image result JSON and PNG SHA-256 hashes were independently checked after downloading the GitHub artifact.

The rendered select control's existing box remains approximately **139×48 CSS px**, not a claim of browser-perfect intrinsic sizing. The experimental text label is visibly inside the control and uses native Parley layout, Stylo styles and actual Vello CPU scene painting.

[Full original job artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43692125454/artifacts/14153331129) includes two raw native PNGs, two normalized PNGs, pixel diff, snapshot HTML, both source hashes, applied upstream diff, real test logs and build logs. This Actions artifact has limited retention, so a one-shot, SHA-verified archival workflow copies the original files to `docs/evidence/blitz-select-label/` in the existing draft branch.

## Patches actually used

The complete experimental engine diff is recorded as `applied-upstream-diff.patch` in the evidence. These **six patches affect only a disposable pinned upstream checkout**, not CALYRA's original author-written HTML/CSS/JS or a production runtime:

1. `document-event-chain.patch`: include the document node in event bubbling.
2. `plain-button-focus.patch`: preserve programmatic focus after ordinary button click.
3. `select-ua-display.patch`: give select a nonzero CSS layout box.
4. `select-default-value.patch`: minimal initial/explicit-selected option getter.
5. `select-label-parley.patch`: reuse the single-line Parley editor as a **temporary display-only** selected-option label buffer.
6. `select-label-readonly.patch`: prevent normal KeyDown editing of that display buffer.

The additional Rust test `patched_label_paint_regression.rs` checks that the original select label produces a real native Parley text line, DOM `.value` remains `balanced`, and a normal character keypress cannot modify the label buffer. No JS exceptions were reported.

## Engineering limitations and next acceptance gates

**Do not ship the temporary Parley text-editor trick as a production select.** It does not implement full `HTMLSelectElement` selectedness, native popup, pointer option selection, `selectedIndex`, `.value` setter semantics, `change/input` events, optgroup, reactive label updates, keyboard navigation, Tab order, IME isolation or accessibility. Blocking the ordinary keyboard path does **not** establish IME safety. A more appropriate architecture is a distinct read-only `SelectData` with shared Parley shaping and a real selection state machine, separate from an editable text input.

The screenshots are JS-free static snapshots. The separate real Boa tests prove initial getter/focus behavior only. These observations do **not** establish hardware GPU acceleration, physical OS input, memory or startup advantages, full CSS parity or production readiness.

**Next concrete experiment:** build a tiny, isolated select semantic state probe on pinned Blitz that tests `value` getter/setter, `selectedIndex`, option selectedness, `input/change` event ordering and reflected visible label after changing selection without rebuilding the document. Compare against a Chromium reference for that same minimal markup, without altering canonical CALYRA fixtures. Use native integration tests first; only then consider popup/OS rendering. Keep OpenSpec task 4.1 unchecked and PR #2 draft.
