#!/usr/bin/env python3
"""Capture an *actual* running Tauri GTK/X11 window, never a substitute HTML page.

This deliberately uses the X11 window id and ImageMagick, not a standalone
WebKitGTK harness. It fail-closes if the window is absent, too small or blank.
Xvfb/X11 pixels do NOT establish macOS WKWebView or hardware GPU fidelity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from PIL import Image

MINIMUM_COLORS = 30


def run(*args: str) -> str:
    p = subprocess.run(args, check=True, capture_output=True, text=True)
    return p.stdout.strip()


def select_window(pid: int) -> tuple[str, str]:
    candidates = []
    until = time.monotonic() + 20
    while time.monotonic() < until:
        for criterion in (("--name", "CALYRA Stage A"), ("--pid", str(pid))):
            result = subprocess.run(["xdotool", "search", *criterion], capture_output=True, text=True)
            if result.returncode == 0:
                for wid in result.stdout.splitlines():
                    if wid not in candidates:
                        candidates.append(wid)
        # Choose the biggest real window rather than a tiny helper widget.
        sized = []
        for wid in candidates:
            try:
                geom = run("xdotool", "getwindowgeometry", "--shell", wid)
                props = dict(row.split("=", 1) for row in geom.splitlines() if "=" in row)
                width, height = int(props["WIDTH"]), int(props["HEIGHT"])
                if width >= 950 and height >= 700:
                    sized.append((width * height, wid, geom))
            except (subprocess.SubprocessError, ValueError, KeyError):
                continue
        if sized:
            _, wid, geom = max(sized)
            return wid, geom
        time.sleep(0.25)
    raise AssertionError(f"No mapped CALYRA window >=950x700 after 20 seconds; XIDs={candidates}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    wid, geom = select_window(args.pid)
    time.sleep(1.5)  # allow first paint in the real WebKitGTK widget

    raw = out / "tauri-native-window.xwd"
    image = out / "tauri-native-window.png"
    run("xwd", "-silent", "-id", wid, "-out", str(raw))
    subprocess.run(["convert", str(raw), str(image)], check=True, capture_output=True)
    assert raw.is_file() and raw.stat().st_size > 10000
    assert image.is_file(), "XWD conversion produced no PNG"
    with Image.open(image) as im:
        im.load()
        width, height = im.size
        preview = im.convert("RGB").resize((96, 96))
        colors = len(preview.getcolors(maxcolors=96 * 96) or [])
    # Save diagnostics even when the capture is only a blank X11 backing
    # surface. Do not treat a tiny valid PNG as a successful WebKit paint.
    diagnostic = {
        "window": wid,
        "geometry": geom,
        "image_size": [width, height],
        "png_bytes": image.stat().st_size,
        "sampled_distinct_colors": colors,
        "disable_compositing": os.environ.get("WEBKIT_DISABLE_COMPOSITING_MODE"),
        "disable_dmabuf": os.environ.get("WEBKIT_DISABLE_DMABUF_RENDERER"),
        "gdk_backend": os.environ.get("GDK_BACKEND"),
        "original_capture": image.name,
        "successful_real_pixels": colors >= MINIMUM_COLORS and image.stat().st_size > 2000,
    }
    (out / "capture-diagnostic.json").write_text(json.dumps(diagnostic, indent=2) + "\n")
    assert 950 <= width <= 1600 and 700 <= height <= 1200, (width, height)
    assert image.stat().st_size > 2000, (
        f"Actual X11 window exists, but PNG compressed to {image.stat().st_size} bytes; "
        f"likely blank compositor, {colors} distinct colors"
    )
    assert colors >= MINIMUM_COLORS, (
        f"Actual Tauri window captured but rendered content appears blank: {colors} colors"
    )
    report = {
        "schema": "calyra.tauri-linux-real-window-pixels.v1",
        "success": True,
        "window": wid,
        "geometry": geom,
        "image": image.name,
        "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "image_size": [width, height],
        "sampled_distinct_colors": colors,
        "pixels_from": "xwd window id of actual Tauri 2 X11 native WebKitGTK widget",
        "app_process_pid": args.pid,
        "gdk_backend": os.environ.get("GDK_BACKEND"),
        "macos_wkwebview_tested": False,
        "webkit_dom_js_verified": False,
        "os_hardware_gpu_verified": False,
        "visual_parity_to_webkit_reference_verified": False,
    }
    (out / "native-window-result.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: real Tauri native window rendered X11 colors =", colors, "dims =", width, height)


if __name__ == "__main__":
    main()
