# Native macOS Blitz form names and values: first proven 5/6, CSS-boundary follow-up

**Date:** 2026-11-17. **Scope:** disposable pinned Blitz `0.3.0-beta.4` checkout, experimental noneditable `SelectData`, explicit AccessKit name/value adapter, log-only activation tracing. **Not full HTML-AAM, original JavaScript in native window or a production Accessibility release.**

## Final native macOS six-field AX contract proof (newest)

**[Actual macOS ARM64 CI #44034737377](https://github.com/AVANT-ICONIC/calyra/actions/runs/44034737377) PASSED ALL STEPS**, including a separate **enforced post-archive 6/6 test**. This is a **second, independently compiled native Mac runner instance**, not a retroactive upgrade of first 5/6 CI #44033572642. The exact same pinned upstream Blitz `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` plus an opt-in experimental native AX semantics adapter ran in a genuine arm64 winit/VelloWindowRenderer GUI, with a real owned CoreGraphics window and read-only trusted macOS `AXUIElement` tree.

| Canonical control | Actual native macOS AX role | Actual native AX title | Actual native AX value | Strict contract |
|---|---|---|---|---|
| Display name | `AXTextField` | `Display name` | `Alex Rivera` | PASS |
| Render priority | `AXPopUpButton` | `Render priority` | `Balanced` | PASS |
| Material intensity | `AXSlider` | `Material intensity 64%` | `64` | PASS, **static attribute-derived only** |
| Enable effects | `AXCheckBox` | `Enable effects Native checkbox with CSS presentation` | `1` | PASS |
| Apply settings | `AXButton` | `Apply settings` | No value required | PASS |
| Reset | `AXButton` | `Reset` | No value required | PASS |

The native Mac test's independent verdict reports `matched_fields: 6`, `total_fields: 6`, `all_six_fields_match: true`. The same actual macOS app exposed **107 AX nodes after lazy activation**, with a correctly handled real `InitialTreeRequested` event and **182 generated internal AccessKit nodes**. **The native form-role/title/value comparison is real OS API output**, not internal Rust assertions or mocked fields. Authored `fixtures/index.html`, `fixtures/reference.css`, `fixtures/reference.js` remained unchanged and original JS was explicitly omitted from the static native GUI test.

The sixth-field repair derives whitespace from **computed CSS block-level outside display** around descendants in an ordinary HTML label, while preserving intentional inline concatenation. The independent [Linux native regression CI #44034710357](https://github.com/AVANT-ICONIC/calyra/actions/runs/44034710357) passed **9/9 real Rust tests**, including both block-boundary and inline-preservation cases. This is no longer a CALYRA-only string tweak.

**Permanent first-party evidence:** [40 original native Mac runner files plus SHA-256 manifest](evidence/blitz-macos-ax-form-semantics/), including [six-field OS AX verdict](evidence/blitz-macos-ax-form-semantics/ax-form-semantic-verdict.json), [actual native AX before/after census](evidence/blitz-macos-ax-form-semantics/actual-native-ax-hit-test-after.json), [real AccessKit event log](evidence/blitz-macos-ax-form-semantics/native-app.log), [screenshot](evidence/blitz-macos-ax-form-semantics/actual-patched-blitz-window.png) SHA-256 `2aced08e83345e5a8846229d02e21ebc5a0d6b16609935fbe45d81c9a45524e9`, full temporary upstream patch source and actual Mac compile logs. [17 original Linux native regression files plus SHA manifest](evidence/blitz-ax-form-regression/) preserve independent `9 passed, 0 failed` results.

**Do not confuse this milestone with complete accessibility:** the synthetic static range value is not live user adjustment; the range thumb and drag remain missing. Native `ActionRequested` is still TODO; no verified VoiceOver, keyboard focus/action, actual OS pointer/IME, full HTML-AAM naming, original CALYRA JS in live native Blitz, GPU device proof, complete CSS parity or fair performance comparison. OpenSpec **3.1, 4.1 and 4.2 remain unchecked**; PR #2 remains draft, unmerged; `main` untouched.

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
