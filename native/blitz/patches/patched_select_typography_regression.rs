
// CALYRA Stage A: test computed CSS typography invalidation on an unchanged
// selected <option> and the same noneditable native SelectData node.
// Physical keyboard, popup and GPU rendering are NOT tested here.
#[test]
fn calyra_select_typography_restyles_without_selection_or_text_mutation() {
    let mut doc = document("controls");
    let select_id = query(&doc, "#priority");
    let option_id = query(&doc, "#priority option");
    doc.eval("window.__calyraTypographyEvents=[]; const s=document.getElementById('priority'); \
        ['input','change'].forEach(type=>s.addEventListener(type,e=>window.__calyraTypographyEvents.push(e.type)));");

    let (initial_height, initial_fingerprint) = {
        let inner = doc.inner();
        let el = inner.get_node(select_id).unwrap().element_data().unwrap();
        assert!(el.text_input_data().is_none());
        let data = el.select_data().expect("native read-only SelectData missing");
        assert_eq!(data.selected_option, Some(option_id));
        assert_eq!(data.label, "Balanced");
        assert!(!data.typography_fingerprint.is_empty());
        (data.layout.height(), data.typography_fingerprint.clone())
    };
    assert!(initial_height > 0.0);

    // This is a genuine CSSOM mutation, not an option value or text edit.
    doc.eval("document.getElementById('priority').style.setProperty('font-size','32px')");
    doc.inner_mut().resolve(0.0);
    let (large_height, large_fingerprint) = {
        let inner = doc.inner();
        let el = inner.get_node(select_id).unwrap().element_data().unwrap();
        let data = el.select_data().unwrap();
        assert_eq!(data.selected_option, Some(option_id));
        assert_eq!(data.label, "Balanced");
        assert!(el.text_input_data().is_none());
        (data.layout.height(), data.typography_fingerprint.clone())
    };
    assert_ne!(large_fingerprint, initial_fingerprint, "computed typography signature did not change");
    assert!(large_height > initial_height * 1.2,
        "style-only font-size must re-shape glyph metrics: initial={initial_height}, large={large_height}");
    assert_eq!(query(&doc, "#priority"), select_id);

    // A paint-only property must not invalidate generated glyph shaping.
    doc.eval("document.getElementById('priority').style.setProperty('background-color','rgb(20,30,40)')");
    doc.inner_mut().resolve(0.0);
    {
        let inner = doc.inner();
        let data = inner.get_node(select_id).unwrap().element_data().unwrap().select_data().unwrap();
        assert_eq!(data.typography_fingerprint, large_fingerprint);
        assert_eq!(data.layout.height(), large_height);
    }

    // A second typography change must re-shape again, without touching
    // selectedness, live value, option text or input/change event dispatch.
    doc.eval("document.getElementById('priority').style.setProperty('font-size','18px')");
    doc.inner_mut().resolve(0.0);
    let small_height = {
        let inner = doc.inner();
        let el = inner.get_node(select_id).unwrap().element_data().unwrap();
        let data = el.select_data().unwrap();
        assert_eq!(data.label, "Balanced");
        assert_eq!(data.selected_option, Some(option_id));
        assert_ne!(data.typography_fingerprint, large_fingerprint);
        data.layout.height()
    };
    assert!(small_height < large_height,
        "font shrink must reduce native shaped height: small={small_height}, large={large_height}");

    let state_json = state(&mut doc,
        "({value:document.getElementById('priority').value, \
           index:document.getElementById('priority').selectedIndex, \
           text:document.querySelector('#priority option').textContent, \
           selected:document.querySelector('#priority option').selected, \
           events:window.__calyraTypographyEvents})"
    );
    assert_eq!(state_json,
        r#"{"value":"balanced","index":0,"text":"Balanced","selected":true,"events":[]}"#);
    let errors = doc.take_js_errors();
    let observation = format!(
        "{{\"same_node\":true,\"state\":{},\"height_before\":{},\"height_large\":{},\"height_small\":{},\"computed_typography_changed\":true}}",
        state_json, initial_height, large_height, small_height
    );
    save("select-typography", &observation, &errors);
    assert!(errors.is_empty(), "JS errors during CSS style changes: {errors:?}");
}
