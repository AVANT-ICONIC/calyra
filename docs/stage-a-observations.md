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


## v0.7 audit: macOS Xcode binary and computed style provenance

The local runner previously failed to resolve a `Release/` multi-config
executable on a follow-up run without `--build`. Now it resolves an existing
built target and still checks the pinned Git checkout and manifest SHA-256.
The RmlUi 6.3 probe now records the actual computed primary-button background
RGBA through the RmlUi computed-values API; the adapted RCSS case must observe
`198,219,116,255`. Unknown/missing computed style or a stale image can no
longer count as a captured successful frame.

**Verification scope:** 45 local Xvfb Python tests passed, including mocked
native executable boundary tests and the existing browser/GTK/static checks.
**Unverified:** compilation and execution against RmlUi 6.3, GL hardware,
macOS GPU evidence, screenshot parity, and real OS-level interactions. The
container's DNS and outbound connections to GitHub are unavailable; official
upstream source and GLFW headers cannot be fetched here.

## First actual RmlUi 6.3 native GitHub runner attempt (2026-11-15)

[Actions run #43664566957](https://github.com/AVANT-ICONIC/calyra/actions/runs/43664566957) executed pinned, clean RmlUi 6.3 sources at `ba95ffe8bfb6370efb2cdcca927eaad4710c5413` on Linux and an actual macOS 15 ARM64 runner. These results are **real build and runtime observations**, unlike the earlier mocked runner tests.

- **Apple Silicon: C++ native build SUCCEEDED.** An executable with SHA-256 `785d0bbcd497a96e9c29ba6e376d72052aa71200721626aa5f0361ca8088316b` and verified upstream/build-source provenance was generated. Both UI modes then returned `exit=4` from GLFW, reporting `GLFW error (0x10009): NSGL: Failed to find a suitable pixel format`. The CI host could not provide a suitable OpenGL context, so **no framebuffer, GPU support claim, or CSS result** exists. [Raw macOS artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43664566957/artifacts/14141765920).
- **Linux: RmlUi core and debugger compiled, but final CALYRA executable link FAILED.** The linker reported undefined `glGetString`, `glGetIntegerv`, `glFinish`, `glReadBuffer`, `glReadPixels`, `glGetError` from CALYRA's `probe.cpp`. Root cause: direct OpenGL calls lacked an explicit `OpenGL::GL` link dependency, although the upstream GLFW backend dynamically loads its own GL symbols. [Raw Linux artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43664566957/artifacts/14141403045).

**Next constrained repair:** link OpenGL explicitly on non-Apple platforms and run the Linux framebuffer probe once more. The Apple Silicon runner is deliberately skipped on this follow-up push: its source compilation is already proven, while its headless GL-context issue requires a separately justified experiment. No speed or CSS compatibility score can be derived from this first run.

## Real Linux native execution after GL linker repair (2026-11-15)

[Run #43664913374](https://github.com/AVANT-ICONIC/calyra/actions/runs/43664913374) **successfully linked and executed** the RmlUi 6.3 C++/GLFW/OpenGL3 application on Linux (unlike the earlier linker failure). The real runtime identified its renderer as **Mesa llvmpipe (LLVM 20.1.2)**, i.e. **software OpenGL, not hardware acceleration**. The RmlUi internal synthetic click event fired and the adapted stylesheet yielded the computed primary color `198,219,116,255`.

The framebuffer capture still failed (`exit=8`). Upstream RmlUi's GL3 renderer draws into an internal framebuffer during `BeginFrame`, resolves it onto the window backbuffer in `EndFrame`, and GLFW swaps buffers during `Backend::PresentFrame`. CALYRA's code had incorrectly attempted `glReadBuffer(GL_BACK)` before `EndFrame`. The repair moves capture after presentation and reads `GL_FRONT`, with a bounded retry and numeric GL-error logging. The run also exposed platform-font mismatch: the machine's DejaVu Sans TTF was loaded, but RCSS asked for Arial. The repair registers that supplied TTF under the explicitly adapted Arial family (regular and bold), without claiming font equivalence. [Raw Linux runtime/build artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43664913374/artifacts/14142146456).

**No screenshot or CSS fidelity conclusion was produced in run #43664913374.** The subsequent capture/font changes must be executed and verified before a success claim.

## Third real Linux RmlUi run: front-buffer uniformity (2026-11-15)

[Run #43665322670](https://github.com/AVANT-ICONIC/calyra/actions/runs/43665322670) compiled and ran RmlUi 6.3 again. The native executable emitted `CALYRA_NATIVE_FRAME=1060x740`, software OpenGL `llvmpipe`, correct adapted computed color `198,219,116,255`, and `CALYRA_NATIVE_CLICK=1`. **But** Pillow rejected the GL_FRONT capture as a uniform-color image: a valid native screenshot was not produced. RmlUi loaded the supplied TTF under the explicit Arial family, confirming that the prior font mapping issue is fixed. Direct CSS continued to emit documented parser-compatibility errors.

Upstream `Backends/RmlUi_Backend_GLFW_GL3.cpp` defines `PresentFrame()` as `render_interface.EndFrame(); glfwSwapBuffers(window);`. To capture the actual resolved backbuffer without the virtual display's empty frontbuffer, CALYRA now calls the upstream `RenderInterface_GL3::EndFrame()`, reads `GL_BACK`, then calls `glfwSwapBuffers(glfwGetCurrentContext())`. This is not a new renderer: it is the same pinned upstream OpenGL3 backend split at the capture boundary. [Raw log artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43665322670/artifacts/14141198503).

The next run must establish whether those captured pixels are nonuniform and visibly meaningful. Until then, no screenshot fidelity or performance claims are supported.

## First verified native RmlUi image and compatibility outcome (2026-11-15)

**[Successful native Linux workflow #43665651869](https://github.com/AVANT-ICONIC/calyra/actions/runs/43665651869)** executed CALYRA's RmlUi 6.3 native C++ probe against the exact pinned upstream revision `ba95ffe8bfb6370efb2cdcca927eaad4710c5413`.

The runner produced two independently validated **1060x740 RGB native framebuffer PNGs** from RmlUi 6.3 using the upstream `GLFW_GL3` backend. The OpenGL identity was `llvmpipe (LLVM 20.1.2, 256 bits) / Mesa`. This is **software-accelerated OpenGL rendering on the CPU, not a hardware-GPU benchmark**. Both result JSONs reported `capture.success=true`, `eligibility=restricted`, `interactive=true` only for the internal programmatically dispatched RmlUi click; `gpu_backed=false`, `measured_performance=false`. The adapted RCSS button reported computed `198,219,116,255` (`#C6DB74`). The direct stylesheet's button reported `0,0,0,0` (transparent). [Download exact run artifacts and screenshots](https://github.com/AVANT-ICONIC/calyra/actions/runs/43665651869/artifacts/14142142998).

The captured images were independently inspected against an actual Chromium rendering of the canonical controls fixture at the **same 1060x740 viewport**. Visual differences are **severe and not reducible to text antialiasing**:

- **Direct CSS:** the unmodified canonical `fixtures/reference.css` is passed to RmlUi, but the RML markup remains translated. The rendered image shows essentially two dark input surfaces on a black background. The runtime logs report numerous CSS errors, including unsupported Grid, browser shorthand/syntax, browser font families, and other declarations. A nonuniform screenshot and functioning native event listener **do not imply CSS compatibility**.
- **Adapted RCSS:** a separately authored stylesheet plus translated RML DOM renders real text, inputs, buttons and the correct accent color. However, typography/flow, spacing, missing navigation/sidebar, missing range/toggle controls, viewport background, and overall structure remain visibly different. The browser UI and RML tree are *not* semantically identical; these images are a **diagnostic illustration**, not a valid pixel-exact fidelity score.
- **Input:** a synthetic RmlUi click was handled by the actual C++ listener. Physical OS pointer/keyboard events, text composition/IME, full focus behavior, screen reader accessibility, and full native framework integration remain unverified.
- **Performance:** no CPU/RAM/GPU memory, cold startup, FPS or frame-pacing benchmark was run. No performance advantage is claimed.

**Decision implication:** RmlUi is an operationally viable *restricted native renderer* for manually adapted RCSS/markup, but this experiment provides no basis for selecting it as CALYRA's primary modern-browser-CSS-compatible backend. Evaluate an HTML/CSS-native engine such as Blitz next. Keep RmlUi as a narrow native candidate rather than investing in hand rewriting every canonical CSS feature.

**Evidence retention:** GitHub Actions binary artifacts expire after their configured retention (7 days). The URLs, report schema, runner source, logs, exact pinned source SHA and output interpretation remain recorded here; reproduce the captures using the CI-free runner or by rerunning the workflow on a suitable Linux host. Do not silently promote a missing or expired artifact into a verified current screenshot.


## Blitz Vello-CPU native HTML/CSS proof (2026-11-15)

[Authentic Actions run #43671027217](https://github.com/AVANT-ICONIC/calyra/actions/runs/43671027217) compiled Blitz 0.3.0-beta.4 and captured all four unchanged-CSS HTML scenes. Verified full-size PNG hashes and local Chromium-image diagnostics show approximate macro-layout compatibility, but a missing native select control, incomplete range styling and font differences. **CPU only, static DOM adaptation, no JS, GPU or input verification.** See [Blitz observations](blitz-stage-a-observations.md). Task 3.2 is completed as an *attempt with real evidence*, not as a full CSS or feature pass.
