# CALYRA pinned native RangeData: actual macOS thumb and current-state proof

**Date:** 2026-11-17. **Status:** native numeric state and real Mac thumb verified in two distinct primary-source CI runs. Dynamic script/two-frame pixel test is a separate acceptance gate, not inferred from the screenshot.

## Verified implementation boundaries

The preexisting pinned [Blitz 0.3.0-beta.4 at `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`](https://github.com/DioxusLabs/blitz/tree/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0) had checkbox/radio and text-input native data, but no native RangeInput current value or native track/thumb painter. The earlier 6/6 macOS AX form semantics experiment exposed `AXSlider` `64`, **derived only from the static HTML attribute**.

This turn's experimental `RangeData` exists as `SpecialElementData::Range` on the **native document node**, independent from Parley `TextInputData`. The source-pinned, fail-closed temporary overlay `native/blitz/experiments/apply_range_state_paint.py` adds first-construction numeric state, min/max/step coercion and clamping, current vs HTML/default value, a direct native document mutation, a state-derived track/fill/thumb renderer, Boa property getter/setter routing and an AX numeric value derived from the same native state. No cloned mutable state in Boa and no synthetic input/change on programmatic setter. The source patch is applied **only to disposable upstream checkouts**, not a bundled production CSS engine or original CALYRA HTML/CSS/JS.

### Proof 1: 16 actual native Rust regressions

[GitHub Actions #44040509280](https://github.com/AVANT-ICONIC/calyra/actions/runs/44040509280) **completed successfully** and compiled the pinned source overlay. All **16/16 tests passed**, including the previous 9 AX name/form cases plus independent `RangeData` default/current, idempotence, step, `step=any`, min/max, invalid numeric coercion, reset, explicit HTML attribute unchanged and direct live AX tree value after a native mutation. The initial run [#44040199473](https://github.com/AVANT-ICONIC/calyra/actions/runs/44040199473) failed before compilation because the patch's exact JS getter anchor didn't match the earlier select overlay; that anchor was repaired and test rerun cleanly. Original runner logs/source hashes/diff and machine-recorded results are preserved as [17 original files plus SHA manifest](evidence/blitz-native-range-regression/).

**Important:** these Rust DOM unit tests are not native macOS user input; no actual mouse/keyboard was used.

### Proof 2: real Apple Silicon native GUI paints the slider thumb

[Actual Mac ARM64 GitHub Actions #44041044304](https://github.com/AVANT-ICONIC/calyra/actions/runs/44041044304) **passed every step**. It compiled the same pinned upstream Blitz with the opt-in `RangeData`, painted a true app-owned `blitz::launch_static_html` Winit/VelloWindowRenderer GUI, captured the CoreGraphics window image at **912 × 740** and enumerated the **actual macOS AXUIElement** tree. The native Mac screenshot's SHA-256 is `a6a4b2ce3413e926f16dcd243c68136cdbef7a6c0428655bf01804fce3de5db3`. A separately archived and independently verified genuine same-geometry earlier native Mac baseline without range thumb has SHA-256 `2aced08e83345e5a8846229d02e21ebc5a0d6b16609935fbe45d81c9a45524e9`.

The predeclared slider image ROI `(270, 593, 827, 630)` contains **1,105 pixels changed at threshold 12/255**, and direct visual inspection confirms a white circular thumb at the correct **64%** state on a track, where the genuine earlier native screenshot showed only a thin white line. This is actual Mac GUI paint evidence rather than a generated illustration or hidden image.

Native macOS AX still exposes **6/6 required canonical control role/title/value pairs**, including real `AXSlider` title `Material intensity 64%` and value `64`, now read from live `RangeData` instead of only the HTML attribute. Full [42 original Mac runner evidence files plus SHA manifest](evidence/blitz-macos-range-thumb/) include [pixel contrast verdict](evidence/blitz-macos-range-thumb/native-range-paint-evidence.json), [actual rendered screenshot](evidence/blitz-macos-range-thumb/actual-patched-blitz-window.png), [6/6 OS AX verdict](evidence/blitz-macos-range-thumb/ax-form-semantic-verdict.json), exact source patch, native executable proof and build logs.

The Mac renderer **did not run the canonical JavaScript in this static GUI**, and this run painted just the initial 64 state. It does **not** prove the thumb moves on an actual OS mouse drag, keyboard arrows, accessibility action, or original browser JS. No hardware GPU device was independently confirmed.

## Separate dynamic behavior acceptance

Added `native/blitz/experiments/range_js_semantics.rs`: three real Boa `ScriptDocument` tests of `input.value` setter/getter, native current vs default/HTML value, no synthetic `input/change`, min/max/step and unaffected text input. Also added `native/blitz/experiments/calyra_live_range_screenshot.rs`, which executes the original authored JavaScript in one native ScriptDocument (inlined delivery), renders Vello **CPU** 1060×800 before **64** and after direct Boa property write **18**, ensures the SAME native DOM node and default value 64, and quantifies real pixel movement across the two frames. These are distinct from native macOS GUI paint and actual OS interactions. The initial #44041208239 JS test build was blocked by a **test-only undeclared `accesskit` dev dependency** in the script crate, not a production code failure; the script-only test was narrowed to JS while independent Rust DOM tests cover AX. Final combined CI: [#44041957819](https://github.com/AVANT-ICONIC/calyra/actions/runs/44041957819). **Do not mark this third gate passed until its current run, actual test logs and image hashes are inspected.**

## Remaining tasks, no false acceptance

A screenshot with a thumb does not constitute a fully interactive slider. Still missing/unverified: actual Mac OS pointer-down/drag/release and keyboard arrows/Home/End, corresponding native `input`/`change` event semantics, real assistive `ActionRequested` dispatch (pinned BlitzShell has a TODO), true VoiceOver, popup for native select, original full JS executed inside the macOS GUI, complete CSS accent-color/appearance, OS IME, actual Metal GPU identification and comparable multi-run performance. Keep existing OpenSpec **3.1/4.1/4.2 unchecked**, draft PR #2 unmerged, and `main` untouched.
