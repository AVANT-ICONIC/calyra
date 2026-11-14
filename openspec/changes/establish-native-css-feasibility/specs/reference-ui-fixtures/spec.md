## ADDED Requirements

### Requirement: Versioned reference interface

CALYRA SHALL define an immutable-for-each-run, versioned reference interface with the same content, interactions, visual states, viewport dimensions, and font assets for each evaluated target.

#### Scenario: Compare two engines on one fixture
- **GIVEN** a versioned fixture and a baseline rendering
- **WHEN** a candidate adapter runs the fixture
- **THEN** the comparison SHALL name the fixture version and include equivalent states, sizes, and input steps
- **AND** any adapter translation SHALL be recorded instead of presented as direct CSS support

### Requirement: Representative workloads

The fixture suite SHALL include (1) a control gallery, (2) a responsive multi-column interface, (3) a visually demanding effects scene, and (4) an interactive input/scroll/focus flow. It SHALL exercise, where supported: CSS cascade/inheritance, custom properties, Flexbox, Grid, typography and fallback, SVG, clipping, transforms, transitions, animations, gradients, shadows, backdrop blur, resizing, keyboard/pointer input, text editing and focus.

#### Scenario: Unsupported visual feature
- **GIVEN** a fixture requests backdrop blur and an engine does not support it
- **WHEN** the evaluator renders the fixture
- **THEN** the report SHALL mark backdrop blur unsupported or adapted
- **AND** SHALL preserve an image or other evidence of the actual rendering
- **AND** SHALL NOT silently replace the fixture with a superficially similar implementation and count it as full CSS compatibility

### Requirement: Functional interaction trace

CALYRA SHALL specify expected user actions and observable results for interactive fixtures, including pointer activation, tab navigation, focus indication, scrolling, resizing, and basic text input.

#### Scenario: Keyboard interaction
- **GIVEN** the control gallery is loaded and focused
- **WHEN** the recorded keyboard-navigation sequence is executed
- **THEN** each intended focus and activation result SHALL be checked against the reference
- **AND** deviations SHALL be recorded as functional failures rather than visual-only findings

### Requirement: Transparent accessibility evidence

CALYRA SHALL record whether accessible names, roles, focus order, keyboard navigation, and platform accessibility APIs are supported, missing, or untested by each implementation.

#### Scenario: No accessibility-tree support
- **GIVEN** an engine cannot expose the required native accessibility semantics
- **WHEN** its evaluation completes
- **THEN** that limitation SHALL be visible in the results
- **AND** visual fidelity SHALL NOT be treated as a substitute for accessibility

### Requirement: Canonical CSS and asset provenance

The fixture source SHALL be identical across targets where parsing is supported. Each engine-specific rewrite, preprocessing rule, substituted asset, or system-font fallback SHALL be versioned and reported separately from direct source execution.

#### Scenario: Unsupported Grid syntax
- **GIVEN** the canonical responsive fixture uses CSS Grid
- **WHEN** an implementation substitutes Flexbox for Grid
- **THEN** the report SHALL classify the Grid capability as adapted or unsupported, never direct
- **AND** the unchanged source fixture SHALL remain available for comparison

#### Scenario: Different font support
- **GIVEN** an engine cannot load the reference web font
- **WHEN** screenshots are compared
- **THEN** CALYRA SHALL record the substitution and font metrics separately
- **AND** SHALL NOT attribute font-specific pixel differences to the GPU renderer

### Requirement: Visual and localization checkpoints

Each fixture SHALL record its intended CSS viewport, device pixel ratio, screenshot timing, and action/state checkpoints. At least one typography-focused variation SHALL exercise longer translated labels and non-ASCII text, with IME/bidirectional text limitations recorded as such.

#### Scenario: A visual diff is reviewed
- **GIVEN** an automated screenshot diff detects differences
- **WHEN** the result is included in a comparison
- **THEN** its dimensions, scale, state, and relevant font setup SHALL be reported
- **AND** layout or interaction errors SHALL be distinguished from expected rasterization differences
