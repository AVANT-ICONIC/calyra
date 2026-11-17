# Contributing to CALYRA

CALYRA is a **native CSS feasibility lab**, not an established production GUI framework. Contributions are welcome when they produce a reproducible answer to a concrete compatibility, rendering, input, accessibility, licensing, or measurement question.

## Before starting

1. Read the [project README](README.md), the existing [OpenSpec change](openspec/changes/establish-native-css-feasibility/proposal.md), its [tasks](openspec/changes/establish-native-css-feasibility/tasks.md), and the current research-branch [handoff](HANDOFF.md). Some of these artifacts live on stacked, unmerged branches rather than `main`.
2. Look for an existing experiment or open PR that owns the same question. Avoid duplicate implementation and new frameworks before existing-engine evidence has been exhausted.
3. State what behavior you intend to prove and what would falsify it. Work in a short-lived branch and open a PR with focused evidence. Do not edit or push to `main` as part of experimental work.

## Run and report experiments

- Prefer canonical fixtures in `fixtures/` and the existing harness/adapters. Do **not** change authored CSS/JavaScript to make one engine appear more compatible.
- The [Blitz reproduction guide](native/blitz/README.md) documents the pinned upstream revision, dependencies, commands, and known capture limitations. Rust/Boa patches in `native/blitz/patches/` are experiments applied to a disposable upstream checkout, not bundled production code.
- Record exact environment, upstream revisions, build commands, source hashes, direct CSS versus translated CSS, screenshots or event traces, and failed attempts as well as successes.
- Identify rendering correctly: Vello **CPU** is not a hardware-GPU result; synthesized DOM events are not physical OS input; a static screenshot is not an interactive control.
- Capture benchmark data under comparable conditions; do not claim latency, memory, CSS parity or accessibility improvements without actual measurements.

## Pull-request checklist

- [ ] The affected existing OpenSpec capability/task is linked; no competing shadow spec is introduced.
- [ ] Tests and actual observed outputs are included, with a reproducible command or documented environmental blocker.
- [ ] Original CSS/JS and archived evidence are unchanged unless explicitly justified; upstream-derived code and licenses are attributed.
- [ ] Results distinguish **verified**, **partial**, **blocked** and **untested**. Production readiness is not implied by experimental success.
- [ ] The README or relevant existing documentation is updated if public behavior or evidence changes.

## Security, attribution and licensing

Do not submit credentials, personal data, nonredistributable media, or private upstream code. Keep the source and license attribution of third-party components, especially Blitz and browser/renderer dependencies. The project's proposed MIT license in this research branch covers contributions owned or legitimately licensed for this project; dependency and derivative-work terms still apply.

For a behavior gap, open an issue with the minimal fixture, expected/actual result, exact versions and relevant screenshots/logs. For work involving native windowing or real OS events, clearly specify the tested operating system.
