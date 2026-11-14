## ADDED Requirements

### Requirement: Engine classification and availability

The evaluation SHALL explicitly distinguish browserless native GPU rendering, native CPU/software rendering, OS-provided WebViews, and bundled browser engines. Each candidate SHALL have documented version/revision, applicable license terms, platform limitations, and buildability.

#### Scenario: Candidate falls back to a WebView
- **GIVEN** a candidate advertises a native renderer but a tested feature executes in a WebView
- **WHEN** its results are reported
- **THEN** the execution path SHALL be labeled browser-backed for that feature
- **AND** it SHALL NOT be counted as browserless evidence

#### Scenario: Candidate cannot be evaluated
- **GIVEN** an engine cannot be built, licensed, or executed in the available environment
- **WHEN** the evaluation is finalized
- **THEN** its status SHALL be recorded as blocked with reason and attempted version
- **AND** no missing measurement SHALL be represented as zero or estimated performance

### Requirement: Reproducible performance protocol

CALYRA SHALL capture environment metadata and raw observations for launch, memory, CPU, frame time, and disk footprint. GPU memory and input latency SHALL be included when reliably measurable; otherwise the report SHALL explain their unavailability. Benchmark runs SHALL use the same fixture states, thermal/power conditions as far as practical, and a documented repetition count.

#### Scenario: Results are compared
- **GIVEN** Tauri and an eligible browserless candidate run the same versioned fixture
- **WHEN** the summary compares them
- **THEN** it SHALL include measurement units, software versions, device/OS information, run count, measurement method, and distribution or raw samples
- **AND** it SHALL distinguish app-only memory from system-provided engine costs when they are not captured in the same process
- **AND** it SHALL avoid claiming a universal win from one device

### Requirement: CSS compatibility and adaptation accounting

CALYRA SHALL classify each relevant feature as direct, adapted, partial, unsupported, or untested. The report SHALL distinguish authored CSS from engine-specific translations and quantify adaptation effort sufficiently to expose maintenance cost.

#### Scenario: Adapter rewrites layout rules
- **GIVEN** a candidate requires rewriting Grid into a proprietary layout API
- **WHEN** compatibility is scored
- **THEN** that feature SHALL be classified as adapted rather than direct
- **AND** the report SHALL describe the conversion and the associated maintenance risk

### Requirement: Reproducible decision report

The final evaluation SHALL include side-by-side evidence, disqualifying limitations, licensing concerns, operational complexity, and a reasoned recommendation. It SHALL explicitly allow `stop`, `integrate existing engine`, `build narrow adapter/compilation layer`, or `run targeted follow-up`.

#### Scenario: No candidate meets the required interactions
- **GIVEN** the candidates have rendered the visual fixture but cannot provide essential text input or keyboard focus behavior
- **WHEN** the decision is drafted
- **THEN** CALYRA SHALL NOT declare the browserless concept production-viable
- **AND** SHALL propose a constrained next experiment or stop with supporting evidence

### Requirement: No predetermined performance winner

CALYRA SHALL not enforce a presupposed memory, CPU, startup, binary-size, or visual-fidelity advantage as a pass condition before measuring baselines.

#### Scenario: Browser-backed baseline wins
- **GIVEN** Tauri performs better for a tested workload
- **WHEN** the report summarizes results
- **THEN** that finding SHALL be included without selective omission
- **AND** the recommendation SHALL reflect the tradeoff

### Requirement: Stage-gated candidate evaluation

CALYRA SHALL run a low-cost documentation/build/feature preflight before full benchmarking. Every candidate SHALL be classified as full-benchmark eligible, restricted-subset eligible, or blocked, with evidence for the classification.

#### Scenario: Engine cannot parse CSS Grid
- **GIVEN** a candidate supports Flexbox but lacks direct Grid layout
- **WHEN** preflight results are reviewed
- **THEN** the Grid feature SHALL remain marked unsupported or adapted
- **AND** any restricted performance comparison SHALL be labeled by its supported fixture subset
- **AND** the candidate SHALL NOT receive a full modern-CSS compatibility rating

#### Scenario: Experimental UI executes privileged content
- **GIVEN** a renderer executes UI inside the application main process
- **WHEN** the implementation plan evaluates security implications
- **THEN** it SHALL record trusted-content boundaries and injection risks
- **AND** SHALL NOT treat untrusted HTML as safely isolated without evidence of a sandbox

### Requirement: Fair readiness and frame measurement

Launch measurements SHALL separately identify window creation, first meaningful frame, and first usable input where possible. Visual animation and scrolling SHALL be measured using actual frame timing rather than an assumed refresh rate.

#### Scenario: Frame-time instrumentation unavailable
- **GIVEN** a backend cannot expose reliable frame timings
- **WHEN** benchmark results are compared
- **THEN** its frame-time metric SHALL be reported as unavailable or via a documented independent method
- **AND** SHALL NOT be assigned a fabricated FPS score
