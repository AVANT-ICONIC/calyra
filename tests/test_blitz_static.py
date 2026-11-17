"""Local static/validation checks; do not imply native Blitz built or rendered."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from native.blitz.prepare_static import FIXTURE_NAMES, generate, sha256, exactly_once


class BlitzSnapshotTests(unittest.TestCase):
    def test_all_four_snapshots_keep_exact_source_css(self):
        css = (ROOT / "fixtures/reference.css").read_text(encoding="utf-8")
        canonical_html = (ROOT / "fixtures/index.html").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            for fixture in FIXTURE_NAMES:
                with self.subTest(fixture=fixture):
                    snapshot = generate(ROOT, Path(tmp), fixture)
                    output = (Path(tmp) / fixture / "index.html").read_text(encoding="utf-8")
                    self.assertIn('<style data-calyra-original-css="true">\n' + css + '\n</style>', output)
                    self.assertNotIn('<script src="./reference.js" defer></script>', output)
                    self.assertIn(f'<section class="case active" data-case="{fixture}"', output)
                    self.assertIn(f'<a data-link="{fixture}" aria-current="page"', output)
                    self.assertEqual(output.count('class="case active"'), 1)
                    self.assertEqual(output.count('aria-current="page"'), 1)
                    self.assertFalse(snapshot['css_bytes_changed'])
                    self.assertTrue(snapshot['html_patched'])
                    self.assertFalse(snapshot['javascript_executed'])
                    self.assertEqual(snapshot['canonical_sha256']['index.html'], sha256(canonical_html.encode()))
                    self.assertEqual(snapshot['generated_html_sha256'], sha256(output.encode()))
                    self.assertEqual(snapshot, json.loads((Path(tmp) / fixture / 'snapshot.json').read_text()))

    def test_unknown_fixture_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'Unknown fixture'):
                generate(ROOT, Path(tmp), 'unsafe')

    def test_missing_or_duplicate_source_marker_rejected(self):
        for html in ('', 'xabcabcx'):
            with self.assertRaisesRegex(ValueError, 'Expected exactly one'):
                exactly_once(html, 'abc', 'xyz')

    def test_rejects_external_css_and_unsafe_style_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / 'fixtures'
            d.mkdir()
            for name in ('index.html','reference.css','reference.js'):
                (d / name).write_bytes((ROOT / 'fixtures' / name).read_bytes())
            for css in ('@import url("https://example.com/x.css");',
                        'a{background:url(https://example.com/asset)}',
                        'a{content:"</style>"}'):
                with self.subTest(css=css):
                    (d / 'reference.css').write_text(css)
                    with self.assertRaises(ValueError):
                        generate(Path(tmp), Path(tmp) / 'out', 'controls')


if __name__ == '__main__':
    unittest.main()
