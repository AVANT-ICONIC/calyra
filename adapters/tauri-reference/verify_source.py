#!/usr/bin/env python3
"""CALYRA: fail-closed source contract for the actual macOS Tauri wrapper.

This verifies authored assets and the adapter configuration only. It cannot
prove a successful Rust compile, a launch, a rendered frame or real OS input.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
ROOT = ADAPTER.parents[1]
FIXTURES = ROOT / "fixtures"
EXPECTED = {
    "index.html": "aa9fa23b242f06be7dc5b760f0f8379ce750d8fe2cd67a977daf1a4ff1bd848a",
    "reference.css": "04635269a8fbd790c87316a03c6469a157806201e58fd730212f632fc86b7b9c",
    "reference.js": "9d565203fc9c3450b0c61d7774cb2322b14ed3e3325926122b17f583e81cf3de",
}


def main() -> None:
    config = json.loads((ADAPTER / "src-tauri/tauri.conf.json").read_text())
    package = json.loads((ADAPTER / "package.json").read_text())
    assert config["identifier"] == "com.avanticonic.calyra.stagea"
    assert config["build"]["frontendDist"] == "../../../fixtures"
    direct = (ADAPTER / "src-tauri" / config["build"]["frontendDist"]).resolve()
    assert direct == FIXTURES.resolve(), f"frontendDist points somewhere else: {direct}"
    assert config["app"]["security"]["csp"] is None
    assert len(config["app"]["windows"]) == 1, "Stage A must not spawn extra windows"
    win = config["app"]["windows"][0]
    assert win["width"] == 1060 and win["height"] == 800
    assert win["innerSize"] is True and win["visible"] is True
    assert win["url"] == "index.html?fixture=controls&motion=off"
    assert config["bundle"]["targets"] == ["app"]
    assert config["bundle"]["icon"] == ["icons/icon.icns"]
    assert package["devDependencies"]["@tauri-apps/cli"] == "2.12.4"
    assert (ADAPTER / "src-tauri/src/main.rs").is_file()
    assert (ADAPTER / "src-tauri/build.rs").is_file()
    actual = {
        name: hashlib.sha256((direct / name).read_bytes()).hexdigest()
        for name in EXPECTED
    }
    assert actual == EXPECTED, f"canonical authored CALYRA content changed: {actual}"
    html = (direct / "index.html").read_text()
    assert '<link rel="stylesheet" href="./reference.css">' in html
    assert '<script src="./reference.js" defer></script>' in html

    print(json.dumps({
        "schema": "calyra.tauri-macos-source-contract.v1",
        "pass": True,
        "app_kind": "Tauri 2 with OS-provided macOS WKWebView",
        "build_status": "NOT_TESTED_BY_THIS_SCRIPT",
        "os_input_tested": False,
        "hardware_gpu_verified": False,
        "tauri_cli_version": "2.12.4",
        "original_assets_modified": False,
        "canonical_sha256": actual,
        "source_root": str(direct),
        "expected_macos_window_css_px": [1060, 800],
    }, indent=2))


if __name__ == "__main__":
    main()
