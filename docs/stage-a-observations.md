# Stage A browserless software-renderer observations

> **Scope:** November 14, 2026, Linux x86_64 container, Python 3.13.5. This is not a native macOS app, not a GPU renderer, not an interactive UI, and not a production fitness test.

## Why WeasyPrint was tested

The available sandbox had no installed Blitz, RmlUi or Electrobun toolchains, and could not resolve github.com for source cloning. WeasyPrint 68.0 was locally available, providing a genuine browserless CSS-to-document rendering path (CSS/Pango/Cairo/PDF, rasterized through MuPDF). It is a **negative control** for the adapter protocol, not a substitute for the planned native GPU comparison.

## Observed fixture results

| Fixture (1440×900 CSS px) | Outcome | Implication |
| --- | --- | --- |
| Controls | **Blocked**: subprocess timed out after 5 seconds | No screenshot or interaction verdict; paged layout may be unsuitable for this scene |
| Responsive dashboard | **Restricted**: static PNG and PDF produced | Visual inspection possible, no interaction fidelity claimed |
| Visual effects | **Restricted**: static PNG and PDF produced | Supports partial image-level comparison, NOT proof of CSS material parity |
| Interaction | **Restricted**: static PNG and PDF produced | State can be statically prepared; event handling/JS entirely absent |

A shorter, deliberately bounded timeout was used for the exploratory matrix. It is **not** a performance benchmark or evidence that a native engine would time out.

## Reproduction

```bash
python -m pip install -r harness/requirements-stage-a.txt
python harness/run_matrix.py --timeout 8 --width 1440 --height 900
python -m unittest discover -s tests -p test_stage_a.py -v
```

Outputs: `evidence/native-stage-a/*.json`, `*.png`, and `*.pdf` on the machine executing the commands. The harness records each source SHA-256, viewport, engine version, adaptations, rendering class, missing behaviors, and explicit blocked results.

Observed source SHA-256:

- `fixtures/index.html`: `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`
- `fixtures/reference.css`: `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`
- `fixtures/reference.js`: `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`

## Actual differences to the Chromium screenshots

The WeasyPrint scene has different typography sizing and placement, missing ring/decorative details, different layout geometry, and opaque/flattened material effects. Some CSS behavior is unsupported or implemented differently. Paged-medium behavior changes the viewport assumptions.

No CSS properties are scored `direct` merely because the rasterized page looks plausible. The renderer does not execute the fixture's JavaScript, and it is not eligible for a general-purpose UI benchmark.

## Validation

- Four targeted Stage A unit tests passed, including JSON contract validation and a real non-uniform pixel capture at 1440×900.
- Existing eight Chromium reference unit tests passed locally unchanged.
- The first attempted 720×640 paged capture did not complete within the available time. This motivated the bounded subprocess matrix; no causal diagnosis or GPU conclusion is claimed.
- This evidence is local, not replicated on macOS. All Blitz/RmlUi/Electrobun native results remain **pending**.

## Next narrow step

Run the **actual** Blitz or RmlUi build on a machine with source/toolchain access. Integrate its rendering path into the same versioned contract and mark unsupported features honestly. Do not build CALYRA's own renderer to work around unverified guesses.

## Additional native GTK3 CSS diagnostic

A separate Linux GTK3 probe (`adapters/gtk3_css_probe.py`) successfully created native widgets, loaded a CSS subset through `GtkCssProvider`, confirmed the real computed button color against the canonical `--accent` value, emitted native GTK button signals, captured an 840×680 screenshot, and validated a restricted Stage A JSON record. Its four dedicated tests passed; the complete local Xvfb test suite passed 24/24. This is **not** one of the three intended native renderer candidates, a GPU result, or evidence of general web CSS compatibility. See `docs/gtk3-native-css-probe.md` for limitations and commands.

### RmlUi v0.6 evidence boundaries (2026-11-15)

The RmlUi integration runner previously reported `interactive: true` from any successful framebuffer capture, even without an interaction event, and inferred `gpu_backed: true` from using OpenGL despite potential software rasterizers. Both were incorrect evidence classifications and have been fixed. The native probe now emits a programmatic button-click marker and GL vendor/renderer strings. The runner distinguishes hardware and software GL, checks native build provenance, and rejects blank frames, stale frames, unknown renderers, missing click markers, or modified binaries. Verified local Python/Xvfb tests are guard tests only: **no RmlUi build, GPU screenshot, hardware claim, or CSS parity score was produced in this environment**.
