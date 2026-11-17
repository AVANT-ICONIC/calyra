# CALYRA: genuine macOS AccessKit lazy activation verified

**2026-11-17 | [Real Apple Silicon CI #44028701883](https://github.com/AVANT-ICONIC/calyra/actions/runs/44028701883) PASSED ALL STEPS.** Actual Blitz 0.3.0-beta.4 `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, genuine arm64 Winit native GUI, unmodified original authored CALYRA HTML/CSS/JS. A statically adapted Controls snapshot omits original browser JavaScript. The same known read-only `SelectData` paint patches and an independent **log-only** accessibility instrumentation patch were applied to a throwaway upstream checkout.

## Why the earlier macOS AX 0/6 verdict was incomplete

A previous read-only macOS AX tree traversal of the real native Blitz GUI returned 50 nodes, almost entirely window chrome/system menu, and zero named CALYRA page controls. That result was accurate **for the immediate observation**, but it was premature to infer Blitz lacked actual native AX page roles.

This controlled experiment ran a first trusted read-only native AX inventory, then a separate AX hit-test/census probe against the **same verified live Blitz CGWindow**, while instrumenting the actual Rust AccessKit events. Exact chronological native stderr records:

```text
CALYRA_AX_UPDATE_IF_ACTIVE_CALLED
CALYRA_AX_UPDATE_IF_ACTIVE_RETURNED
CALYRA_AX_BACKEND_EVENT_RECEIVED=InitialTreeRequested
CALYRA_AX_INITIAL_TREE_EVENT_DISPATCHED
CALYRA_AX_UPDATE_IF_ACTIVE_CALLED
CALYRA_AX_TREE_ACTUALLY_BUILT_NODES=182
CALYRA_AX_UPDATE_IF_ACTIVE_RETURNED
```

**The initial update did not produce a tree; the true `InitialTreeRequested` event came later, reached the native eventloop and built 182 internal AccessKit nodes.** After the first census triggered asynchronous activation, the **second census already found 107 native macOS AX nodes even before the nine additional read-only hit tests**. The hit tests found the existing group and did not change total node count. Therefore the activation was not caused by the nine hit tests; do not conflate those effects.

| Native Apple Accessibility measurement | First census | Second census, before hit tests | Second census, after hit tests |
|---|---:|---:|---:|
| Total AX nodes including OS chrome/menus | 50 | **107** | **107** |
| `AXTextField` | 0 | **1** | **1** |
| `AXPopUpButton` | 0 | **1** | **1** |
| `AXSlider` | 0 | **1** | **1** |
| `AXCheckBox` | 0 | **1** | **1** |
| `AXLink` | 0 | **5** | **5** |
| `AXButton` including native window chrome | 3 | **5** | **5** |

On the second census, the OS also returned **16 AXGroup, 27 AXUnknown, 5 AXStaticText and 1 Heading** nodes, along with normal macOS application/menu/window elements. Every one of nine `AXUIElementCopyElementAtPosition` calls succeeded with AX error 0 and returned an `AXGroup` owning one child.

This is a **real proof of the native macOS Accessibility integration path**, not a mock accessibility tree: winit AppKit NSView → AccessKit subclass adapter → asynchronous activation → BlitzShell eventloop → Blitz DOM generated AccessKit tree → actual Mac AXUIElement roles. The real Winit screenshot still showed the preverified `Balanced` label in the experimental native SelectData box.

## The remaining semantics are a separate actual defect

The now-visible native `AXTextField`, `AXPopUpButton`, `AXSlider`, `AXCheckBox` and two content `AXButton` nodes **do not yet expose the required CALYRA names and current values** via this OS API traversal. The strict role/title/value matches are still **0/6**. By contrast the original native Tauri WKWebView reference exposes:

| Control | Tauri's actual native AX title/value | Blitz after activation |
|---|---|---|
| Display name | `Display name` / `Alex Rivera` | role present, title/value absent |
| Render priority | `Render priority` / `Balanced` | role present, title/value absent |
| Material intensity | `Material intensity 64%` / `64` | role present, title/value absent |
| Enable effects | `Enable effects Native checkbox with CSS presentation` / `1` | role present, title/value absent |
| Apply settings | button title `Apply settings` | role present, title absent |
| Reset | button title `Reset` | role present, title absent |

**Known pinned source defect:** Blitz's [`build_accessibility_node`](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-dom/src/accessibility.rs) assigns semantic roles and explicit ARIA attributes but does not derive ordinary HTML `<label for>` names and current field values for these controls in this snapshot. Even if names/values were added, [`BlitzShell`'s `ActionRequested` handler](https://github.com/DioxusLabs/blitz/blob/4f61cffacee50fe4f944ebe9d0470d9a5d3997e0/packages/blitz-shell/src/application.rs) is a `TODO`; no operational assistive action is proven.

## Complete original evidence and boundaries

[Original 37 real runner files plus SHA-256 manifest](evidence/blitz-macos-ax-activation/), including [two-stage read-only AX data and nine hit-test observations](evidence/blitz-macos-ax-activation/actual-native-ax-hit-test-after.json), [actual application event trace](evidence/blitz-macos-ax-activation/native-app.log), [machine-readable activation and role summary](evidence/blitz-macos-ax-activation/ax-activation-diagnostic.json), full source-pinned Rust build logs and applied upstream experimental diff, unmodified source hashes, actual winit window/screenshot pixel data, and the original native Tauri baseline references.

No keyboard, mouse/pointer OS input, AX actions, focus/value mutations, system permission requests, VoiceOver, IME, actual hardware GPU identification or fair memory/performance comparison was performed. The nine **read-only AX hit-test API queries** do not qualify as pointer events. The original authored CALYRA fixtures were untouched. This is a restricted but verified implementation discovery, **not complete native control accessibility**.

**Next precise development step:** Add semantically correct native `label` and current `value` propagation into Blitz's AccessKit document tree (including checkbox checkedness and current range value, respecting dynamic JS changes), and verify titles/values via actual macOS AX API. Only after that investigate actual `ActionRequested` routing and trusted OS input. The separate missing range-thumb painter also remains unimplemented. OpenSpec tasks **3.1, 4.1, 4.2 UNCHECKED**; draft PR #2 unmerged, `main` untouched.
