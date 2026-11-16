# Blitz live select: semantics versus actual pixels

**Status (2026-11-16):** native selectedness and label-buffer state proven by Rust/Boa tests; same-document Vello CPU bitmap transition **not yet verified**. This is a restricted Stage A experiment, not a production select widget.

## Native evidence already passed

[Real GitHub Actions run #43699535417](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535417) completed successfully on the existing draft branch using the pinned **official** Blitz upstream revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0` plus explicitly applied experimental patches. The test job passed **9/9** Rust/Boa integration tests and the assertions for seven live JS selection states. The same native select DOM node was retained.

The current selected option is stored independently of its markup `selected` / `defaultSelected` attributes. Programmatic `select.value`, `select.selectedIndex`, and `option.selected` update the getter and the existing Parley paint-label buffer, without dispatching synthetic `input` / `change` events. This is **not** proof that pixels changed; the buffer still reuses editable `TextInputData`, which remains unsafe/unvalidated for IME and paste.

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

## Screenshot acceptance boundary

A *separate* one-shot workflow, `.github/workflows/native-blitz-select-live-paint-proof.yml`, compiles the native Vello CPU screenshot example `native/blitz/experiments/calyra_live_screenshot.rs`. It captures **Balanced** then mutates `select.value='quality'` on the *same* ScriptDocument and captures **Visual fidelity**, verifying unchanged node identity, image sizes, hashes, change count and localized pixel bounds.

The earlier [run #43699535421](https://github.com/AVANT-ICONIC/calyra/actions/runs/43699535421) failed to compile this **separate** screenshot target because the `blitz_dom::Document` trait was missing from scope; its nine Rust/Boa tests passed. Fix commits on the current branch explicitly import the trait and pass a `&mut BaseDocument` reference to the painter instead of the document guard by value. Do **not** record the bitmap transition as passed until a later actual CI job builds and inspects it.

## Next engineering gate

Once two *real, same-document* native PNGs pass and are preserved, replace the temporary TextInputData/Parley editor hack with a noneditable `SelectData` and a proper selected-option invalidation contract. Assess IME/paste, keyboard navigation and OS event semantics independently; keep OpenSpec 4.1 unchecked until its much broader acceptance criteria are met. No hardware GPU, broad CSS parity, interactive dropdown, OS input or production architecture is proven.
