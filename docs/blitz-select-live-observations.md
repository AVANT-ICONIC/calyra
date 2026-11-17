# Blitz live select: semantics versus actual pixels

**Status (2026-11-16):** **real same-document reactive Vello CPU pixels verified and permanently archived**; this is a restricted Stage A experiment, not a production select widget.

## Native evidence already passed

[Real GitHub Actions run #43699535417](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535417) completed successfully on the existing draft branch using the pinned **official** Blitz upstream revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` plus explicitly applied experimental patches. The test job passed **9/9** Rust/Boa integration tests and the assertions for seven live JS selection states. The same native select DOM node was retained.

The current selected option is stored independently of its markup `selected` / `defaultSelected` attributes. Programmatic `select.value`, `select.selectedIndex`, and `option.selected` update the getter and the existing Parley paint-label buffer, without dispatching synthetic `input` / `change` events. The subsequent real native bitmap proof below confirms the paint buffer also changes **raster pixels in place**. However, the buffer still reuses editable `TextInputData`, which remains unsafe/unvalidated for IME, paste and other text-editing paths.

## Independent Chromium baseline (local, not native)

On 2026-11-16, headless **Chromium 144.0.7559.96** via Playwright on Linux ran the isolated three-direct-option HTML and the seven programmatic assignments defined by `harness/chromium_select_contract.py`. The canonical CALYRA HTML/CSS/JS were not modified. The observed states were:

| Mutation | selectedIndex | value | selected option | defaultSelected changes | input/change events |
| --- | ---: | --- | --- | --- | --- |
| initial | 0 | balanced | Balanced | none | none |
| value='quality' | 1 | quality | Visual fidelity | none | none |
| selectedIndex=2 | 2 | performance | Performance | none | none |
| option[0].selected=true | 0 | balanced | Balanced | none | none |
| value='nonexistent' | -1 | empty | none | none | none |
| selectedIndex=1 | 1 | quality | Visual fidelity | none | none |
| option[2].defaultSelected=true | 1 | quality | Visual fidelity | option 2 only | none |

The same output is reproducible using `harness/chromium_select_contract.py --chromium /usr/bin/chromium --out <file>` with Playwright and Chromium installed. This verifies only the enumerated behavior. It does not validate keyboard/pointer option selection, select reset, disabled options, optgroups, focus, accessibility, OS input or paint fidelity.

## Chromium keyboard-event reference (separate from programmatic setter contract)

An additional Playwright/headless Chromium 144.0.7559.96 probe focused the same native browser `<select>` and sent **trusted** user-like `ArrowDown` key presses. On this Linux Chromium configuration, each ArrowDown emitted `keydown` (at the preceding selection) followed by `input`, then `change`, both at the new selected index/value: first `quality` / 1, then `performance` / 2. A subsequent Escape emitted `keydown` without changing selection or dispatching `input`/`change`. This is browser-specific measured behavior, not a universal native OS event ordering guarantee and **not** a Blitz implementation result. The current CALYRA native test intentionally covers only programmatic changes, which dispatch no such events.

## Verified real same-document native Vello CPU pixels

**[CI run #43778999121](https://github.com/AVANT-ICONIC/calyra/actions/runs/43778999121) PASSED** all native steps: pinned upstream + experimental patches, **9/9** native Rust/Boa integration tests, compiled release `calyra_live_screenshot`, executed the original CALYRA JavaScript, captured two authentic **1060×800** Vello **CPU** frames and independently counted a localized pixel transition.

- **One ScriptDocument and one `#priority` node**, not two static HTML snapshots. `Balanced` was painted before `select.value='quality'`, `Visual fidelity` afterward; neither the canonical CSS nor JS files were changed.
- Exactly **732** RGB pixels differ by at least 12/255 in any channel, localized to bounding box **[687, 490, 794, 505]**. No full-scene layout change, screenshot compositing, Chromium painting, hardware GPU or OS input is implied.
- SHA-256 `live-before-balanced.png`: `4bd397daf2be6b314dd788c472545bf0154d3f806cdea2fb1ad66353eb9e4a4f`.
- SHA-256 `live-after-quality.png`: `5d8b90174327eb1689727675122125f49f85a2e1560cf8142cff9bbe80810dcc`.
- SHA-256 `live-paint-pixel-diff.png`: `9e726ca001eff382821d16479afda62c00cf4b0e01ba35c2e119f18b7e7115d5`.
- The original job artifact was validated and archived byte-for-byte by **[archival CI #43780409985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43780409985)**. The archival workflow verified PNG byte hashes, real pixel count and bounds, seven native selection states, 9/9 Rust tests, pinned upstream patch diff, all 16 source hashes, unchanged original CSS and JS, and copied all **18** original files into [docs/evidence/blitz-select-live/](https://github.com/AVANT-ICONIC/calyra/tree/feat/reference-fixtures/docs/evidence/blitz-select-live).

Earlier failed attempts remain part of the audit: [#43699535421](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535421) failed because the example lacked the `Document` trait import, and [#43778282277](https://github.com/AVANT-ICONIC/calyra/actions/runs/43778282277) exposed `DocGuardMut` vs `&mut BaseDocument` in `paint_scene`. Both errors were source-level example build issues, fixed in the verified run.

The **success is narrow**: live pixels and selected-option programmatic state, **not** a popup, accessible `<select>`, physical keyboard/pointer selection, IME safety, hardware-GPU throughput, complete CSS support, Windows/macOS compatibility or production readiness.

## Next engineering gate

With two *real, same-document* native PNGs now verified and preserved, replace the temporary TextInputData/Parley editor hack with a noneditable `SelectData` and a proper selected-option invalidation contract. Assess IME/paste, keyboard navigation and OS event semantics independently; keep OpenSpec 4.1 unchecked until its much broader acceptance criteria are met. No hardware GPU, broad CSS parity, interactive dropdown, OS input or production architecture is proven.
