# Native macOS Blitz form names and values: first proven 5/6, CSS-boundary follow-up

**Date:** 2026-11-17. **Scope:** disposable pinned Blitz `0.3.0-beta.4` checkout, experimental noneditable `SelectData`, explicit AccessKit name/value adapter, log-only activation tracing. **Not full HTML-AAM, original JavaScript in native window or a production Accessibility release.**

## Actual first macOS Apple Accessibility evidence

[Native Mac ARM64 CI #44033572642](https://github.com/AVANT-ICONIC/calyra/actions/runs/44033572642) **fully PASSED its source-pinned native diagnostic**, built genuine arm64 BlitzShell/winit/VelloWindowRenderer, ran the actual macOS window, and enumerated actual native AX roles/titles/values from the real process after async AccessKit activation. The original authored CALYRA HTML/CSS/JS were byte-identical and the static test snapshot explicitly omitted JavaScript.

**Five of six strict reference fields matched actual OS AX role/title/value:**

| Field | Actual macOS AX role | Observed native AX title | Observed value | Original Tauri matching contract |
|---|---|---|---|---|
| Display name | AXTextField | `Display name` | `Alex Rivera` | Passed |
| Render priority | AXPopUpButton | `Render priority` | `Balanced` | Passed |
| Material intensity | AXSlider | `Material intensity 64%` | `64` | Passed **for attribute-derived static range state only** |
| Enable effects | AXCheckBox | `Enable effectsNative checkbox with CSS presentation` | `1` | **Failed title spacing** |
| Apply settings | AXButton | `Apply settings` | n/a | Passed |
| Reset | AXButton | `Reset` | n/a | Passed |

This is a genuine incremental improvement over the previous 0/6 **name/value** matches. Earlier actual native Mac Accessibility activation proved all six *roles* were already exposed after the delayed `InitialTreeRequested` event. The patched code uses HTML `<label for>` and enclosing-label text, actual `TextInputData`, native read-only `SelectData`, checkbox toggled state and simple attribute-derived range numeric value/min/max. The implementation does **not** hardcode the CALYRA names or values.

Raw native screenshot, 107-node OS Accessibility census, actual activation logs, full patched upstream diff, hashes and runner/build records are archived as **39 original runner files plus separate SHA-256 manifest** in [`docs/evidence/blitz-macos-ax-form-semantics/`](evidence/blitz-macos-ax-form-semantics/). See [machine-readable six-control verdict](evidence/blitz-macos-ax-form-semantics/ax-form-semantic-verdict.json).

## Independent original native Rust regression (not a macOS substitute)

[Linux pinned native Rust CI #44034096672](https://github.com/AVANT-ICONIC/calyra/actions/runs/44034096672) compiled and **passed 7/7** actual integration tests against disposable pinned upstream Blitz and experimental adapter, including external/enclosing labels, ARIA name precedence, real SelectData selected text, checkbox checkedness, range numeric min/max/clamping, and ignoring `aria-hidden` button decoration. **16 original runner records plus SHA manifest** are preserved in [`docs/evidence/blitz-ax-form-regression/`](evidence/blitz-ax-form-regression/). This unit result does not prove platform-native macOS AX roles by itself.

## Precisely isolated sixth-field bug

The original `FlatText` accumulator joins text nodes inside adjacent elements without automatically inserting whitespace. CALYRA's actual `<label>` has adjacent styled `<strong>` and `<small>` with **computed CSS `display:block`**. The initial adapter concatenated `effectsNative` despite native macOS WKWebView exposing `effects Native`.

The revised restricted adapter in `native/blitz/experiments/apply_ax_form_semantics.py` uses each child's **computed display outside** to add word boundaries only around actual block-level descendants. It does not hardcode `small`, `strong` or the fixture's label. A new **nine-test** native Rust regression adds a computed `display:block` label case and a contrasting truly inline `Pre<strong>fix</strong>` concatenation case. **The expanded [Linux CI #44034710357](https://github.com/AVANT-ICONIC/calyra/actions/runs/44034710357) has now PASSED 9/9 genuine native Rust tests** including both computed-CSS block spacing and inline concatenation, with [17 original runner files plus SHA-256 manifest](evidence/blitz-ax-form-regression/). The updated Mac CI enforces **6/6 actual OS AX matches only after archiving diagnostic evidence**; any partial result remains a real failure, not a cosmetic success. These reruns are separate exact revisions and must be reviewed independently before declaring the last field fixed.

## Remaining functional limitations

A correctly named `AXSlider` does not mean its visual thumb or pointer drag exists. The pinned native Blitz painter still lacks `type=range` thumb painting and range input has no live state model; the current `64` is attribute-derived only. The BlitzShell `ActionRequested` event handler remains TODO; there is **no real accessibility action dispatch**, VoiceOver test, OS keyboard/pointer or IME input, original JavaScript running in this window, hardware GPU identification, full CSS compatibility or matched-performance proof. Keep OpenSpec 3.1, 4.1, 4.2 unchecked, PR #2 draft/unmerged and `main` untouched.
