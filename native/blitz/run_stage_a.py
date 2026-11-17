#!/usr/bin/env python3
"""Run Blitz's *actual* upstream CPU screenshot renderer against CALYRA HTML/CSS.

Official Blitz source and CLI are mandatory. This script never uses Chromium or
WeasyPrint as a fallback, never implies GPU acceleration and never executes JS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from prepare_static import FIXTURE_NAMES, generate, sha256

ROOT = Path(__file__).resolve().parents[2]
PIN = "4f61cffacee50fe4f944ebe9d0470d9a5d3997e0"
BLITZ_VERSION = "0.3.0-beta.4"
CAPTURE_EXAMPLE = "examples/screenshot.rs"


def run_command(argv: list[str], cwd: Path | None = None, timeout: int = 1200):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def pinned_source(source: Path) -> tuple[bool, str]:
    required = ("Cargo.lock", "Cargo.toml", CAPTURE_EXAMPLE)
    for name in required:
        if not (source / name).is_file():
            return False, f"Blitz source missing: {name}"
    try:
        rev = run_command(["git", "-C", str(source), "rev-parse", "HEAD"], timeout=10)
        dirty = run_command(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], timeout=10)
    except (OSError, subprocess.TimeoutExpired) as err:
        return False, f"Could not verify Blitz checkout: {err}"
    if rev.returncode or rev.stdout.strip() != PIN:
        return False, "Blitz checkout not at pinned revision " + PIN
    if dirty.returncode or dirty.stdout.strip():
        return False, "Blitz checkout has tracked modifications"
    return True, ""


def expected_png_location(source: Path, file_url: str) -> Path:
    """Upstream screenshot.rs compute_filename() exactly, pinned to revision PIN."""
    sanitized = "".join(char for char in file_url if char.isascii() and char.isalnum())[:12]
    return source / "examples" / "output" / (sanitized + ".png")


def report_template(root: Path, fixture: str) -> dict:
    manifest = json.loads((root / "fixtures" / "manifest.json").read_text())
    fixture_info = manifest["fixtures"][fixture]
    return {
        "schema": "calyra.adapter-result.v1",
        "adapter": {"id": "blitz-0.3.0-beta.4-vello-cpu", "version": BLITZ_VERSION,
                    "kind": "browserless-software"},
        "fixture": {"name": fixture, "version": manifest["version"],
                    "width_css_px": 1060, "height_css_px": 800, "state": "default", "motion": "off"},
        "source": {"html_sha256": sha256((root / "fixtures/index.html").read_bytes()),
                   "css_sha256": sha256((root / "fixtures/reference.css").read_bytes()),
                   "js_sha256": sha256((root / "fixtures/reference.js").read_bytes()),
                   "css_modified": False, "dom_patched": True, "js_executed": False,
                   "external_network_used": False,
                   "adaptations": ["CSS text inserted verbatim into a style element instead of an external link",
                                   "Native static HTML snapshot sets active fixture and selected nav state",
                                   "Script tag omitted: no JavaScript or input interaction"]},
        "environment": {"os": platform.platform(), "architecture": platform.machine(),
                        "python_version": platform.python_version()},
        "execution": {"browser_engine": False, "gpu_backed": False, "interactive": False,
                      "render_backend": "Blitz HTML/Stylo/Taffy/Vello CPU (unverified until native executable succeeds)"},
        "capture": {"success": False, "page_count": 0, "png_paths": [], "pdf_path": None,
                    "pixel_scale": 2.0, "measured_performance": False},
        "coverage": {name: "untested" for name in fixture_info["features"]}
                    | {"javascript": "unsupported", "input-events": "untested"},
        "eligibility": "blocked",
        "limitations": ["Static, non-interactive rendering only: no JavaScript, input, IME or accessibility proof",
                        "Screenshot uses Vello CPU; cannot prove native windowing or hardware GPU",
                        "One 1060 CSS-px wide capture; no performance or compatibility pass-rate"]
    }


def verify_render(raw: Path, normalized: Path, width: int = 1060, height: int = 800) -> dict:
    from PIL import Image, ImageStat
    with Image.open(raw) as probe:
        probe.verify()
    with Image.open(raw) as image:
        image.load()
        if image.width != width * 2 or image.height < height * 2:
            raise ValueError(f"Unexpected native screenshot resolution: {image.size}")
        if image.width > 16000 or image.height > 16000:
            raise ValueError("Implausible screenshot dimensions")
        canvas = image.convert("RGB").crop((0, 0, width * 2, height * 2))
        extrema = canvas.getextrema()
        if all(low == high for low, high in extrema):
            raise ValueError("Native screenshot is uniform/blank")
        observed = ImageStat.Stat(canvas)
        canvas.resize((width, height), Image.Resampling.LANCZOS).save(normalized)
        return {"raw_size": list(image.size), "viewport_px": [width, height],
                "mean_rgb": [round(x, 2) for x in observed.mean],
                "raw_sha256": sha256(raw.read_bytes()),
                "normalized_sha256": sha256(normalized.read_bytes())}


def run(root: Path, source: Path | None, output: Path, fixture: str, *, build: bool = False,
        build_timeout: int = 2400, run_timeout: int = 150) -> tuple[int, dict]:
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / f"blitz-{fixture}-result.json"
    raw = output / f"blitz-{fixture}-raw.png"
    normalized = output / f"blitz-{fixture}-viewport.png"
    # Never promote evidence left by an earlier run.
    for path in (result_path, raw, normalized):
        path.unlink(missing_ok=True)
    report = report_template(root, fixture)
    issue = None
    if source is None:
        issue = "BLOCKED: pinned official Blitz source checkout not supplied"
    else:
        ok, why = pinned_source(source)
        if not ok:
            issue = "BLOCKED: " + why
    binary = source / "target/release/examples/screenshot" if source else None
    if not issue and build:
        argv = ["cargo", "build", "--release", "--locked", "--example", "screenshot", "-j", "2"]
        try:
            proc = run_command(argv, cwd=source, timeout=build_timeout)
            (output / "cargo-build.log").write_text(proc.stdout + "\n" + proc.stderr)
            if proc.returncode:
                issue = f"BLOCKED: upstream cargo build returned exit {proc.returncode}"
        except (OSError, subprocess.TimeoutExpired) as err:
            issue = f"BLOCKED: native build exception: {err}"
    if not issue and (not binary.is_file()):
        issue = "BLOCKED: no upstream Blitz screenshot executable; retry with --build"
    if not issue:
        try:
            snapshot_root = output / "snapshots"
            snapshot = generate(root, snapshot_root, fixture)
            input_file = (snapshot_root / fixture / "index.html").resolve()
            uri = input_file.as_uri()
            upstream_png = expected_png_location(source, uri)
            upstream_png.parent.mkdir(parents=True, exist_ok=True)
            upstream_png.unlink(missing_ok=True)
            start = time.monotonic()
            proc = run_command([str(binary), uri, "1060"], cwd=source, timeout=run_timeout)
            elapsed = time.monotonic() - start
            (output / f"runtime-{fixture}.log").write_text(proc.stdout + "\n" + proc.stderr)
            if proc.returncode:
                raise RuntimeError(f"Native screenshot binary exit {proc.returncode}")
            if not upstream_png.is_file():
                raise RuntimeError(f"Blitz returned 0 but expected PNG does not exist: {upstream_png}")
            # Copy the raw real upstream PNG bytes; create a separate normalized viewport.
            raw.write_bytes(upstream_png.read_bytes())
            observation = verify_render(raw, normalized)
            report["execution"]["render_backend"] = "Blitz 0.3.0-beta.4, Stylo/Taffy and AnyRender/Vello CPU"
            report["capture"].update(success=True, page_count=1, png_paths=[str(raw), str(normalized)])
            report["eligibility"] = "restricted"
            report["limitations"].append(
                "Native screenshot generated; no CSS property has been scored direct from pixels alone")
            (output / f"blitz-{fixture}-provenance.json").write_text(json.dumps({
                "schema": "calyra.blitz-native-proof.v1", "upstream_commit": PIN,
                "version": BLITZ_VERSION, "binary_sha256": sha256(binary.read_bytes()),
                "snapshot": snapshot, "image": observation,
                "elapsed_seconds_diagnostic_only": round(elapsed, 3),
                "performance_benchmark": False,
            }, indent=2) + "\n")
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as err:
            issue = f"BLOCKED: real Blitz capture failed: {err}"
    if issue:
        raw.unlink(missing_ok=True)
        normalized.unlink(missing_ok=True)
        report["limitations"].append(issue)
    result_path.write_text(json.dumps(report, indent=2) + "\n")
    try:
        from jsonschema import validate
        validate(report, json.loads((root / "harness/adapter-contract.schema.json").read_text()))
    except ImportError:
        pass
    return (0 if report["capture"]["success"] else 2), report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--source", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "evidence/native-stage-a/blitz")
    p.add_argument("--fixture", choices=FIXTURE_NAMES, default="controls")
    p.add_argument("--build", action="store_true")
    p.add_argument("--build-timeout", type=int, default=2400)
    p.add_argument("--run-timeout", type=int, default=150)
    args = p.parse_args()
    code, report = run(args.root.resolve(), args.source.resolve() if args.source else None,
                       args.output.resolve(), args.fixture, build=args.build,
                       build_timeout=args.build_timeout, run_timeout=args.run_timeout)
    print(json.dumps({"status": report["eligibility"], "reason": report["limitations"][-1],
                      "capture": report["capture"]["success"]}, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
