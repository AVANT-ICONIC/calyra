

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


/// CALYRA's exact original menu handler must retain the focus it sets within
/// the button's click handler, not merely after a delayed test intervention.
#[test]
fn calyra_unmodified_menu_click_retains_command_focus() {
    let mut doc = document("interaction");
    let command = query(&doc, "#menu-popover button");
    click(&mut doc, "#menu-toggle");
    let after_open = state(&mut doc, "({
        expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
        hidden:document.getElementById('menu-popover').hidden,
        focused:document.activeElement&&document.activeElement.getAttribute('data-command')
    })");
    let native_command_focused = doc.inner().get_focussed_node_id() == Some(command);
    doc.handle_ui_event(UiEvent::KeyDown(calyra_escape_key()));
    doc.inner_mut().resolve(0.0);
    let after_escape = state(&mut doc, "({
        expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
        hidden:document.getElementById('menu-popover').hidden,
        focused:document.activeElement&&document.activeElement.id
    })");
    let errors = doc.take_js_errors();
    save("focus-patched", &format!(
        "{{\"after_open\":{after_open},\"native_command_focused\":{native_command_focused},\"after_escape\":{after_escape}}}"
    ), &errors);
    assert!(errors.is_empty(), "original menu script threw an exception: {errors:?}");
    assert!(native_command_focused, "Blitz cleared the focus set synchronously by original JS");
    assert!(after_open.contains(r#""focused":"inspect""#), "command not immediately focused: {after_open}");
    assert!(after_escape.contains(r#""expanded":"false""#), "Escape did not close menu: {after_escape}");
    assert!(after_escape.contains(r#""hidden":true"#), "menu still visible: {after_escape}");
    assert!(after_escape.contains(r#""focused":"menu-toggle""#), "focus not restored to toggle: {after_escape}");
}

/// Preserve focus set synchronously by CALYRA's other original button handler.
/// This prevents a menu-specific fix from hiding a generic plain-button bug.
#[test]
fn calyra_unmodified_focus_destination_click_keeps_target_focused() {
    let mut doc = document("interaction");
    let dest = query(&doc, "#destination");
    click(&mut doc, "#focus-target");
    let focused = doc.inner().get_focussed_node_id() == Some(dest);
    let result = state(&mut doc, "({
        focused:document.activeElement&&document.activeElement.id,
        status:document.getElementById('interaction-status').value
    })");
    let errors = doc.take_js_errors();
    save("destination-focus-patched", &format!(
        "{{\"native_destination_focused\":{focused},\"after_click\":{result}}}"
    ), &errors);
    assert!(errors.is_empty());
    assert!(focused, "plain button click default action cleared JS-defined focus: {result}");
    assert!(result.contains(r#""focused":"destination""#), "browser-visible activeElement did not match native focus: {result}");
}
