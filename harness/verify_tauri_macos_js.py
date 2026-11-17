#!/usr/bin/env python3
"""Fail-closed verification of actual Tauri/WKWebView JavaScript callback records.

This must be run AFTER a macOS Tauri binary compiled with stage-a-js-probe
has evaluated the original CALYRA reference.js handlers. No synthetic records
or fallback browser results are permitted.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_HASHES = {
    "index.html": "aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a",
    "reference.css": "04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c",
    "reference.js": "9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de",
}
SHARED = {
    "original_js_ready": "true",
    "native_webkit_user_agent": True,
}
CASES = {
    "controls": {
        **SHARED,
        "canonical_active_section": "controls",
        "initial_name": "Alex Rivera",
        "initial_select": "balanced",
        "initial_slider": "64",
        "initial_status": "Ready for input",
        "slider_original_input_handler": "73%",
        "apply_original_click_handler": "Applied: Calyra macOS JS · quality · 73% · off",
        "reset_original_click_handler": "Settings reset",
        "reset_name": "Alex Rivera",
        "reset_select": "balanced",
        "reset_slider": "64",
        "reset_slider_output": "64%",
        "reset_checkbox": True,
    },
    "interaction": {
        **SHARED,
        "canonical_active_section": "interaction",
        "initial_menu_closed": True,
        "menu_opens": False,
        "menu_aria_expanded": "true",
        "menu_command_focus": "inspect",
        "document_escape_handler": True,
        "escape_restores_focus": "menu-toggle",
        "command_original_click_handler": "Command: inspect",
        "command_closes_menu": True,
        "focus_target_original_click_handler": "destination",
        "focus_status_original_click_handler": "Destination focused",
        "programmatic_scroll": True,
    },
}

def main() -> None:
    assert len(sys.argv) == 2, "usage: verify_tauri_macos_js.py <actual-results-dir>"
    path = Path(sys.argv[1]).resolve()
    assert path.is_dir(), f"missing real native results directory: {path}"
    for name, digest in FIXTURE_HASHES.items():
        actual = hashlib.sha256((ROOT / "fixtures" / name).read_bytes()).hexdigest()
        assert actual == digest, f"canonical fixture changed: {name}"

    log = (path / "native-app.log").read_text()
    summary: dict = {
        "schema": "calyra.macos-native-wkwebview-js-verified.v1",
        "canonical_fixture_sha256": FIXTURE_HASHES,
        "results": {},
        "verified_native_eval_callback": False,
        "trusted_os_input_verified": False,
        "hardware_gpu_verified": False,
        "matched_memory_benchmark_verified": False,
    }
    for fixture, expected in CASES.items():
        original = path / f"{fixture}-native-eval.json"
        assert original.is_file() and original.stat().st_size > 20, \
            f"real WKWebView eval callback absent: {original}"
        data = json.loads(original.read_text())
        # Tauri may JSON-encode a JS return value a second time.
        if isinstance(data, str):
            data = json.loads(data)
        assert isinstance(data, dict), f"unexpected native eval type: {type(data)}"
        assert data.get("schema") == "calyra.tauri-macos-native-js.v1"
        assert data.get("fixture") == fixture, data.get("fixture")
        assert f"fixture={fixture}" in data.get("url", "")
        assert data.get("protocol") not in (None, "file:"), data.get("protocol")
        assert "AppleWebKit" in data.get("user_agent", "")
        assert data.get("document_ready") in ("interactive", "complete")
        assert isinstance(data.get("viewport_css_px"), list)
        assert len(data["viewport_css_px"]) == 2
        assert all(isinstance(v, (int, float)) and v > 100
                   for v in data["viewport_css_px"])
        assertions = data.get("assertions")
        assert isinstance(assertions, list) and len(assertions) == len(expected), \
            (fixture, len(assertions) if isinstance(assertions, list) else None, len(expected))
        observed = {a.get("name"): a for a in assertions}
        assert set(observed) == set(expected), (fixture, sorted(observed), sorted(expected))
        for name, value in expected.items():
            assertion = observed[name]
            assert assertion.get("expected") == value, (fixture, name, assertion)
            assert assertion.get("actual") == value, (fixture, name, assertion)
            assert assertion.get("pass") is True, (fixture, name, assertion)
        assert data.get("pass") is True and not data.get("exception"), (fixture, data)
        assert f"{fixture}-native-eval.json" in log and \
            "CALYRA_PROBE_CALLBACK" in log, f"missing native callback provenance {fixture}"
        summary["results"][fixture] = {
            "original_js_handler_assertions_passed": len(assertions),
            "native_app_origin": data["url"],
            "user_agent": data["user_agent"],
            "viewport_css_px": data["viewport_css_px"],
            "device_pixel_ratio": data["device_pixel_ratio"],
            "callback_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        }

    summary["verified_native_eval_callback"] = True
    (path / "validated-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
