#!/usr/bin/env python3
"""CI-free Apple Silicon RmlUi Stage A preflight and native execution.

Default action is a read-only preflight. --run opts in to a pinned upstream
checkout and native build; never installs software or runs remote scripts.
"""
from __future__ import annotations

import argparse
from importlib.util import find_spec
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN = "ba95ffe8bfb6370efb2cdcca927eaad4710c5413"
UPSTREAM = "https://github.com/mikke89/RmlUi.git"
DEFAULT_SOURCE = ROOT / ".local" / "rmlui-6.3"
DEFAULT_OUTPUT = ROOT / "evidence" / "native-stage-a" / "rmlui"


def execute(argv, *, timeout=25, env=None):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)


def tool(name):
    return shutil.which(name) is not None


def choose_font(requested):
    if requested:
        return Path(requested).expanduser().resolve()
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ):
        p = Path(candidate)
        if p.is_file() and p.suffix.lower() == ".ttf":
            return p
    return None


def brew_paths():
    """Help CMake/pkg-config see keg-only FreeType, without mutating shell."""
    env = os.environ.copy()
    paths = []
    pkg_paths = []
    if not tool("brew"):
        return env
    for formula in ("glfw", "freetype"):
        try:
            p = execute(["brew", "--prefix", formula], timeout=10)
            if p.returncode == 0:
                prefix = Path(p.stdout.strip())
                if prefix.is_dir():
                    paths.append(str(prefix))
                    for pkg in (prefix / "lib/pkgconfig", prefix / "share/pkgconfig"):
                        if pkg.is_dir():
                            pkg_paths.append(str(pkg))
        except (OSError, subprocess.TimeoutExpired):
            pass
    if paths:
        env["CMAKE_PREFIX_PATH"] = os.pathsep.join(paths + ([env["CMAKE_PREFIX_PATH"]] if env.get("CMAKE_PREFIX_PATH") else []))
    if pkg_paths:
        env["PKG_CONFIG_PATH"] = os.pathsep.join(pkg_paths + ([env["PKG_CONFIG_PATH"]] if env.get("PKG_CONFIG_PATH") else []))
    return env


def check_environment(font):
    osname, arch = platform.system(), platform.machine()
    issues = []
    if osname != "Darwin":
        issues.append("requires macOS desktop display; this host is not macOS")
    if arch != "arm64":
        issues.append(f"Apple Silicon arm64 validation unavailable on architecture {arch}")
    tools = {t: tool(t) for t in ("git", "cmake", "c++", "pkg-config", "brew", "xcrun")}
    for t in ("git", "cmake", "c++", "pkg-config"):
        if not tools[t]:
            issues.append(f"missing executable: {t}")
    env = brew_paths() if osname == "Darwin" else os.environ.copy()
    packages = {}
    if tools["pkg-config"]:
        for package in ("glfw3", "freetype2"):
            try:
                result = execute(["pkg-config", "--modversion", package], env=env)
                packages[package] = result.stdout.strip() if result.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                packages[package] = None
            if not packages[package]:
                issues.append(f"missing pkg-config dependency: {package}")
    else:
        packages = {"glfw3": None, "freetype2": None}
    python_modules = {name: find_spec(name) is not None for name in ("PIL", "jsonschema")}
    for name, present in python_modules.items():
        if not present:
            issues.append(f"missing Python dependency: {name}; install native/rmlui/requirements-macos.txt in a virtual environment")
    if font is None or not font.is_file() or font.suffix.lower() != ".ttf":
        issues.append("missing local .ttf font (use --font <path>)")
    return {
        "system": osname, "arch": arch, "commands": tools, "packages": packages,
        "python_modules": python_modules, "font": str(font) if font else None,
        "issues": issues, "ready": not issues,
    }, env


def verify_upstream(source):
    """Do not reuse a forged, dirty or mismatched source tree."""
    try:
        sha = execute(["git", "-C", str(source), "rev-parse", "HEAD"], timeout=10)
        dirty = execute(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return (sha.returncode == 0 and sha.stdout.strip() == PIN and dirty.returncode == 0
            and not dirty.stdout.strip() and (source / "CMakeLists.txt").is_file()
            and (source / "LICENSE.txt").is_file())


def run(args):
    font = choose_font(args.font)
    preflight, env = check_environment(font)
    info = {"schema": "calyra.macos-rmlui-preflight.v1", "stage": "A", "upstream_sha": PIN,
            "preflight": preflight, "attempted_native_build": False, "modes": {}, "status": "blocked"}
    if not args.run or not preflight["ready"]:
        print(json.dumps(info, indent=2))
        return 0 if preflight["ready"] and not args.run else 2

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        # An opt-in clone of the official source only; no remote install scripts.
        try:
            clone = execute(["git", "clone", "--no-checkout", UPSTREAM, str(source)], timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            info["error"] = f"source clone unavailable: {exc}"
            print(json.dumps(info, indent=2))
            return 2
        if clone.returncode != 0:
            info["error"] = "source clone failed: " + clone.stderr[-900:]
            print(json.dumps(info, indent=2))
            return 2
        try:
            checkout = execute(["git", "-C", str(source), "checkout", "--detach", PIN], timeout=60)
        except (OSError, subprocess.TimeoutExpired) as exc:
            info["error"] = f"source checkout unavailable: {exc}"
            print(json.dumps(info, indent=2))
            return 2
        if checkout.returncode != 0:
            info["error"] = "pinned checkout failed: " + checkout.stderr[-900:]
            print(json.dumps(info, indent=2))
            return 2
    if not verify_upstream(source):
        info["error"] = "upstream tree is not the exact clean pinned RmlUi commit"
        print(json.dumps(info, indent=2))
        return 2

    out = Path(args.output).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    info["attempted_native_build"] = True
    for mode in ("direct", "adapted"):
        command = [sys.executable, str(ROOT / "harness/run_rmlui.py"),
                   "--source", str(source), "--font", str(font),
                   "--mode", mode, "--output", str(out)]
        if mode == "direct":
            command.append("--build")
        # Pass locally discovered Homebrew CMake/package paths, never modify the user shell.
        try:
            proc = execute(command, timeout=args.timeout, env=env)
            record = out / f"rmlui-{mode}-result.json"
            result = json.loads(record.read_text()) if record.is_file() else None
            info["modes"][mode] = {"exit_code": proc.returncode,
                                  "report": str(record) if result else None,
                                  "status": result["eligibility"] if result else "blocked",
                                  "native_capture": bool(result and result["capture"]["success"]),
                                  "render_backend": result["execution"]["render_backend"] if result else None,
                                  "stderr_tail": proc.stderr[-800:]}
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
            info["modes"][mode] = {"status": "blocked", "error": str(exc)}
        if info["modes"][mode]["status"] == "blocked":
            break

    info["status"] = "restricted" if len(info["modes"]) == 2 and all(
        item.get("native_capture") for item in info["modes"].values()) else "blocked"
    report = out / "macos-preflight-summary.json"
    report.write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps({"status": info["status"], "report": str(report), "modes": info["modes"]}, indent=2))
    return 0 if info["status"] == "restricted" else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Opt in to pinned clone, native build and both CSS modes")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Pinned RmlUi checkout path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Report and screenshot directory")
    parser.add_argument("--font", help="Existing .ttf, not a downloadable network font")
    parser.add_argument("--timeout", type=int, default=900, help="Max seconds for each native runner invocation")
    sys.exit(run(parser.parse_args()))
