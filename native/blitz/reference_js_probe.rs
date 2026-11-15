//! CALYRA's original JS, unchanged, against pinned Blitz ScriptDocument + Boa.
//! Embedded URL and stylesheet delivery are adapted; no browser/WebView is used.
use blitz_dom::{Document, DocumentConfig, NodeId};
use blitz_traits::events::{BlitzKeyEvent, DomEvent, KeyState, UiEvent};
use blitz_vibey_script::ScriptDocument;
use keyboard_types::{Code, Key, Location, Modifiers, NamedKey};
use std::{env, fs, path::Path};

fn read(key: &str) -> String {
    fs::read_to_string(env::var(key).expect("CALYRA source env var missing")).expect("source missing")
}

fn document(fixture: &str) -> ScriptDocument {
    let html = read("CALYRA_CANONICAL_HTML");
    let css = read("CALYRA_CANONICAL_CSS");
    let js = read("CALYRA_CANONICAL_JS");
    assert!(!css.contains("</style>") && !js.contains("</script>"));
    let css_link = r#"<link rel="stylesheet" href="./reference.css">"#;
    let js_link = r#"<script src="./reference.js" defer></script>"#;
    assert_eq!(html.matches(css_link).count(), 1);
    assert_eq!(html.matches(js_link).count(), 1);
    // Author CSS and JS bytes are untouched. The preceding test script only
    // supplies the desired fixture query in place of browser navigation.
    let html = html.replace(css_link, &format!("<style>\n{css}\n</style>"));
    let html = html.replace(js_link, &format!(
        "<script>window.__calyraFixtureQuery = '?fixture={fixture}&motion=off';</script><script>\n{js}\n</script>"
    ));
    let mut doc = ScriptDocument::from_html(&html, DocumentConfig::default())
        .without_timer_thread();
    doc.execute_scripts();
    doc.inner_mut().resolve(0.0);
    doc
}

fn query(doc: &ScriptDocument, selector: &str) -> NodeId {
    doc.inner().query_selector(selector).unwrap().expect(selector)
}

fn click(doc: &mut ScriptDocument, selector: &str) {
    let event = {
        let inner = doc.inner();
        let id = inner.query_selector(selector).unwrap().expect(selector);
        DomEvent::new(id, inner.get_node(id).unwrap().synthetic_click_event(Modifiers::empty()))
    };
    doc.dispatch_dom_event(event);
    doc.inner_mut().resolve(0.0);
}

fn state(doc: &mut ScriptDocument, expr: &str) -> String {
    doc.eval(&format!("__blitz_send_message(JSON.stringify({expr}))"));
    doc.take_messages().into_iter().last().unwrap_or_else(|| "null".to_string())
}

fn save(scene: &str, observations: &str, errors: &[String]) {
    let dir = env::var("CALYRA_JS_OUT").expect("report directory unset");
    let path = Path::new(&dir).join(format!("calyra-js-{scene}.json"));
    let json = format!(
        "{{\"schema\":\"calyra.blitz-js.v1\",\"fixture\":\"{scene}\",\"reference_js_modified\":false,\"javascript_execution_attempted\":true,\"os_input_tested\":false,\"gpu_tested\":false,\"js_error_count\":{},\"observations\":{observations}}}",
        errors.len()
    );
    fs::write(&path, format!("{json}\n")).expect("cannot write native JS evidence");
    for error in errors { eprintln!("CALYRA_NATIVE_JS_ERROR={error}"); }
    println!("CALYRA_NATIVE_JS_REPORT={}", path.display());
}

#[test]
fn calyra_original_controls_script() {
    let mut doc = document("controls");
    let before = state(&mut doc, "({ready:document.body.dataset.ready,active:document.querySelectorAll('.case.active').length,selectedNav:document.querySelectorAll('[aria-current=page]').length})");
    click(&mut doc, "#apply");
    let after = state(&mut doc, "({ready:document.body.dataset.ready,status:document.getElementById('action-status').value,focused:document.activeElement&&document.activeElement.id})");
    let errors = doc.take_js_errors();
    save("controls", &format!("{{\"before\":{before},\"after_click\":{after}}}"), &errors);
    assert_ne!(query(&doc, "#apply"), query(&doc, "#reset"));
}

#[test]
fn calyra_original_interaction_script() {
    let mut doc = document("interaction");
    let before = state(&mut doc, "({ready:document.body.dataset.ready,active:document.querySelectorAll('.case.active').length,expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),hidden:document.getElementById('menu-popover').hidden})");
    click(&mut doc, "#menu-toggle");
    let opened = state(&mut doc, "({expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),hidden:document.getElementById('menu-popover').hidden,focused:document.activeElement&&document.activeElement.getAttribute('data-command')})");
    doc.handle_ui_event(UiEvent::KeyDown(BlitzKeyEvent {
        key: Key::Named(NamedKey::Escape), code: Code::Escape, modifiers: Modifiers::empty(),
        location: Location::Standard, is_auto_repeating: false,
        is_composing: false, state: KeyState::Pressed, text: None,
    }));
    doc.inner_mut().resolve(0.0);
    let closed = state(&mut doc, "({expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),hidden:document.getElementById('menu-popover').hidden,focused:document.activeElement&&document.activeElement.id})");
    let errors = doc.take_js_errors();
    save("interaction", &format!("{{\"before\":{before},\"after_click\":{opened},\"after_escape\":{closed}}}"), &errors);
}
