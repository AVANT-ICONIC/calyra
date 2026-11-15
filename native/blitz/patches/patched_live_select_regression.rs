
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
            .text_input_data().unwrap().editor.raw_text().to_string()
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
