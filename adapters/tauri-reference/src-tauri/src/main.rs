#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    // Intentionally bare: Tauri runs a real OS WebView (WKWebView on macOS).
    // No privileged Rust commands or altered copies of canonical CALYRA assets.
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("CALYRA Tauri system-WebView reference failed to launch");
}
