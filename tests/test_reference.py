"""Local Chromium reference checks, not native-engine performance measurements."""
import json
import os
import shutil
import unittest
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen
from urllib.parse import quote
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "fixtures/manifest.json").read_text())

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class ReferenceFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        executable = (os.environ.get("CALYRA_CHROMIUM_EXECUTABLE")
                      or shutil.which("chromium")
                      or shutil.which("google-chrome")
                      or shutil.which("chromium-browser"))
        launch_options = {"headless": True}
        if executable:
            launch_options["executable_path"] = executable
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            launch_options["args"] = ["--no-sandbox"]
        cls.browser = cls.playwright.chromium.launch(**launch_options)
        (ROOT / "evidence").mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        

    def page(self, fixture, width=1440, height=900, state=""):
        ctx = self.browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1, reduced_motion="reduce")
        self.addCleanup(ctx.close)
        p = ctx.new_page()
        extra = f"&state={quote(state)}" if state else ""
        html = (ROOT / "fixtures/index.html").read_text()
        html = html.replace('<link rel="stylesheet" href="./reference.css">', "")
        html = html.replace('<script src="./reference.js" defer></script>', "")
        p.set_content(html, wait_until="domcontentloaded")
        p.add_style_tag(content=(ROOT / "fixtures/reference.css").read_text())
        p.evaluate("q => { window.__calyraFixtureQuery = q }", f"?fixture={fixture}&motion=off{extra}")
        p.add_script_tag(content=(ROOT / "fixtures/reference.js").read_text())
        p.locator('body[data-ready="true"]').wait_for()
        return p

    def test_manifest(self):
        self.assertEqual(MANIFEST["schema"], "calyra.fixtures.v1")
        self.assertEqual(set(MANIFEST["fixtures"]), {"controls", "dashboard", "visual", "interaction"})
        for name in MANIFEST["canonicalFiles"]:
            self.assertTrue((ROOT / "fixtures" / name).is_file())

    def test_served_assets(self):
        """Validate actual same-origin static assets even when Chromium navigation is blocked."""
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            partial(QuietHandler, directory=str(ROOT / "fixtures")),
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for asset in MANIFEST["canonicalFiles"] + ["manifest.json"]:
                with self.subTest(asset=asset):
                    with urlopen(f"http://127.0.0.1:{server.server_address[1]}/{asset}", timeout=3) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.read(), (ROOT / "fixtures" / asset).read_bytes())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_cases_only_one_visible(self):
        for fixture in MANIFEST["fixtures"]:
            with self.subTest(fixture=fixture):
                p = self.page(fixture)
                self.assertEqual(p.locator(".case:visible").count(), 1)
                self.assertEqual(p.locator(".case:visible").first.get_attribute("data-case"), fixture)
                self.assertEqual(p.locator('[aria-current="page"]').count(), 1)

    def test_controls_inputs(self):
        p = self.page("controls")
        p.locator("#person-name").fill("Mara Novak")
        p.locator("#priority").select_option("quality")
        p.locator("#intensity").fill("73")
        self.assertEqual(p.locator("#intensity-output").evaluate("el => el.value"), "73%")
        p.locator("#effects").uncheck()
        p.locator("#apply").click()
        self.assertIn("Mara Novak · quality · 73% · off", p.locator("#action-status").evaluate("el => el.value"))
        p.locator("#reset").click()
        self.assertEqual(p.locator("#person-name").input_value(), "Alex Rivera")
        self.assertEqual(p.locator("#priority").input_value(), "balanced")
        self.assertTrue(p.locator("#effects").is_checked())

    def test_interaction_keyboard_escape(self):
        p = self.page("interaction")
        p.locator("#menu-toggle").click()
        self.assertEqual(p.locator("#menu-toggle").get_attribute("aria-expanded"), "true")
        self.assertTrue(p.locator("#menu-popover").is_visible())
        self.assertEqual(p.locator(":focus").get_attribute("data-command"), "inspect")
        p.keyboard.press("Escape")
        self.assertEqual(p.locator("#menu-toggle").get_attribute("aria-expanded"), "false")
        self.assertEqual(p.locator(":focus").get_attribute("id"), "menu-toggle")
        p.locator("#focus-target").click()
        self.assertEqual(p.locator(":focus").get_attribute("id"), "destination")
        p.locator("#scroll-region").evaluate("element => element.scrollTop = 500")
        self.assertGreater(p.locator("#scroll-region").evaluate("element => element.scrollTop"), 0)

    def test_snapshot_state(self):
        p = self.page("interaction", state="menu-open")
        self.assertEqual(p.locator("#menu-toggle").get_attribute("aria-expanded"), "true")
        self.assertTrue(p.locator("#menu-popover").is_visible())
        self.assertEqual(p.locator(":root").get_attribute("data-motion"), "off")

    def test_no_horizontal_overflow(self):
        for width,height in ((1440,900),(900,900),(650,850),(390,844),(320,700)):
            for fixture in MANIFEST["fixtures"]:
                with self.subTest(width=width,fixture=fixture):
                    p = self.page(fixture, width, height)
                    sizes = p.evaluate("({ viewport: document.documentElement.clientWidth, width: document.documentElement.scrollWidth })")
                    self.assertLessEqual(sizes["width"], sizes["viewport"]+1, str(sizes))

    def test_reference_capture(self):
        for width,height,label in ((1440,900,"desktop"),(390,844,"mobile")):
            for fixture in MANIFEST["fixtures"]:
                p = self.page(fixture, width, height)
                target = ROOT / "evidence" / f"{fixture}-{label}.png"
                p.screenshot(path=str(target), full_page=True, animations="disabled")
                self.assertGreater(target.stat().st_size, 1500)

if __name__ == "__main__":
    unittest.main(verbosity=2)
