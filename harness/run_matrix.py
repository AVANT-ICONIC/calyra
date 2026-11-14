#!/usr/bin/env python3
"""Bounded Stage A execution; timeouts are explicit failures, never invented renders."""
import argparse
from importlib import metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jsonschema import validate
from harness.run_stage_a import ROOT, FIXTURES, CONTRACT_PATH, sha256


def execute_fixture(fixture, width, height, timeout, output):
    output.mkdir(parents=True, exist_ok=True)
    name = f"{fixture}-{width}x{height}-default"
    cmd = [sys.executable, str(ROOT / "harness" / "run_stage_a.py"), "--fixture", fixture,
           "--width", str(width), "--height", str(height), "--output", str(output)]
    try:
        process = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)
        if process.returncode == 0:
            record = json.loads((output / f"{name}.json").read_text(encoding="utf-8"))
            validate(record, json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
            return record
        reason = f"Renderer exited {process.returncode}: {process.stderr.strip()[-300:]}"
    except subprocess.TimeoutExpired:
        reason = f"Renderer did not finish within {timeout}s; terminated by harness. This is a preflight timeout, not a frame-time benchmark."
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    record = {
        "schema": "calyra.adapter-result.v1",
        "adapter": {"id": "weasyprint-static", "version": metadata.version("weasyprint"), "kind": "document-only"},
        "fixture": {"name": fixture, "version": manifest["version"], "width_css_px": width, "height_css_px": height, "state": "default", "motion": "off"},
        "source": {"html_sha256": sha256(FIXTURES / "index.html"), "css_sha256": sha256(FIXTURES / "reference.css"), "js_sha256": sha256(FIXTURES / "reference.js"),
                   "css_modified": False, "dom_patched": True, "js_executed": False, "external_network_used": False,
                   "adaptations": ["Static fixture selection", "Paged document viewport", "JavaScript disabled"]},
        "environment": {"os": platform.platform(), "architecture": platform.machine(), "python_version": platform.python_version()},
        "execution": {"browser_engine": False, "gpu_backed": False, "interactive": False,
                      "render_backend": "WeasyPrint -> PDF -> MuPDF PNG (attempted)"},
        "capture": {"success": False, "page_count": 0, "png_paths": [], "pdf_path": None, "pixel_scale": 1.0, "measured_performance": False},
        "coverage": {f: "untested" for f in manifest["fixtures"][fixture]["features"]},
        "eligibility": "blocked",
        "limitations": [reason, "No screenshot, CSS coverage, or performance inference from blocked run"]
    }
    validate(record, json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    (output / f"{name}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeout", type=int, default=8, help="Maximum seconds per fixture before terminating subprocess")
    p.add_argument("--width", type=int, default=1440)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--output", type=Path, default=ROOT / "evidence" / "native-stage-a")
    args = p.parse_args()
    if args.timeout < 1:
        p.error("timeout must be >=1 seconds")
    results = [execute_fixture(name, args.width, args.height, args.timeout, args.output.resolve())
               for name in ("controls", "dashboard", "visual", "interaction")]
    overview = {
        "schema": "calyra.stage-a-summary.v1",
        "mode": "weasyprint document-only browserless CPU smoke control; not native GUI, not GPU benchmark",
        "runs": [{"fixture": r["fixture"]["name"], "eligibility": r["eligibility"], "capture": r["capture"]["success"], "reason": r["limitations"][0] if r["eligibility"] == "blocked" else None} for r in results],
    }
    (args.output.resolve() / "summary.json").write_text(json.dumps(overview, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(overview, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
