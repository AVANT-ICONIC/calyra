# CALYRA Stage A adapter contract

This is a *small real experiment*, not a replacement rendering engine.

## Why it exists

The **canonical input** is `fixtures/index.html`, `fixtures/reference.css`, `fixtures/reference.js`, and `fixtures/manifest.json`. All adapters SHALL report the source hashes, CSS adaptation, rendering classification, test viewport, capture paths, and unsupported behavior in `calyra.adapter-result.v1` (`adapter-contract.schema.json`). Only comparable interactive GUI candidates can advance to full Stage B benchmarks.

`run_stage_a.py` currently implements **`weasyprint-static`** as a constrained browserless CPU/document-renderer negative control. It uses unchanged authored CSS with explicit static-DOM and paged-layout adaptation, producing actual PNG captures and a JSON result. It does **not** prove a functioning native desktop UI, JavaScript behavior, accessibility, CSS fidelity, or a GPU advantage.

## Reproduce

Tested using Python 3.13; requires `weasyprint`, `pymupdf` (`fitz`), `lxml`, and `jsonschema`; optional `Pillow` for tests. It intentionally does not use GitHub Actions.

```bash
python harness/run_stage_a.py --fixture visual --width 1440 --height 900
python harness/run_matrix.py --timeout 8 --width 1440 --height 900
python -m unittest discover -s tests -p 'test_stage_a.py' -v
```

The matrix runner enforces a timeout so unexpectedly slow or hanging paged layouts are recorded as blocked rather than freezing indefinitely. Default output goes into ignored `evidence/native-stage-a/`. No runtime data is uploaded to a remote service. Record *static, document-only, restricted*, not a native GPU pass. No benchmarks are implied by renderer execution time.

## Contract requirements for future GUI adapters

1. Record engine version/commit, license and OS/platform separately in the candidate report.
2. Do not load remote scripts/assets or claim untrusted UI is sandboxed without verifying that property.
3. Run the same authored CSS first; version **all** transformations separately.
4. Capture visible states at the prescribed CSS viewport and device pixel ratio, including the renderer's actual pixel dimensions.
5. Replay `fixtures/manifest.json` action traces only if the backend supports them. A static renderer marks interactions unsupported rather than simulating successful events.
6. Separate OS WebView, bundled browser, native software and native GPU execution paths. No stealth browser fallback.
7. Distinguish `full`, `restricted`, `blocked` eligibility from per-feature statuses `direct`, `adapted`, `partial`, `unsupported`, `blocked`, `untested`.
8. Do not score unsupported or untested features as zero, or compare unavailable frame timings against measured ones.

**Not yet provided:** Blitz/RmlUi/Electrobun adapters, hardware macOS GPU evidence, packaged Tauri reference, native accessibility/IME probes. They require compatible builds, executable backends, and appropriate OS access.

## Optional GTK3 native CSS subset diagnostic (Linux only)

The optional `adapters/gtk3_css_probe.py` exercises an actual **native GTK3 CSS parser and interactive widget stack** without Chromium. It does not claim unchanged web CSS, a native GPU backend, or equivalence to the named RmlUi/Blitz/Electrobun candidates. Its output is explicitly `restricted` and uses the common result schema. See `docs/gtk3-native-css-probe.md` for exact setup, evidence, and missing features.
