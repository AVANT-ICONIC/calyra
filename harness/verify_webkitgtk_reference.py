#!/usr/bin/env python3
"""Fail-closed verification of CALYRA real Linux system-WebKitGTK captures."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import validate
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = (
    ("controls", 1060, 800, "default", 2),
    ("dashboard", 1060, 800, "default", 1),
    ("visual", 1060, 800, "default", 1),
    ("interaction", 1060, 800, "default", 2),
    ("interaction", 1060, 800, "menu-open", 1),
    ("dashboard", 390, 844, "default", 1),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_all(directory: Path) -> dict:
    schema = json.loads((ROOT / "harness/adapter-contract.schema.json").read_text())
    expected_sources = {
        "html_sha256": "aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a",
        "css_sha256": "04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c",
        "js_sha256": "9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de",
    }
    for name, digest in expected_sources.items():
        filename = {"html_sha256": "index.html", "css_sha256": "reference.css",
                    "js_sha256": "reference.js"}[name]
        assert sha256(ROOT / "fixtures" / filename) == digest, filename
    summary = []
    png_count = 0
    for fixture, width, height, state, image_count in SCENARIOS:
        prefix = f"webkitgtk-{fixture}-{width}x{height}-{state}"
        adapter = json.loads((directory / f"{prefix}.json").read_text())
        trace = json.loads((directory / f"{prefix}-probe.json").read_text())
        validate(adapter, schema)
        assert adapter["adapter"]["kind"] == "system-webview"
        assert adapter["adapter"]["id"] == "webkit2gtk-system-backend-reference"
        assert adapter["execution"]["browser_engine"] is True
        assert adapter["execution"]["gpu_backed"] is False
        assert adapter["capture"]["measured_performance"] is False
        assert adapter["source"]["js_executed"] is True
        assert adapter["source"]["external_network_used"] is False
        assert adapter["source"]["css_modified"] is False
        assert adapter["source"]["dom_patched"] is False
        assert all(adapter["source"][key] == digest for key, digest in expected_sources.items())
        assert adapter["fixture"]["name"] == fixture
        assert adapter["fixture"]["state"] == state
        assert adapter["fixture"]["width_css_px"] == width
        assert adapter["fixture"]["height_css_px"] == height
        assert adapter["eligibility"] == "restricted"
        assert trace["required_assets_observed"] is True, trace["requested_local_paths"]
        assert trace["scripted_input_class"] == "javascript-dom-synthetic-not-os"
        assert trace["states"]["initial"]["active"] == [fixture]
        assert trace["states"]["initial"]["viewport"] == [width, height]
        assert len(trace["captures"]) == image_count, (fixture, trace["captures"])
        if fixture == "controls":
            assert trace["states"]["controls_action"]["priority"] == "quality"
            assert "Mara Novak" in trace["states"]["controls_action"]["status"]
        if fixture == "interaction" and state == "default":
            assert trace["states"]["menu_open"]["visible"] is True
            assert trace["states"]["menu_close"]["expanded"] == "false"
            assert trace["states"]["menu_close"]["scrollTop"] > 0
        if fixture == "interaction" and state == "menu-open":
            assert trace["states"]["initial"]["menuExpanded"] == "true"
        for capture in trace["captures"].values():
            file = ROOT / capture["path"]
            assert file.exists() and file.stat().st_size > 3000, file
            assert sha256(file) == capture["sha256"]
            with Image.open(file) as png:
                assert png.size == (width, height), (file, png.size)
                # Check genuine nonblank composited GUI pixels, not a black
                # Xvfb frame or stale uninitialized pixbuf.
                counts = png.convert("RGB").resize((64,64)).getcolors(4096)
                assert counts is not None and len(counts) > 35, (file, len(counts or []))
            png_count += 1
        summary.append({
            "fixture": fixture, "state": state, "viewport_css_px": [width, height],
            "capture_count": image_count, "webkit_version": adapter["adapter"]["version"],
            "engine_kind": "linux-system-webkitgtk-not-tauri",
            "scripted_actions": list(trace["states"]),
            "eligibility": "restricted",
        })
    result = {
        "schema": "calyra.system-webkitgtk-stage-a.v1",
        "candidate": "linux-system-webkitgtk-backend",
        "tauri_app_executed": False, "macos_wkwebview_tested": False,
        "hardware_gpu_tested": False, "os_level_input_tested": False,
        "canonical_assets_unchanged": True,
        "comparable_performance_measured": False,
        "scenario_count": len(summary), "png_count": png_count, "runs": summary,
    }
    assert result["png_count"] == 8, result
    (directory / "verified-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PASS:", len(summary), "actual Linux WebKitGTK windows;",
          png_count, "nonblank WebKit/GTK PNG screenshots; JS states verified")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path,
                        default=ROOT / "evidence/native-stage-a/system-webkitgtk")
    args = parser.parse_args()
    validate_all(args.directory.resolve())


if __name__ == "__main__":
    main()
