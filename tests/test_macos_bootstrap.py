"""Fail-closed tests for CI-free macOS preparation, not native GPU evidence."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from native.rmlui import bootstrap_macos
from harness import run_rmlui


class MacOsBootstrapTests(unittest.TestCase):
    def test_preflight_does_not_checkout_or_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'must-not-be-created'
            output = Path(tmp) / 'must-not-be-created-output'
            result = subprocess.run([
                sys.executable, str(ROOT / 'native/rmlui/bootstrap_macos.py'),
                '--source', str(source), '--output', str(output),
            ], capture_output=True, text=True, timeout=20)
            record = json.loads(result.stdout)
            self.assertFalse(record['attempted_native_build'])
            self.assertEqual(record['modes'], {})
            self.assertFalse(source.exists())
            self.assertFalse(output.exists())
            if sys.platform != 'darwin':
                self.assertEqual(result.returncode, 2)
                self.assertEqual(record['status'], 'blocked')
                self.assertIn('not macOS', ' '.join(record['preflight']['issues']))

    def test_nonmac_run_does_not_clone_even_when_opted_in(self):
        if sys.platform == 'darwin':
            self.skipTest('non-macOS guard only')
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'no-clone'
            result = subprocess.run([
                sys.executable, str(ROOT / 'native/rmlui/bootstrap_macos.py'),
                '--run', '--source', str(source),
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(source.exists())
            self.assertFalse(json.loads(result.stdout)['attempted_native_build'])

    def test_upstream_verification_rejects_impersonated_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / 'CMakeLists.txt').write_text('project(fake)')
            (fake / 'LICENSE.txt').write_text('fake')
            self.assertFalse(bootstrap_macos.verify_upstream(fake))

    def test_adapter_manifest_invalidated_when_cpp_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            exe = p / 'binary'
            exe.write_bytes(b'development test artifact')
            src = p / 'source'
            src.mkdir()
            (p / run_rmlui.PROVENANCE_FILE).write_text(json.dumps({
                'upstream_sha': run_rmlui.UPSTREAM_SHA,
                'source_root': str(src.resolve()),
                'binary_path': str(exe.resolve()),
                'binary_sha256': run_rmlui.hash_file(exe),
                'adapter_build_source_hashes': run_rmlui.adapter_build_source_hashes(),
            }))
            self.assertTrue(run_rmlui.read_provenance(p, src, exe)[0])
            with patch.object(run_rmlui, 'adapter_build_source_hashes', return_value={'probe.cpp': 'changed'}):
                valid, reason = run_rmlui.read_provenance(p, src, exe)
            self.assertFalse(valid)
            self.assertIn('CALYRA adapter source changed', reason)


if __name__ == '__main__':
    unittest.main()
