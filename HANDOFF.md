# CALYRA — HANDOFF

**Updated:** 2026-11-15
**Repository:** AVANT-ICONIC/calyra (private)
**Working branch:** feat/reference-fixtures
**PR:** https://github.com/AVANT-ICONIC/calyra/pull/2 — DRAFT and UNMERGED
**PR base:** docs/openspec-native-css-feasibility (stacked; do not change main)

**FIRST THING IN ANY NEW CHAT:** Read this HANDOFF.md from the current working branch. Continue the existing change rather than re-planning it from scratch.

## Goal

Build evidence for a browserless native HTML/CSS UI renderer that preserves familiar authored CSS without bundling Chromium/WebView. CALYRA remains a feasibility lab, **not** an approved production runtime. Compare actual rendering fidelity, behavior, OS input, performance, cost and compatibility. Do not silently substitute mock screenshots for native frames or mislabel CPU rendering as hardware GPU.

## What to read next

1. openspec/changes/establish-native-css-feasibility/tasks.md and design.md, plus relevant specs. Keep using this existing OpenSpec change, not a duplicate.
2. docs/blitz-select-label-observations.md (latest breakthrough), docs/blitz-select-observations.md, docs/blitz-plain-button-focus-observations.md, docs/blitz-document-event-chain-observations.md, docs/blitz-stage-a-observations.md.
3. native/blitz/README.md, native/blitz/reference_js_probe.rs, native/blitz/patches/, .github/workflows/native-blitz-select-label-proof.yml, and .github/workflows/preserve-blitz-selected-label-evidence.yml.
4. docs/evidence/blitz-select-label/ (permanent unmodified source artifacts).
5. fixtures/index.html, fixtures/reference.css, fixtures/reference.js, harness/adapter-contract.schema.json.

Use AVANT-ICONIC/skills/openspec-workflow and AVANT-ICONIC/gpt-webui-skills/visual-chat as complementary skills for significant work.

## Done: real, verified evidence

- **RmlUi 6.3:** Native Linux OpenGL framebuffer on Mesa llvmpipe. Original browser CSS is poorly supported; adapted RCSS only partially matches. RmlUi remains a restricted comparison backend, not a candidate with modern full CSS parity.
- **Blitz 0.3.0-beta.4** pinned at official upstream SHA **4f61cffacee50fe4f944ebe9d0470d9a5d3997e0**: all four CALYRA static HTML/CSS scenes rendered via Stylo/Taffy/AnyRender/Vello CPU, preserving unchanged original CSS bytes. Permanent screenshots: docs/evidence/blitz/.
- **Blitz/Boa original JS:** Real native Rust tests executed CALYRA's original unchanged reference.js, no browser/WebView. Restricted synthetic typing, checkbox and scroll worked; this is not actual OS input.
- **Document Escape bug:** Pinned Blitz BaseDocument::node_chain() excludes non-element document node from bubbling. Experimental native patch document-event-chain.patch restores CALYRA's original document keydown Escape handler. Real CI #43684229853 passed; durable before-after evidence in docs/evidence/blitz-keydown/.
- **Immediate focus bug:** Pinned Blitz plain button click default action clears JS-set focus. Experimental plain-button-focus.patch restores synchronous focus on menu command and Focus destination button. Real native CI #43687424754 passed 7/7; durable evidence docs/evidence/blitz-focus/.
- **Select baseline:** Clean Blitz gives 0×0 select and empty JS value. Experimental select-ua-display.patch gives a 139×48 CSS-px box (NOT Chromium sizing parity); select-default-value.patch gives initial 'balanced' and explicit-selected 'quality' values with three direct options only. CI #43687941941 passed 8/8; docs/evidence/blitz-select/.

### Latest verified milestone: **real native selected-option label pixels**

- Real CI **#43692125454**: https://github.com/AVANT-ICONIC/calyra/actions/runs/43692125454
- **9/9 real Rust/Boa integration tests passed**, pinned source compiled, official Blitz Vello CPU screenshot example built and executed, zero JS exceptions.
- Two genuine 1060×800 CPU screenshots: default select visibly renders **Balanced**; separate HTML static snapshot with selected attribute on the quality option renders **Visual fidelity**.
- Those two actual PNGs differ at **1,012 pixels** by >=12/255 in any RGB channel, localized in **bbox [685,489,796,510]** (111×21 px). Downloaded artifact and independently reverified PNG SHA-256, dimensions, source digests and pixel math.
- SHA-256 Balanced PNG: **b331a392a3a20594283d25cc08e5db81b12657524befcd419a4008fbbb211c1b**.
- SHA-256 Quality PNG: **0a9fbc495df35a779347c48cf4b754ff7bce234ad55d08b6c3a520ce6051bd27**.
- Canonical authored CSS unchanged SHA-256 **04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c**; JS unchanged SHA-256 **9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de**.
- The two screenshot scenes use **static HTML adaptations** and do NOT execute JavaScript during screenshot capture. Different selected-option states are represented by **one extra selected attribute in second HTML snapshot**, not by live interaction.
- New experiment-only patches: native/blitz/patches/select-label-parley.patch (reuses Parley text-input paint buffer to display initial option) and select-label-readonly.patch (blocks ordinary KeyDown from editing that buffer). Together with four previous patches these run only on a temporary, clean SHA-pinned official Blitz checkout. **Do not ship these hacks.**
- CI archive run **#43693424066** passed: https://github.com/AVANT-ICONIC/calyra/actions/runs/43693424066
- **13 exact SHA-256-verified original evidence files permanently saved** in docs/evidence/blitz-select-label/: raw and normalized Vello CPU PNGs, pixel diff, result JSON, Rust label JSON, full applied upstream diff, source hash manifest, both static HTML snapshots, test log, release build log. Full report: docs/blitz-select-label-observations.md. Current PR description links all evidence.

## OpenSpec / workflow constraints

- Existing change tasks currently **5/18 checked**. Stage A task 3.2 was completed as a real candidate attempt, not CSS parity. Task 4.1 remains **UNCHECKED** because full focus/keyboard/scroll/native OS-input acceptance is NOT proven.
- Keep **PR #2 draft and unmerged**, stacked on docs/openspec-native-css-feasibility. Do not change main or canonical fixtures directly. No production branch changes.
- New native research is executed in dedicated one-shot workflows, ideally triggered only by their own workflow-file edits; do not run expensive CI on every source commit.
- Any source patch for Blitz must record pinned upstream SHA, clean checkout, applied diff and real CI artifacts. Never claim production compatibility based solely on tests of internal synthetic events.

## Open problems

1. **No working select dropdown.** No pointer/keyboard option selection, selectedIndex semantics, JS value setter, option.selected reactive state, input/change event ordering, optgroup, a11y or IME.
2. Experimental select display uses **TextInputData as a rendering buffer**. Ordinary KeyDown editing is blocked, but IME/paste/edit commands, focus/caret behavior and native input safety are **not proven**. Need dedicated read-only SelectData (or equivalent) with shared text shaping and actual selection state.
3. The selected visual label comes from **initial HTML selected attr**. It is unproven and likely stale after **live JS selection changes**. True reactive label updates require a proper state/invalidation model.
4. Select width 139px in current fixture isn't browser intrinsic sizing parity; arrow, control painting, CSS clipping/transforms and real popup overlay not solved. Range input visuals remain imperfect.
5. Hardware GPU rendering, actual OS keyboard/pointer, macOS/Windows behavior, IME, accessibility, benchmarked memory/CPU/startup and full CSS feature parity remain unproven. The screenshots use **Vello CPU**; do not claim a GPU result.
6. Event-chain and button-focus patches are experimental. Review event propagation / button default semantics broadly before upstreaming or shipping.

## **Next concrete step**

**Continue on feat/reference-fixtures.** Build a targeted real Rust/Boa **select semantics and reactive-label** experiment rather than polishing static screenshots:

1. Update the existing OpenSpec design/acceptance criteria for a minimum native select state model: default option selection, selectedIndex, JS .value getter/setter, programmatic option.selected mutation, input/change event ordering, visible label update without reconstructing the entire document. Compare behavior with Chromium on identical small HTML; do not alter canonical fixtures.
2. Prototype **noneditable SelectData** with a clear selected-option state and separate Parley visual layout, not a TextInputData editor; ensure no accidental typing/IME editing.
3. Add focused source-pinned Rust/Boa regression tests and a one-shot CI workflow. Preserve exact failing results as well as successes. After live DOM semantics work, verify a real screenshot transition and consider option popup keyboard/pointer interactions and OS window integration.
4. Update the OpenSpec tasks/evidence honestly, PR #2 summary, and **HANDOFF.md at end of the next turn**. Keep branch draft and unmerged.

Do not ask the user to reconfirm these standing constraints for a simple "continue".

## Durable URLs

- PR #2: https://github.com/AVANT-ICONIC/calyra/pull/2
- Working branch: https://github.com/AVANT-ICONIC/calyra/tree/feat/reference-fixtures
- Native paint run: https://github.com/AVANT-ICONIC/calyra/actions/runs/43692125454
- Permanent 13-file proof: https://github.com/AVANT-ICONIC/calyra/tree/feat/reference-fixtures/docs/evidence/blitz-select-label
- Hash verification archival run: https://github.com/AVANT-ICONIC/calyra/actions/runs/43693424066
