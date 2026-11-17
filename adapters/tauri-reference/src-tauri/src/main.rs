#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(feature = "stage-a-js-probe")]
mod stage_a_js_probe;

fn main() {
    // Opt-in research probe, compiled ONLY with --features stage-a-js-probe.
    // The ordinary reference .app has no JS eval callbacks or added bridge.
    #[cfg(feature = "stage-a-js-probe")]
    {
        stage_a_js_probe::run();
    }

    #[cfg(not(feature = "stage-a-js-probe"))]
    {
        // Real OS WebView; original canonical CALYRA HTML/CSS/JS unchanged.
        // No privileged Rust commands or replacement frontend bundle.
        tauri::Builder::default()
            .run(tauri::generate_context!())
            .expect("CALYRA Tauri system-WebView reference failed to launch");
    }
}
