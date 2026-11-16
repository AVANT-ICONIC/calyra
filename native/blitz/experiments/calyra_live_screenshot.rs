//! CALYRA: genuine Vello-CPU screenshots from a single live Blitz/Boa document.
//! This is a source-pinned Stage A experiment. The author CSS and JS strings
//! are inlined byte-exactly; only fixture query delivery is adapted.
//! No browser engine, OS input, GPU, popup or production select widget.
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

fn content() -> String {
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

fn selected_label(doc:&ScriptDocument,id:NodeId)->String {
    doc.inner().get_node(id).unwrap().element_data().unwrap()
        .text_input_data().unwrap().editor.raw_text().to_owned()
}

fn write_png(path:&Path, buffer:&[u8]) {
    let file=File::create(path).expect("PNG output");
    let mut encoder=png::Encoder::new(file,WIDTH,HEIGHT);
    encoder.set_color(png::ColorType::Rgba);
    encoder.set_depth(png::BitDepth::Eight);
    let mut writer=encoder.write_header().expect("PNG header");
    writer.write_image_data(buffer).expect("PNG RGBA");
    writer.finish().expect("finish PNG");
}

fn capture(doc:&mut ScriptDocument, path:&Path) {
    let buffer=render_to_buffer::<VelloCpuImageRenderer,_>(
        |scene| {
            scene.fill(
                Fill::NonZero,
                Default::default(),
                Color::WHITE,
                Default::default(),
                &Rect::new(0.0,0.0,WIDTH as f64,HEIGHT as f64),
                AntiAliasing::Enabled,
            );
            paint_scene(scene,doc.inner_mut(),1.0,WIDTH,HEIGHT,0,0);
        },
        WIDTH,
        HEIGHT,
    );
    write_png(path,&buffer);
}

fn main() {
    let out=env::var("CALYRA_LIVE_PAINT_OUT").expect("output dir");
    let out=Path::new(&out);
    fs::create_dir_all(out).unwrap();
    let html=content();
    let mut doc=ScriptDocument::from_html(&html,DocumentConfig{
        viewport:Some(Viewport::new(WIDTH,HEIGHT,1.0,ColorScheme::Dark)),
        ..Default::default()
    }).without_timer_thread();
    doc.execute_scripts();
    doc.inner_mut().resolve(0.0);
    let id=doc.inner().query_selector("#priority").unwrap().expect("priority");
    let before=selected_label(&doc,id);
    assert_eq!(before,"Balanced");
    capture(&mut doc,&out.join("live-before-balanced.png"));

    // One JS property write. No re-parse, re-create, or new Document.
    doc.eval("document.getElementById('priority').value='quality'");
    doc.inner_mut().resolve(0.0);
    assert_eq!(doc.inner().query_selector("#priority").unwrap(),Some(id));
    let after=selected_label(&doc,id);
    assert_eq!(after,"Visual fidelity");
    capture(&mut doc,&out.join("live-after-quality.png"));

    let errs=doc.take_js_errors();
    assert!(errs.is_empty(),"Blitz JS errors: {errs:?}");
    println!("CALYRA_LIVE_SAME_DOCUMENT=true");
    println!("CALYRA_LIVE_FROM={before}");
    println!("CALYRA_LIVE_TO={after}");
    println!("CALYRA_LIVE_RENDER_BACKEND=Vello_CPU");
}
