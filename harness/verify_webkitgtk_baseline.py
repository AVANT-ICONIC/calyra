#!/usr/bin/env python3
"""Fail-closed verification of original CALYRA Linux WebKitGTK Stage A captures.

The verifier is intentionally independent of the capture process. It uses
actual PNG image bytes and original reference files. No Tauri, macOS,
trusted OS input, performance, or hardware GPU conclusions are permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

FIXTURES = ("controls", "dashboard", "visual", "interaction")
EXPECTED = {
    "index.html": "aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a",
    "reference.css": "04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c",
    "reference.js": "9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fixtures", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve(strict=True)
    root = args.fixtures.resolve(strict=True)
    for file, sha in EXPECTED.items():
        assert digest(root / file) == sha, f"canonical original content changed: {file}"

    records = {}
    image_names = []
    versions = set()
    for fixture in FIXTURES:
        path = out / f"{fixture}-webkitgtk.json"
        assert path.is_file(), f"missing original WebKitGTK result: {path}"
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["schema"] == "calyra.system-webview.webkitgtk-stage-a.v1"
        assert record["fixture"] == fixture and record["success"] is True, fixture
        assert record["errors"] == [], (fixture, record["errors"])
        for key in (
            "tauri_shell_tested", "macos_wkwebview_tested",
            "physical_os_input_tested", "hardware_gpu_verified",
            "repeated_performance_samples",
        ):
            assert record[key] is False, (fixture, key)
        assert record["js_interactions_untrusted"] is True
        assert record["source_hashes"] == EXPECTED, fixture
        env = record["environment"]
        assert env["viewport_css_pixels"] == [1060, 800]
        assert env["configured_scale"] == 1
        assert env["display"] and env["webkit"]
        versions.add(env["webkit"])
        initial = record["events"]["initial"]
        assert initial["ready"] == "true"
        assert initial["fixture"] == initial["requested"] == fixture
        assert initial["active"] == [fixture]
        assert initial["nav"] == [fixture]
        assert initial["motion"] == "off"
        assert initial["styleSheets"] >= 1
        assert initial["cssGridSupported"] is True
        assert initial["viewport"] == {"width": 1060, "height": 800, "dpr": 1}
        assert initial["priority"] == {"value": "balanced", "index": 0}
        assert initial["shellDisplay"] in ("grid", "flex")
        assert record["timings_ms"]["js_ready"] >= record["timings_ms"]["load_finished"] >= 0
        assert record["timings_ms"]["end"] >= record["timings_ms"]["js_ready"]

        if fixture == "controls":
            events = record["events"]["programmatic_interactions"]
            assert events["events"] == []
            assert events["applied"]["value"] == "quality"
            assert events["reset"]["value"] == "balanced"
            assert events["eventOrigin"].endswith("(untrusted)")
        if fixture == "interaction":
            events = record["events"]["programmatic_interactions"]
            assert events["opened"]["expanded"] == "true"
            assert events["opened"]["hidden"] is False
            assert events["closed"]["expanded"] == "false"
            assert events["closed"]["hidden"] is True
            assert events["destination"]["focused"] == "destination"
            assert "synthetic" in events["eventOrigin"]

        expected_frames = {"initial", "after-dom-events"} if fixture in ("controls", "interaction") else {"initial"}
        assert set(record["screenshots"]) == expected_frames, fixture
        for label, image in record["screenshots"].items():
            name = image["path"]
            assert name == f"{fixture}-{label}.png", name
            file = out / name
            assert file.is_file() and file.stat().st_size == image["bytes"]
            assert digest(file) == image["sha256"], name
            assert image["width"] == 1060 and image["height"] == 800
            assert image["source"].startswith("real WebKitGTK")
            with Image.open(file) as png:
                png.verify()
            with Image.open(file) as png:
                assert png.size == (1060, 800) and png.format == "PNG"
            image_names.append(name)
        records[fixture] = {
            "webkit_version": env["webkit"],
            "ms_to_js_ready_single_run": record["timings_ms"]["js_ready"],
            "pngs": sorted(image["path"] for image in record["screenshots"].values()),
            "process_rss_diagnostic": record["memory_diagnostic"],
            "programmatic_events_only": True,
        }

    assert len(versions) == 1, f"inconsistent engine versions {versions}"
    assert len(image_names) == 6
    report = {
        "schema": "calyra.system-webview.stage-a-verification.v1",
        "pass": True,
        "reference_engine": "Linux WebKitGTK 4.1, not the Tauri shell or macOS WKWebView",
        "screenshot_count": 6,
        "fixture_count": 4,
        "webkit_version": next(iter(versions)),
        "original_asset_sha256": EXPECTED,
        "all_tests_untrusted_js_interaction": True,
        "physical_os_input_tested": False,
        "hardware_gpu_verified": False,
        "tauri_shell_tested": False,
        "macos_wkwebview_tested": False,
        "performance_comparison_eligible": False,
        "reason_not_comparable": "single Xvfb per-fixture Linux process samples, shared-memory RSS, no same-environment native baseline or repeated measurements",
        "fixtures": records,
    }
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(records)} real Linux WebKitGTK fixture runs and {len(image_names)} verified 1060x800 PNGs")
    print("LIMIT: neither Tauri shell nor macOS WKWebView, trusted OS input or comparative performance tested")


if __name__ == "__main__":
    main()
