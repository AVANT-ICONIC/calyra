// CALYRA Stage A: inspect the real macOS window belonging to a known app PID,
// or evaluate a real screencapture PNG. No mock frames or frontend rewriting.
import AppKit
import CoreGraphics
import Foundation

func output(_ dictionary: [String: Any]) {
    let json = try! JSONSerialization.data(
        withJSONObject: dictionary, options: [.prettyPrinted, .sortedKeys])
    print(String(data: json, encoding: .utf8)!)
}

let args = CommandLine.arguments
guard args.count == 3 else {
    fputs("Usage: swift macos_native_window_probe.swift windows <pid> | inspect <png>\n", stderr)
    exit(64)
}

switch args[1] {
case "windows":
    guard let targetPID = Int32(args[2]), targetPID > 0 else { exit(64) }
    let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
    let allWindows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] ?? []
    var candidates: [[String: Any]] = []
    for item in allWindows {
        guard let owner = item[kCGWindowOwnerPID as String] as? NSNumber,
              owner.int32Value == targetPID,
              let number = item[kCGWindowNumber as String] as? NSNumber,
              let rect = item[kCGWindowBounds as String] as? [String: Any] else {
            continue
        }
        let width = (rect["Width"] as? NSNumber)?.intValue ?? 0
        let height = (rect["Height"] as? NSNumber)?.intValue ?? 0
        let layer = (item[kCGWindowLayer as String] as? NSNumber)?.intValue ?? -1
        guard layer == 0, width >= 400, height >= 300 else { continue }
        candidates.append([
            "window_id": number.intValue,
            "owner_pid": targetPID,
            "width": width,
            "height": height,
            "layer": layer,
        ])
    }
    candidates.sort {
        (($0["width"] as! Int) * ($0["height"] as! Int)) >
        (($1["width"] as! Int) * ($1["height"] as! Int))
    }
    output([
        "schema": "calyra.macos-app-window-list.v1",
        "owner_pid": targetPID,
        "visible_window_candidates": candidates,
        "window_found": !candidates.isEmpty,
    ])

case "inspect":
    guard let data = try? Data(contentsOf: URL(fileURLWithPath: args[2])),
          let rep = NSBitmapImageRep(data: data) else {
        output(["schema": "calyra.macos-window-pixels.v1", "accepted": false,
                "reason": "missing_or_invalid_png"])
        exit(2)
    }
    let width = rep.pixelsWide
    let height = rep.pixelsHigh
    let stepX = max(1, width / 48)
    let stepY = max(1, height / 48)
    var colors = Set<Int>()
    var samples = 0
    var nonWhite = 0
    // Ignore chrome at the edges; sample the meaningful inside of this exact
    // app-owned window. Distinct colors alone are NOT CSS fidelity or JS proof.
    if width >= 600 && height >= 450 {
        for y in stride(from: height / 8, to: height * 7 / 8, by: stepY) {
            for x in stride(from: width / 8, to: width * 7 / 8, by: stepX) {
                guard let c = rep.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB) else {
                    continue
                }
                let r = min(255, max(0, Int(c.redComponent * 255)))
                let g = min(255, max(0, Int(c.greenComponent * 255)))
                let b = min(255, max(0, Int(c.blueComponent * 255)))
                colors.insert(((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3))
                samples += 1
                if r < 243 || g < 243 || b < 243 { nonWhite += 1 }
            }
        }
    }
    let accepted = width >= 600 && height >= 450 &&
        samples >= 100 && colors.count >= 24 && nonWhite >= 50
    output([
        "schema": "calyra.macos-window-pixels.v1",
        "accepted": accepted,
        "width": width,
        "height": height,
        "sampled_pixels": samples,
        "quantized_distinct_colors": colors.count,
        "nonwhite_sampled_pixels": nonWhite,
        "pixel_gate_only_not_css_or_js_parity": true,
    ])
    if !accepted { exit(3) }

default:
    fputs("Unknown mode\n", stderr)
    exit(64)
}
