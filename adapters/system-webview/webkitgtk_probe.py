#!/usr/bin/python3
"""CALYRA Stage A system-WebView engine baseline (Linux / WebKitGTK 4.1).

Loads the ORIGINAL fixtures/index.html, reference.css, reference.js via file:
and records actual GTK WebKit2 snapshots and JS DOM observations. This is NOT
a Tauri app, macOS WKWebView, synthetic HTML replacement, input automation,
GPU benchmark, or comparable memory/performance benchmark.

Run under Xvfb using Ubuntu 24.04 system /usr/bin/python3 and apt PyGObject.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2  # noqa: E402


WIDTH, HEIGHT = 1060, 800
FIXTURES = ("controls", "dashboard", "visual", "interaction")
START = time.perf_counter()

# WebKit's JavaScriptCore returns the JSON-encoded JS string as a JS string,
# so we need exactly one json.loads() in Python after to_string().
INITIAL_JS = r"""JSON.stringify((() => {
  const chosen = new URLSearchParams(location.search).get("fixture");
  const active = Array.from(document.querySelectorAll("[data-case].active"), n=>n.dataset.case);
  const nav = Array.from(document.querySelectorAll("[data-link][aria-current=page]"), n=>n.dataset.link);
  const shell = document.querySelector(".shell");
  const css = getComputedStyle(shell);
  const s = document.getElementById("priority");
  return {
    ready: document.body.dataset.ready,
    fixture: document.body.dataset.fixture,
    requested: chosen,
    active, nav, motion: document.documentElement.dataset.motion,
    styleSheets: document.styleSheets.length,
    shellDisplay: css.display,
    bodyBackground: getComputedStyle(document.body).backgroundColor,
    cssGridSupported: CSS.supports("display","grid"),
    priority: { value:s.value,index:s.selectedIndex },
    viewport: {width: innerWidth,height:innerHeight,dpr:devicePixelRatio},
    userAgent: navigator.userAgent
  };
})())"""

CONTROL_JS = r"""JSON.stringify((() => {
  const s = document.getElementById("priority");
  const name = document.getElementById("person-name");
  const status = document.getElementById("action-status");
  const events=[];
  for (const name of ["input","change"])
    s.addEventListener(name, e=>events.push({type:e.type,trusted:e.isTrusted}));
  s.value = "quality";
  name.value = "CALYRA QA";
  document.getElementById("apply").click();
  const applied = {status:status.value,value:s.value,name:name.value};
  document.getElementById("reset").click();
  return {
    applied,
    reset: {status:status.value,value:s.value,name:name.value,
      intensity:document.getElementById("intensity").value,
      effects:document.getElementById("effects").checked},
    events, eventOrigin:"JS DOM click / property writes (untrusted)"
  };
})())"""

INTERACTION_JS = r"""JSON.stringify((() => {
  const toggle = document.getElementById("menu-toggle");
  const pop = document.getElementById("menu-popover");
  const status = document.getElementById("interaction-status");
  toggle.click();
  const opened = {
    expanded:toggle.getAttribute("aria-expanded"),
    hidden:pop.hidden,
    status:status.value,
    focusedCommand:document.activeElement?.getAttribute("data-command")||null
  };
  document.dispatchEvent(new KeyboardEvent("keydown",{
    key:"Escape",bubbles:true,cancelable:true
  }));
  const closed = {
    expanded:toggle.getAttribute("aria-expanded"),
    hidden:pop.hidden,
    status:status.value,
    focused:document.activeElement?.id||null
  };
  document.getElementById("focus-target").click();
  const destination = {
    focused:document.activeElement?.id||null,
    status:status.value
  };
  return {opened,closed,destination,eventOrigin:"JS DOM click / synthetic KeyboardEvent (untrusted)"};
})())"""


def file_digest(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


def process_rss_sample() -> dict:
    """One diagnostic RSS snapshot; sums double-count shared WebKit pages."""
    rows = {}
    try:
        output = subprocess.check_output(
            ["ps", "-eo", "pid=,ppid=,rss=,comm="], text=True, timeout=3
        )
        for line in output.splitlines():
            parts = line.strip().split(None, 3)
            if len(parts) == 4:
                try:
                    pid, ppid, rss = map(int, parts[:3])
                    rows[pid] = {"pid": pid, "ppid": ppid, "rss_kib": rss, "name": parts[3]}
                except ValueError:
                    continue
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "method": "ps unavailable"}

    own = os.getpid()
    included = {own}
    for _ in range(20):
        new = included | {p for p, row in rows.items() if row["ppid"] in included}
        if new == included:
            break
        included = new
    processes = [rows[p] for p in sorted(included) if p in rows]
    return {
        "available": bool(processes),
        "method": "single ps RSS sample, host PID and reachable child PID tree",
        "rss_sum_kib": sum(x["rss_kib"] for x in processes),
        "shared_memory_double_count_possible": True,
        "excludes_external_xvfb_and_system_daemons": True,
        "processes": processes,
    }


class Probe:
    def __init__(self, html: Path, fixture: str, output: Path):
        self.html = html
        self.fixture = fixture
        self.output = output
        self.status = 1
        self.finished = False
        self.started = time.perf_counter()
        self.record = {
            "schema": "calyra.system-webview.webkitgtk-stage-a.v1",
            "candidate": "WebKitGTK 4.1 system WebView in a minimal GTK3 host",
            "tauri_shell_tested": False,
            "macos_wkwebview_tested": False,
            "physical_os_input_tested": False,
            "hardware_gpu_verified": False,
            "js_interactions_untrusted": True,
            "repeated_performance_samples": False,
            "fixture": fixture,
            "source": str(html),
            "source_hashes": {file.name: file_digest(file)
                              for file in (html, html.parent / "reference.css",
                                           html.parent / "reference.js")},
            "environment": {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "display": os.environ.get("DISPLAY"),
                "gdk_backend": os.environ.get("GDK_BACKEND", ""),
                "gtk": f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
                "webkit": ".".join(str(x) for x in (
                    WebKit2.get_major_version(),
                    WebKit2.get_minor_version(),
                    WebKit2.get_micro_version()
                )),
                "viewport_css_pixels": [WIDTH, HEIGHT],
                "configured_scale": 1,
            },
            "events": {},
            "screenshots": {},
            "timings_ms": {},
            "errors": [],
        }
        self.output.mkdir(parents=True, exist_ok=True)

        self.window = Gtk.Window(title=f"CALYRA WebKitGTK | {fixture}")
        self.window.set_default_size(WIDTH, HEIGHT)
        self.window.set_resizable(False)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())

        self.web = WebKit2.WebView()
        self.web.set_size_request(WIDTH, HEIGHT)
        self.web.connect("load-changed", self.on_load)
        self.web.connect("load-failed", self.on_load_failed)
        self.web.connect("web-process-terminated", self.on_terminated)
        self.window.add(self.web)
        self.window.show_all()

        GLib.timeout_add_seconds(30, self.timeout)
        self.web.load_uri(html.as_uri() + f"?fixture={fixture}&motion=off")

    def millis(self) -> float:
        return round((time.perf_counter() - self.started) * 1000.0, 2)

    def timeout(self) -> bool:
        if not self.finished:
            self.fail("timeout: WebKitGTK page did not produce state and screenshots")
        return False

    def fail(self, error: object) -> None:
        if self.finished:
            return
        self.record["errors"].append(str(error))
        self.complete(False)

    def complete(self, ok: bool) -> None:
        if self.finished:
            return
        self.finished = True
        self.status = 0 if ok else 1
        self.record["timings_ms"]["end"] = self.millis()
        self.record["memory_diagnostic"] = process_rss_sample()
        self.record["success"] = ok
        name = f"{self.fixture}-webkitgtk.json"
        (self.output / name).write_text(
            json.dumps(self.record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"CALYRA_WEBKITGTK_REPORT={self.output / name}", flush=True)
        print(f"CALYRA_WEBKITGTK_SUCCESS={str(ok).lower()}", flush=True)
        if not ok:
            print("CALYRA_WEBKITGTK_ERROR=" + " | ".join(self.record["errors"]),
                  file=sys.stderr, flush=True)
        Gtk.main_quit()

    def on_load_failed(self, _view, _event, uri, error):
        self.fail(f"main-resource load failed {uri}: {error}")
        return False

    def on_terminated(self, _view, reason):
        self.fail(f"WebKit web process terminated: {reason}")

    def on_load(self, _view, event):
        if self.finished or event != WebKit2.LoadEvent.FINISHED:
            return
        self.record["timings_ms"]["load_finished"] = self.millis()
        # Give first paint a deterministic quiet interval, not a readiness lie.
        GLib.timeout_add(350, self.check_ready)

    def check_ready(self) -> bool:
        if not self.finished:
            self.evaluate(INITIAL_JS, self.got_initial)
        return False

    def evaluate(self, expression: str, callback):
        def finished(view, result):
            if self.finished:
                return
            try:
                js_result = view.run_javascript_finish(result)
                value = js_result.get_js_value().to_string()
                data = json.loads(value)
                callback(data)
            except Exception as e:
                self.fail(f"JavaScript evaluation failed: {e}")
        self.web.run_javascript(expression, None, finished)

    def got_initial(self, data: dict):
        self.record["timings_ms"]["js_ready"] = self.millis()
        self.record["events"]["initial"] = data
        if not (
            data.get("ready") == "true"
            and data.get("fixture") == self.fixture
            and data.get("requested") == self.fixture
            and data.get("active") == [self.fixture]
            and data.get("nav") == [self.fixture]
            and data.get("motion") == "off"
            and data.get("styleSheets", 0) >= 1
            and data.get("cssGridSupported") is True
            and data.get("viewport", {}).get("width") == WIDTH
            and data.get("viewport", {}).get("height") == HEIGHT
        ):
            self.fail(f"canonical HTML/CSS/JS or viewport mismatch: {data!r}")
            return
        self.capture("initial", self.after_initial_image)

    def capture(self, state: str, callback):
        def received(view, result):
            if self.finished:
                return
            try:
                surface = view.get_snapshot_finish(result)
                if surface is None:
                    raise RuntimeError("WebKit returned null Cairo surface")
                width, height = surface.get_width(), surface.get_height()
                if (width, height) != (WIDTH, HEIGHT):
                    raise AssertionError(f"snapshot size {width}x{height}, expected 1060x800")
                png = self.output / f"{self.fixture}-{state}.png"
                surface.write_to_png(str(png))
                if png.stat().st_size < 1000:
                    raise AssertionError("PNG appears empty")
                self.record["screenshots"][state] = {
                    "path": png.name, "width": width, "height": height,
                    "bytes": png.stat().st_size, "sha256": file_digest(png),
                    "source": "real WebKitGTK WebView.get_snapshot Cairo surface",
                }
                self.record["timings_ms"][f"snapshot_{state}"] = self.millis()
                callback()
            except Exception as e:
                self.fail(f"WebKitGTK snapshot failed: {e}")
        self.web.get_snapshot(
            WebKit2.SnapshotRegion.VISIBLE,
            WebKit2.SnapshotOptions.NONE,
            None, received,
        )

    def after_initial_image(self):
        if self.fixture == "controls":
            self.evaluate(CONTROL_JS, self.after_controls)
        elif self.fixture == "interaction":
            self.evaluate(INTERACTION_JS, self.after_interaction)
        else:
            self.complete(True)

    def after_controls(self, data: dict):
        self.record["events"]["programmatic_interactions"] = data
        applied, reset = data.get("applied", {}), data.get("reset", {})
        if not (
            applied.get("value") == "quality"
            and applied.get("name") == "CALYRA QA"
            and applied.get("status", "").startswith("Applied: CALYRA QA")
            and reset == {
                "status": "Settings reset", "value": "balanced",
                "name": "Alex Rivera", "intensity": "64", "effects": True
            }
            and data.get("events") == []
        ):
            self.fail(f"original controls JavaScript behavior mismatch: {data!r}")
            return
        self.capture("after-dom-events", lambda: self.complete(True))

    def after_interaction(self, data: dict):
        self.record["events"]["programmatic_interactions"] = data
        opened, closed, destination = (
            data.get("opened", {}), data.get("closed", {}), data.get("destination", {})
        )
        if not (
            opened.get("expanded") == "true"
            and opened.get("hidden") is False
            and opened.get("focusedCommand") is not None
            and closed.get("expanded") == "false"
            and closed.get("hidden") is True
            and closed.get("focused") == "menu-toggle"
            and destination.get("focused") == "destination"
            and destination.get("status") == "Destination focused"
        ):
            self.fail(f"original menu/Escape/focus JS behavior mismatch: {data!r}")
            return
        self.capture("after-dom-events", lambda: self.complete(True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--fixture", choices=FIXTURES, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    html = args.html.resolve(strict=True)
    if not all((html.parent / name).is_file()
               for name in ("reference.css", "reference.js")):
        parser.error("canonical CSS and JS must exist beside the HTML")
    probe = Probe(html, args.fixture, args.out.resolve())
    Gtk.main()
    return probe.status


if __name__ == "__main__":
    raise SystemExit(main())
