"""Pixel comparison smoke tests; NOT an engine compatibility test."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compare_static', ROOT / 'native/blitz/compare_static.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComparisonTests(unittest.TestCase):
    def test_identical_images_have_zero_difference(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            Image.new('RGB', (320, 320), '#151c23').save(d / 'a.png')
            result = module.compare(d / 'a.png', d / 'a.png', d / 'out.png')
            self.assertEqual(result['rgb_mean_absolute_difference_0_to_255'], 0)
            self.assertEqual(result['changed_pixel_fraction_threshold_32'], 0)
            self.assertTrue(result['not_a_css_compatibility_score'])
            self.assertTrue((d / 'out.png').exists())
            self.assertTrue((d / 'out.json').exists())

    def test_changed_pixels_are_reported_without_claiming_css_support(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            Image.new('RGB', (320, 320), '#000000').save(d / 'a.png')
            candidate = Image.new('RGB', (320, 320), '#000000')
            candidate.paste((255, 255, 255), (0, 0, 100, 100))
            candidate.save(d / 'b.png')
            result = module.compare(d / 'a.png', d / 'b.png', d / 'out.png')
            self.assertAlmostEqual(result['changed_pixel_fraction_threshold_32'], 10000/(320**2), places=5)
            self.assertGreater(result['rgb_mean_absolute_difference_0_to_255'], 0)

    def test_size_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            Image.new('RGB', (320, 320)).save(d / 'a.png')
            Image.new('RGB', (320, 321)).save(d / 'b.png')
            with self.assertRaisesRegex(ValueError, 'Incomparable viewport geometry'):
                module.compare(d / 'a.png', d / 'b.png', d / 'out.png')

if __name__ == '__main__':
    unittest.main()
