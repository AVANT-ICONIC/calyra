

/// Native paint-buffer experiment for <select>. This is not a dropdown.
#[test]
fn calyra_select_selected_label_has_real_parley_layout() {
    let mut doc = document("controls");
    doc.inner_mut().resolve(0.0);
    let id = query(&doc, "#priority");
    let (native_label, text_line_exists) = {
        let inner = doc.inner();
        let node = inner.get_node(id).expect("select node missing");
        let text_input = node.element_data()
            .and_then(|el| el.text_input_data())
            .expect("no native Parley text layout attached to select");
        (
            text_input.editor.raw_text().to_string(),
            text_input.editor.try_layout()
                .is_some_and(|layout| layout.lines().next().is_some()),
        )
    };
    let value = state(&mut doc, "({value:document.getElementById('priority').value})");
    let js_errors = doc.take_js_errors();
    let result = format!(
       "{{\"parley_label\":{:?},\"parley_line\":{text_line_exists},\"js_value\":{value}}}",
       native_label,
    );
    save("select-label", &result, &js_errors);
    assert!(js_errors.is_empty());
    assert_eq!(native_label, "Balanced");
    assert!(text_line_exists, "no Parley text line for selected label");
    assert!(value.contains(r#""value":"balanced""#), "JS value diverged: {value}");

    // Focusing a select must NOT make its paint-only text buffer editable.
    doc.eval("document.getElementById('priority').focus()");
    doc.handle_ui_event(UiEvent::KeyDown(BlitzKeyEvent {
        key: Key::Character("x".into()),
        code: Code::KeyX,
        modifiers: Modifiers::empty(),
        location: Location::Standard,
        is_auto_repeating: false,
        is_composing: false,
        state: KeyState::Pressed,
        text: Some("x".into()),
    }));
    let after = doc.inner();
    let raw = after.get_node(id).unwrap().element_data().unwrap()
        .text_input_data().unwrap().editor.raw_text().to_string();
    assert_eq!(raw, "Balanced", "select's native paint buffer was modified by typing");
}
