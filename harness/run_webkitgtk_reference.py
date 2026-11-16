#!/usr/bin/python3
"""CALYRA Stage A Linux system-WebView *backend* reference (WebKit2GTK 4.1).

This is NOT a packaged Tauri app and NOT macOS WKWebView. It exercises the
same Linux system WebKitGTK family Tauri uses, keeping the canonical assets
byte-identical and running their *real* JavaScript over 127.0.0.1.

JS-driven actions are explicit synthetic DOM events, NOT physical OS inputs.
Window screenshots are captured from actual GTK/X11 compositor pixels.
No timing/RSS/GPU/battery superiority is inferred from these smoke captures.
"""
from __future__ import annotations

import argparse
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import platform
from pathlib import Path
from threading import Thread
import traceback

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, Gdk, GLib, WebKit2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "fixtures"
CONTRACT = ROOT / "harness" / "adapter-contract.schema.json"


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


class QuietFixtureServer(SimpleHTTPRequestHandler):
    requested_paths: list[str] = []

    def do_GET(self):
        self.requested_paths.append(self.path.split("?", 1)[0])
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass


INITIAL_JS = r"""JSON.stringify((() => {
  const fixture = document.body.dataset.fixture;
  const styles = {
    mainGrid: getComputedStyle(document.querySelector('.workspace')).display,
    metricsGrid: getComputedStyle(document.querySelector('.metrics-grid')).display,
    selectedColor: getComputedStyle(document.body).color,
    glassBackdrop: getComputedStyle(document.querySelector('.glass-surface')).backdropFilter,
  };
  return {
    ready: document.body.dataset.ready,
    fixture: fixture,
    motion: document.documentElement.dataset.motion,
    active: [...document.querySelectorAll('.case.active')].map(x=>x.dataset.case),
    selectedNav: document.querySelectorAll('[aria-current="page"]').length,
    viewport: [window.innerWidth,window.innerHeight],
    htmlScrollWidth: document.documentElement.scrollWidth,
    styles: styles,
    priority: document.getElementById('priority').value,
    menuExpanded: document.getElementById('menu-toggle').getAttribute('aria-expanded')
  };
})())"""

CONTROLS_ACTION = r"""JSON.stringify((() => {
  const name=document.getElementById('person-name');
  const priority=document.getElementById('priority');
  const intensity=document.getElementById('intensity');
  name.value='Mara Novak';
  name.dispatchEvent(new Event('input',{bubbles:true}));
  priority.value='quality';
  priority.dispatchEvent(new Event('change',{bubbles:true}));
  intensity.value='73';
  intensity.dispatchEvent(new Event('input',{bubbles:true}));
  document.getElementById('effects').checked=false;
  document.getElementById('apply').click();
  return {
    name:name.value,priority:priority.value,intensity:intensity.value,
    intensityOutput:document.getElementById('intensity-output').value,
    effects:document.getElementById('effects').checked,
    status:document.getElementById('action-status').value
  };
})())"""

MENU_OPEN_ACTION = r"""JSON.stringify((() => {
  document.getElementById('menu-toggle').click();
  return {
    expanded:document.getElementById('menu-toggle').getAttribute('aria-expanded'),
    visible:!document.getElementById('menu-popover').hidden,
    focus:document.activeElement && document.activeElement.dataset.command,
    status:document.getElementById('interaction-status').value
  };
})())"""

MENU_CLOSE_ACTION = r"""JSON.stringify((() => {
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  const expanded=document.getElementById('menu-toggle').getAttribute('aria-expanded');
  const focused=document.activeElement && document.activeElement.id;
  document.getElementById('focus-target').click();
  const destinationFocus=document.activeElement && document.activeElement.id;
  document.getElementById('scroll-region').scrollTop=500;
  return {
    expanded:expanded,focusAfterEscape:focused,
    destinationFocus:destinationFocus,
    scrollTop:document.getElementById('scroll-region').scrollTop
  };
})())"""


def checked_state(fixture: str, step: str, state: dict, width: int, height: int) -> None:
    if step == "initial":
        assert state["ready"] == "true", state
        assert state["fixture"] == fixture, state
        assert state["motion"] == "off", state
        assert state["active"] == [fixture], state
        assert state["selectedNav"] == 1, state
        assert state["viewport"] == [width, height], state
        assert state["htmlScrollWidth"] <= width + 1, state
        # The canonical @media(max-width:650px) intentionally collapses
        # .workspace from grid to block. This is *correct* responsive CSS.
        expected_display = "block" if width <= 650 else "grid"
        assert state["styles"]["mainGrid"] == expected_display, state
        assert state["styles"]["metricsGrid"] == "grid", state
        assert state["priority"] == "balanced", state
    elif step == "controls_action":
        assert state == {
            "name": "Mara Novak", "priority": "quality", "intensity": "73",
            "intensityOutput": "73%", "effects": False,
            "status": "Applied: Mara Novak · quality · 73% · off",
        }, state
    elif step == "menu_open":
        assert state == {
            "expanded": "true", "visible": True, "focus": "inspect", "status": "Menu open"
        }, state
    elif step == "menu_close":
        assert state["expanded"] == "false", state
        assert state["focusAfterEscape"] == "menu-toggle", state
        assert state["destinationFocus"] == "destination", state
        assert state["scrollTop"] > 0, state
    else:
        raise AssertionError(f"Unexpected scripted step: {step}")


class WebKitFixtureRun:
    def __init__(self, args, url: str):
        self.args = args
        self.url = url
        self.main_loop = GLib.MainLoop()
        self.states = {}
        self.captures = {}
        self.error = None
        self.step_index = 0
        self.steps = [("initial", INITIAL_JS, True)]
        if args.fixture == "controls":
            self.steps.append(("controls_action", CONTROLS_ACTION, True))
        if args.fixture == "interaction" and args.state == "default":
            self.steps.extend((
                ("menu_open", MENU_OPEN_ACTION, True),
                ("menu_close", MENU_CLOSE_ACTION, False),
            ))
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_default_size(args.width, args.height)
        self.window.connect("destroy", self.on_destroy)
        self.view = WebKit2.WebView()
        self.view.get_settings().set_enable_javascript(True)
        self.view.connect("load-changed", self.on_load_changed)
        self.view.connect("load-failed", self.on_load_failed)
        self.window.add(self.view)
        self.window.show_all()
        self.window.resize(args.width, args.height)

    def on_destroy(self, *_):
        if self.error is None and len(self.states) != len(self.steps):
            self.error = RuntimeError("Window closed before completing native WebKit probe")
        self.main_loop.quit()

    def on_load_failed(self, _view, event, uri, error):
        self.fail(f"WebKit load failed: event={event} uri={uri}: {error}")
        return False

    def fail(self, message):
        self.error = str(message)
        self.main_loop.quit()
        return False

    def on_load_changed(self, _view, event):
        if event == WebKit2.LoadEvent.FINISHED:
            GLib.timeout_add(400, self.next_step)

    def screenshot(self, name: str):
        target = self.args.output / (
            f"webkitgtk-{self.args.fixture}-{self.args.width}x{self.args.height}-{self.args.state}-{name}.png"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        window = self.window.get_window()
        assert window is not None, "No GDK window"
        gdk_window_width = window.get_width()
        gdk_window_height = window.get_height()
        assert (gdk_window_width, gdk_window_height) == (
            self.args.width, self.args.height
        ), (gdk_window_width, gdk_window_height)
        pixels = Gdk.pixbuf_get_from_window(
            window, 0, 0, self.args.width, self.args.height
        )
        assert pixels is not None, "No GDK pixel buffer from actual WebKit window"
        assert (pixels.get_width(), pixels.get_height()) == (
            self.args.width, self.args.height
        )
        pixels.savev(str(target), "png", [], [])
        assert target.stat().st_size > 2000, f"Blank or failed capture: {target}"
        self.captures[name] = {
            "path": str(target.relative_to(ROOT)),
            "sha256": hash_file(target),
            "bytes": target.stat().st_size,
        }

    def next_step(self):
        if self.error is not None:
            return False
        if self.step_index >= len(self.steps):
            self.main_loop.quit()
            return False
        name, script, _capture = self.steps[self.step_index]
        try:
            # Async native WebKit2 API, JavaScript executed in the actual
            # WebKit web process, not a mock interpreter or static HTML parse.
            self.view.run_javascript(script, None, self.on_js, name)
        except Exception:
            self.fail(traceback.format_exc())
        return False

    def on_js(self, view, task, name):
        try:
            result = view.run_javascript_finish(task)
            raw = result.get_js_value().to_string()
            state = json.loads(raw)
            checked_state(
                self.args.fixture, name, state, self.args.width, self.args.height
            )
            self.states[name] = state
            should_capture = self.steps[self.step_index][2]
            self.step_index += 1
            if should_capture:
                GLib.timeout_add(300, self.capture_then_continue, name)
            else:
                GLib.timeout_add(50, self.next_step)
        except Exception:
            self.fail(traceback.format_exc())

    def capture_then_continue(self, name):
        try:
            self.screenshot(name)
        except Exception:
            return self.fail(traceback.format_exc())
        return self.next_step()

    def run(self):
        GLib.timeout_add_seconds(30, self.timeout)
        self.view.load_uri(self.url)
        self.main_loop.run()
        self.window.destroy()
        if self.error:
            raise RuntimeError(self.error)
        assert len(self.states) == len(self.steps), self.states
        return self.states, self.captures

    def timeout(self):
        return self.fail("Native WebKitGTK run did not finish within 30s")


def baseline_report(args, states, captures, requested_paths, version):
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text())
    features = manifest["fixtures"][args.fixture]["features"]
    coverage = {feature: "untested" for feature in features}
    if states.get("initial", {}).get("styles", {}).get("mainGrid") == "grid":
        coverage["grid"] = "direct" if "grid" in coverage else "untested"
    if args.fixture == "controls":
        coverage["select"] = "direct"
        coverage["inputs"] = "partial"  # JS setters, NOT OS key/IME.
    if args.fixture == "interaction":
        coverage["pointer"] = "partial"  # scripted Element.click(), not X11 pointer.
        coverage["keyboard"] = "partial"  # constructed KeyboardEvent, not X11 key.
    report = {
        "schema": "calyra.adapter-result.v1",
        "adapter": {"id": "webkit2gtk-system-backend-reference",
                    "version": version, "kind": "system-webview"},
        "fixture": {"name": args.fixture, "version": manifest["version"],
                    "width_css_px": args.width, "height_css_px": args.height,
                    "state": args.state, "motion": "off"},
        "source": {"html_sha256": hash_file(FIXTURE_DIR / "index.html"),
                   "css_sha256": hash_file(FIXTURE_DIR / "reference.css"),
                   "js_sha256": hash_file(FIXTURE_DIR / "reference.js"),
                   "css_modified": False, "dom_patched": False, "js_executed": True,
                   "external_network_used": False, "adaptations": [
                       "Unmodified HTML/CSS/JS served verbatim from local HTTP only",
                       "Harness-only asynchronous WebKit JavaScript probes and synthetic DOM events",
                       "GDK pixels from an undecorated GTK3 WebKit2GTK desktop window",
                   ]},
        "environment": {"os": platform.platform(), "architecture": platform.machine(),
                        "python_version": platform.python_version()},
        "execution": {"browser_engine": True, "gpu_backed": False, "interactive": True,
                      "render_backend": "WebKit2GTK-4.1 / GTK3 / X11 / virtual display; GPU not verified"},
        "capture": {"success": bool(captures), "page_count": 1,
                    "png_paths": [x["path"] for x in captures.values()],
                    "pdf_path": None, "pixel_scale": 1.0,
                    "measured_performance": False},
        "coverage": coverage,
        "eligibility": "restricted",
        "limitations": [
            "Linux WebKitGTK system browser backend; NOT a packaged Tauri app or macOS WKWebView",
            "Viewport/GTK screenshot tested, but OS user input, native accessibility, IME and keyboard traversal NOT tested",
            "JS scripted click/keydown is not physical or synthetic OS-level input",
            "Xvfb compositor may rasterize in software; no hardware GPU performance claim",
            "Single smoke pass per scene; no repetitions, RSS/process tree, startup/idle metrics or comparative speed claim",
            "CSS property support is not pixel-fidelity verification against Chromium",
        ],
    }
    extra = {
        "schema": "calyra.webkitgtk-reference-probe.v1",
        "engine_class": "linux-system-webview-backend-not-tauri",
        "webkit_version": version,
        "fixture": args.fixture, "viewport_css_px": [args.width, args.height],
        "motion": "off", "state": args.state,
        "scripted_steps": list(states),
        "scripted_input_class": "javascript-dom-synthetic-not-os",
        "states": states, "captures": captures,
        "requested_local_paths": sorted(set(requested_paths)),
        "required_assets_observed": all(
            p in requested_paths for p in ("/", "/reference.css", "/reference.js")
        ),
    }
    return report, extra


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True,
                        choices=("controls", "dashboard", "visual", "interaction"))
    parser.add_argument("--state", choices=("default", "menu-open"), default="default")
    parser.add_argument("--width", type=int, default=1060)
    parser.add_argument("--height", type=int, default=800)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "system-webview-stage-a")
    args = parser.parse_args()
    assert 320 <= args.width <= 1900 and 320 <= args.height <= 1100
    assert args.state == "default" or args.fixture == "interaction"
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    QuietFixtureServer.requested_paths = []
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietFixtureServer, directory=str(FIXTURE_DIR))
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        version = ".".join(str(x) for x in (
            WebKit2.get_major_version(), WebKit2.get_minor_version(),
            WebKit2.get_micro_version(),
        ))
        query = f"?fixture={args.fixture}&motion=off"
        if args.state != "default":
            query += f"&state={args.state}"
        url = f"http://127.0.0.1:{server.server_port}/{query}"
        states, captures = WebKitFixtureRun(args, url).run()
        record, evidence = baseline_report(
            args, states, captures, QuietFixtureServer.requested_paths, version
        )
        assert evidence["required_assets_observed"], evidence["requested_local_paths"]
        from jsonschema import validate
        validate(record, json.loads(CONTRACT.read_text(encoding="utf-8")))
        label = f"webkitgtk-{args.fixture}-{args.width}x{args.height}-{args.state}"
        (args.output / f"{label}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (args.output / f"{label}-probe.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "engine": "system-WebKitGTK-4.1", "version": version,
            "fixture": args.fixture, "steps": list(states),
            "captures": len(captures), "asset_paths": evidence["requested_local_paths"],
            "eligibility": record["eligibility"], "os_input_tested": False,
            "gpu_performance_tested": False,
        }))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
