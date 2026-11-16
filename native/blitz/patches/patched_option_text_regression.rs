
// CALYRA Stage A: direct selected-option text mutations must update the
// noneditable native Parley label without changing selectedness or dispatching
// programmatic input/change events. This is NOT general DOM mutation coverage.
#[test]
fn calyra_selected_option_text_mutation_refreshes_native_label() {
    let mut doc = document("controls");
    let select_id = query(&doc, "#priority");
    let option_id = query(&doc, "#priority option");
    doc.eval("window.__calyraOptionTextEvents=[]; const s=document.getElementById('priority'); \
        ['input','change'].forEach(type=>s.addEventListener(type,e=>window.__calyraOptionTextEvents.push(e.type)));");

    // Explicit value attr remains 'balanced'; only the visible label changes.
    doc.eval("document.querySelector('#priority option').textContent='Balanced updated'");
    {
        let inner = doc.inner();
        let option = inner.get_node(option_id).unwrap();
        assert_eq!(option.text_content(), "Balanced updated");
        let el = inner.get_node(select_id).unwrap().element_data().unwrap();
        let data = el.select_data().expect("native SelectData missing");
        assert_eq!(data.selected_option, Some(option_id));
        assert_eq!(data.label, "Balanced updated", "label must refresh synchronously");
        assert!(el.text_input_data().is_none());
        assert!(data.layout.lines().next().is_some(), "label must remain shaped by Parley");
    }
    doc.inner_mut().resolve(0.0);
    assert_eq!(query(&doc, "#priority"), select_id);

    // Altering another option must not overwrite the selected label.
    doc.eval("document.querySelectorAll('#priority option')[1].textContent='Not selected'");
    {
        let inner = doc.inner();
        let data = inner.get_node(select_id).unwrap().element_data().unwrap().select_data().unwrap();
        assert_eq!(data.label, "Balanced updated");
    }

    // Mutate the selected option's direct Text node via Node.nodeValue.
    doc.eval("document.querySelector('#priority option').firstChild.nodeValue='Balanced live'");
    {
        let inner = doc.inner();
        let data = inner.get_node(select_id).unwrap().element_data().unwrap().select_data().unwrap();
        assert_eq!(data.selected_option, Some(option_id));
        assert_eq!(data.label, "Balanced live");
    }
    doc.inner_mut().resolve(0.0);
    let json = state(&mut doc,
        "({value:document.getElementById('priority').value, \
           index:document.getElementById('priority').selectedIndex, \
           selected:document.querySelector('#priority option').selected, \
           text:document.querySelector('#priority option').textContent, \
           events:window.__calyraOptionTextEvents})"
    );
    assert_eq!(json, r#"{"value":"balanced","index":0,"selected":true,"text":"Balanced live","events":[]}"#);
    let errors = doc.take_js_errors();
    save("option-text", &format!("{{\"same_node\":true,\"state\":{json},\"native_label\":\"Balanced live\"}}"), &errors);
    assert!(errors.is_empty(), "JS errors during text mutation: {errors:?}");
}
