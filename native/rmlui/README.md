# CALYRA: RmlUi 6.3 native GPU probe

Status: **C++ source and a bounded Stage A runner committed; actual RmlUi build/runtime not yet verified** in the Linux sandbox. It lacks the upstream source checkout, GLFW and FreeType development dependencies. The runner fails closed and writes an explicit blocked report. It never substitutes Chromium, GTK or a PDF renderer.

## What it exercises

- Pinned upstream **RmlUi 6.3** at commit `ba95ffe8bfb6370efb2cdcca927eaad4710c5413`. License: MIT; retain upstream notices and verify license on checkout.
- The upstream **GLFW_GL3** OpenGL 3 native renderer and event delivery, not a browser or WebView.
- A limited RML translation of the CALYRA controls fixture.
- Two distinct modes: `direct` supplies the **original, unmodified** `fixtures/reference.css` to RmlUi, exposing any unsupported features; `adapted` supplies explicit, hand-authored `controls.rcss`. Both require DOM adaptation. Neither proves browser HTML/JS parity.
- Upon actual rendering, the C++ app captures the **OpenGL backbuffer** as PPM; the Python runner converts that genuine capture into PNG, preserving the existing Stage A JSON schema.
- The C++ button handler demonstrates a real native event hookup when clicked. Full keyboard, IME and accessibility behavior remain untested.

## Run locally on macOS

CMake >=3.21, C++17, Git, GLFW >=3.3, FreeType and Python 3 with Pillow and jsonschema are expected.

```bash
brew install cmake glfw freetype
git clone https://github.com/mikke89/RmlUi.git /tmp/calyra-rmlui-6.3
git -C /tmp/calyra-rmlui-6.3 checkout ba95ffe8bfb6370efb2cdcca927eaad4710c5413
git -C /tmp/calyra-rmlui-6.3 rev-parse HEAD
python -m pip install pillow jsonschema
python harness/run_rmlui.py --source /tmp/calyra-rmlui-6.3 --font '/System/Library/Fonts/Supplemental/Arial.ttf' --mode direct --build
python harness/run_rmlui.py --source /tmp/calyra-rmlui-6.3 --font '/System/Library/Fonts/Supplemental/Arial.ttf' --mode adapted
```

Use a different **local** TrueType font path if Arial is unavailable. Record substituted fonts in the report. The first command builds the `calyra_rmlui_probe` target into the ignored evidence directory; the second reuses the binary. The native window stays open briefly for manual mouse/keyboard exploration. Files are emitted into `evidence/native-stage-a/rmlui`.

## Offline / failure behavior

```bash
python harness/run_rmlui.py
```

This intentionally returns exit code **2** with a valid `blocked` result. It does **not** report GPU rendering, screenshots or fake timings. An incorrect upstream revision, missing font, failed CMake build, crashed executable or missing framebuffer image similarly blocks success.

## Important limits

1. macOS OpenGL is deprecated; this does not establish Metal performance or distribution readiness.
2. The RML markup is different from the canonical browser HTML. All comparisons must declare the adaptation.
3. RmlUi RCSS is not full modern CSS. In particular, Grid properties of the canonical fixture are not supported.
4. The `adapted` mode is an integration demonstration, **not CSS fidelity evidence**. It must not be ranked against the browser as a direct-source comparison.
5. A successful frame capture is **not** an FPS, GPU cost, CSS parity, font fidelity, native accessibility or shipping claim.
6. This change is within the existing CALYRA OpenSpec experiment; no new language, compiler or renderer is being developed.

## Test the contract without GPU dependencies

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
# GTK/Tk tests need a display on Linux:
xvfb-run -a python -m unittest discover -s tests -p 'test_*.py' -v
```

On the CALYRA sandbox, the native probe's blocked path and local static contracts were tested; RmlUi itself was not compiled. There are no GitHub Actions jobs in this workflow.
