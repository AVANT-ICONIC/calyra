# CALYRA Stage A: Blitz document-level event propagation

**Date:** 2026-11-15. **Pinned candidate:** DioxusLabs/Blitz 0.3.0-beta.4, revision 4f61cffacee50fe4f944ebe9d0470d9a5d3997e0.

**Outcome:** Confirmed upstream document-event propagation defect and verified a one-line experimental engine patch against the **original, byte-unchanged CALYRA JavaScript**. These are internal native headless event tests, not OS keyboard or production compatibility results.

## Before: original clean Blitz source

[Actual native diagnostic #43684009049](https://github.com/AVANT-ICONIC/calyra/actions/runs/43684009049) compiled and passed on Linux. The original CALYRA JS SHA-256 was 9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de. Read-only diagnostic listeners were registered after CALYRA's script executed.

| Escape path | Listeners that actually received the event | Original menu closes |
|---|---|---|
| Native UiEvent::KeyDown on focused command | command, body, window | **No** |
| Explicit DOM event on focused command | command, body, window | **No** |
| Explicit DOM event on body | body, window | **No** |
| Explicit DOM event targeting document | document, window | **Yes** |

All events had event.key = Escape and bubbles = true; zero JS exceptions.

### Root cause in pinned upstream

Blitz's packages/blitz-dom/src/traversal.rs BaseDocument::node_chain() retains only ancestor nodes where is_element() is true. The document root node is not an HTML Element and gets excluded. Document-level addEventListener() registers correctly but does not receive bubbling keyboard events. Window listeners are dispatched independently, explaining why they worked before the fix.

## After: exact scoped engine patch

[One-line test patch](../native/blitz/patches/document-event-chain.patch) includes the document root id in the event chain. The patch was applied **only inside a disposable Blitz checkout after checking its clean pinned revision**, not to the original CALYRA HTML/CSS/JS.

[Actual patched native run #43684229853](https://github.com/AVANT-ICONIC/calyra/actions/runs/43684229853) compiled and passed the checks:

- Native keydown now bubbles to command, body, **document**, and window, closing the menu using the original JS handler.
- Even without delayed-focus instrumentation, the original menu open → Escape → close sequence succeeds. Menu is hidden, aria-expanded is false, and focus returns to the menu-toggle button.
- The instrumented document listener observed key = Escape; zero JS exceptions.
- **Still broken:** immediate focus when opening the menu; a later JavaScript focus() succeeds.
- **Still broken:** select layout (0×0) and missing selected-option value; the patch does not address control behavior.

## Verifiable source files

| Exact original artifact | SHA-256 |
|---|---|
| Unpatched keyboard-routing JSON | e9eb2b0fb8c173641a0a87721be4502d6bd92625eae49da1b8ef38f5c1f15e92 |
| Patched keyboard-routing JSON | e7d65be71cd98f333cb450e8e734b75500c36c078bb8946586f1caf249082c4f |
| Patched original-JS interaction JSON | 21d6c0101857db7bc13283a064fabf70d9aac8d41421969e2c4b5f695f7c27db |
| Patched Escape regression JSON | 0fc1e754481f65737451114669895f4b77f12e3eb5a3ceb3e4b0cd0f0116441b |
| Actual applied upstream diff | 9f52e05db2d807adab7ce1f2992c7efd090f242a490df84a959d25e570419fb3 |

[Original native artifacts](https://github.com/AVANT-ICONIC/calyra/actions/runs/43684009049) and [patched native artifacts](https://github.com/AVANT-ICONIC/calyra/actions/runs/43684229853) have limited retention. The dedicated one-shot archival workflow copies the five exact verified originals into docs/evidence/blitz-keydown/ only if all file hashes and critical event observations pass. Do not mark durable archival complete until its GitHub run succeeds.

## Review boundaries

The patch affects document-level bubbling for **all event types**, not only keydown. Wider pointer/click/capture-phase regression tests, an upstream code review, and separate native OS input checks are required before shipping it as a runtime modification.

Hardware GPU, IME, accessibility, event ordering, complete browser compatibility, memory/performance improvements and Apple Silicon native execution are unverified by this test. OpenSpec task 3.2 remains completed as a candidate experiment; task 4.1 remains unchecked. CALYRA PR #2 stays draft and stacked.
