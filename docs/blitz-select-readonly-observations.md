# CALYRA read-only SelectData experiment

**Date:** 2026-11-16. **Scope:** source-pinned Blitz Stage A experiment. **Not a production select or a replacement browser.**

## Architectural change

The previous working [live-label experiment](blitz-select-live-observations.md) stored current selection in Boa state and rendered text via `TextInputData` / `parley::PlainEditor`. This experiment instead runs a strict, fail-closed source adapter (`native/blitz/experiments/apply_readonly_select.py`) after six upstream patches in a disposable, clean checkout pinned to Blitz `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`.

- `SpecialElementData::Select(SelectData)` stores **current option NodeId, label String and shaped Parley Layout<TextBrush>** on the native select node itself.
- Boa JS bindings `select.value`, `selectedIndex`, `option.selected` and `defaultSelected` use the native selected-option model, **not a separate select_current map**.
- Text shaping is performed via Parley's `tree_builder`, keeping authored CSS typography, without creating a `PlainEditor` or editor cursor.
- Vello painting uses a separate `draw_select_label` path, rather than `draw_text_input_text`. The native select gets its own clipping rule.
- The previous, successfully archived editor-based proof remains untouched. All source changes are isolated to a temporary pinned upstream clone; the canonical author CSS and JS are unchanged.

## Verification

[Native CI run #43781785053](https://github.com/AVANT-ICONIC/calyra/actions/runs/43781785053) applied the adapter but **failed** Rust compilation because the new enum variant was not covered by `blitz-dom/src/mutator.rs`'s exhaustive node-removal match (E0004). The adapter was fixed and a strict preflight added; that failure is retained rather than reclassified.

[Follow-up CI run #43782046600](https://github.com/AVANT-ICONIC/calyra/actions/runs/43782046600) passed Rust/Boa tests and the native Vello CPU screenshot. A later [source-pinned verification and archival run #43783621933](https://github.com/AVANT-ICONIC/calyra/actions/runs/43783621933) also passed and preserved **17 original evidence files** in [docs/evidence/blitz-select-readonly/](evidence/blitz-select-readonly/). The read-only implementation produced two genuine **1060×800** frames from one `ScriptDocument`, with `select.value='quality'` changing **731 pixels** at RGB threshold 12/255, confined to bbox **[687, 490, 794, 505]**. Full-size PNG SHA-256 hashes are in `live-paint-result.json`; seven native JS selection states matched the expected values, and **9/9** Rust tests passed at the archived source revision. This proves CPU label repaint with no editor, not a production dropdown, real OS IME or a GPU renderer.

The new Rust tests assert that a select does not have `TextInputData`, that the Parley label has shaped lines, and that synthetic keydown, IME Commit and paste do not mutate the selected label or JS selection. This does **not** verify real OS IME composition or accessibility.

## Remaining gates and risks

- Live read-only label repaint is **proved and archived at its source-pinned CI revision**. Subsequent source edits require a new exact-head compile/test receipt before their behavior can be described as verified.
- The `calyra_set_select_selection` construction path currently requests redraw even if the selection/label did not change. A future window host must guard against redundant invalidation and measure redraw loops.
- No working popup, user pointer/keyboard selection, input/change dispatch from actual selection, form reset, disabled/optgroup semantics, screen reader output, hardware GPU or macOS/Windows benchmark.
- Keep OpenSpec task 4.1 unchecked and PR #2 draft/unmerged.

## Verified follow-up: idempotent JS setters (separate archival receipt)

[One-shot CI #43865517201](https://github.com/AVANT-ICONIC/calyra/actions/runs/43865517201) passed **10/10 native Rust/Boa tests**, including a new no-op setter regression. Repeated `.value`, `.selectedIndex` and `option.selected` writes to the already-selected option, as well as repeating unmatched values when selection is empty, preserve native state and dispatch no programmatic `input`/`change` events. A guard in `select_state_readonly.rs` returns before `calyra_set_select_selection` when the chosen `NodeId` is unchanged, avoiding that method's label re-shaping and redraw request. It does not prove an end-to-end redraw-rate or speed improvement.

This run compiled the pinned native adapter, kept the seven older JS states passing and archived **11 exact source/log/JSON files** separately under [`docs/evidence/blitz-select-idempotent/`](evidence/blitz-select-idempotent/). **No optimized screenshot rebuild was performed.** The earlier 17-file, 731-pixel read-only Vello CPU proof remains intact; CI jobs and source heads are not interchangeable. The next gap is testing native text/style invalidation and option content changes, without confusing those with identical JS setter calls.
