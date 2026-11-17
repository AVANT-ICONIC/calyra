# CALYRA: real native macOS Blitz selected-value painting and AX inventory

**Date:** 2026-11-17. **Status:** *genuine native GUI select value painted*; macOS accessibility fields **not yet surfaced** in this read-only inventory. No original browser JS/OS input, native popup or complete accessibility compliance claimed.

## Native Apple Silicon verification

**[Actual GitHub Actions #44024203468](https://github.com/AVANT-ICONIC/calyra/actions/runs/44024203468) fully PASSED** on macOS ARM64, using exact pinned upstream Blitz `0.3.0-beta.4` revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`.

- Checkout verified clean before applying **six** existing, previously Linux-tested experimental patches in known order: `document-event-chain`, `plain-button-focus`, `select-ua-display`, `select-default-value`, `select-state-accessors`, `select-live-form-controls`; then `apply_readonly_select.py` plus isolated `select_state_readonly.rs`.
- All modifications applied **only to the disposable pinned upstream checkout**, with full source diff archived. Canonical CALYRA HTML, CSS, JS remain byte-identical to prior evidence. A deterministic static Controls HTML snapshot inlines original CSS, marks one state visible and intentionally omits original browser JS.
- A genuine `blitz::launch_static_html` app compiled as arm64 and ran with actual PID **17758**, owning layer-0 CoreGraphics Window **24** at **800×628**. Genuine macOS `screencapture -l` produced a **912×740** PNG with **SHA-256 `b8aca27c4838510a745e0072f0810e4c0fdb3c12137e29345ba7b5d18798a199`**.
- [Original patched screenshot](evidence/blitz-macos-select-ax/actual-patched-blitz-window.png) visibly shows the **Render priority** control, rendered box and selected **Balanced** label. [Original unpatched Mac window](evidence/blitz-macos-native-window/actual-blitz-native-window.png) had no visible select control or label.
- Source-verified unpatched baseline image **SHA-256 `b00bb80f0b4297ab8b2e9cac69af61a7704028564698c457d14efc5dfc7a1133`**. Both native-window images are the same **912×740 pixel geometry**. At RGB-channel change threshold 12/255, **12,515** pixels changed in total; **12,477** of those lie in the predeclared select-region ROI (`x=545..815, y=460..570`). This is strong scoped paint evidence, **not** native popup/keyboard behavior or exact browser-CSS parity.
- [Full archived original evidence](evidence/blitz-macos-select-ax/) includes **33 raw files plus a separate SHA-256 manifest**, an upstream source diff, exact build/host/process metadata, raw macOS AX inventory, unmodified static fixture snapshot, native screenshot and full pixel-difference image.

## macOS AX comparison: visible paint is not yet exposed controls

The same native Blitz PID's Accessibility API was traversed using `harness/macos_ax_inventory.swift` with **true OS Accessibility trust** and no mutations, event posting, value writes, focus changes, permission requests or VoiceOver simulation.

| Evidence from actual macOS `AXUIElement` tree | Original Tauri WKWebView baseline | Patched native Blitz window |
|---|---:|---:|
| AX nodes returned including OS menus/chrome | 221 | 50 |
| `AXTextField` | 1 | 0 |
| `AXPopUpButton` | 1 | 0 |
| `AXSlider` | 1 | 0 |
| `AXCheckBox` | 1 | 0 |
| `AXWebArea` | 1 | 0 (expected: browserless) |
| Matching canonical fields by role/title/current value | Original reference exposed name, select, slider, checkbox, Apply/Reset | **0/6** |

The native Blitz AX output in this test contained the application/window and ordinary macOS menu/control chrome (e.g. 36 menu items), plus an `unknown` role node and a generic group. **No CALYRA page controls or their value/labels were returned by this read-only traversal.** This demonstrates the accessibility surface exposed to *this process and query method in this window state*, not a proof that AccessKit is compiled out, or that a VoiceOver-triggered activation can never reveal content. In fact the pinned upstream Blitz package's **default features explicitly include `accessibility`**, and `blitz-dom/src/accessibility.rs` maps `select` to `Role::ComboBox` and `input[type=range]` to `Role::Slider`; actual OS exposure and complete values are separate questions. Further accesskit activation/window NSView diagnostics should be prioritized before claiming an irreparable AX deficiency.

Compare [actual native Blitz inventory](evidence/blitz-macos-select-ax/actual-native-ax-inventory.json) to the [already verified original Tauri macOS AX tree](evidence/tauri-macos-original-ax-tree/actual-ax-tree.json); do not conflate `AXWebArea` or system menu nodes with six control fields.

## Range control still not implemented by native painter

Unchanged `fixtures/reference.css` requests `accent-color: var(--accent)` for its range control. However pinned original Blitz's [native input painter](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-paint/src/render/form_controls.rs) only dispatches the `checkbox` and `radio` paint branches, and returns early without their `checkbox_input_checked()` data. No range thumb is implemented there. This matches the white-line-only slider in both original and patched macOS native screenshots. A separate geometry, input, value-state and native AX semantics implementation is required; merely painting a decorative thumb would not meet Stage A functionality.

## Decision

**Confirmed incremental win:** the Mac native Blitz window can display a selected `<select>` label using the existing experimental DOM/paint patch rather than substituting WebView, HTML/CSS rewriting, or screenshots.

**Critical gaps remain:** no verified native popup or OS-delivered keyboard/pointer selection, no accessible CALYRA input fields returned by this AX traversal, no native range thumb, no original JS inside this GUI, no IME, no validated hardware-GPU device and no fair performance win. A next bounded experiment should distinguish **AccessKit/macOS NSView adapter activation** from the separate missing input value/label semantics, then separately prioritize range as a full control contract. Do not promote these patches to a production renderer. OpenSpec 3.1/4.1/4.2 **remain unchecked**; PR #2 draft/unmerged, main unchanged.
