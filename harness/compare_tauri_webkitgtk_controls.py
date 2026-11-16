#!/usr/bin/env python3
"""Compare genuine, hash-pinned Tauri 2 native X11 vs standalone WebKitGTK pixels.

Both source images are archived, verified originals. No rerendering, HTML/CSS
transformation, pixel registration or claimed CSS compatibility percentage.
The purpose is to inspect whether the *actual Tauri app* paints the same
canonical CALYRA Controls first view as the independent Linux WebKit backend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

SOURCES = (
    ("tauri", "docs/evidence/tauri-linux-window-pixels/tauri-native-window.png",
     "8d035f42495d2b5d0d006c37c2cba1e6124c9795768937d42e66b77b743dc6e9"),
    ("webkitgtk", "docs/evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default-initial.png",
     "22b9bb1b3369bc3fd78773e580bcb57e306014eb9368bba1c8bbae27655cdbad"),
)
REGIONS = {
    "whole_view": (0, 0, 1060, 800),
    "header": (0, 0, 1060, 85),
    "sidebar": (0, 85, 258, 800),
    "main_intro": (258, 85, 1060, 450),
    "control_surface": (258, 450, 1060, 800),
    "select_control": (670, 465, 1010, 525),
    "range_control": (310, 585, 1010, 630),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(diff: Image.Image, box: tuple[int, int, int, int]) -> dict:
    crop = diff.crop(box).convert("RGB")
    n = crop.width * crop.height
    changed12, changed32, absolute = 0, 0, 0
    for px in crop.getdata():
        max_diff = max(px)
        changed12 += max_diff >= 12
        changed32 += max_diff >= 32
        absolute += sum(px)
    return {
        "bounds": list(box),
        "pixels": n,
        "changed_at_12": changed12,
        "fraction_at_12": round(changed12 / n, 6),
        "changed_at_32": changed32,
        "fraction_at_32": round(changed32 / n, 6),
        "mean_abs_rgb_channel": round(absolute / (3 * n), 6),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    opened = {}
    for name, rel, sha in SOURCES:
        path = repo / rel
        assert path.is_file(), f"Missing source evidence {path}"
        assert digest(path) == sha, f"Original {name} PNG hash mismatch"
        with Image.open(path) as img:
            img.load()
            assert img.size == (1060, 800) and img.format == "PNG", name
            opened[name] = img.convert("RGB")

    diff = ImageChops.difference(opened["tauri"], opened["webkitgtk"])
    out_diff = out / "tauri-vs-webkitgtk-raw-difference.png"
    diff.save(out_diff)

    # Montage is a derivative of two original PNGs, never a rerendered UI.
    montage = Image.new("RGB", (3 * 1060, 800 + 34), (12, 17, 23))
    for idx, (label, image) in enumerate((
        ("ACTUAL TAURI X11", opened["tauri"]),
        ("SYSTEM WEBKITGTK", opened["webkitgtk"]),
        ("ABSOLUTE RGB DIFFERENCE", diff),
    )):
        x = idx * 1060
        montage.paste(image, (x, 34))
        ImageDraw.Draw(montage).text((x + 16, 10), label, fill=(238, 241, 244))
    out_montage = out / "tauri-vs-webkitgtk-montage.png"
    montage.save(out_montage)

    result = {
        "schema": "calyra.tauri-webkitgtk-exploratory-controls-comparison.v1",
        "scene": "controls first view, 1060x800 native pixels",
        "sources": {
            name: {"path": rel, "sha256": sha}
            for name, rel, sha in SOURCES
        },
        "images": {
            p.name: digest(p) for p in (out_diff, out_montage)
        },
        "regions": {name: metrics(diff, box) for name, box in REGIONS.items()},
        "meaning": "uncorrected native pixel difference, not CSS support score",
        "source_content_modified": False,
        "actual_tauri_runtime_source": True,
        "hardware_gpu_measured": False,
        "wkwebview_macos_tested": False,
        "native_os_input_tested": False,
        "performance_measured": False,
        "different_capture_backends": True,
        "color_fonts_scale_normalized": False,
        "limitation": "The Tauri X11 window was captured by xwd, standalone WebKitGTK by WebView native snapshot, on separate CI runner jobs; decorations, antialiasing, font fallback and raster pipeline may differ. Large flat backgrounds make whole-frame percentages misleading.",
    }
    target = out / "tauri-vs-webkitgtk-comparison.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    m = result["regions"]["whole_view"]
    print(f"VERIFIED: native Tauri vs standalone WebKitGTK Controls: {m['changed_at_12']}/{m['pixels']} RGB pixels differ at threshold 12")
    print("CAVEAT: direct visual diagnostic only, not CSS compatibility or performance")
    assert all(x.stat().st_size > 1500 for x in (out_diff, out_montage, target))


if __name__ == "__main__":
    main()
