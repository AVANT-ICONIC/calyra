
// CALYRA Stage A: a restricted, attribute-independent current-selection model.
// Real Chromium baseline in harness/chromium_select_contract.py.
// No popup, OS input or fake input/change events for JS property assignments.
fn calyra_live_select_snapshot(doc: &mut ScriptDocument, name: &str, id: NodeId) -> String {
    let js = state(doc, "(() => {
        const s=document.getElementById('priority');
        const opts=Array.from(document.querySelectorAll('#priority option'));
        return {
          index:s.selectedIndex, value:s.value,
          selected:opts.map(o=>o.selected),
          defaultSelected:opts.map(o=>o.defaultSelected),
          events:window.__calyraSelectEvents
        };
    })()");
    let label = {
        let inner=doc.inner();
        inner.get_node(id).unwrap().element_data().unwrap()
            .select_data().unwrap().label.clone()
    };
    format!("{{\"name\":{:?},\"js\":{js},\"native_label\":{:?}}}",name,label)
}

#[test]
fn calyra_live_selection_state_and_reactive_native_label() {
    let mut doc=document("controls");
    let id=query(&doc,"#priority");
    doc.eval("window.__calyraSelectEvents=[]; \
        const s=document.getElementById('priority'); \
        ['input','change'].forEach(type=>s.addEventListener(type,e=>\
            window.__calyraSelectEvents.push({type:e.type,value:s.value,index:s.selectedIndex})));");
    let mut snapshots=Vec::new();
    snapshots.push(calyra_live_select_snapshot(&mut doc,"initial",id));

    let mutations=[
        ("value=quality","document.getElementById('priority').value='quality'"),
        ("selectedIndex=2","document.getElementById('priority').selectedIndex=2"),
        ("option0.selected=true","document.querySelectorAll('#priority option')[0].selected=true"),
        ("value=nonexistent","document.getElementById('priority').value='nonexistent'"),
        ("selectedIndex=1","document.getElementById('priority').selectedIndex=1"),
        ("option2.defaultSelected=true","document.querySelectorAll('#priority option')[2].defaultSelected=true"),
    ];
    for (name,script) in mutations {
        doc.eval(script);
        doc.inner_mut().resolve(0.0);
        assert_eq!(query(&doc,"#priority"),id,"native DOM select identity changed");
        snapshots.push(calyra_live_select_snapshot(&mut doc,name,id));
    }
    let errors=doc.take_js_errors();
    let result=format!("{{\"same_node\":true,\"snapshots\":[{}]}}",snapshots.join(","));
    save("select-live",&result,&errors);
    assert!(errors.is_empty(),"JS errors in live select: {errors:?}");
    let expected=[
        ("initial",0,"balanced","Balanced"),
        ("value=quality",1,"quality","Visual fidelity"),
        ("selectedIndex=2",2,"performance","Performance"),
        ("option0.selected=true",0,"balanced","Balanced"),
        ("value=nonexistent",-1,"",""),
        ("selectedIndex=1",1,"quality","Visual fidelity"),
        ("option2.defaultSelected=true",1,"quality","Visual fidelity"),
    ];
    assert_eq!(snapshots.len(),expected.len());
    for (index,(name,selected_index,value,label)) in expected.iter().enumerate() {
        let snap=&snapshots[index];
        assert!(snap.contains(&format!(r#""name":"{name}""#)), "{snap}");
        assert!(snap.contains(&format!(r#""index":{selected_index}"#)), "{snap}");
        assert!(snap.contains(&format!(r#""value":"{value}""#)), "{snap}");
        assert!(snap.contains(&format!(r#""native_label":"{label}""#)), "{snap}");
        assert!(snap.contains(r#""events":[]"#),"programmatic change emitted input/change: {snap}");
    }
    assert!(snapshots.last().unwrap().contains(r#""defaultSelected":[false,false,true]"#));
}


#[test]
fn calyra_select_has_no_editor_and_rejects_keyboard_ime_paste_edits() {
    use blitz_traits::events::BlitzImeEvent;
    let mut doc = document("controls");
    let id = query(&doc, "#priority");
    {
        let inner = doc.inner();
        let node = inner.get_node(id).unwrap();
        let el = node.element_data().unwrap();
        assert!(el.text_input_data().is_none(), "select illegally owns a text editor");
        let select = el.select_data().expect("real native SelectData missing");
        assert_eq!(select.label, "Balanced");
        assert_eq!(select.selected_option, Some(query(&doc, "#priority option")));
        assert!(select.layout.lines().next().is_some(), "read-only label needs shaped glyphs");
    }

    doc.inner_mut().set_focus_to(id);
    doc.handle_ui_event(UiEvent::KeyDown(BlitzKeyEvent {
        key: Key::Character("x".into()), code: Code::KeyX,
        modifiers: Modifiers::empty(), location: Location::Standard,
        is_auto_repeating: false, is_composing: false,
        state: KeyState::Pressed, text: Some("x".into()),
    }));
    doc.handle_ui_event(UiEvent::Ime(BlitzImeEvent::Commit("IME injection".into())));
    doc.handle_ui_event(UiEvent::Paste("Paste injection".into()));
    doc.inner_mut().resolve(0.0);
    assert_eq!(state(&mut doc, "({value:document.getElementById('priority').value, index:document.getElementById('priority').selectedIndex})"),
        r#"{"value":"balanced","index":0}"#);
    let inner = doc.inner();
    let node = inner.get_node(id).unwrap();
    let el = node.element_data().unwrap();
    let select = el.select_data().unwrap();
    assert_eq!(select.label, "Balanced");
    assert!(el.text_input_data().is_none(), "IME must not create an editor");
}


#[test]
fn calyra_select_idempotent_js_writes_preserve_native_state_without_events() {
    let mut doc = document("controls");
    let id = query(&doc, "#priority");
    doc.eval("window.__calyraIdempotentEvents=[]; 
        const s=document.getElementById('priority'); 
        ['input','change'].forEach(type=>s.addEventListener(type,e=> 
            window.__calyraIdempotentEvents.push(e.type)));");

    // Three independent JS setter paths assign the already-selected option.
    // This is an explicit no-op at the native boundary: no label rebuild/redraw
    // should be requested by these property writes.
    doc.eval("document.getElementById('priority').value='balanced'; 
        document.getElementById('priority').selectedIndex=0; 
        document.querySelector('#priority option').selected=true;");
    doc.inner_mut().resolve(0.0);
    assert_eq!(query(&doc, "#priority"), id);
    assert_eq!(
        state(&mut doc, "({value:document.getElementById('priority').value,index:document.getElementById('priority').selectedIndex,events:window.__calyraIdempotentEvents})"),
        r#"{"value":"balanced","index":0,"events":[]}"#
    );
    {
        let inner = doc.inner();
        let el = inner.get_node(id).unwrap().element_data().unwrap();
        assert_eq!(el.select_data().unwrap().label, "Balanced");
        assert!(el.text_input_data().is_none());
    }

    // Unmatched values intentionally clear the selection. Repeating that
    // assignment remains a no-op and must not resurrect the first option.
    doc.eval("document.getElementById('priority').value='missing'; 
        document.getElementById('priority').value='still-missing'; 
        document.getElementById('priority').selectedIndex=-1;");
    doc.inner_mut().resolve(0.0);
    assert_eq!(
        state(&mut doc, "({value:document.getElementById('priority').value,index:document.getElementById('priority').selectedIndex,events:window.__calyraIdempotentEvents})"),
        r#"{"value":"","index":-1,"events":[]}"#
    );
    let inner = doc.inner();
    let el = inner.get_node(id).unwrap().element_data().unwrap();
    assert_eq!(el.select_data().unwrap().label, "");
    assert!(el.text_input_data().is_none());
    drop(inner);
    assert!(doc.take_js_errors().is_empty());
}
