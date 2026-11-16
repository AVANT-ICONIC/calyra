# CALYRA / Blitz: native noneditable select renderer proposal

**Status:** historical architecture proposal, subsequently implemented as a **restricted experimental adapter** (not production). Date: 2026-11-16. Verified implementation and 731-pixel same-document native proof: [blitz-select-readonly-observations.md](blitz-select-readonly-observations.md), [CI #43783621933](https://github.com/AVANT-ICONIC/calyra/actions/runs/43783621933). This document retains the original design reasoning and proposed gates as historical context.

## The distinction that matters

Real CI [#43778999121](https://github.com/AVANT-ICONIC/calyra/actions/runs/43778999121) proves an unchanged `ScriptDocument` can repaint option-label pixels, but the label currently lives in `SpecialElementData::TextInput(TextInputData)`. KeyDown is prevented by an extra patch; other editor operations, IME, cut/paste, focus/caret and selection are not safely excluded. Do **not** promote the current workaround as a production control.

## Existing upstream integration points (Blitz 0.3.0-beta.4, pinned SHA `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`)

| Source | Verified architectural responsibility |
| --- | --- |
| `packages/blitz-dom/src/node/element.rs` | `SpecialElementData` holds `TextInput` or native checkbox state; introduce a **different** `Select` variant |
| `packages/blitz-dom/src/node/text.rs` | `TextInputData` owns a `parley::PlainEditor`; never reuse that editor object for select |
| `packages/blitz-dom/src/layout/construct.rs` | experimental `create_text_editor` path selects initial label, sets focus/IME and editor styles; replace select-specific branch with a read-only shaping path |
| `packages/blitz-paint/src/render.rs` | `ElementCx.draw_text_input_text` draws text **and** caret/selection; add a distinct label-only paint path |
| `packages/blitz-vibey-script/src/dom/element/select_state.rs` | current experimental JS selection store with setters/getters; migrate ownership to one native model |
| `packages/blitz-dom/src/document.rs` | current `calyra_sync_select_label` writes editor text; bridge must call native read-only label shaping and request repaint instead |
| `packages/blitz-dom/src/events/keyboard.rs` | current KeyDown bypass is insufficient to prove IME/clipboard safety; remove reliance on editor routing entirely |

## Pinned upstream source audit (2026-11-16; inspected, not compiled)

The integration points below were inspected directly from upstream [Blitz commit `4f61cffa`](https://github.com/DioxusLabs/blitz/tree/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0). They refine the implementation route, **not** the acceptance status.

1. **Typed DOM state must extend clone semantics.** `packages/blitz-dom/src/node/element.rs` implements `Clone` for `SpecialElementData` with an explicit exhaustive `match`. Adding `SpecialElementData::Select` without its clone arm will fail compilation; cloning current selection must be defined intentionally. `ElementData` already has `inline_layout_data: Option<Box<TextLayout>>`, but that is ordinary inline content and should not be silently repurposed as a select's mutable editor.
2. **An existing read-only shaping primitive exists.** `packages/blitz-dom/src/node/text.rs` defines `TextLayout { text, layout: parley::layout::Layout<TextBrush>, content_box_subpixel_offset, … }` with `Clone + Default`. `layout/inline/build.rs::build_inline_layout_into` uses `LayoutContext::tree_builder(font_ctx, scale, …)` followed by `builder.build_into(&mut text_layout.layout)`. Investigate using that path for the generated select label before adding a second Parley API wrapper. Test CSS font, alignment, line height and intrinsic sizing rather than assuming the normal inline-root path is directly reusable.
3. **The editor constructor is intrinsically unsafe for a select.** `layout/construct.rs::create_text_editor` always creates `TextInputData` / `parley::PlainEditor` and calls `shell_provider.set_ime_enabled(true)` for an already-focused input. The new select constructor must not call this function. A temporary KeyDown bypass does not cover all editor, composition or clipboard routes.
4. **Paint has a shared glyph pipeline but an editor-specific caret path.** `packages/blitz-paint/src/render.rs::draw_text_input_text` draws selection geometry and a caret when focused before it calls `crate::text::stroke_text`. Noneditable select paint should use the shared glyph stroke function with its own clipped transform/offset and shaped label, never `editor.try_layout()`, `selection_geometry()`, or `cursor_geometry()`. Keep the exact same-document two-frame Vello CPU proof as the pixel gate.
5. **State migration must be atomic.** The current experiment's `blitz-vibey-script/.../select_state.rs` holds JS selectedness independently. Native `SelectData` should own the single current selection used by Boa getters/setters and paint. If a transition layer is necessary, make its authority unidirectional and test all seven Chromium-compatible programmatic states before deleting old code.

**First compile gate:** define the new variant plus correct clone, read-only layout ownership and direct accessors; assert the select has no `TextInputData`/editor and that a focused select never enables IME via the text-input constructor. **Second gate:** link JS setters to that native state and reprove the 9 Rust/Boa behaviors. **Third gate:** render 1060×800 native same-document before/after frames and inspect exact raster changes. These are a proposed dependency order, not executed tests.

**Known risk:** `TextLayout` and the ordinary inline shaping path assume an inline-root tree, while a select's visible label derives from an option. Reuse the shaping machinery, not an implicit assumption that original option nodes should paint as normal inline children. If synthetic label layout cannot integrate with sizing and clipping without duplicating the renderer, report the limitation rather than extending the experimental patch indefinitely.

## Proposed minimal data contract

```rust
// Conceptual sketch; confirm exact Parley APIs with the pinned compiler.
struct SelectData {
    selected_option: Option<NodeId>,
    visible_label: String,
    shaped_label: parley::layout::Layout<TextBrush>,
    content_box_subpixel_offset: taffy::Point<f32>,
}
```

The **native select node** becomes the single source of truth for current selection; HTML `selected` / `defaultSelected` remains author-defined default state. A separate read-only Parley `Layout<TextBrush>` handles glyph shaping, line metrics and paint without exposing any editor `cursor`, `insert`, `selection`, `preedit` or clipboard mutation. The conceptual fields above are **not compiled code**.

### Necessary invariants

1. A select uses `SpecialElementData::Select` and has **no `TextInputData` and no `PlainEditor` instance**; focus does not enable text IME.
2. The native selected option is the authoritative state, shared by Boa getter/setter, native paint and eventually user input, not mirrored in two separate stores.
3. `select.value`, `selectedIndex` and `option.selected` apply to **the same native DOM node**, update the read-only layout in place, request one repaint and emit no programmatic `input`/`change`.
4. Programmatic `defaultSelected` mutates the markup default without replacing current selection; form reset remains a separate, **unimplemented** acceptance test.
5. Painting uses the existing computed CSS typography and clipping, but **never** calls the editor caret/selection code. Updating the label should invalidate text shaping and paint without rebuilding the author markup.
6. Actual user selection, when later implemented, must be tested separately against Chromium's `input` then `change` behavior; do not synthesize those events from property writes.

## Proposed minimal proof workflow (next implementation experiment)

- Use a disposable, clean upstream checkout at the exact pinned SHA. Add a **separate experimental patch** for `SelectData`; do not overwrite or rewrite the existing successful evidence or canonical fixtures.
- Native unit/integration tests must first assert no `TextInputData` is present for the select, current selection is consistent with JS API, and keydown / IME / paste cannot edit visible label independently of selected state. No fake physical OS input verdict.
- Native Vello **CPU** source-pinned screenshot must again capture the same 1060×800 `ScriptDocument` before and after `select.value='quality'`; test a localized nonzero diff and exact label raster; preserve both frames and complete native logs, **even if failing**.
- Compare with independent Chromium on the same minimal fixture, including focus and event order; retain different labels for restricted/current versus full/production behavior.
- Track intrinsic select sizing, popup options, keyboard, disabled/optgroup, form reset, accessibility and macOS/Windows as **explicit open gaps**, not as accepted features.

## Stop condition

If isolated read-only shaping cannot preserve CSS typography and in-place pixels without requiring substantial text-rendering duplication or introducing editor behavior again, classify the candidate as **restricted**. Do not spend unlimited engineering effort turning an experimental native demo into a replacement browser engine.

**Change boundary:** continue the existing `openspec/changes/establish-native-css-feasibility/`; task 4.1 is still unchecked. Keep PR #2 draft and unmerged.
