// Native CALYRA research: read-only macOS AX hit-test activation and before/after
// census of one verified app-owned CoreGraphics window. No click, keyboard,
// pointer event posting, focus/AX action, TCC request or value manipulation.
import ApplicationServices
import CoreGraphics
import Foundation

func axRead(_ node: AXUIElement, _ attribute: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(node, attribute as CFString, &value) == .success else {
        return nil
    }
    return value
}
func axText(_ node: AXUIElement, _ attr: String) -> String? {
    guard let v = axRead(node, attr) else { return nil }
    if let s = v as? String { return String(s.prefix(160)) }
    if let n = v as? NSNumber { return n.stringValue }
    return nil
}
func census(_ root: AXUIElement) -> [String: Any] {
    var nodes = [[String: Any]]()
    var count = 0
    let limit = 500
    func walk(_ node: AXUIElement, _ depth: Int) {
        guard depth < 24 && count < limit else { return }
        count += 1
        var item: [String: Any] = [
            "role": axText(node, kAXRoleAttribute) ?? "unknown",
            "index": count, "depth": depth
        ]
        for (key, name) in [
            (kAXTitleAttribute, "title"),
            (kAXValueAttribute, "value"),
            (kAXDescriptionAttribute, "description"),
            (kAXRoleDescriptionAttribute, "role_description")
        ] {
            if let t = axText(node, key) { item[name] = t }
        }
        nodes.append(item)
        if let children = axRead(node, kAXChildrenAttribute) as? [AXUIElement] {
            for child in children {
                if count >= limit { break }
                walk(child, depth + 1)
            }
        }
    }
    walk(root, 0)
    let groups = Dictionary(grouping: nodes, by: {$0["role"] as? String ?? "unknown"})
    let counts = groups.mapValues { $0.count }
    let candidates = nodes.filter {
        ["AXTextField","AXPopUpButton","AXComboBox","AXSlider","AXCheckBox","AXButton",
         "AXWebArea","AXGroup","unknown"].contains($0["role"] as? String ?? "")
    }
    return [
        "count": count,
        "truncated": count >= limit,
        "role_counts": counts,
        "control_candidates": candidates,
    ]
}
func output(_ value: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject:value,
        options:[.prettyPrinted,.sortedKeys])
    print(String(data:data,encoding:.utf8)!)
}
guard CommandLine.arguments.count == 3,
      let pid = Int32(CommandLine.arguments[1]),pid > 0,
      let expectedWindowID = Int(CommandLine.arguments[2]),expectedWindowID > 0 else {
    fputs("usage: macos_ax_activation_probe <live Bltiz app PID> <verified CGWindow ID>\n",stderr)
    exit(64)
}
let trusted = AXIsProcessTrusted()
guard trusted else {
    output(["schema":"calyra.macos-ax-lazy-activation.v1",
            "trusted":false,"permission_request_attempted":false])
    exit(2)
}
let available = CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],
    kCGNullWindowID) as? [[String:Any]] ?? []
guard let owned = available.first(where: {
      ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid &&
      ($0[kCGWindowNumber as String] as? NSNumber)?.intValue == expectedWindowID &&
      ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0
    }),
    let bounds = owned[kCGWindowBounds as String] as? [String:Any],
    let x = (bounds["X"] as? NSNumber)?.doubleValue,
    let y = (bounds["Y"] as? NSNumber)?.doubleValue,
    let width = (bounds["Width"] as? NSNumber)?.doubleValue,
    let height = (bounds["Height"] as? NSNumber)?.doubleValue,
    width >= 400,height >= 300 else {
    fputs("Verified live app-owned CoreGraphics window not found\n",stderr)
    exit(3)
}
let app = AXUIElementCreateApplication(pid)
AXUIElementSetMessagingTimeout(app, 2.0)
let before = census(app)
// Query a small representative grid inside the content area. The API is
// deliberately read-only; it may or may not activate the AccessKit adapter.
// Record errors and returned roles rather than treating a missing hit as fatal.
let fractions:[(Double,Double)]=[
    (0.2,0.25),(0.5,0.25),(0.8,0.25),
    (0.2,0.5),(0.5,0.5),(0.8,0.5),
    (0.2,0.7),(0.5,0.7),(0.8,0.7)
]
var hits = [[String:Any]]()
for (fx,fy) in fractions {
    let px = Float(x + width*fx)
    let py = Float(y + height*fy)
    var hit:AXUIElement?
    let error = AXUIElementCopyElementAtPosition(app,px,py,&hit)
    var item:[String:Any] = [
        "x": px,"y":py,"fraction_x":fx,"fraction_y":fy,
        "ax_error":error.rawValue,
        "returned_element":hit != nil
    ]
    if let node=hit {
        item["role"] = axText(node,kAXRoleAttribute) ?? "unknown"
        if let title=axText(node,kAXTitleAttribute) { item["title"]=title }
        if let value=axText(node,kAXValueAttribute) { item["value"]=value }
        if let children=axRead(node,kAXChildrenAttribute) as? [AXUIElement] {
            item["child_count"]=children.count
        }
    }
    hits.append(item)
}
Thread.sleep(forTimeInterval: 1.5)
let after = census(app)
output([
    "schema":"calyra.macos-ax-lazy-activation.v1",
    "pid":pid,"window_id":expectedWindowID,
    "verified_live_cgwindow_bounds":[
        "x":x,"y":y,"width":width,"height":height
    ],
    "trusted":trusted,"before":before,"read_only_hit_tests":hits,
    "after":after,"samples":hits.count,
    "events_posted":false,"actions_performed":false,
    "focus_or_values_modified":false,"permission_request_attempted":false,
    "voiceover_tested":false,"real_os_keyboard_pointer_tested":false
])
