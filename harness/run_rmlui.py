#!/usr/bin/env python3
"""CALYRA Stage A RmlUi 6.3 native probe. No Chromium, browser or synthetic success."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
NATIVE = ROOT / "native" / "rmlui"
PIN = "ba95ffe8bfb6370efb2cdcca927eaad4710c5413"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verified_source(path):
    if not (path / "CMakeLists.txt").is_file() or not (path / "LICENSE.txt").is_file():
        return False, "source or license missing"
    try:
        r = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=6, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"cannot verify commit: {exc}"
    return (r.stdout.strip() == PIN), f"expected {PIN}; actual {r.stdout.strip()}"

def result_template(mode):
    manifest = json.loads((FIX / "manifest.json").read_text())
    return {
        "schema": "calyra.adapter-result.v1",
        "adapter": {"id": "rmlui-6.3-glfw-gl3", "version": "6.3", "kind": "browserless-gpu"},
        "fixture": {"name": "controls", "version": manifest["version"],
                    "width_css_px": 1060, "height_css_px": 740, "state": "default", "motion": "off"},
        "source": {
            "html_sha256": sha(FIX / "index.html"),
            "css_sha256": sha(FIX / "reference.css"),
            "js_sha256": sha(FIX / "reference.js"),
            "css_modified": mode == "adapted", "dom_patched": True,
            "js_executed": False, "external_network_used": False,
            "adaptations": [
                "Original HTML replaced by documented RML controls translation",
                "Browser JS not executed; C++ RmlUi event handler used",
                "Native GLFW GL3 renderer, not a WebView",
                ("Hand-adapted controls.rcss replaces canonical CSS: not direct CSS compatibility"
                 if mode == "adapted" else
                 "Original reference.css passed unmodified to RmlUi; unsupported CSS not removed"),
            ]
        },
        "environment": {"os": platform.platform(), "architecture": platform.machine(),
                        "python_version": platform.python_version()},
        "execution": {"browser_engine": False, "gpu_backed": False, "interactive": False,
                      "render_backend": "GLFW_GL3: unverified attempt"},
        "capture": {"success": False, "page_count": 0, "png_paths": [],
                    "pdf_path": None, "pixel_scale": 1.0, "measured_performance": False},
        "coverage": {f: "untested" for f in manifest["fixtures"]["controls"]["features"]}
                    | {"html-dom": "adapted", "javascript-interactions": "unsupported"},
        "eligibility": "blocked",
        "limitations": [
            "No CPU/RAM/GPU performance metrics or CSS fidelity claims",
            "RML DOM translated; no direct browser DOM compatibility",
            "Accessibility, keyboard navigation and IME remain unverified"
        ],
    }

def run(args):
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = result_template(args.mode)
    source = Path(args.source).expanduser().resolve() if args.source else None
    binary = Path(args.binary).expanduser().resolve() if args.binary else out / "build" / "calyra_rmlui_probe"
    problem = None
    if source is None:
        problem = "BLOCKED: pinned RmlUi source not supplied; no substitute renderer"
    else:
        good, message = verified_source(source)
        if not good:
            problem = "BLOCKED: unverified RmlUi 6.3 checkout: " + message
    if not problem and args.build:
        build = out / "build"
        for cmd in [
            ["cmake", "-S", str(NATIVE), "-B", str(build),
             "-DCALYRA_RMLUI_SOURCE=" + str(source), "-DCMAKE_BUILD_TYPE=Release"],
            ["cmake", "--build", str(build), "--target", "calyra_rmlui_probe", "--parallel", "2"]
        ]:
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
                with (out / "build-log.txt").open("a") as log:
                    log.write("> " + " ".join(cmd) + "\n" + p.stdout[-16000:] + "\n" + p.stderr[-16000:] + "\n")
                if p.returncode:
                    problem = f"BLOCKED: CMake returned {p.returncode}; see build-log.txt"
                    break
            except (OSError, subprocess.SubprocessError) as exc:
                problem = f"BLOCKED: CMake unavailable or timed out: {exc}"
                break
    if not problem and not binary.is_file():
        problem = f"BLOCKED: binary missing ({binary}); pass --build"
    if not problem and (not args.font or not Path(args.font).is_file()):
        problem = "BLOCKED: missing local TTF font file (--font)"
    if not problem:
        ppm = out / f"rmlui-{args.mode}.ppm"
        css = FIX / "reference.css" if args.mode == "direct" else NATIVE / "controls.rcss"
        cmd = [str(binary), str(NATIVE / "controls.rml"), str(css),
               str(Path(args.font).resolve()), str(ppm)]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=22)
            (out / f"runtime-{args.mode}.log").write_text(p.stdout + "\n" + p.stderr)
            if p.returncode or "CALYRA_NATIVE_RENDER_OK=1" not in p.stdout or not ppm.is_file():
                problem = f"BLOCKED: native execution failed (exit={p.returncode}); check runtime log"
            else:
                from PIL import Image
                with Image.open(ppm) as im:
                    im.verify()
                with Image.open(ppm) as im:
                    width = im.width
                    png = out / f"rmlui-{args.mode}.png"
                    im.save(png)
                report["capture"].update(success=True, png_paths=[str(png.relative_to(ROOT))
                    if png.is_relative_to(ROOT) else str(png)], pixel_scale=width / 1060)
                report["execution"].update(gpu_backed=True, interactive=True,
                    render_backend="RmlUi 6.3 GLFW GL3 real native framebuffer")
                report["eligibility"] = "restricted"
                report["limitations"].append("Window rendered; still no equivalence or speed claim")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            problem = f"BLOCKED: native run/capture failed: {exc}"
    if problem:
        report["limitations"].append(problem)
    path = out / f"rmlui-{args.mode}-result.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    try:
        from jsonschema import validate
        validate(report, json.loads((ROOT / "harness" / "adapter-contract.schema.json").read_text()))
    except ImportError:
        pass
    print(json.dumps({"eligibility": report["eligibility"], "captured": report["capture"]["success"],
                      "report": str(path), "reason": problem}, indent=2))
    return 2 if problem else 0

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", help="Git checkout of pinned official RmlUi 6.3 commit")
    p.add_argument("--font", help="Local TTF font (never downloaded implicitly)")
    p.add_argument("--binary", help="Already-compiled binary (default: output/build)")
    p.add_argument("--build", action="store_true", help="Build using CMake, without network fallback")
    p.add_argument("--mode", choices=("direct", "adapted"), default="direct")
    p.add_argument("--output", default=str(ROOT / "evidence" / "native-stage-a" / "rmlui"))
    sys.exit(run(p.parse_args()))
