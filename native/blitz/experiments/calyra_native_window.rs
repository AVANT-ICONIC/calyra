//! CALYRA's opt-in Blitz 0.3.0-beta.4 native-window feasibility probe.
//!
//! Copy this file ONLY to an untracked examples/calyra_native_window.rs in
//! an exact pinned upstream Git checkout. Neither original engine files nor
//! authored CALYRA HTML/CSS/JS are patched. prepare_static.py performs the
//! declared active-state DOM adaptation and omits browser JavaScript.
//!
//! launch_static_html uses Blitz's upstream winit native window, BlitzShell
//! event loop and VelloWindowRenderer. Not a GPU/input/a11y parity claim.
use std::{env, fs, path::PathBuf};

fn main() {
    let path: PathBuf = env::args_os()
        .nth(1)
        .expect("usage: calyra_native_window <absolute static HTML snapshot>")
        .into();
    assert!(path.is_absolute(), "must supply an explicit absolute fixture path");
    assert!(path.is_file(), "static fixture missing");
    let html = fs::read_to_string(&path).expect("cannot read generated fixture");
    assert!(
        html.contains("data-calyra-original-css=\"true\""),
        "expected original CSS-inlined CALYRA snapshot"
    );
    assert!(
        html.contains("No JavaScript execution in this static Blitz HTML probe"),
        "the non-JavaScript-adapted input was not declared"
    );
    eprintln!("CALYRA_BLITZ_NATIVE_WINDOW_START fixture={}", path.display());
    blitz::launch_static_html(&html);
}
