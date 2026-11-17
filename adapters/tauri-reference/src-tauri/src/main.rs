#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(all(feature = "stage-a-js-probe", feature = "stage-a-process-pids"))]
compile_error!("Stage A probe features are mutually exclusive");

#[cfg(feature = "stage-a-js-probe")]
mod stage_a_js_probe;

#[cfg(feature = "stage-a-process-pids")]
mod stage_a_process_pids;

fn main() {
    // Both diagnostic entry points are opt-in and absent from the normal app.
    // They must never become a privileged frontend IPC API.
    #[cfg(feature = "stage-a-js-probe")]
    {
        stage_a_js_probe::run();
    }

    #[cfg(feature = "stage-a-process-pids")]
    {
        stage_a_process_pids::run();
    }

    #[cfg(not(any(feature = "stage-a-js-probe", feature = "stage-a-process-pids")))]
    {
        // Real OS WebView; original canonical CALYRA HTML/CSS/JS unchanged.
        // No privileged Rust commands or replacement frontend bundle.
        tauri::Builder::default()
            .run(tauri::generate_context!())
            .expect("CALYRA Tauri system-WebView reference failed to launch");
    }
}
