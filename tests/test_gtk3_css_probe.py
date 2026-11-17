"""Real Gtk3 widget/CSS probe. No browser, no fake screenshot, no GPU claim."""
from __future__ import annotations
import ctypes as C
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest

from PIL import Image, ImageStat
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapters.gtk3_css_probe import Gtk3NativeProbe, select_native_styles, V, UI

class GdkRGBA(C.Structure):
    _fields_ = [('red', C.c_double), ('green', C.c_double), ('blue', C.c_double), ('alpha', C.c_double)]

@unittest.skipUnless(os.environ.get('DISPLAY'), 'Real GTK3 X11 display required; use xvfb-run -a')
class NativeGtk3CssTests(unittest.TestCase):
    def setUp(self):
        self.app = Gtk3NativeProbe()

    def tearDown(self):
        self.app.close()

    def test_canonical_css_extraction_is_explicitly_partial(self):
        css, tokens, extracted = select_native_styles()
        self.assertEqual(tokens['--accent'], '#c6db74')
        self.assertIn('button.action.primary', css)
        self.assertGreaterEqual(len(extracted), 5)
        self.assertNotIn('grid-template-columns', css)
        self.assertNotIn('backdrop-filter', css)

    def test_native_provider_actually_applies_css(self):
        rgba = GdkRGBA()
        getter = self.app.gtk.gtk_style_context_get_background_color
        getter.restype = None
        getter.argtypes = [V, UI, C.POINTER(GdkRGBA)]
        getter(self.app.gtk_widget_get_style_context(self.app.apply_button), 0, C.byref(rgba))
        self.assertAlmostEqual(rgba.red, 198/255, places=3)
        self.assertAlmostEqual(rgba.green, 219/255, places=3)
        self.assertAlmostEqual(rgba.blue, 116/255, places=3)

    def test_native_widget_signals_change_state(self):
        self.app.gtk_entry_set_text(self.app.entry, b'Ada Lovelace')
        self.app.gtk_combo_box_set_active(self.app.combo, 2)
        self.app.gtk_range_set_value(self.app.scale, 87)
        self.app.emit_apply()
        self.assertEqual(self.app.get_status(), 'Saved: Ada Lovelace / Performance / 87%')
        self.app.emit_reset()
        self.assertEqual(self.app.get_status(), 'Reset to defaults')
        self.assertEqual(self.app.gtk_entry_get_text(self.app.entry), b'Alex Rivera')

    def test_native_screenshot_and_result_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / 'native-gtk.png'
            dimensions = self.app.screenshot(image)
            self.assertEqual(dimensions, [840,680])
            with Image.open(image) as im:
                self.assertEqual(im.size, (840,680))
                self.assertGreater(max(ImageStat.Stat(im.convert('RGB')).stddev), 30)
            obj = self.app.record(image, dimensions)
            schema = json.loads((ROOT / 'harness' / 'adapter-contract.schema.json').read_text())
            jsonschema.validate(obj, schema)
            self.assertFalse(obj['execution']['browser_engine'])
            self.assertFalse(obj['execution']['gpu_backed'])
            self.assertEqual(obj['eligibility'], 'restricted')
            self.assertTrue(obj['source']['dom_patched'])
            self.assertEqual(obj['coverage']['css-grid'], 'unsupported')

if __name__ == '__main__': unittest.main()
