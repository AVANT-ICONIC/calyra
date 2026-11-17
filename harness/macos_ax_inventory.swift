// CALYRA: read-only macOS Accessibility inventory of one verified native GUI PID.
// Do not inject keyboard/pointer events, focus, edit, request permissions or
// infer app compliance from a screenshot. Designed for Blitz & WKWebView alike.
import ApplicationServices
import Foundation

func read(_ node: AXUIElement, _ attribute: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(node, attribute as CFString, &value) == .success else {
        return nil
    }
    return value
}

func valueString(_ node: AXUIElement, _ attribute: String) -> String? {
    guard let value = read(node, attribute) else { return nil }
    if let s = value as? String { return String(s.prefix(160)) }
    if let n = value as? NSNumber { return n.stringValue }
    return nil
}

guard CommandLine.arguments.count == 2,
      let pid = Int32(CommandLine.arguments[1]),
      pid > 0 else {
    fputs("usage: macos_ax_inventory <verified native GUI PID>\n", stderr)
    exit(64)
}

let trusted = AXIsProcessTrusted()
let target = AXUIElementCreateApplication(pid)
AXUIElementSetMessagingTimeout(target, 3.0)

var elements = [[String: Any]]()
var visited = 0
let maxNodes = 500
let maxDepth = 22

func inspect(_ node: AXUIElement, _ depth: Int) {
    if depth > maxDepth || visited >= maxNodes { return }
    visited += 1
    var entry: [String: Any] = [
        "index": visited,
        "depth": depth,
        "role": valueString(node, kAXRoleAttribute) ?? "unknown",
    ]
    for (attribute, name) in [
        (kAXTitleAttribute, "title"),
        (kAXDescriptionAttribute, "description"),
        (kAXValueAttribute, "value"),
        (kAXHelpAttribute, "help"),
        (kAXRoleDescriptionAttribute, "role_description"),
        (kAXSubroleAttribute, "subrole"),
    ] {
        if let v = valueString(node, attribute) { entry[name] = v }
    }
    if let enabled = read(node, kAXEnabledAttribute) as? NSNumber {
        entry["enabled"] = enabled.boolValue
    }
    elements.append(entry)
    if let children = read(node, kAXChildrenAttribute) as? [AXUIElement] {
        for child in children {
            if visited >= maxNodes { break }
            inspect(child, depth + 1)
        }
    }
}

if trusted { inspect(target, 0) }
let grouped = Dictionary(grouping: elements) { $0["role"] as? String ?? "unknown" }
let roles = grouped.mapValues { $0.count }
let fields: [String: [String: String]] = [
    "display_name": ["role": "AXTextField", "title": "Display name", "value": "Alex Rivera"],
    "render_priority": ["role": "AXPopUpButton", "title": "Render priority", "value": "Balanced"],
    "material_intensity": ["role": "AXSlider", "value": "64"],
    "enable_effects": ["role": "AXCheckBox"],
    "apply_settings": ["role": "AXButton", "title": "Apply settings"],
    "reset": ["role": "AXButton", "title": "Reset"],
]
var fieldMatches: [String: Bool] = [:]
for (name, required) in fields {
    fieldMatches[name] = elements.contains { observed in
        required.allSatisfy { key, expected in
            observed[key] as? String == expected
        }
    }
}
let report: [String: Any] = [
    "schema": "calyra.macos-native-ax-inventory.v1",
    "target_pid": pid,
    "macos": ProcessInfo.processInfo.operatingSystemVersionString,
    "accessibility_trusted": trusted,
    "node_count": visited,
    "truncated": visited >= maxNodes,
    "maximum_depth": maxDepth,
    "role_counts": roles,
    "canonical_field_role_matches": fieldMatches,
    "tree": elements,
    "read_only": true,
    "events_posted": false,
    "focus_modified": false,
    "values_modified": false,
    "screen_reader_tested": false,
    "ime_tested": false,
]
let json = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
print(String(data: json, encoding: .utf8)!)
if !trusted { exit(2) }
// Do not exit nonzero on missing fields; a verified absence is a research result.
