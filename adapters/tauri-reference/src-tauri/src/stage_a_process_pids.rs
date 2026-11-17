//! Isolated Stage A macOS WKWebView-owned helper PID evidence.
//! Opt-in ONLY: no JavaScript or canonical CALYRA fixture modifications.
//! Uses dynamically messaged PRIVATE WebKit selectors for research diagnostics;
//! never link to, expose, or ship these APIs in the normal production app.
//! Missing/private selectors fail closed as null in the original JSON.

#[cfg(not(target_os = "macos"))]
compile_error!("stage-a-process-pids is a macOS-only research feature");

use std::{env, ffi::{c_char, c_void}, fs, path::PathBuf};
use tauri::webview::PageLoadEvent;

#[link(name = "objc", kind = "dylib")]
unsafe extern "C" {
    fn sel_registerName(name: *const c_char) -> *mut c_void;
    fn object_getClass(obj: *mut c_void) -> *mut c_void;
    fn class_respondsToSelector(class: *mut c_void, sel: *mut c_void) -> bool;
    fn objc_msgSend();
}

unsafe fn selector(bytes: &'static [u8]) -> *mut c_void {
    debug_assert!(bytes.last() == Some(&0));
    sel_registerName(bytes.as_ptr().cast())
}

unsafe fn responds(obj: *mut c_void, sel: *mut c_void) -> bool {
    !obj.is_null()
        && !sel.is_null()
        && class_respondsToSelector(object_getClass(obj), sel)
}

unsafe fn get_object(obj: *mut c_void, method: &'static [u8]) -> Option<*mut c_void> {
    let sel = selector(method);
    if !responds(obj, sel) {
        return None;
    }
    let invoke: unsafe extern "C" fn(*mut c_void, *mut c_void) -> *mut c_void =
        std::mem::transmute(objc_msgSend as *const ());
    let result = invoke(obj, sel);
    (!result.is_null()).then_some(result)
}

unsafe fn get_pid(obj: *mut c_void, method: &'static [u8]) -> Option<i32> {
    let sel = selector(method);
    if !responds(obj, sel) {
        return None;
    }
    let invoke: unsafe extern "C" fn(*mut c_void, *mut c_void) -> i32 =
        std::mem::transmute(objc_msgSend as *const ());
    let result = invoke(obj, sel);
    (result > 0).then_some(result)
}

fn json_pid(value: Option<i32>) -> String {
    value.map_or_else(|| "null".to_owned(), |pid| pid.to_string())
}

pub fn run() {
    let output = PathBuf::from(
        env::var_os("CALYRA_STAGE_A_PID_DIR")
            .expect("stage-a-process-pids requires CALYRA_STAGE_A_PID_DIR"),
    );
    fs::create_dir_all(&output).expect("create process PID evidence directory");
    tauri::Builder::default()
        .on_page_load(move |webview, payload| {
            if !matches!(payload.event(), PageLoadEvent::Finished)
                || webview.label() != "main"
            {
                return;
            }
            let file = output.join("actual-wkwebview-process-pids.json");
            if let Err(error) = webview.with_webview(move |platform| {
                unsafe {
                    let view = platform.inner().cast::<c_void>();
                    let web_pid = get_pid(view, b"_webProcessIdentifier\0");
                    let gpu_pid = get_pid(view, b"_gpuProcessIdentifier\0");
                    let store = get_object(view, b"configuration\0")
                        .and_then(|configuration| get_object(configuration, b"websiteDataStore\0"));
                    let network_pid = store.and_then(|data_store| {
                        get_pid(data_store, b"_networkProcessIdentifier\0")
                    });
                    let json = format!(
                        "{{\n  \"schema\": \"calyra.macos-native-wkwebview-pids.v1\",\n  \
                         \"tauri_ui_process_pid\": {},\n  \
                         \"webkit_webcontent_pid\": {},\n  \
                         \"webkit_network_pid\": {},\n  \
                         \"webkit_gpu_pid\": {},\n  \
                         \"source\": \"live Tauri WKWebView Objective-C runtime\",\n  \
                         \"private_diagnostic_only\": true,\n  \
                         \"canonical_html_css_js_unmodified\": true\n}}\n",
                        std::process::id(),
                        json_pid(web_pid),
                        json_pid(network_pid),
                        json_pid(gpu_pid),
                    );
                    if let Err(error) = fs::write(&file, json) {
                        eprintln!("CALYRA_NATIVE_PID_ERROR writing {}: {error}", file.display());
                    } else {
                        eprintln!("CALYRA_NATIVE_PID_CALLBACK: {}", file.display());
                    }
                }
            }) {
                eprintln!("CALYRA_NATIVE_PID_ERROR with_webview: {error}");
            }
        })
        .run(tauri::generate_context!())
        .expect("CALYRA native WKWebView process PID experiment could not launch");
}
