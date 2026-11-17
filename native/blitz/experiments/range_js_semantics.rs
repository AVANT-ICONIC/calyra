//! CALYRA isolated, source-pinned script-layer RangeData integration tests.
//! Confirms actual Boa getters/setters use native DOM range state, not an
//! attribute update or duplicate JS state. No OS pointer/keyboard events here.
use blitz_dom::{Document, DocumentConfig};
use blitz_vibey_script::ScriptDocument;

fn native_script_document(html: &str) -> ScriptDocument {
    let mut doc = ScriptDocument::from_html(html, DocumentConfig::default());
    doc.inner_mut().resolve(0.0);
    doc
}

#[test]
fn programmatic_js_value_updates_native_range_not_default_html_or_events() {
    let mut doc = native_script_document(
        r#"<label for="level">Level</label><input id="level" type="range" value="64">"#
    );
    doc.eval(r#"
        const input = document.getElementById('level');
        let synthetic = 0;
        input.addEventListener('input', () => synthetic++);
        input.addEventListener('change', () => synthetic++);
        __blitz_send_message(input.value);
        __blitz_send_message(input.getAttribute('value'));
        input.value = "18";
        __blitz_send_message(input.value);
        __blitz_send_message(input.getAttribute('value'));
        __blitz_send_message(String(synthetic));
        input.value = "18";
        __blitz_send_message(input.value);
    "#);
    assert_eq!(doc.take_js_errors(), Vec::<String>::new());
    assert_eq!(doc.take_messages(),
        ["64","64","18","64","0","18"]);
    let inner = doc.inner();
    let id = inner.get_element_by_id("level").unwrap();
    let state = inner.get_node(id).unwrap().element_data().unwrap().range_data().unwrap();
    assert_eq!(state.value, 18.0);
    assert_eq!(state.default_value, 64.0);
}

#[test]
fn programmatic_js_range_step_and_bounds_use_same_native_state() {
    let mut doc = native_script_document(
        r#"<input id="level" type="range" min="20" max="80" step="5" value="26">"#
    );
    doc.eval(r#"
        const input = document.getElementById('level');
        __blitz_send_message(input.value);
        input.value = '73';
        __blitz_send_message(input.value);
        input.value = '-400';
        __blitz_send_message(input.value);
        input.value = '900';
        __blitz_send_message(input.value);
    "#);
    assert_eq!(doc.take_js_errors(), Vec::<String>::new());
    assert_eq!(doc.take_messages(), ["25","75","20","80"]);
    let inner = doc.inner();
    let id = inner.get_element_by_id("level").unwrap();
    assert_eq!(inner.get_node(id).unwrap().element_data().unwrap()
        .range_data().unwrap().value, 80.0);
}

#[test]
fn native_range_getter_remains_undefined_for_non_range_dom_case() {
    let mut doc = native_script_document(
        r#"<input id="text" value="Hello"><input id="range" type="range" value="11">"#
    );
    doc.eval(r#"
        __blitz_send_message(document.getElementById('text').value);
        __blitz_send_message(document.getElementById('range').value);
    "#);
    assert_eq!(doc.take_js_errors(), Vec::<String>::new());
    assert_eq!(doc.take_messages(), ["Hello","11"]);
}

#[test]
fn ordinary_text_input_object_conversion_occurs_exactly_once() {
    let mut doc = native_script_document(r#"<input id="name" type="text" value="Initial">"#);
    doc.eval(r#"
        let conversions = 0;
        const special = {toString() { conversions++; return 'Converted'; }};
        const input = document.getElementById('name');
        input.value = special;
        __blitz_send_message(String(conversions));
        __blitz_send_message(input.value);
    "#);
    assert_eq!(doc.take_js_errors(), Vec::<String>::new());
    assert_eq!(doc.take_messages(), ["1","Converted"]);
}
