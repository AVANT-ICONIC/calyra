# CALYRA: native Blitz form controls are three separate integration layers

**2026-11-17 source audit**, pinned upstream Blitz `0.3.0-beta.4`, original Git revision `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`.

## Source-backed diagnosis

| Responsibility | Upstream code | What is actually implemented at this revision |
| --- | --- | --- |
| Styling and native pixels | [`packages/blitz-paint/src/render/form_controls.rs`](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-paint/src/render/form_controls.rs) | `ElementCx::draw_input` early-returns unless `checkbox_input_checked()` is available and contains painter branches only for `checkbox` and `radio`. **No native range thumb painting branch** is present. |
| Document semantics/state | [`packages/blitz-dom/src/accessibility.rs`](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-dom/src/accessibility.rs) | `role_from_element_data` maps ordinary `select` to `Role::ComboBox`, and `input type=range` to `Role::Slider`. This mapping alone **does not prove exposure of current values or user changes**. |
| OS accessibility integration | [`packages/blitz-shell/src/accessibility.rs`](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-shell/src/accessibility.rs) · [`packages/accesskit_xplat/src/platform_impl/macos.rs`](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/accesskit_xplat/src/platform_impl/macos.rs) | BlitzShell constructs AccessKit cross-platform adapter, whose macOS backend uses `SubclassingAdapter`. The document accessibility tree emits HTML role mappings. Whether Apple Accessibility API actually exposes the expected live fields/labels/values **requires a real running native macOS window**. |

The current screenshot failure is therefore **not simply missing author CSS**. The unchanged CALYRA stylesheet explicitly requests `.field input[type=range] { width:100%; accent-color:var(--accent); cursor:pointer };` but the native form-control painter has no corresponding range thumb implementation. The first actual Mac Blitz winit/Vello window [passed](https://github.com/AVANT-ICONIC/calyra/actions/runs/44018682112) and reproduces the plain white-line range and absent select value.

Also note that Blitz's `build_accessibility_node` sets element `role`, tag and explicit ARIA attributes, but its ordinary element path has no generic `set_value` for a select/range current value in this source. It *does* set `value` for `TextRun`. This raises a concrete OS-level values/labels question rather than proving current AX output.

## Targeted controlled experiment

The new isolated [macOS native SelectData + AX workflow](../.github/workflows/blitz-macos-select-ax-proof.yml) applies only the existing Linux-proven source-pinned select adapter to a temporary, exact-revision Blitz checkout. It independently verifies a real app-owned macOS window, captures its genuine pixels and reads the actual macOS AX tree via [`harness/macos_ax_inventory.swift`](../harness/macos_ax_inventory.swift) without posting OS input, changing focus or values, or requesting permissions. Its AX inventory is compared to the already verified original Tauri WKWebView native AX baseline. Missing fields must remain explicit, not silently counted as passing.

**Scope guard:** A visible selected label is a distinct, narrow milestone from a functional native popup and keyboard/IME behavior. Range thumb painting, pointer drag and value changes are also separate. Do not claim complete control compatibility, WGPU/Metal device acceleration, Accessibility acceptance, or a performance ranking until actual matched runtime evidence exists. OpenSpec 3.1/4.1/4.2 remain open; original CALYRA HTML/CSS/JS are untouched.
