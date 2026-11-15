

// Stage A control gap: this test intentionally uses the original CALYRA
// controls HTML, CSS and JavaScript. Only the upstream engine is patched.
// It tests select geometry and a minimal default/selected value getter,
// NOT popup interaction, keyboard navigation or full HTMLSelectElement.
#[test]
fn calyra_select_layout_and_default_value_experiment() {
    let mut doc = document("controls");
    doc.inner_mut().resolve(0.0);
    let id = query(&doc, "#priority");
    let (w,h) = {
        let inner = doc.inner();
        let layout = inner.get_node(id).expect("priority select node missing").final_layout();
        (layout.size.width, layout.size.height)
    };
    let before = state(&mut doc, "({
        value:document.getElementById('priority').value,
        options:document.querySelectorAll('#priority option').length
    })");
    click(&mut doc, "#apply");
    let applied = state(&mut doc, "({
        value:document.getElementById('priority').value,
        status:document.getElementById('action-status').value
    })");
    // The selected attribute case tests the narrow opt-in branch separately.
    doc.eval("document.querySelector('#priority option[value=quality]').setAttribute('selected','')");
    let selected = state(&mut doc, "({
        value:document.getElementById('priority').value
    })");
    let errors = doc.take_js_errors();
    let observations = format!(
        "{{\"layout\":{{\"width\":{w},\"height\":{h}}},\"before\":{before},\"after_apply\":{applied},\"explicit_selected\":{selected}}}"
    );
    save("select-patched", &observations, &errors);
    assert!(errors.is_empty(), "JS exception in select control: {errors:?}");
    assert!(w > 1.0 && h > 1.0, "select remains zero-sized: {w}x{h}");
    assert!(before.contains(r#""value":"balanced""#), "default first option not returned: {before}");
    assert!(applied.contains("balanced"), "original apply handler ignored select value: {applied}");
    assert!(selected.contains(r#""value":"quality""#), "explicit selected option not returned: {selected}");
}
