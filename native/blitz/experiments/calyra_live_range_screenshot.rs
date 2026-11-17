//! CALYRA: two genuine native Vello-CPU frames from ONE live Blitz/Boa
//! ScriptDocument with a real DOM RangeData 64 -> 18 transition.
//! Authored original CSS/JS/HTML are read byte-exact; only delivery inlined.
//! No trusted OS pointer/keyboard events, macOS GPU or full browser parity.
use anyrender::{AntiAliasing, PaintScene as _, render_to_buffer};
use anyrender_vello_cpu::VelloCpuImageRenderer;
use blitz_dom::{Document, DocumentConfig, NodeId, util::Color};
use blitz_paint::paint_scene;
use blitz_traits::shell::{ColorScheme, Viewport};
use blitz_vibey_script::ScriptDocument;
use peniko::{Fill, kurbo::Rect};
use std::{env, fs, fs::File, path::Path};

const WIDTH:u32=1060;
const HEIGHT:u32=800;

fn canonical_source() -> String {
    let html=fs::read_to_string(env::var("CALYRA_CANONICAL_HTML").expect("HTML env")).expect("HTML");
    let css=fs::read_to_string(env::var("CALYRA_CANONICAL_CSS").expect("CSS env")).expect("CSS");
    let js=fs::read_to_string(env::var("CALYRA_CANONICAL_JS").expect("JS env")).expect("JS");
    let css_marker=r#"<link rel="stylesheet" href="./reference.css">"#;
    let js_marker=r#"<script src="./reference.js" defer></script>"#;
    assert_eq!(html.matches(css_marker).count(),1);
    assert_eq!(html.matches(js_marker).count(),1);
    assert!(!css.contains("</style>"));
    assert!(!js.contains("</script>"));
    html.replace(css_marker,&format!("<style>\n{css}\n</style>"))
        .replace(js_marker,&format!(
            "<script>window.__calyraFixtureQuery='?fixture=controls&motion=off';</script><script>\n{js}\n</script>"
        ))
}

fn current(doc:&ScriptDocument,id:NodeId)->(f64,f64,f64) {
    let inner=doc.inner();
    let node=inner.get_node(id).expect("same range DOM node exists");
    assert!(node.element_data().unwrap().text_input_data().is_none());
    let range=node.element_data().unwrap().range_data()
        .expect("native nontext RangeData missing");
    (range.value,range.default_value,range.progress())
}

fn write_png(path:&Path,buffer:&[u8]) {
    let file=File::create(path).expect("PNG output");
    let mut encoder=png::Encoder::new(file,WIDTH,HEIGHT);
    encoder.set_color(png::ColorType::Rgba);
    encoder.set_depth(png::BitDepth::Eight);
    let mut writer=encoder.write_header().expect("PNG header");
    writer.write_image_data(buffer).expect("PNG RGBA");
    writer.finish().expect("finish PNG");
}

fn capture(doc:&mut ScriptDocument,path:&Path) {
    let buffer=render_to_buffer::<VelloCpuImageRenderer,_>(
        |scene| {
            scene.fill(
                Fill::NonZero, Default::default(), Color::WHITE, Default::default(),
                &Rect::new(0.0,0.0,WIDTH as f64,HEIGHT as f64),
                AntiAliasing::Enabled,
            );
            paint_scene(scene,&mut *doc.inner_mut(),1.0,WIDTH,HEIGHT,0,0);
        },WIDTH,HEIGHT,
    );
    write_png(path,&buffer);
}

fn main() {
    let out=env::var("CALYRA_LIVE_RANGE_OUT").expect("output directory");
    let out=Path::new(&out);
    fs::create_dir_all(out).unwrap();
    let html=canonical_source();
    let mut doc=ScriptDocument::from_html(&html,DocumentConfig{
        viewport:Some(Viewport::new(WIDTH,HEIGHT,1.0,ColorScheme::Dark)),
        ..Default::default()
    }).without_timer_thread();
    doc.execute_scripts();
    doc.inner_mut().resolve(0.0);
    let id=doc.inner().query_selector("#intensity").unwrap().expect("native range");
    assert_eq!(current(&doc,id),(64.0,64.0,0.64));
    capture(&mut doc,&out.join("range-before-64.png"));

    // Exactly the SAME live ScriptDocument and SAME DOM node id.
    // A JS property write updates RangeData (not the 'value' HTML attribute).
    // The original page script receives no synthetic input/change user event.
    doc.eval("document.getElementById('intensity').value='18'");
    doc.inner_mut().resolve(0.0);
    assert_eq!(doc.inner().query_selector("#intensity").unwrap(),Some(id));
    assert_eq!(current(&doc,id),(18.0,64.0,0.18));
    assert_eq!(doc.inner().get_node(id).unwrap()
        .attr(blitz_dom::local_name!("value")),Some("64"));
    capture(&mut doc,&out.join("range-after-18.png"));

    let errors=doc.take_js_errors();
    assert!(errors.is_empty(),"native script errors: {errors:?}");
    println!("CALYRA_RANGE_SAME_DOCUMENT=true");
    println!("CALYRA_RANGE_INITIAL_VALUE=64");
    println!("CALYRA_RANGE_FINAL_VALUE=18");
    println!("CALYRA_RANGE_DEFAULT_VALUE_UNCHANGED=64");
    println!("CALYRA_RANGE_RENDERER=Blitz_Vello_CPU");
    println!("CALYRA_RANGE_NATIVE_OS_INPUT_TESTED=false");
}
