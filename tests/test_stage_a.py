"""Contract + real browserless STATIC renderer tests, no Chromium or Actions."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.run_stage_a import run_weasyprint, prepare_markup, CONTRACT_PATH

from jsonschema import validate, ValidationError
from PIL import Image, ImageStat


class StageAContractTests(unittest.TestCase):
    def test_schema_requires_backend_and_provenance(self):
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["properties"]["schema"]["const"], "calyra.adapter-result.v1")
        self.assertIn("external_network_used", data["properties"]["source"]["required"])
        self.assertIn("browser_engine", data["properties"]["execution"]["required"])
        self.assertIn("untested", data["properties"]["coverage"]["additionalProperties"]["enum"])

    def test_invalid_viewport_and_state_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_weasyprint("controls", 100, 900, "default", Path(tmp))
            with self.assertRaises(ValueError):
                run_weasyprint("controls", 390, 844, "menu-open", Path(tmp))

    def test_static_state_is_explicit_and_scripts_absent(self):
        content = prepare_markup("interaction", "menu-open")
        self.assertNotIn("<script", content)
        self.assertIn('data-ready="static-document"', content)
        self.assertIn('aria-expanded="true"', content)
        self.assertIn('data-motion="off"', content)

    def test_software_renderer_real_pixels_and_contract(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "evidence") as tmp:
            output = Path(tmp)
            report = run_weasyprint("visual", 1440, 900, "default", output)
            self.assertEqual(report["adapter"]["kind"], "document-only")
            self.assertFalse(report["execution"]["browser_engine"])
            self.assertFalse(report["execution"]["gpu_backed"])
            self.assertFalse(report["execution"]["interactive"])
            self.assertFalse(report["source"]["css_modified"])
            self.assertFalse(report["source"]["js_executed"])
            self.assertEqual(report["eligibility"], "restricted")
            self.assertTrue(report["capture"]["success"])
            self.assertGreaterEqual(report["capture"]["page_count"], 1)
            validate(report, json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
            with Image.open(ROOT / report["capture"]["png_paths"][0]) as image:
                self.assertEqual(image.size, (1440, 900))
                # This is rendered output, not an empty/solid-color placeholder.
                self.assertGreater(max(ImageStat.Stat(image.convert("RGB")).stddev), 15)

if __name__ == "__main__":
    unittest.main(verbosity=2)
