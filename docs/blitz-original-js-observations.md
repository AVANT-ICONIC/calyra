# Blitz Stage A: original CALYRA JavaScript on Boa (2026-11-15)

**Outcome:** real unmodified JavaScript evaluated with no reported exceptions on the Blitz **ScriptDocument** runtime. **Partial functional behavior**, not browser compatibility or an end-user-ready application.

## Actual runtime provenance

- [Successful run 43680014113](https://github.com/AVANT-ICONIC/calyra/actions/runs/43680014113), Ubuntu 24.04, Rust 1.91, exact upstream Blitz **0.3.0-beta.4**, revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, via actual `blitz-vibey-script` + Boa.
- **2/2 actual Rust integration tests compiled and ran.** Script engine build finished and report JSON records actual messages from `ScriptDocument::take_messages()`; `take_js_errors()` reported **zero** for both tests.
- `fixtures/reference.js` was **byte-identical**, SHA-256 `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`; the unchanged canonical CSS SHA-256 was checked separately: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`.
- The canonical HTML was adapted **only to inline the original CSS/JS assets** and prepend a tiny test-only `window.__calyraFixtureQuery` assignment to choose fixture. Unlike previous *static* Blitz capture, DOM state was not pre-patched by the harness: the original JS performed the initialization.
- The temporary Rust test was overlaid on the pinned upstream source in CI, not pushed to upstream. Exact executed test SHA-256: `0dafe6d1ce53df84e0a5280fb6aa7ce1ddafeaf7a7f03dd93fc44fa17f10feae`.
- Raw build/runtime logs and original result/provenance JSON are available in [artifact 14148246315](https://github.com/AVANT-ICONIC/calyra/actions/runs/43680014113/artifacts/14148246315) (7-day retention).

## Observed original-script behavior

| Original `reference.js` behavior | Actual observation |
|---|---|
| Set `body.dataset.ready` on page initialization | `true` |
| Activate exactly one fixture and selected nav item | `1` / `1` |
| Apply-button `click` handler | Executed, status changed to `Applied: Alex Rivera ·  · 64% · on` |
| Read selected `<select>` value | **Empty string**, where Chromium reports `balanced` |
| Open menu with real original JS listener | `aria-expanded=true`, `hidden=false` |
| Focus first command on open | **Not observed**: `document.activeElement` null |
| Escape closes menu | **No**: expanded stayed true; hidden stayed false |
| Uncaught JS errors | **0** in both test cases |

The select behavior is consistent with the observed layout defect (native `select` has 0×0 px) and a source-backed API limitation: in this pinned build `blitz-vibey-script/src/dom/element/form_controls.rs` returns a generic value attribute when an element lacks a text editor, rather than computing selected option value for a select. The button/menu focus and Escape failures require isolation, because the test dispatches synthetic internal events, not actual OS input or keyboard routing.

**Machine-readable evidence:** [controls](evidence/blitz-js/calyra-js-controls.json) and [interaction](evidence/blitz-js/calyra-js-interaction.json). These records preserve the exact original JSON fields; reproduction requires the pinned Blitz checkout and the CALYRA CI workflow.

## Architecture impact

The static `blitz` HTML wrapper is not interactive; Blitz's optional `blitz-vibey-script` is a distinct **Boa JavaScript engine with native DOM event handling**. The original CALYRA script running, even partially, substantially strengthens Blitz as the native HTML/CSS/JS candidate compared with RmlUi's adapted RCSS-only path.

Still **NOT demonstrated**: complete DOM/browser behavior, native OS input, default native select widget, range styling, focus/key semantics parity, GPU hardware acceleration, IME, accessibility, memory, binary size or performance. Do not check OpenSpec task 4.1 yet; it requires broader input/focus and visual fidelity evidence.

**Next precise diagnostic:** after a menu opens, attempt an explicitly delayed `.focus()` after a style/layout flush, then repeat Escape event routing, to distinguish focus timing from event dispatch or JS listener errors. Separately isolate select-option value lookup.
