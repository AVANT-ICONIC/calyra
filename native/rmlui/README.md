# RmlUi 6.3 native GPU probe (Stage A)

**State:** Native C++ and GLFW GL3 integration authored; build and runtime screenshot **not verified** in the CALYRA sandbox because official RmlUi source/development dependencies are not locally available. The runner records a blocked result rather than simulating a native frame.

## What this tests

- Actual **RmlUi 6.3** CSS/RCSS parser, layout and native GLFW/OpenGL 3 renderer, with C++ event listener and framebuffer capture.
- `direct`: passes the **canonical, unchanged** `fixtures/reference.css` into the RmlUi style parser. RML element tree is explicitly adapted, meaning **HTML DOM compatibility is not being tested**.
- `adapted`: uses a separate `controls.rcss` authored for RmlUi from the same design colors. This is **not CSS parity**. Rendering success must never be counted as direct CSS support.
- Neither mode executes browser JavaScript. Native control events are handled by RmlUi and C++.

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
