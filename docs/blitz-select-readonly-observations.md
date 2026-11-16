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

[Follow-up CI run #43782046600](https://github.com/AVANT-ICONIC/calyra/actions/runs/43782046600) applied the corrected adapter, completed native Rust/Boa integration tests and checked seven JavaScript selectedness states successfully. Its separate optimized Vello CPU screenshot build was **still running when this note was written**. A passing integration test is not proof of updated rendered pixels.

The new Rust tests assert that a select does not have `TextInputData`, that the Parley label has shaped lines, and that synthetic keydown, IME Commit and paste do not mutate the selected label or JS selection. This does **not** verify real OS IME composition or accessibility.

## Remaining gates and risks

- Do not count live pixel repaint until source-pinned same-document before/after PNGs have passed and been preserved with exact hashes.
- The `calyra_set_select_selection` construction path currently requests redraw even if the selection/label did not change. A future window host must guard against redundant invalidation and measure redraw loops.
- No working popup, user pointer/keyboard selection, input/change dispatch from actual selection, form reset, disabled/optgroup semantics, screen reader output, hardware GPU or macOS/Windows benchmark.
- Keep OpenSpec task 4.1 unchecked and PR #2 draft/unmerged.
