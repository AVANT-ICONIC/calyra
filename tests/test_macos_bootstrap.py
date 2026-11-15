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

    def test_private_vendor_checkout_is_gitignored(self):
        ignores = (ROOT / '.gitignore').read_text().splitlines()
        self.assertIn('.local/', ignores)
        self.assertIn('evidence/', ignores)

    def test_missing_python_dependencies_are_fail_closed(self):
        with patch.object(bootstrap_macos, 'find_spec', side_effect=lambda name: None if name == 'PIL' else object()):
            record, _ = bootstrap_macos.check_environment(Path('/nonexistent/font.ttf'))
        self.assertFalse(record['python_modules']['PIL'])
        self.assertFalse(record['ready'])
        self.assertIn('missing Python dependency: PIL', ' '.join(record['issues']))

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

class MacOsDualModeEvidenceTests(unittest.TestCase):
    """Exercise the actual macOS entrypoint orchestration without native GPU claims."""

    def test_direct_css_failure_does_not_skip_adapted_native_renderer(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'pinned-upstream'
            source.mkdir()
            output = root / 'out'
            calls = []

            def native_runner(cmd, *, timeout, env):
                mode = cmd[cmd.index('--mode') + 1]
                calls.append(mode)
                outcome = mode == 'adapted'
                (output / f'rmlui-{mode}-result.json').write_text(json.dumps({
                    'eligibility': 'restricted' if outcome else 'blocked',
                    'capture': {'success': outcome},
                    'execution': {'render_backend': 'RmlUi / real test would report GL'},
                }))
                return subprocess.CompletedProcess(cmd, 0 if outcome else 2, stdout='', stderr='')

            args = SimpleNamespace(run=True, source=str(source), output=str(output),
                                   font=None, timeout=20)
            with patch.object(bootstrap_macos, 'check_environment',
                              return_value=({'ready': True}, {})), \
                 patch.object(bootstrap_macos, 'verify_upstream', return_value=True), \
                 patch.object(bootstrap_macos, 'execute', side_effect=native_runner), \
                 patch.object(bootstrap_macos, 'choose_font', return_value=root / 'font.ttf'):
                self.assertEqual(bootstrap_macos.run(args), 1)
            self.assertEqual(calls, ['direct', 'adapted'])
            summary = json.loads((output / 'macos-preflight-summary.json').read_text())
            self.assertEqual(summary['status'], 'partial')
            self.assertEqual(summary['successful_modes'], 1)
            self.assertFalse(summary['modes']['direct']['native_capture'])
            self.assertTrue(summary['modes']['adapted']['native_capture'])

    def test_stale_report_and_nonzero_runner_never_count_as_native_capture(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'pinned-upstream'
            source.mkdir()
            output = root / 'out'
            output.mkdir()
            for mode in ('direct', 'adapted'):
                (output / f'rmlui-{mode}-result.json').write_text(json.dumps({
                    'eligibility': 'restricted', 'capture': {'success': True},
                    'execution': {'render_backend': 'fabricated'},
                }))
            calls = []
            def failing_runner(cmd, *, timeout, env):
                calls.append(cmd[cmd.index('--mode') + 1])
                return subprocess.CompletedProcess(cmd, 2, stdout='', stderr='')
            args = SimpleNamespace(run=True, source=str(source), output=str(output),
                                   font=None, timeout=20)
            with patch.object(bootstrap_macos, 'check_environment',
                              return_value=({'ready': True}, {})), \
                 patch.object(bootstrap_macos, 'verify_upstream', return_value=True), \
                 patch.object(bootstrap_macos, 'execute', side_effect=failing_runner), \
                 patch.object(bootstrap_macos, 'choose_font', return_value=root / 'font.ttf'):
                self.assertEqual(bootstrap_macos.run(args), 2)
            self.assertEqual(calls, ['direct', 'adapted'])
            self.assertFalse((output / 'rmlui-direct-result.json').exists())
            self.assertFalse((output / 'rmlui-adapted-result.json').exists())
            summary = json.loads((output / 'macos-preflight-summary.json').read_text())
            self.assertEqual(summary['status'], 'blocked')
            self.assertEqual(summary['successful_modes'], 0)
