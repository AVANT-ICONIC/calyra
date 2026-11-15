"""Stage A negative and output checks. These do not pretend to execute Blitz."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calyra_blitz_runner', ROOT/'native/blitz/run_stage_a.py')
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT/'native/blitz'))
spec.loader.exec_module(module)


class BlitzRunnerTests(unittest.TestCase):
    def test_blocked_without_source_and_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, report = module.run(ROOT, None, Path(tmp), 'controls')
            self.assertEqual(status, 2)
            self.assertEqual(report['eligibility'], 'blocked')
            self.assertEqual(report['adapter']['kind'], 'browserless-software')
            self.assertFalse(report['capture']['success'])
            self.assertTrue(report['source']['dom_patched'])
            self.assertFalse(report['source']['css_modified'])
            self.assertFalse(report['execution']['gpu_backed'])
            self.assertFalse(report['execution']['interactive'])
            self.assertEqual(report['capture']['png_paths'], [])
            self.assertTrue((Path(tmp)/'blitz-controls-result.json').is_file())
            from jsonschema import validate
            validate(report, json.loads((ROOT/'harness/adapter-contract.schema.json').read_text()))

    def test_rejects_stale_images_on_blocked_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for path in ('blitz-controls-raw.png','blitz-controls-viewport.png'):
                (d/path).write_bytes(b'stale')
            code, _ = module.run(ROOT, None, d, 'controls')
            self.assertEqual(code, 2)
            self.assertFalse((d/'blitz-controls-raw.png').exists())
            self.assertFalse((d/'blitz-controls-viewport.png').exists())

    def test_checks_real_raw_image_geometry_and_nonuniformity(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'raw.png'
            dst = Path(tmp)/'viewport.png'
            image = Image.new('RGB', (2120, 1600), (14, 19, 25))
            image.paste((198, 219, 116), (100, 100, 200, 200))
            image.save(src)
            info = module.verify_render(src, dst)
            self.assertEqual(info['viewport_px'], [1060, 800])
            with Image.open(dst) as result:
                self.assertEqual(result.size, (1060,800))
            Image.new('RGB', (2120,1600), (255,255,255)).save(src)
            with self.assertRaisesRegex(ValueError, 'uniform'):
                module.verify_render(src, dst)

    def test_filename_matches_pinned_upstream_algorithm(self):
        path = module.expected_png_location(Path('/source'), 'file:///tmp/my-fixture/index.html')
        self.assertEqual(path, Path('/source/examples/output/filetmpmyfix.png'))

if __name__ == '__main__':
    unittest.main()
