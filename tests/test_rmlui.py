"""CALYRA RmlUi 6.3 Stage A offline contract tests (not native GPU results)."""
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness import run_rmlui

class RmlUiStageATests(unittest.TestCase):
    def test_rml_markup_well_formed(self):
        root = ET.parse(ROOT / "native" / "rmlui" / "controls.rml").getroot()
        self.assertEqual(root.tag, "rml")
        self.assertIsNotNone(root.find('.//*[@id="apply"]'))
        self.assertIsNotNone(root.find('.//*[@id="person-name"]'))

    def test_adapted_rcss_parses_as_stylesheet(self):
        import tinycss2
        content = (ROOT / "native" / "rmlui" / "controls.rcss").read_text()
        self.assertIn("ADAPTED RCSS", content)
        rules = tinycss2.parse_stylesheet(content, skip_whitespace=True, skip_comments=True)
        self.assertFalse([r for r in rules if r.type == "error"])

    def test_blocked_without_source(self):
        with tempfile.TemporaryDirectory() as td:
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "run_rmlui.py"),
                                "--output", td], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 2, p.stderr)
            result = json.loads((Path(td) / "rmlui-direct-result.json").read_text())
            self.assertEqual(result["eligibility"], "blocked")
            self.assertFalse(result["capture"]["success"])
            self.assertFalse(result["execution"]["gpu_backed"])
            self.assertFalse(result["execution"]["interactive"])
            self.assertFalse(result["source"]["css_modified"])
            self.assertTrue(result["source"]["dom_patched"])
            self.assertEqual(result["capture"]["png_paths"], [])
            self.assertIn("pinned RmlUi source not supplied", " ".join(result["limitations"]))
            try:
                from jsonschema import validate
                schema = json.loads((ROOT / "harness" / "adapter-contract.schema.json").read_text())
                validate(result, schema)
            except ImportError:
                pass

    def test_adapter_modes_are_reported_differently(self):
        direct = run_rmlui.result_template("direct")
        adapted = run_rmlui.result_template("adapted")
        self.assertFalse(direct["source"]["css_modified"])
        self.assertTrue(adapted["source"]["css_modified"])
        self.assertTrue(direct["source"]["dom_patched"])
        self.assertTrue(adapted["source"]["dom_patched"])

    def test_reject_unpinned_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "CMakeLists.txt").write_text("project(fake)")
            (folder / "LICENSE.txt").write_text("fake")
            valid, _ = run_rmlui.verified_source(folder)
            self.assertFalse(valid)

    def test_cmake_fails_cleanly_without_upstream(self):
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run(["cmake", "-S", str(ROOT / "native" / "rmlui"), "-B", td],
                                    capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing RmlUi source", result.stdout + result.stderr)

    def test_gpu_probe_not_a_webview_simulator(self):
        cpp = (ROOT / "native" / "rmlui" / "probe.cpp").read_text()
        cm = (ROOT / "native" / "rmlui" / "CMakeLists.txt").read_text()
        self.assertIn("Backend::Initialize", cpp)
        self.assertIn("context->Render()", cpp)
        self.assertIn("glReadPixels", cpp)
        self.assertIn("std::unique_ptr<ApplyListener>", cpp)
        self.assertIn("GLFW_GL3", cm)
        self.assertNotIn("WebView", cm)

if __name__ == "__main__":
    unittest.main()
