# Proposal: Establish CALYRA's native CSS feasibility

## Why

CSS is an expressive and familiar interface authoring system, but many cross-platform desktop applications rely on browser engines or adopt incompatible styling APIs. The hypothesis that a small, browserless native renderer can offer comparable real-world CSS fidelity with materially different cost has not been demonstrated for CALYRA.

Several candidate engines already exist. Building a custom renderer before understanding their strengths and gaps would be a high-cost, low-evidence decision.

## What Changes

- Establish a common reference interface and interaction contract that is intentionally challenging but bounded.
- Compare browserless candidates **Blitz**, **RmlUi**, and **Electrobun experimental GPU UI** with **Tauri/system-WebView** as a browser-backed control, when technically available.
- Produce a compatibility matrix and reproducible measurements for fidelity, functionality, accessibility, startup, CPU/RAM/GPU use, frame pacing, package footprint, and integration effort.
- Make an evidence-based recommendation: integrate an existing engine, build a small compilation/adapter layer, run a second experiment, or stop.
- Document licensing, platform support, limitations, and missing data rather than smoothing them over.

## Capabilities

### New Capabilities

- `reference-ui-fixtures`: a versioned, shared set of CSS-authored scenarios and observable interactions.
- `engine-evaluation`: classified candidate adapters, repeatable benchmark protocol, evidence reports, and explicit decision criteria.

## Non-goals

- Building a production runtime, CSS parser, independent layout engine, general-purpose GUI framework, or GPU renderer.
- Guaranteeing modern CSS coverage, one identical cross-platform binary, or a particular memory/performance win.
- Designing a new CSS dialect, portable UI intermediate representation, C ABI, or package manager.
- Implementing Material Grammar, physical simulations, shader-based Materialism effects, remote UI transport, or framework retrofit adapters in this change.
- Shipping Windows/Linux/iOS/Android binaries. macOS is the initial measured environment; other platforms are scoped separately.

## Impact

- Initializes CALYRA's first OpenSpec change and the eventual reproducible experimental harness.
- No existing product code or users are affected.
- Feasibility conclusions depend on actual candidate API status, platform access, and license terms at evaluation time.

## Decision to make after the experiment

Pick a narrowly justified next change based on observed gaps and adoption leverage. Do **not** preselect a renderer or design an entire new framework from assumptions.

## Risks

- A candidate may be unbuildable, immature, or incorrectly described as browserless.
- Perfect CSS fidelity is not feasible across engines. The report must distinguish native CSS, adapted CSS, and unsupported features.
- Apparent memory savings may shift costs into system-provided components or GPU memory.
- Different input, text, and accessibility stacks can dominate development effort despite impressive screenshots.
- Engine licensing may prohibit the intended redistribution or integration.

## Rollback

All planned outputs are experimental. If candidates are unviable, retain evidence and close/archive this change without creating a runtime. No production migration is required.
