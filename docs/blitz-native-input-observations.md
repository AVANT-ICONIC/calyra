# Blitz Stage A: actual CALYRA input behavior (2026-11-15)

**Provenance:** [real Linux GitHub Actions run 43679854771](https://github.com/AVANT-ICONIC/calyra/actions/runs/43679854771), upstream pinned Blitz **0.3.0-beta.4** commit `4f61cffacee50fe4f944ebe9d0470d9a5d3997e0`, Rust 1.91. A first build failed at compile because the probe used the wrong keyboard-types enum (`Key::Escape`); this was fixed to `Key::Named(NamedKey::Escape)` in commit `81e0aece`. The corrected run compiled the **real upstream test harness** and executed **2/2** CALYRA-native event tests successfully, without a browser/WebView. Build/test log and original result JSON are in [artifact 14147872214](https://github.com/AVANT-ICONIC/calyra/actions/runs/43679854771/artifacts/14147872214), with time-limited GitHub retention.

**Scope:** unchanged original authored CSS SHA-256 `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c` in statically activated HTML fixtures; JavaScript intentionally not executed. Events are synthesized by the *actual* `blitz-test-harness` through Blitz's internal UI event driver. This is **not** a test of OS keyboard/mouse routing, dropdown popup, accessibility, browser JavaScript or GPU acceleration. Exact executed probe SHA-256: `566c01f5ddc602470a6150ff4a18973cb0d20f1394d0b0bc3afbbf080f09e5a5`.

| Observation | Real outcome |
| --- | --- |
| Text input receives focus from harness click | **True** |
| Text editor changes after typing the character Z | **True** |
| Checkbox checked initially | **True** |
| Checkbox toggles when clicking its label | **True** |
| Wheel scroll in original CALYRA scroll area | **184px** after 250px synthetic wheel event (from 0) |
| Select element and its 3 options exist in DOM | **True** |
| Select receives a nonempty layout box | **False**: **0 × 0px** |
| Range receives a nonempty layout box | **True**: **696 × 6px** |
| Command button becomes focused after native click | **False** in this run |
| Menu reacts to click/Escape without JavaScript | **False**, **expected** because the fixture's JS was intentionally not executed |

The select defect is a **layout/control construction gap**, not merely a missing colored widget: 3 option nodes parse successfully, but the select is 0×0. Range has a real box, but its Chromium styling and thumb remain visibly absent in the prior paint comparison. Button focus differs from browser expectations and requires an isolated focus test before assigning cause.

Full machine-readable facts are preserved at [controls](evidence/blitz-input/calyra-controls-input.json) and [interaction](evidence/blitz-input/calyra-interaction-input.json) (original content transcribed without altering fields). The time-limited original artifact provides execution logs.

**Next gate:** distinguish native control defaults and JavaScript-triggered behavior using Blitz's optional Boa `ScriptDocument` and CALYRA's **byte-identical reference.js**, then investigate the select box construction path upstream. OpenSpec task 4.1 remains **unchecked** until focus/scroll/keyboard and behavior are confirmed across supported native targets and against Chromium.
