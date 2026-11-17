# CALYRA: reactive selected-option text without editor input

**Date:** 2026-11-16. **Scope:** isolated Stage A Blitz/Boa/Vello CPU feasibility experiment at upstream `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`. Not a production HTML select, general DOM invalidation engine, or hardware GPU result.

## Problem and implementation

The earlier `SelectData` no-op setter optimization correctly skipped redundant redraws when a programmatic `select.value` or `selectedIndex` write chose the same option. But changing the **visible text of the already-selected option** also preserves the selected `NodeId`, so current selection alone cannot tell whether its cached Parley label is stale.

An isolated second adapter, `native/blitz/experiments/apply_select_option_text_refresh.py`, adds a native label refresh specifically after Boa's `Node.textContent` and `Node.nodeValue` mutations. The callback:

1. Resolves the changed option itself, or the direct parent of a changed text child, and requires a direct parent `<select>`.
2. Requires the option to equal native `SelectData.selected_option`, without selecting another option or resurrecting an empty selection.
3. Compares the current trimmed option text with `SelectData.label` and only requests a new read-only Parley shape/redraw when they differ.
4. Runs **after** dropping the DOM mutator, avoiding nested mutable document borrows.

The original noneditable `SelectData`, no-`PlainEditor` invariant and idempotent JS selection property optimization are preserved. The canonical `fixtures/reference.css` and `reference.js` bytes remain unchanged.

## Actual native tests and pixels

- [Producing CI #43868624637](https://github.com/AVANT-ICONIC/calyra/actions/runs/43868624637): clean pinned upstream checkout, isolated adapter applied, **11/11 native Rust/Boa integration tests passed**, seven pre-existing JS selectedness states unchanged. New test exercises `option.textContent` and direct `TextNode.nodeValue` immediately and after layout resolve. Other option text mutation does not overwrite current label; no programmatic `input` or `change` events.
- The producing run's **two actual 1060×800 Vello CPU frames** share one `ScriptDocument`. JavaScript changes the selected option's `textContent` from **Balanced** to **Balanced updated**, leaving its selected value `balanced`. Independent recomputation gives **381 RGB pixels changed** at threshold 12/255 in bbox **[767, 490, 832, 505]**.
- Image SHA-256: before `485552ed102b35a3934fa3aeb0adac00bb974ef876f932a2a0c5fd374a39188a`; after `7c2f240530b5e641b1bfbd567c2ba5b307f74314962d022f2cd61f0c521bb84d`; diff `e53cc0c35c0fe8e1593e96d6c692f14ed037b0e6ea0cf33164c38b9f7d13720a`.
- The producing workflow status is **failure**, strictly because its final archival check still expected `new_label='Visual fidelity'` from an earlier scenario. The actual Rust, rendering, pixel-diff generation and upload steps **succeeded**. Preserve this failed result as an auditable harness error, not as a renderer failure.
- [Separate archival CI #43871323400](https://github.com/AVANT-ICONIC/calyra/actions/runs/43871323400) **PASSED**: downloaded the same producing-run artifact, verified the exact 381-pixel result and both 1060×800 PNGs, all source SHA-256 entries, 11/11 Rust test log, JS native labels, original author CSS/JS, and committed **18 original byte-for-byte files** to [`docs/evidence/blitz-select-option-text/`](evidence/blitz-select-option-text/).
- The producing workflow's stale label assertion is corrected and its expensive native build is now **manual-only**, so documentation commits cannot accidentally launch repeated release builds. This edit was not rerun; archival success is instead attributable to the separate exact-artifact verification.

## Deliberate compatibility limits

- Only direct selected-option `textContent` and direct text-child `nodeValue` mutations through the probed Boa setters are demonstrated. `innerHTML`, arbitrary append/replace/remove APIs, nested option content, option removal, dynamic lists, form reset and DOM mutation observers are **not** verified.
- Style-only changes (CSS variables, font family/size/weight, class changes, stylesheet changes), intrinsic select sizing, user keyboard/pointer dropdown selection, OS IME, accessibility and hardware GPU remain separate unknowns.
- No production correctness or redraw-rate/performance claim is supported. Pixel counts prove localized visible ink changes, not Chromium-perfect rendering.
- **OpenSpec task 4.1 stays unchecked.** Continue `openspec/changes/establish-native-css-feasibility/`; PR #2 stays draft/unmerged on `feat/reference-fixtures`; `main` untouched.

**Next bounded experiment:** source-pinned same-document style-only typography invalidation with exact rendered glyph metrics and pixel evidence. If this requires pervasive rebuilding of the browser style machinery, classify native select support as restricted rather than endlessly patching a feasibility lab.
