// CALYRA Stage A: non-interactive macOS event-injection permission preflight.
// Does not request TCC permissions, send events or modify OS settings.
// The result applies to THIS process on THIS GitHub runner, not all Macs.
import ApplicationServices
import CoreGraphics
import Foundation

let post = CGPreflightPostEventAccess()
let accessibility = AXIsProcessTrusted()
let listening = CGPreflightListenEventAccess()
let screen = CGPreflightScreenCaptureAccess()
let result: [String: Any] = [
    "schema": "calyra.macos-real-os-input-preflight.v1",
    "platform": ProcessInfo.processInfo.operatingSystemVersionString,
    "post_event_access": post,
    "accessibility_trusted": accessibility,
    "listen_event_access": listening,
    "screen_capture_access_for_swift_process": screen,
    "os_event_injection_preflight_permitted": post && accessibility,
    "permission_prompt_requested": false,
    "events_posted": false,
    "actual_input_delivered_to_tauri": false,
    "physical_keyboard_or_mouse_tested": false,
    "scope": "GitHub-hosted macOS runner, current Swift process only"
]
let data = try JSONSerialization.data(
    withJSONObject: result, options: [.prettyPrinted, .sortedKeys]
)
print(String(data: data, encoding: .utf8)!)
