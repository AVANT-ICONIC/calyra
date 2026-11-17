# CALYRA · Linux system-WebView Stage A (real WebKitGTK 4.1)

**Date:** 2026-11-16. **Engine:** system WebKitGTK **2.52.6** on Ubuntu 24.04, GTK3, Xvfb/X11. **Status:** all original-asset WebKitGTK rendering and JavaScript checks **passed**, with a separate successful archival run. This is a **Linux engine probe, not an application packaged or launched by Tauri**, and **not macOS WKWebView**.

## Exact evidence and outcomes

- [Producing run #43932124401](https://github.com/AVANT-ICONIC/calyra/actions/runs/43932124401): all four real WebKitGTK scene launches **passed**, using original `fixtures/index.html`, `reference.css` and `reference.js` loaded as local file URLs with ordinary relative asset references. The independent `harness/verify_webkitgtk_baseline.py` passed all state, dimensions, source SHA-256, screenshot SHA-256 and original programmatic-control interaction tests.
- **Four initial 1060×800 snapshots**, plus after-DOM-interaction captures for `controls` and `interaction`, **six actual WebKitGTK Cairo PNGs**. Controls prove `select.value`, apply/reset output and event silence from the original JS. Interaction proves original menu open, simulated Escape close and focus-to-destination behavior. All actions are **untrusted JS-generated events**, not native X11 keyboard/pointer input.
- The producing run's final Git push was **rejected because another process committed to `feat/reference-fixtures` during the test**. The rendering and verifier stages were green and the complete 18-file original artifact had already uploaded. This is not an engine failure.
- [Archive run #43932469917](https://github.com/AVANT-ICONIC/calyra/actions/runs/43932469917) **passed**, retrieved that exact producing-run artifact, independently checked the original code and PNG hashes, re-verified the four scenes, and committed **18 original byte-for-byte files** at [`docs/evidence/webkitgtk-linux-stage-a/`](evidence/webkitgtk-linux-stage-a/). Its branch updates use fetch/recheckout/retry for concurrent writers.
- The full capture's `verification.json` explicitly states `tauri_shell_tested=false`, `macos_wkwebview_tested=false`, `physical_os_input_tested=false`, `hardware_gpu_verified=false`, and `performance_comparison_eligible=false`.
- Original asset hashes: HTML `aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a`; CSS `04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c`; JS `9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de`.

## Independent baseline comparison already present on branch

An independently built source-pinned WebKitGTK Stage A workflow [#43930684985](https://github.com/AVANT-ICONIC/calyra/actions/runs/43930684985) also **passed** and permanently archived **6 scenarios and 8 images**, including 390×844 mobile dashboard, at [`docs/evidence/system-webkitgtk-reference/`](evidence/system-webkitgtk-reference/). It is a separate harness and test design.

Source hashes and image bytes show **two exact cross-harness matches** under WebKitGTK 2.52.6:

| Fixture at 1060×800 | SHA-256 initial PNG | Result |
| --- | --- | --- |
| Controls | `22b9bb1b3369bc3fd78773e580bcb57e306014eb9368bba1c8bbae27655cdbad` | Exact between our Cairo snapshot and independent native snapshot |
| Visual | `6b9b3c391cf657709e8889882b2e388eb44a77a698591e905b499ea148a45fe3` | Exact between the two native snapshot paths |

Other scenario hashes differ. The independent runner sometimes captured via **GDK X11 window pixbuf** rather than native WebKit snapshot, and itself archived blank X11 capture diagnostics for some scenes; do not imply general pixel-level determinism across all capture paths.

The separate [controls pixel comparison](evidence/comparisons/webkitgtk-blitz-controls/controls-comparison-result.json) against Blitz/Boa/Vello CPU reports **51,944 / 848,000 pixels** differing at RGB threshold 12 (**6.1255%**), with intentionally scoped select region **16,257 / 20,400** differing (**79.6912%**). Header and sidebar regions differ much less. The comparison uses **different GitHub runner jobs** and uncontrolled font/capture antialiasing and is **not** a CSS-property support percentage or fairness-corrected visual ranking.

## Memory/timing diagnostics: NOT a benchmark

The additional probe captured one system `ps` RSS sample of itself plus reachable WebKit child processes after each fixture, yielding **544,632–556,788 KiB summed RSS (~532–544 MiB)** (raw field expressed in KiB; includes a short-lived `ps` child, shared mapped pages and unshared process accounting). This is **not private memory**, **not 20-tab memory** and **not comparable to Blitz**. Four sequential single-run JavaScript readiness observations ranged from ~1.05 to 1.44 seconds, but startup/process scheduling, warm caches, Xvfb and runner variance were not controlled. Neither result should be marketed as a speed or resource claim.

## Gate decisions

- **Linux system-WebKitGTK engine baseline:** proven for four CALYRA fixtures and synthetic DOM interactions, with durable original images and logs.
- **OpenSpec task 3.1 (Tauri system WebView):** **unchecked**, because neither WebKitGTK harness is Tauri's actual shell and no macOS WKWebView was exercised.
- **OpenSpec task 4.1 (real OS input, comparative states):** **unchecked**. Synthetic click and keydown are not physical/trusted keyboard or pointer events; accessibility/IME untouched.
- **OpenSpec task 4.2 (five comparable measurements):** **unchecked**. Single noisy diagnostic samples and cross-run screenshot differences are not repeated matched performance measurements.
- **Next highest-value technical gate:** run a real Tauri 2 window (and macOS WKWebView when available) with the same canonical assets, instrument trusted OS events and 5+ repeatable process/launch measurements on the *same hardware/software environment*. Prioritize the select and range form-control regions for correctness before chasing blanket speed claims.
