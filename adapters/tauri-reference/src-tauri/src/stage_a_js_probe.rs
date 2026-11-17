//! Opt-in, test-only instrumentation for the real macOS Tauri WKWebView.
//! No network, no privileged IPC command, no modifications to canonical files.
//! The normal Tauri binary does not compile or include this module.

use std::{env, fs, path::PathBuf};
use tauri::webview::PageLoadEvent;

pub fn run() {
    // A missing path is an error, never silently write to a user directory.
    let output = PathBuf::from(
        env::var_os("CALYRA_STAGE_A_PROBE_DIR")
            .expect("stage-a-js-probe requires CALYRA_STAGE_A_PROBE_DIR"),
    );
    fs::create_dir_all(&output).expect("create Stage A results directory");

    tauri::Builder::default()
        .on_page_load(move |webview, payload| {
            if !matches!(payload.event(), PageLoadEvent::Finished) {
                return;
            }
            if webview.label() != "main" {
                eprintln!("CALYRA_PROBE_ERROR: unexpected webview label");
                return;
            }

            let url = payload.url().as_str();
            let fixture = if url.contains("fixture=controls") {
                "controls"
            } else if url.contains("fixture=interaction") {
                "interaction"
            } else {
                eprintln!("CALYRA_PROBE_ERROR: unexpected page URL {url}");
                return;
            };
            let result_path = output.join(format!("{fixture}-native-eval.json"));
            let navigation_webview = webview.clone();
            let is_controls = fixture == "controls";

            // No injected HTML or rewritten reference.js: eval is issued only
            // after the actual bundled WebKit page finishes loading.
            let attempt = webview.eval_with_callback(
                include_str!("stage_a_js_probe.js"),
                move |raw_result| {
                    if let Err(error) = fs::write(&result_path, raw_result.as_bytes()) {
                        eprintln!("CALYRA_PROBE_ERROR: write {result_path:?}: {error}");
                        return;
                    }
                    eprintln!("CALYRA_PROBE_CALLBACK: {}", result_path.display());
                    if is_controls {
                        // Navigate the SAME live Tauri window to exercise the
                        // original interaction fixture in its visible state.
                        if let Err(error) = navigation_webview.eval(
                            "window.location.assign('index.html?fixture=interaction&motion=off')",
                        ) {
                            eprintln!("CALYRA_PROBE_ERROR: interaction navigation: {error}");
                        }
                    }
                },
            );
            if let Err(error) = attempt {
                eprintln!("CALYRA_PROBE_ERROR: eval_with_callback: {error}");
            }
        })
        .run(tauri::generate_context!())
        .expect("CALYRA Stage A macOS WKWebView JS probe could not launch");
}
