# CALYRA Stage A: Blitz select layout and value experiment

**2026-11-15, restricted result.** Genuine native Rust/Boa run succeeded using pinned Blitz `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, but the select control **is not fully implemented**.

## Real execution

[GitHub Actions run #43687941941](https://github.com/AVANT-ICONIC/calyra/actions/runs/43687941941) compiled the official upstream Blitz 0.3.0-beta.4 with four **explicit experimental source patches**, then executed 8/8 Rust integration tests with zero JavaScript errors. The original CALYRA HTML, CSS and JS were unchanged, with CSS SHA-256 `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c` and JS SHA-256 `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`.

The two previously tested patches preserve document-level keydown bubbling and synchronous focus set by `type=button` JavaScript handlers. Two **new, separate patches**:

1. [Experimental select UA display](../native/blitz/patches/select-ua-display.patch): Adds `display:inline-block` to the upstream default CSS `select` rule. No authored CSS changed. It gives CALYRA's select a layout box but not full native appearance or a rendered selected-value label.
2. [Experimental minimal select value getter](../native/blitz/patches/select-default-value.patch): For direct `option` children, returns the explicitly selected option value, or the first option value if none has a selected attribute. It **does not** implement full `HTMLSelectElement` selectedness, `.value` setter behavior, optgroups, keyboard options, or interactive popup.

The patches were applied to an isolated verified clean upstream checkout, and the [independent Rust regression test](../native/blitz/patches/patched_select_regression.rs) was appended only in the select-specific workflow. No original CALYRA JavaScript was rewritten.

## Exact measured behavior

| Check | Clean upstream baseline | Experimental patched upstream |
|---|---|---|
| `#priority` layout box | 0×0 px | **139×48 px** |
| Initial `#priority.value` | Empty string | **balanced** |
| Three parsed option nodes | Yes | Yes |
| `#priority option[value=quality]` with selected attribute | No semantic result | **quality** |
| Original Apply button status | `Applied: Alex Rivera ·  · 64% · on` | `Applied: Alex Rivera · balanced · 64% · on` |
| Original immediate menu focus and Escape | Requires independent engine patches | Both passed again |
| Reported JS errors | 0 | 0 |

**139 px width is not verified browser layout parity.** The width of a control box alone does not demonstrate correct painting, clipping, focus ring, pointer dropdown, native OS integration or accessibility. No screenshot was captured in this test. The selected option is still not demonstrably drawn inside the box.

## Original artifact identity

- `calyra-js-select-patched.json`: SHA-256 `518f0eecf9f711bc12d40f18f11943bd6d739889b6671ebbda08202002664eff`.
- `applied-upstream-diff.patch`: SHA-256 `6370622d2010da7f9bb309b875e84bdeb10b007e3a8bfc98bcf39bfef1be28b0`.
- `source-sha256.txt`: SHA-256 `77c0667562932ec97447a1bab1cd7248740834d2e13f2b81e52fb210ee2a08a2`.

The [original evidence artifact](https://github.com/AVANT-ICONIC/calyra/actions/runs/43687941941/artifacts/14151655455) is subject to time-limited retention. A dedicated one-shot archival workflow writes the exact checksum-verified records under `docs/evidence/blitz-select/` only after their identity and observations are checked.

## Architecture implications

The problem is not limited to CSS rendering. The upstream UA stylesheet delegates native select appearance to an implementation this headless renderer does not have, and Blitz's Boa DOM getter previously returned a generic value attribute instead of an option's selected value. A production solution would require a genuine control implementation, text and option painting, default option/current selection semantics, keyboard/IME, focus and native accessibility. A platform-native widget overlay is one possible architecture, but compositing and transform limitations would have to be evaluated; it is not justified by this small experiment alone.

**Next gate:** isolate actual selected-label painting and pointer/keyboard option selection, followed by real OS-level behavior. Keep OpenSpec task 4.1 unchecked, and keep CALYRA PR #2 draft and unmerged. The current result is a narrow native-engine experiment, not a production select widget.
