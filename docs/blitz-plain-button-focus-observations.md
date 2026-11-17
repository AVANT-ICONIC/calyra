# CALYRA Stage A: real Blitz/Boa plain-button focus fix (2026-11-15)

**Experimental result: SUCCESS in a headless native-engine test, not OS pointer parity.**

## Source and execution

- [Actual Linux build and test #43687424754](https://github.com/AVANT-ICONIC/calyra/actions/runs/43687424754): **7/7 Rust/Boa tests passed**, no reported JavaScript exceptions. Official pinned Blitz revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, Rust 1.91.0.
- Original CALYRA `fixtures/reference.js` SHA-256 `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`; CSS SHA-256 `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`. Both were checked and left untouched.
- Two **separate experimental upstream patches** applied to a temporary clean pinned checkout: [document-event bubbling](../native/blitz/patches/document-event-chain.patch) and [plain button focus](../native/blitz/patches/plain-button-focus.patch). Neither is merged into upstream Blitz or shipped as a CALYRA runtime.

## Root cause and targeted patch

In pinned `packages/blitz-dom/src/events/pointer.rs`, `handle_click` invokes the original JavaScript listener before running the default click action. On `<button type="button">`, no branch qualifies as a handled click; the generic fallback calls `clear_focus()`, erasing focus set synchronously by the original JavaScript handler.

The experimental patch adds a branch for **non-submit buttons with `type="button"`** that treats the click as handled, preventing the unconditional focus clear. This deliberately does not alter checkbox/radio inputs, form submissions, or clicks on noninteractive elements. It is not a complete specification of HTML button focus behavior or event-capture semantics.

## Verified original behavior without delayed focus intervention

| Test | Native Blitz/Boa observation |
|---|---|
| Original menu-toggle click | `aria-expanded="true"`, menu visible |
| Immediate focus after original menu-open handler | `data-command="inspect"` focused, verified both via native node ID and `document.activeElement` |
| Escape dispatched through native UI event queue | Menu closes: `aria-expanded="false"`, `hidden=true` |
| Focus restoration on closing menu | `document.activeElement.id="menu-toggle"` |
| Original Focus destination button click | `document.activeElement.id="destination"`, native node focus matches |
| Original `interaction-status` update | `Destination focused` |
| JavaScript exceptions | 0 |

The original event bubbling fix remains necessary for document-level Escape. [Prior before/after evidence](blitz-document-event-chain-observations.md) independently isolates it.

## Exact native artifact digests

| Original run file | SHA-256 |
|---|---|
| `calyra-js-focus-patched.json` | `baeddf5043b462b3e1b55e023351ca6987faa3fe356df7d5d3435313bbd54870` |
| `calyra-js-destination-focus-patched.json` | `b5d67d49404e661532f81165a83e9023d9739ff81f1359e445f78d1627f89463` |
| `applied-upstream-diff.patch` | `b5352edc1092bb3b7ed815d0e758b2965719631b9a8088ef738f6d1f17f17e3b` |
| `source-sha256.txt` | `4649dfa2c805567cdbf49fb576ce43b5c135f0477160246b204b076c4d0b49ef` |

The [original CI artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43687424754/artifacts/14150639783) has temporary retention. A separate one-shot archive workflow copies the four exact originals to `docs/evidence/blitz-focus/` only after hash and result validation. Verify that archival run before claiming permanence.

## Remaining compatibility gates

- Physical operating-system mouse/keyboard and real window, keyboard Tab-order/Shift-Tab, click event phases, IME, accessibility and hardware GPU remain untested.
- The `<select>` control is still zero-sized and its `.value` fails to return the selected option. Range styling also differs.
- The engine patch is a narrow experiment, not production-ready until reviewed against general button semantics, regression behavior and upstream acceptance.
- OpenSpec task 4.1 stays **unchecked**. CALYRA PR #2 stays **draft and unmerged**.

This experiment provides a focused, reproducible implementation path instead of requiring a rewrite of application JS.
