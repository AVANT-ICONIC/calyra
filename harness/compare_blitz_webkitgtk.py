#!/usr/bin/env python3
"""Exploratory pixel-level CSS control-scene comparison, not a speed benchmark.

Inputs are archived ORIGINAL 1060x800 native CPU Blitz and actual Linux
system-WebKitGTK screenshots. Never confuse identical background pixels with
feature-level parity. Differences include fonts, native control painting,
capture paths and distinct CI environments.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageDraw, ImageFont, ImageStat

ROOT = Path(__file__).resolve().parents[1]
BLITZ_IMAGE = ROOT / "docs/evidence/blitz-select-typography/typography-before.png"
WEBKIT_IMAGE = ROOT / "docs/evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default-initial.png"
BLITZ_REPORT = ROOT / "docs/evidence/blitz-select-typography/typography-result.json"
WEBKIT_TRACE = ROOT / "docs/evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default-probe.json"
WEBKIT_REPORT = ROOT / "docs/evidence/system-webkitgtk-reference/webkitgtk-controls-1060x800-default.json"
REGIONS = {
    "header": (0, 0, 1060, 85),
    "sidebar": (0, 85, 258, 800),
    "main_intro": (258, 85, 1060, 450),
    "control_surface": (258, 450, 1060, 800),
    "select_control": (670, 465, 1010, 525),
    "range_control": (310, 585, 1010, 630),
}
THRESHOLD = 12


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def count_pixels(diff: Image.Image, threshold: int = THRESHOLD) -> int:
    return sum(max(p) >= threshold for p in diff.getdata())


def region_result(diff: Image.Image, area: tuple[int, int, int, int]) -> dict:
    pixels = (area[2] - area[0]) * (area[3] - area[1])
    crop = diff.crop(area)
    changed = count_pixels(crop)
    return {
        "box": list(area), "pixels": pixels,
        "changed_rgb_pixels_at_12": changed,
        "changed_fraction": round(changed / pixels, 6),
        "mean_abs_channel_difference": round(sum(ImageStat.Stat(crop).mean) / 3, 6),
    }


def render_contact_sheet(web: Image.Image, native: Image.Image,
                         diff: Image.Image, output: Path) -> None:
    tile_width, tile_height = 530, 400
    header, gap, footer = 52, 14, 40
    page = Image.new("RGB", (tile_width * 3 + gap * 4,
                             tile_height + header + footer), (17, 22, 29))
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    label = ImageFont.truetype(str(font_path), 12) if font_path.exists() else ImageFont.load_default()
    enhanced = ImageEnhance.Contrast(diff).enhance(2.5)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(4)
    items = (
        ("WebKitGTK · system WebView", web),
        ("Blitz · Vello CPU", native),
        ("Amplified RGB difference", enhanced),
    )
    draw = ImageDraw.Draw(page)
    for i, (title, image) in enumerate(items):
        x = gap + i * (tile_width + gap)
        page.paste(image.resize((tile_width, tile_height), Image.Resampling.LANCZOS), (x, header))
        draw.text((x, 18), title, font=font, fill=(227, 236, 241))
    draw.text((gap, header + tile_height + 10),
              "Same 1060x800 controls fixture. Separate CI runners; font/GPU/input parity NOT established.",
              font=label, fill=(157, 174, 183))
    page.save(output)


def compare(output: Path) -> dict:
    br = json.loads(BLITZ_REPORT.read_text())
    wk = json.loads(WEBKIT_REPORT.read_text())
    trace = json.loads(WEBKIT_TRACE.read_text())
    assert br["schema"] == "calyra.blitz-select-typography-paint.v1"
    assert br["old_label"] == "Balanced"
    assert br["same_document"] is True
    assert br["original_css_modified"] is False and br["original_js_modified"] is False
    assert wk["source"]["css_modified"] is False and wk["source"]["dom_patched"] is False
    assert wk["source"]["js_executed"] is True
    assert wk["fixture"]["name"] == "controls"
    assert wk["fixture"]["width_css_px"] == 1060 and wk["fixture"]["height_css_px"] == 800
    assert wk["fixture"]["state"] == "default" and wk["fixture"]["motion"] == "off"
    assert trace["states"]["initial"]["priority"] == "balanced"
    assert trace["states"]["initial"]["viewport"] == [1060, 800]
    assert trace["required_assets_observed"] is True
    assert br["images"]["typography-before.png"] == digest(BLITZ_IMAGE)
    assert trace["captures"]["initial"]["sha256"] == digest(WEBKIT_IMAGE)
    assert wk["source"]["html_sha256"] == "aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a"
    assert wk["source"]["css_sha256"] == "04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c"
    assert wk["source"]["js_sha256"] == "9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de"
    assert wk["adapter"]["version"] == "2.52.6", wk["adapter"]
    assert trace["captures"]["initial"]["backend"] in (
        "gdk-x11-window-pixbuf", "webkit2gtk-native-snapshot-fallback"
    )

    output.mkdir(parents=True, exist_ok=True)
    with Image.open(BLITZ_IMAGE) as native_file, Image.open(WEBKIT_IMAGE) as web_file:
        native = native_file.convert("RGB")
        web = web_file.convert("RGB")
        assert native.size == web.size == (1060, 800)
        difference = ImageChops.difference(web, native)
        total_pixels = native.width * native.height
        changed = count_pixels(difference)
        exact = count_pixels(difference, 1)
        mean = sum(ImageStat.Stat(difference).mean) / 3
        diff_path = output / "controls-raw-rgb-diff.png"
        difference.save(diff_path)
        montage_path = output / "controls-comparison-montage.png"
        render_contact_sheet(web, native, difference, montage_path)
        result = {
            "schema": "calyra.exploratory-webkitgtk-blitz-diff.v1",
            "input_state": "controls initial, selected value balanced, motion off",
            "viewport_css_px": [1060, 800],
            "total_pixels": total_pixels,
            "comparison_method": "per-channel absolute RGB difference; changed if max channel >= 12",
            "changed_rgb_pixels_at_12": changed,
            "changed_fraction_at_12": round(changed / total_pixels, 6),
            "exact_match_pixels": total_pixels - exact,
            "exact_match_fraction": round((total_pixels - exact) / total_pixels, 6),
            "mean_abs_channel_difference": round(mean, 6),
            "regions": {
                key: region_result(difference, region) for key, region in REGIONS.items()
            },
            "source": {
                "blitz": {
                    "engine": "Blitz/Stylo/Taffy/Vello CPU + Boa; experimental patched SelectData",
                    "upstream_commit": br["upstream_commit"],
                    "producing_run": 43919838241,
                    "png_path": str(BLITZ_IMAGE.relative_to(ROOT)),
                    "png_sha256": digest(BLITZ_IMAGE),
                    "generated_screenshot": "typography-before.png, initial label Balanced"
                },
                "webview": {
                    "engine": "Linux system WebKitGTK 2.52.6; GTK/X11",
                    "producing_run": 43930684985,
                    "png_path": str(WEBKIT_IMAGE.relative_to(ROOT)),
                    "png_sha256": digest(WEBKIT_IMAGE),
                    "screenshot_backend": trace["captures"]["initial"]["backend"],
                },
                "author_css_sha256": wk["source"]["css_sha256"],
                "author_js_sha256": wk["source"]["js_sha256"],
                "author_html_sha256": wk["source"]["html_sha256"]
            },
            "derived_images": {
                "raw_difference_path": str(diff_path.relative_to(ROOT)),
                "raw_difference_sha256": digest(diff_path),
                "montage_path": str(montage_path.relative_to(ROOT)),
                "montage_sha256": digest(montage_path)
            },
            "limits": [
                "Different GitHub Actions jobs, no locked font file/OS font metrics baseline.",
                "Same visual scene/viewport and source hashes, but different rendering/capture pipelines.",
                "No color-management/antialiasing normalization or registration transforms.",
                "Pixel matches include large unchanged dark backgrounds: NOT percentage CSS compatibility.",
                "Region boxes are manually scoped diagnostic ROIs, not automatically detected controls.",
                "No hardware GPU, OS input, macOS WKWebView, Tauri packaging or performance comparison.",
                "Full interactive parity and cross-platform accessibility remain untested."
            ]
        }
    (output / "controls-comparison-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps({
        "comparison": "WebKitGTK 2.52.6 vs pinned native Blitz/Vello CPU",
        "changed_px_at_12": changed,
        "fraction_at_12": round(changed / total_pixels, 4),
        "control_region_at_12": result["regions"]["control_surface"]["changed_fraction"],
        "select_region_at_12": result["regions"]["select_control"]["changed_fraction"],
        "note": "Exploratory visual diagnostic; not a scored compatibility benchmark"
    }))
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path,
                   default=ROOT / "evidence" / "comparisons" / "controls")
    args = p.parse_args()
    compare(args.output.resolve())


if __name__ == "__main__":
    main()
