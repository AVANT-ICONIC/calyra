# RmlUi 6.3 native GPU probe (Stage A)

**State:** Native C++ and GLFW GL3 integration authored; build and runtime screenshot **not verified** in the CALYRA sandbox because official RmlUi source/development dependencies are not locally available. The runner records a blocked result rather than simulating a native frame.

## What this tests

- Actual **RmlUi 6.3** CSS/RCSS parser, layout and native GLFW/OpenGL 3 renderer, with C++ event listener and framebuffer capture.
- `direct`: passes the **canonical, unchanged** `fixtures/reference.css` into the RmlUi style parser. RML element tree is explicitly adapted, meaning **HTML DOM compatibility is not being tested**.
- `adapted`: uses a separate `controls.rcss` authored for RmlUi from the same design colors. This is **not CSS parity**. Rendering success must never be counted as direct CSS support.
- Neither mode executes browser JavaScript. Native control events are handled by RmlUi and C++.

## Single-command Apple Silicon preflight and opt-in run

From CALYRA's root:

```bash
# Read-only check. Does not clone sources, install packages, create outputs, or run CI.
python3 native/rmlui/bootstrap_macos.py

# Install missing development dependencies yourself only if preflight requests them:
brew install cmake glfw freetype pkg-config
# Use an isolated Python environment. No installation into system Python.
python3 -m venv .local/venv
.local/venv/bin/python -m pip install -r native/rmlui/requirements-macos.txt

# Explicit opt-in: clone official source, verify pinned clean commit, compile, then run direct/adapted probes.
.local/venv/bin/python native/rmlui/bootstrap_macos.py --run
```

Use `--font /absolute/path/to/font.ttf` if Arial is absent, `--source` for an existing official checkout, or `--output` for an alternate evidence directory. The script captures failures as a `blocked` JSON report. It never installs dependencies, runs remote shell scripts, or reuses a modified upstream tree. On success it writes `evidence/native-stage-a/rmlui/macos-preflight-summary.json` together with the two independent adapter reports and captures.

**Important:** `--run` is a real, opt-in native build request that needs a working macOS desktop and an internet connection for the initial Git clone. It can legitimately fail on unsupported source APIs, missing graphics drivers, or unavailable fonts. Neither the script nor its Linux preflight tests are evidence that the native GPU renderer has worked.

**Renderer-selection note:** GLFW_GL3 is a compatibility smoke test using the OpenGL API. It is not a Metal backend. The upstream 6.3 tree also includes an SDL3 GPU backend suitable for a later Metal/D3D/Vulkan comparison, but CALYRA has not built or verified that backend.

**Freshness invariant:** the native build manifest now pins both the upstream commit and the SHA-256 of `native/rmlui/probe.cpp` and `native/rmlui/CMakeLists.txt`. Updating native adapter source invalidates prior binaries until `--build` succeeds again. An unchanged binary digest alone would have accepted stale builds.

## macOS setup (no GitHub Actions)

Prerequisites: CMake 3.21+, C++17 compiler, GLFW 3.3+, FreeType, macOS OpenGL 3.3 Core support, Git, Python + Pillow + jsonschema.

```bash
brew install cmake glfw freetype
# Clone only from the official repository and verify the exact source commit.
git clone https://github.com/mikke89/RmlUi.git /tmp/calyra-rmlui-6.3
git -C /tmp/calyra-rmlui-6.3 checkout ba95ffe8bfb6370efb2cdcca927eaad4710c5413
git -C /tmp/calyra-rmlui-6.3 rev-parse HEAD
python harness/run_rmlui.py --source /tmp/calyra-rmlui-6.3 --font '/System/Library/Fonts/Supplemental/Arial.ttf' --mode direct --build
python harness/run_rmlui.py --source /tmp/calyra-rmlui-6.3 --font '/System/Library/Fonts/Supplemental/Arial.ttf' --mode adapted
```

Run from the CALYRA repository root. The first run builds the `calyra_rmlui_probe` target into `evidence/native-stage-a/rmlui/build/`, and both runs produce independent result JSON, runtime logs, and, **only upon success**, native framebuffer PNG captures. The executable holds a native OpenGL window briefly for interaction and screenshot verification. If the font doesn't exist on the target macOS version, provide a different local TTF file and record that substitution.

## Build/reproducibility boundaries

- Offline CALYRA sandbox check: `python harness/run_rmlui.py` returns **exit 2 + blocked JSON**, with no screenshot and no false performance claims.
- Upstream source must match commit `ba95ffe8bfb6370efb2cdcca927eaad4710c5413`, identified by RmlUi tag `6.3`.
- RmlUi code is **not vendored** into CALYRA; its original license and exact commit must be checked when building.
- Backend: upstream `GLFW_GL3` uses deprecated-but-available Apple OpenGL Core Profile. It does **not** prove Metal support. GLFW must have an actual working desktop display, not headless-only software GL.
- The PPM capture is taken from the real GPU backbuffer and converted by Pillow. This is not a browser screenshot or a synthetic illustration.
- Only `controls` is currently mapped, and RML/RCSS adaptation remains declared. Grid, JS behavior, accessibility tree, input composition/IME, shaders and native memory/performance remain unmeasured.
- This prototype does not attempt unauthenticated remote script downloads or run any GitHub Actions.

The current protocol intentionally separates **source-level evidence**, **attempted build**, **native execution** and **fidelity proof**. Those are different milestones.

## Verification hardening (v0.6)

Stage A distinguishes four separate observations: **native build**, **native frame**, **RmlUi event dispatch**, and **hardware-backed OpenGL**. None implies the others.

- A successful `--build` now writes `rmlui-build-provenance.json` containing the pinned and clean upstream checkout, binary path, and SHA-256 of the produced executable. Reusing the binary with `--mode adapted` requires that the digest still matches. The runner supports single- and multi-configuration CMake executable locations.
- The probe prints `CALYRA_GL_RENDERER` and `CALYRA_GL_VENDOR` from its active OpenGL context. Software renderers such as llvmpipe/SwiftShader are classified as `browserless-software`, not hardware GPU. Unknown renderers remain blocked rather than being guessed.
- A frame requires a valid, correctly sized, non-uniform PPM converted to PNG and a matching `CALYRA_NATIVE_FRAME` marker; old frames are removed before each attempt. A successful process exit or a file alone is insufficient.
- The probe programmatically dispatches pointer movement/press/release to the actual RmlUi button and requires the C++ click listener to emit `CALYRA_NATIVE_CLICK=1`. This validates **RmlUi's internal event path only**. It does not yet verify physical OS mouse events, keyboard focus, IME or assistive technologies.
- No comparison can report FPS, GPU memory, native CSS fidelity, or accessibility success from this small probe. It is Stage A restricted evidence only.

**Current outcome:** local unit tests verify these negative and provenance paths; an actual upstream RmlUi C++ build, real window, real framebuffer, and GPU vendor string remain unexecuted because the pinned source and GLFW development headers are not available in the current container. The CI-free macOS build above is still the way to obtain a first genuine execution result.


## Verification corrections (v0.7)

Two cross-platform failure cases were identified and fixed by inspecting the
runner and upstream RmlUi 6.3 APIs. **Neither fix represents a successful
RmlUi native build in this sandbox.**

1. **Xcode/multi-config reuse:** on an Apple machine using the Xcode CMake
   generator, the built executable may be at `build/Release/calyra_rmlui_probe`.
   The second invocation without `--build` now detects that path and still
   verifies its SHA-256 against the existing build provenance.
2. **Actual CSS application:** the C++ probe reads the primary button's
   `GetComputedValues().background_color()` (public RmlUi 6.3 API) and writes
   the observed RGBA channels to a log marker. Both modes require a real style
   marker. Adapted RCSS additionally requires the fixture color
   `198,219,116,255` (`#C6DB74`). Direct CSS makes no promise that this
   specific rule matches the adapted RML tree. A nonuniform screenshot without
   a computed-style marker is **not** sufficient evidence of RCSS execution.
3. **Stale screenshots:** failed or blocked invocations remove prior PPM/PNG
   paths so leftover pixels can never be read as the current run's capture.

The runner's `capture.success` reports only the small Stage A native frame +
RmlUi-internal click probe with classified OpenGL renderer. It does not mean
full CSS compatibility, accessible OS controls, verified physical mouse input,
IME, performance superiority, or hardware GPU rendering on every machine.

### macOS reproduction

After verifying the pinned upstream checkout is clean, run the two commands
above in the same `--output` directory. Review both result JSONs and the
separate `runtime-direct.log` and `runtime-adapted.log` before comparing
frames. Explicitly record the GPU vendor/renderer and screen pixel scale.
Do not copy an adapted RCSS success into a direct CSS compatibility score.


## Independent CSS mode results (Stage A v0.9)

The macOS bootstrap deliberately attempts **both** rendering modes, even if
a native build succeeded but the direct canonical CSS test failed. This is
essential: a parser or selector mismatch in the direct mode must not conceal
an otherwise viable RmlUi render path with explicitly adapted RCSS.

The two modes have separate result JSON files. Every invocation first removes
its previous result JSON; a subprocess exit code must agree with a fresh
`capture.success=true` and `eligibility=restricted`. Previous screenshots are
already discarded by the native runner, so a crash cannot leave behind a
seemingly successful comparison.

The summary now distinguishes:

- **`restricted` (exit 0):** direct and adapted captured independently. This
  still does **not** establish CSS parity or accessibility.
- **`partial` (exit 1):** exactly one mode captured; inspect its evidence, keep
  the other failure visible, and do not claim a paired comparison.
- **`blocked` (exit 2):** neither mode captured, or preflight failed.

The summary includes both status records, their exit codes and output tails.
Local unit tests verify the important failure path: direct CSS blocked while
adapted RCSS succeeds. These tests use mocked runner responses and are **not**
native RmlUi execution.
