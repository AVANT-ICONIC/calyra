//! CALYRA narrow generic native AccessKit field semantics regression cases.
//! Run only after source-pinned disposable Blitz SelectData and AX patch overlays.
//! This does not emulate OS assistive-tech actions or real user input.

use accesskit::{Node as AccessKitNode, NodeId, Role, Toggled};
use blitz_dom::DocumentConfig;
use blitz_html::{HtmlDocument, HtmlProvider};
use blitz_traits::shell::{ColorScheme, Viewport};
use std::sync::Arc;

fn field(html: &str, target_id: &str) -> AccessKitNode {
    let mut document = HtmlDocument::from_html(
        html,
        DocumentConfig {
            viewport: Some(Viewport::new(800, 600, 1.0, ColorScheme::Light)),
            html_parser_provider: Some(Arc::new(HtmlProvider) as _),
            ..Default::default()
        },
    );
    document.resolve(0.0);
    let target = document.get_element_by_id(target_id)
        .unwrap_or_else(|| panic!("Missing control #{target_id}"));
    document.build_accessibility_tree().nodes.into_iter()
        .find(|(id, _)| *id == NodeId(target.as_u64()))
        .unwrap_or_else(|| panic!("Missing AccessKit control #{target_id}")).1
}

#[test]
fn calyra_ax_external_html_label_and_text_current_value() {
    let control = field(
        r#"<label for="person">Display name</label><input id="person" value="Taylor">"#,
        "person",
    );
    assert_eq!(control.role(), Role::TextInput);
    assert_eq!(control.label(), Some("Display name"));
    assert_eq!(control.value(), Some("Taylor"));
}

#[test]
fn calyra_ax_noneditable_selected_option_value_and_label() {
    let control = field(
        r#"<label for="priority">Render priority</label><select id="priority"><option value="balanced">Balanced</option><option value="quality">Visual fidelity</option></select>"#,
        "priority",
    );
    assert_eq!(control.role(), Role::ComboBox);
    assert_eq!(control.label(), Some("Render priority"));
    assert_eq!(control.value(), Some("Balanced"));
}

#[test]
fn calyra_ax_checkbox_enclosing_label_and_actual_checked_state() {
    let control = field(
        r#"<label>Enable effects<input id="effects" type="checkbox" checked></label>"#,
        "effects",
    );
    assert_eq!(control.role(), Role::CheckBox);
    assert_eq!(control.label(), Some("Enable effects"));
    assert_eq!(control.toggled(), Some(Toggled::True));
}

#[test]
fn calyra_ax_range_clamps_attribute_value_and_records_bounds() {
    let control = field(
        r#"<label for="level">Level</label><input id="level" type="range" min="20" max="80" value="900">"#,
        "level",
    );
    assert_eq!(control.role(), Role::Slider);
    assert_eq!(control.label(), Some("Level"));
    assert_eq!(control.value(), Some("80"));
    assert_eq!(control.numeric_value(), Some(80.0));
    assert_eq!(control.min_numeric_value(), Some(20.0));
    assert_eq!(control.max_numeric_value(), Some(80.0));
}

#[test]
fn calyra_ax_button_name_skips_aria_hidden_ornament() {
    let control = field(
        r#"<button id="apply">Apply settings <span aria-hidden="true">↗</span></button>"#,
        "apply",
    );
    assert_eq!(control.label(), Some("Apply settings"));
}

#[test]
fn calyra_ax_explicit_aria_label_takes_priority_over_html_label() {
    let control = field(
        r#"<label for="input">A visible label</label><input id="input" aria-label="Custom accessibility name" value="Test">"#,
        "input",
    );
    assert_eq!(control.label(), Some("Custom accessibility name"));
}

#[test]
fn calyra_ax_aria_labelledby_precedence_over_html_label() {
    let control = field(
        r#"<label for="input">Ignored</label><span id="actual">External</span><input id="input" aria-labelledby="actual" value="Test">"#,
        "input",
    );
    assert_eq!(control.label(), Some("External"));
}

#[test]
fn calyra_ax_computed_block_css_inserts_name_word_boundary() {
    let control = field(
        r#"<style>label strong, label small { display: block }</style>
        <label><span><strong>Enable effects</strong><small>Native checkbox with CSS presentation</small></span>
        <input id="effect" type="checkbox" checked></label>"#,
        "effect",
    );
    assert_eq!(control.label(), Some("Enable effects Native checkbox with CSS presentation"));
    assert_eq!(control.toggled(), Some(Toggled::True));
}

#[test]
fn calyra_ax_adjacent_inline_text_preserves_deliberate_concatenation() {
    let control = field(
        r#"<button id="save">Pre<strong>fix</strong></button>"#,
        "save",
    );
    assert_eq!(control.label(), Some("Prefix"));
}
