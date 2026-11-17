// Read-only CoreServices Accessibility census of CALYRA's actual WKWebView.
// Does not post key/mouse events, focus elements, request TCC or edit the app.
// Values are from the local canonical test fixtures, not user documents.
import ApplicationServices
import Foundation

func get(_ element: AXUIElement, _ key: CFString) -> CFTypeRef? {
    var result: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, key, &result) == .success else {
        return nil
    }
    return result
}

func text(_ element: AXUIElement, _ key: CFString) -> String? {
    guard let result = get(element, key) else { return nil }
    if let value = result as? String {
        return String(value.prefix(250))
    }
    if let number = result as? NSNumber {
        return number.stringValue
    }
    return nil
}

let pid: Int32
if CommandLine.arguments.count == 2,
   let parsed = Int32(CommandLine.arguments[1]), parsed > 0 {
    pid = parsed
} else {
    fputs("Usage: calyra_ax_readonly.swift <verified CALYRA app PID>\n", stderr)
    exit(64)
}

let app = AXUIElementCreateApplication(pid)
AXUIElementSetMessagingTimeout(app, 5)
var elements: [[String: Any]] = []
var seen = 0
let maxElements = 450
let maxDepth = 22

func visit(_ node: AXUIElement, _ depth: Int) {
    guard depth <= maxDepth && seen < maxElements else { return }
    seen += 1
    var observation: [String: Any] = [
        "index": seen,
        "depth": depth,
        "role": text(node, kAXRoleAttribute) ?? "unknown",
    ]
    for (key, label) in [
        (kAXTitleAttribute, "title"),
        (kAXDescriptionAttribute, "description"),
        (kAXValueAttribute, "value"),
        (kAXHelpAttribute, "help"),
        (kAXRoleDescriptionAttribute, "role_description"),
    ] {
        if let value = text(node, key) { observation[label] = value }
    }
    if let enabled = get(node, kAXEnabledAttribute) as? NSNumber {
        observation["enabled"] = enabled.boolValue
    }
    elements.append(observation)

    if let children = get(node, kAXChildrenAttribute) as? [AXUIElement] {
        for child in children {
            visit(child, depth + 1)
            if seen >= maxElements { break }
        }
    }
}

let trusted = AXIsProcessTrusted()
if trusted { visit(app, 0) }
let roles = Dictionary(grouping: elements, by: { $0["role"] as? String ?? "unknown" })
let counts = roles.mapValues { $0.count }
let textFieldHasExpectedDefault = elements.contains {
    $0["role"] as? String == "AXTextField" &&
    $0["value"] as? String == "Alex Rivera"
}
let result: [String: Any] = [
    "schema": "calyra.macos-native-accessibility-readonly.v1",
    "target_app_pid": pid,
    "macos_version": ProcessInfo.processInfo.operatingSystemVersionString,
    "accessibility_permission_trusted": trusted,
    "element_count": seen,
    "sample_was_truncated": seen >= maxElements,
    "maximum_recursion_depth": maxDepth,
    "role_counts": counts,
    "canonical_name_field_exposed_with_value": textFieldHasExpectedDefault,
    "tree": elements,
    "permission_request_attempted": false,
    "events_posted": false,
    "focus_or_value_mutated": false,
    "voiceover_screenreader_tested": false,
    "actual_os_keyboard_or_pointer_tested": false,
]
let data = try JSONSerialization.data(
    withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
print(String(data: data, encoding: .utf8)!)
if !trusted { exit(2) }
if seen < 10 { exit(3) }
if !textFieldHasExpectedDefault { exit(4) }
