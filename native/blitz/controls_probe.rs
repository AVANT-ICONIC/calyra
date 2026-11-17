//! CALYRA integration tests against pinned Blitz 0.3.0-beta.4.
//! Uses Blitz's actual internal DOM event dispatcher, not browser JavaScript.
use blitz_test_harness::{Harness, HarnessOptions};
use blitz_traits::shell::ColorScheme;
use keyboard_types::{Key, NamedKey};
use std::{env, fs, path::Path};

fn html(path_var: &str) -> String {
    fs::read_to_string(env::var(path_var).expect("CALYRA snapshot env var missing"))
        .expect("CALYRA HTML snapshot missing")
}

fn save_report(name: &str, json: &str) {
    let dir = env::var("CALYRA_PROBE_OUT").expect("CALYRA_PROBE_OUT not set");
    let output = Path::new(&dir).join(format!("calyra-{name}-input.json"));
    fs::write(&output, format!("{json}\n")).expect("Cannot write native Blitz report");
    println!("CALYRA_NATIVE_INPUT_REPORT={}", output.display());
}

fn bool_json(value: bool) -> &'static str {
    if value { "true" } else { "false" }
}

#[test]
fn calyra_controls_probe() {
    let mut h = Harness::from_html_with(
        &html("CALYRA_CONTROLS_HTML"),
        HarnessOptions { width: 1060, height: 800, scale: 1.0, color_scheme: ColorScheme::Dark, ..Default::default() },
    );
    let select_exists = h.query("#priority").is_some();
    let select_options = h.query_all("#priority option").len();
    let select_rect = h.layout_rect("#priority");
    let select_has_box = select_rect.width > 2.0 && select_rect.height > 2.0;
    let range_rect = h.layout_rect("#intensity");
    let range_has_box = range_rect.width > 2.0 && range_rect.height > 2.0;
    let name_id = h.node("#person-name");
    let read_name = |h: &Harness| -> String {
        let doc = h.base();
        let node = doc.get_node(name_id).expect("person-name node missing");
        let element = node.element_data().expect("input is not an element");
        element.text_input_data().expect("no input editor").editor.text().to_string()
    };
    let original_text = read_name(&h);
    h.click("#person-name");
    let name_focused = h.focused() == Some(name_id);
    h.type_text("Z");
    let typed_text = read_name(&h);
    let input_text_changed = typed_text != original_text && typed_text.contains('Z');

    let effects_id = h.node("#effects");
    let is_checked = |h: &Harness| -> Option<bool> {
        h.base().get_node(effects_id)
            .and_then(|node| node.element_data())
            .and_then(|el| el.checkbox_input_checked())
    };
    let checked_before = is_checked(&h);
    h.click(".toggle-row");
    let checked_after = is_checked(&h);
    let checkbox_toggled = checked_before.is_some() && checked_after == checked_before.map(|v| !v);

    let report = format!(
        "{{\"schema\":\"calyra.blitz-input.v1\",\"fixture\":\"controls\",\"input_source\":\"blitz_test_harness_synthetic_native_events\",\"css_modified\":false,\"javascript_executed\":false,\"select_exists_in_dom\":{},\"select_option_count\":{},\"select_layout_has_box\":{},\"select_box_width\":{},\"select_box_height\":{},\"range_layout_has_box\":{},\"range_box_width\":{},\"range_box_height\":{},\"name_focused_after_click\":{},\"name_text_changed_after_typing\":{},\"checkbox_initially_checked\":{},\"checkbox_toggled_by_label\":{}}}",
        bool_json(select_exists), select_options,
        bool_json(select_has_box), select_rect.width, select_rect.height,
        bool_json(range_has_box), range_rect.width, range_rect.height,
        bool_json(name_focused), bool_json(input_text_changed),
        bool_json(checked_before == Some(true)), bool_json(checkbox_toggled),
    );
    save_report("controls", &report);
    assert!(select_exists && select_options >= 2, "wrong canonical CALYRA fixture");
}

#[test]
fn calyra_interaction_probe() {
    let mut h = Harness::from_html_with(
        &html("CALYRA_INTERACTION_HTML"),
        HarnessOptions { width: 1060, height: 800, scale: 1.0, color_scheme: ColorScheme::Dark, ..Default::default() },
    );
    let scroll_id = h.node("#scroll-region");
    let rect = h.layout_rect("#scroll-region");
    let offset = |h: &Harness| -> f64 {
        h.base().get_node(scroll_id).unwrap().scroll_offset().y
    };
    let before = offset(&h);
    if rect.width > 1.0 && rect.height > 1.0 {
        h.wheel_at(rect.x + rect.width / 2.0, rect.y + rect.height / 2.0, 0.0, -250.0);
    }
    let after = offset(&h);
    let scroll_moved = after > before;

    let button_id = h.node("#menu-toggle");
    h.click("#menu-toggle");
    let button_focused = h.focused() == Some(button_id);
    let expanded_after_click = h.attr("#menu-toggle", "aria-expanded") == Some("true".into());
    // Browser JS was removed from the snapshot; we intentionally do not
    // conflate missing script behavior with broken native pointer dispatch.
    h.press(Key::Named(NamedKey::Escape));
    let expanded_after_escape = h.attr("#menu-toggle", "aria-expanded") == Some("true".into());
    let report = format!(
        "{{\"schema\":\"calyra.blitz-input.v1\",\"fixture\":\"interaction\",\"input_source\":\"blitz_test_harness_synthetic_native_events\",\"css_modified\":false,\"javascript_executed\":false,\"scroll_box_width\":{},\"scroll_box_height\":{},\"scroll_offset_before\":{},\"scroll_offset_after\":{},\"scroll_moved_after_wheel\":{},\"button_focused_after_click\":{},\"menu_expanded_without_javascript\":{},\"menu_expanded_after_escape_without_javascript\":{}}}",
        rect.width, rect.height, before, after, bool_json(scroll_moved),
        bool_json(button_focused), bool_json(expanded_after_click), bool_json(expanded_after_escape),
    );
    save_report("interaction", &report);
}
