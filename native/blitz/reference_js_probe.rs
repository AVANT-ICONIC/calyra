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


#[test]
fn calyra_focus_dispatch_diagnostic() {
    // A separate *diagnostic* experiment. The original JS is unchanged.
    // We intervene after the failing menu-open path to isolate whether
    // focus() or keyboard-event propagation is responsible.
    let mut doc = document("interaction");
    click(&mut doc, "#menu-toggle");
    let command = query(&doc, "#menu-popover button");
    let focused_initial = doc.inner().get_focussed_node_id() == Some(command);
    let before = state(&mut doc, "({expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),focused:document.activeElement&&document.activeElement.id})");

    // Attempt focus after the menu has become visible and layout updated.
    doc.eval("document.querySelector('#menu-popover button').focus()");
    doc.inner_mut().resolve(0.0);
    let focused_after_delayed_js = doc.inner().get_focussed_node_id() == Some(command);
    let after_js_focus = state(&mut doc, "({focused:document.activeElement&&document.activeElement.getAttribute('data-command')})");

    // Distinguish failed JS focus from failed keyboard dispatch by making
    // the native engine focus the same node directly. This is instrumentation,
    // never counted as unmodified browser behavior.
    doc.inner_mut().set_focus_to(command);
    let focused_after_native = doc.inner().get_focussed_node_id() == Some(command);
    doc.handle_ui_event(UiEvent::KeyDown(BlitzKeyEvent {
        key: Key::Named(NamedKey::Escape), code: Code::Escape, modifiers: Modifiers::empty(),
        location: Location::Standard, is_auto_repeating: false,
        is_composing: false, state: KeyState::Pressed, text: None,
    }));
    doc.inner_mut().resolve(0.0);
    let after_escape = state(&mut doc, "({expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),hidden:document.getElementById('menu-popover').hidden,focused:document.activeElement&&document.activeElement.id})");
    let errors = doc.take_js_errors();
    let observations = format!(
        "{{\"focused_after_original_open\":{},\"before\":{},\"focused_after_delayed_js_focus\":{},\"after_delayed_js_focus\":{},\"focused_after_forced_native_focus\":{},\"after_escape\":{}}}",
        focused_initial, before, focused_after_delayed_js, after_js_focus, focused_after_native, after_escape
    );
    save("focus-diagnostic", &observations, &errors);
}


/// Compare native UI KeyDown routing with explicit DOM events at a focused
/// descendant, body and document. The author's reference.js is untouched.
/// The trace is instrumentation: its observations are not automatically
/// interpreted as "keyboard support", nor are these physical OS key events.
fn calyra_escape_key() -> BlitzKeyEvent {
    BlitzKeyEvent {
        key: Key::Named(NamedKey::Escape),
        code: Code::Escape,
        modifiers: Modifiers::empty(),
        location: Location::Standard,
        is_auto_repeating: false,
        is_composing: false,
        state: KeyState::Pressed,
        text: None,
    }
}

#[test]
fn calyra_keyboard_routing_diagnostic() {
    use blitz_traits::events::DomEventData;
    let mut results = Vec::new();
    let mut all_errors = Vec::new();

    for route in ["ui", "dom-focused", "dom-body", "dom-document"] {
        let mut doc = document("interaction");
        // Add read-only listeners after original source script has executed.
        // These probes do not alter CALYRA's original application listeners.
        doc.eval(r#"
            window.__calyraKeyTrace = [];
            [
              [document.querySelector('#menu-popover button'), 'command'],
              [document.body, 'body'],
              [document, 'document'],
              [window, 'window']
            ].forEach(([target, where]) => {
              target.addEventListener('keydown', event => {
                window.__calyraKeyTrace.push({
                  where: where,
                  key: event.key,
                  target: event.target && event.target.id || '',
                  bubbles: event.bubbles
                });
              });
            });
        "#);
        click(&mut doc, "#menu-toggle");
        doc.eval("document.querySelector('#menu-popover button').focus()");
        doc.inner_mut().resolve(0.0);

        let before = state(&mut doc, "({
            expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
            focused:document.activeElement&&document.activeElement.getAttribute('data-command'),
            listeners:window.__calyraKeyTrace.length
        })");

        let key = calyra_escape_key();
        match route {
            "ui" => doc.handle_ui_event(UiEvent::KeyDown(key)),
            "dom-focused" => {
                let id = query(&doc, "#menu-popover button");
                doc.dispatch_dom_event(DomEvent::new(id, DomEventData::KeyDown(key)));
            }
            "dom-body" => {
                let id = query(&doc, "body");
                doc.dispatch_dom_event(DomEvent::new(id, DomEventData::KeyDown(key)));
            }
            "dom-document" => {
                let id = doc.inner().root_node().id;
                doc.dispatch_dom_event(DomEvent::new(id, DomEventData::KeyDown(key)));
            }
            _ => unreachable!(),
        }
        doc.inner_mut().resolve(0.0);
        let after = state(&mut doc, "({
            expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
            hidden:document.getElementById('menu-popover').hidden,
            focused:document.activeElement&&document.activeElement.id,
            trace:window.__calyraKeyTrace
        })");
        results.push(format!(
            "{{\"route\":\"{route}\",\"before\":{before},\"after\":{after}}}"
        ));
        all_errors.extend(doc.take_js_errors());
    }
    let observations = format!("{{\"routes\":[{}]}}", results.join(","));
    save("keyboard-routing", &observations, &all_errors);
    assert!(all_errors.is_empty(), "instrumented keyboard routing must not throw JS exceptions");
}
