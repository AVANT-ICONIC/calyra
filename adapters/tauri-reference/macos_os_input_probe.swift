// CALYRA Stage A: targeted Quartz mouse + keyboard against OUR Tauri app.
// Requires TCC approval; aborts if the wrong application is frontmost.
// No permission requests, no external app input and no fixture JS injection.
import AppKit
import ApplicationServices
import CoreGraphics
import Foundation

func json(_ dictionary: [String: Any]) {
    let data = try! JSONSerialization.data(
        withJSONObject: dictionary, options: [.prettyPrinted, .sortedKeys]
    )
    print(String(data: data, encoding: .utf8)!)
}

func attribute(_ element: AXUIElement, _ key: String) -> AnyObject? {
    var value: CFTypeRef?
    let status = AXUIElementCopyAttributeValue(element, key as CFString, &value)
    return status == .success ? value as AnyObject? : nil
}

func findInitialName(_ element: AXUIElement, _ depth: Int = 0) -> AXUIElement? {
    guard depth <= 28 else { return nil }
    let role = attribute(element, kAXRoleAttribute) as? String ?? ""
    let value = attribute(element, kAXValueAttribute) as? String ?? ""
    if role == "AXTextField" && value == "Alex Rivera" {
        return element
    }
    let children = attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? []
    for child in children {
        if let found = findInitialName(child, depth + 1) { return found }
    }
    return nil
}

func point(_ element: AXUIElement) -> CGPoint? {
    guard let raw = attribute(element, kAXPositionAttribute) as? AXValue,
          AXValueGetType(raw) == .cgPoint else { return nil }
    var value = CGPoint.zero
    return AXValueGetValue(raw, .cgPoint, &value) ? value : nil
}

func size(_ element: AXUIElement) -> CGSize? {
    guard let raw = attribute(element, kAXSizeAttribute) as? AXValue,
          AXValueGetType(raw) == .cgSize else { return nil }
    var value = CGSize.zero
    return AXValueGetValue(raw, .cgSize, &value) ? value : nil
}

func sendKey(_ virtualKey: CGKeyCode, flags: CGEventFlags = []) {
    guard let down = CGEvent(keyboardEventSource: nil, virtualKey: virtualKey, keyDown: true),
          let up = CGEvent(keyboardEventSource: nil, virtualKey: virtualKey, keyDown: false) else {
        return
    }
    down.flags = flags
    up.flags = flags
    down.post(tap: .cghidEventTap)
    usleep(75_000)
    up.post(tap: .cghidEventTap)
}

func typeUnicode(_ text: String) {
    let units = Array(text.utf16)
    units.withUnsafeBufferPointer { buffer in
        guard let p = buffer.baseAddress,
              let down = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: true),
              let up = CGEvent(keyboardEventSource: nil, virtualKey: 0, keyDown: false) else {
            return
        }
        down.keyboardSetUnicodeString(stringLength: units.count, unicodeString: p)
        up.keyboardSetUnicodeString(stringLength: units.count, unicodeString: p)
        down.post(tap: .cghidEventTap)
        usleep(90_000)
        up.post(tap: .cghidEventTap)
    }
}

guard CommandLine.arguments.count == 2,
      let targetPID = Int32(CommandLine.arguments[1]), targetPID > 0 else {
    fputs("usage: swift macos_os_input_probe.swift <Tauri app pid>\n", stderr)
    exit(64)
}
let permitted = CGPreflightPostEventAccess()
let trusted = AXIsProcessTrusted()
guard permitted && trusted else {
    json([
        "schema": "calyra.macos-tauri-os-input.v1", "pass": false,
        "blocked": "Accessibility or Quartz posting permission denied",
        "post_access": permitted, "accessibility_trusted": trusted,
        "events_posted": false
    ])
    exit(2)
}
guard let application = NSRunningApplication(processIdentifier: targetPID),
      application.executableURL?.lastPathComponent == "calyra-tauri-reference" else {
    fputs("BLOCKED: target PID does not own CALYRA native executable\n", stderr)
    exit(3)
}
let activated = application.activate(options: [.activateAllWindows])
Thread.sleep(forTimeInterval: 0.5)
let frontmost = NSWorkspace.shared.frontmostApplication?.processIdentifier
guard activated && frontmost == targetPID else {
    json([
        "schema": "calyra.macos-tauri-os-input.v1", "pass": false,
        "blocked": "Target application did not become macOS frontmost",
        "activated": activated, "frontmost_pid": frontmost ?? -1,
        "target_pid": targetPID, "events_posted": false
    ])
    exit(4)
}
let root = AXUIElementCreateApplication(targetPID)
AXUIElementSetMessagingTimeout(root, 5)
guard let field = findInitialName(root) else {
    json([
        "schema": "calyra.macos-tauri-os-input.v1", "pass": false,
        "blocked": "Original input was not found in native accessibility tree",
        "target_pid": targetPID, "events_posted": false
    ])
    exit(5)
}
guard let origin = point(field), let dimensions = size(field),
      dimensions.width >= 100, dimensions.height >= 20 else {
    json([
        "schema": "calyra.macos-tauri-os-input.v1", "pass": false,
        "blocked": "Native input lacks usable AXPosition/AXSize",
        "target_pid": targetPID, "events_posted": false
    ])
    exit(6)
}
// Actual macOS screen coordinates from the element's own AX tree.
let destination = CGPoint(x: origin.x + dimensions.width / 2,
                          y: origin.y + dimensions.height / 2)
guard let mouseDown = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown,
                              mouseCursorPosition: destination, mouseButton: .left),
      let mouseUp = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp,
                            mouseCursorPosition: destination, mouseButton: .left) else {
    fputs("BLOCKED: unable to construct Quartz pointer events\n", stderr)
    exit(7)
}
mouseDown.post(tap: .cghidEventTap)
usleep(90_000)
mouseUp.post(tap: .cghidEventTap)
Thread.sleep(forTimeInterval: 0.25)

// Cmd+A, then Unicode keyboard events go through the actual Quartz OS event
// stream to the focused WebKit text input. No DOM .value writes or JS eval.
sendKey(0, flags: [.maskCommand])
Thread.sleep(forTimeInterval: 0.1)
typeUnicode("CalyraNative")
Thread.sleep(forTimeInterval: 0.5)
let final = attribute(field, kAXValueAttribute) as? String ?? ""
let success = final == "CalyraNative"
json([
    "schema": "calyra.macos-tauri-os-input.v1",
    "pass": success,
    "target_pid": targetPID,
    "frontmost_pid": frontmost ?? -1,
    "permission_to_post": permitted,
    "accessibility_trusted": trusted,
    "source": "macOS CoreGraphics CGEventPost / cghidEventTap",
    "mouse_events_posted": 2,
    "command_a_keyboard_events_posted": 2,
    "unicode_keyboard_events_posted": 2,
    "ax_original_text": "Alex Rivera",
    "ax_after_os_input": final,
    "ax_target_position": ["\(origin.x)", "\(origin.y)"],
    "ax_target_size": ["\(dimensions.width)", "\(dimensions.height)"],
    "os_key_event_text_changed_canonical_input": success,
    "manual_physical_keyboard_used": false,
    "ime_or_accessibility_screen_reader_tested": false
])
if !success { exit(8) }
