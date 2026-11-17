# CALYRA: computed CSS typography invalidation of native SelectData

**Status:** native Rust/Boa and Vello CPU experiment **verified**, not production CSS/input compatibility. Source-pinned experiment date: **2026-11-16**. Primary [successful CI #43919838241](https://github.com/AVANT-ICONIC/calyra/actions/runs/43919838241) and [19 original preserved artifacts](evidence/blitz-select-typography/).

## Specific failure being addressed

Prior native experiments proved JavaScript selectedness, read-only noneditable selected-label rendering, idempotent JS property writes, and direct selected-option text mutation. They did **not** prove that changing **computed CSS typography** while the selected option and its text remain unchanged re-shapes the cached Parley glyph layout. A browserless CSS runtime needs this separation: a style change can alter glyph metrics without changing the DOM selection.

## Experiment (restricted prototype, upstream unmodified outside disposable checkout)

The new `native/blitz/experiments/apply_select_typography_refresh.py` runs **after** `apply_readonly_select.py` and `apply_select_option_text_refresh.py` against Blitz commit `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`. It fail-closes on exact source-anchor drift and modifies only the temporary upstream clone.

- `SelectData` additionally caches `typography_fingerprint: String`, based on computed Stylo values for font family/size/weight/stretch, font variations/features, line height, letter/word spacing, white-space/wrap, word/line breaks, direction and other shaping-related properties, plus viewport scale.
- `BaseDocument::resolve` calls `calyra_refresh_select_typography_after_restyle()` immediately **after** `resolve_stylist` and before Taffy construction/layout. Only changed fingerprints call the existing `calyra_set_select_selection` read-only Parley shaping path.
- The selection's native `NodeId`, value and option text are unaffected by a style-only change. A paint-only background change does not change the fingerprint or force the explicit select glyph rebuild.
- This is an **experimental correctness-first scan** of select elements and serialized computed CSS properties each resolve. It is **not** an optimized incremental invalidation algorithm. Work proportional to full DOM size and number of selects has not been measured, and could be inappropriate for production.

The canonical `fixtures/reference.css` and `fixtures/reference.js` were pinned by exact SHA-256 and not modified; the temporary screenshot harness injects an explicit runtime CSSOM property write `select.style.setProperty('font-size','32px')` into the original single `ScriptDocument`.

## Real evidence

- **[CI #43919838241](https://github.com/AVANT-ICONIC/calyra/actions/runs/43919838241) PASSED fully.** Actual pinned Rust/Boa **12/12 tests** passed, including existing seven JS selectedness states, noneditable no-editor invariant, programmatic event silence, selected-option text mutation and new computed CSS typography regression.
- Native Parley shaped label height: **19 → 38 px** for font growth to `32px`; after shrinking to `18px`, height **21 px**. The selected option, visible text `Balanced`, value `balanced`, index `0` and recorded `input`/`change` events remained unchanged.
- Two real **1060×800 Vello CPU** frames from **the same document**, with no HTML replacement/reparse, differ at **1,639 pixels** (RGB-channel threshold 12/255), localized to bbox **[688, 483, 833, 507]**. This is demonstrated native glyph/ink change, not a synthetic screenshot or hardware GPU render.
- The producing CI verified and **committed 19 original byte-exact artifacts** to [`docs/evidence/blitz-select-typography/`](evidence/blitz-select-typography/), including two PNGs, pixel-diff PNG, JSON result, native Rust test and optimized build logs, original applied-upstream diff, original JS state snapshots, and source hash manifest.
- Screenshot hashes: before `485552ed102b35a3934fa3aeb0adac00bb974ef876f932a2a0c5fd374a39188a`, after `f89c8f68b73141d32304ea87e31b485263952f46da2819b497021d8db1d03f10`, diff `d785af3883928add1ac1834390efd78cee9ade84376b45769e77fdd28b2ce627`. Original canonical CSS SHA-256 `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c` and JS SHA-256 `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`.
- The producing workflow was subsequently made **manual-only**. Its CI report applies to the exact producing source/commit. Disabling the push trigger afterward does not constitute a new runtime test.

## Acceptance boundaries

**Proved for this experiment:** an inline CSSOM `font-size` change can re-shape and repaint the native selected-label glyphs without a selection/text mutation; unchanged computed typography avoids the new explicit style-update path; prior label mutation and JS state cases still pass.

**Still not proven:** style changes from classes, inherited styles, custom properties, dynamic stylesheet replacement, @font-face and fallback loading, zoom/device-scale transitions, complete text shaping/RTL, accessibility semantics, OS IME, actual keyboard/pointer user selection, popup behavior, GPU rendering, Windows/macOS parity, pixel parity against Chromium, layout intrinsic sizing or latency/memory performance.

**Next decision, not a license for endless patches:** prioritize source-pinned CSS class/inheritance invalidation and no-op performance inspection only if these are material for Stage A, then return to the broader engine comparison. A select can be an impressive narrow proof while still being the wrong production foundation. Keep `openspec/changes/establish-native-css-feasibility/` **task 4.1 unchecked**, PR #2 **DRAFT / UNMERGED**, `main` unchanged.
