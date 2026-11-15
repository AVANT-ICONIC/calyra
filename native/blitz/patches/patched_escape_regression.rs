

/// Only executed by the CALYRA patched-event-chain comparison workflow.
/// The original application JS is unchanged; the *Blitz engine* is explicitly
/// modified inside a disposable upstream checkout and its patch is recorded.
#[test]
fn calyra_patched_document_escape_regression() {
    let mut doc = document("interaction");
    // Passive trace attached to the same document target as reference.js.
    doc.eval(r#"
        window.__calyraPatchKeys = [];
        document.addEventListener('keydown', e =>
            window.__calyraPatchKeys.push({key:e.key,target:e.target&&e.target.id||''})
        );
    "#);
    click(&mut doc, "#menu-toggle");
    doc.eval("document.querySelector('#menu-popover button').focus()");
    doc.inner_mut().resolve(0.0);
    let before = state(&mut doc, "({
        expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
        focused:document.activeElement&&document.activeElement.getAttribute('data-command')
    })");

    doc.handle_ui_event(UiEvent::KeyDown(calyra_escape_key()));
    doc.inner_mut().resolve(0.0);
    let after = state(&mut doc, "({
        expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
        hidden:document.getElementById('menu-popover').hidden,
        trace:window.__calyraPatchKeys
    })");
    let errors = doc.take_js_errors();
    let observations = format!("{{\"before\":{before},\"after\":{after}}}");
    save("escape-patched", &observations, &errors);
    assert!(errors.is_empty(), "JS errors in patched document-level keyboard path");
    assert!(before.contains(r#""expanded":"true""#), "menu did not open: {before}");
    assert!(after.contains(r#""expanded":"false""#), "Escape did not reach CALYRA's original handler: {after}");
    assert!(after.contains(r#""hidden":true"#), "menu did not close: {after}");
    assert!(after.contains(r#""key":"Escape""#), "document trace received no Escape event: {after}");
}
