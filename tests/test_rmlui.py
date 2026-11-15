"""Static/preflight checks for CALYRA RmlUi native adapter.

These do NOT pretend to compile or execute the RmlUi GPU backend.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness import run_rmlui


class RmlUiStageATests(unittest.TestCase):
    def test_rml_fixture_is_xml_well_formed(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(ROOT / 'native' / 'rmlui' / 'controls.rml').getroot()
        self.assertEqual(root.tag, 'rml')
        self.assertIsNotNone(root.find('.//*[@id="apply"]'))
        self.assertIsNotNone(root.find('.//*[@id="person-name"]'))

    def test_adapted_rcss_has_no_browser_url_dependency(self):
        import tinycss2
        content = (ROOT / 'native' / 'rmlui' / 'controls.rcss').read_text()
        self.assertNotIn('http:', content)
        self.assertNotIn('https:', content)
        self.assertIn('ADAPTED RCSS', content)
        css = tinycss2.parse_stylesheet(content, skip_comments=True, skip_whitespace=True)
        self.assertFalse([x for x in css if x.type == 'error'])

    def test_runner_records_blocked_not_fabricated_native_success(self):
        with tempfile.TemporaryDirectory() as directory:
            cmd = [sys.executable, str(ROOT / 'harness' / 'run_rmlui.py'), '--output', directory]
            p = subprocess.run(cmd, text=True, capture_output=True, timeout=20)
            self.assertEqual(p.returncode, 2, p.stderr)
            doc = json.loads((Path(directory) / 'rmlui-direct-result.json').read_text())
            self.assertEqual(doc['eligibility'], 'blocked')
            self.assertFalse(doc['capture']['success'])
            self.assertFalse(doc['execution']['gpu_backed'])
            self.assertFalse(doc['execution']['interactive'])
            self.assertFalse(doc['source']['css_modified'])
            self.assertTrue(doc['source']['dom_patched'])
            self.assertEqual(doc['capture']['png_paths'], [])
            self.assertTrue(any('pinned RmlUi source not provided' in msg for msg in doc['limitations']))
            try:
                from jsonschema import validate
                schema = json.loads((ROOT / 'harness' / 'adapter-contract.schema.json').read_text())
                validate(doc, schema)
            except ImportError:
                pass

    def test_adapted_css_explicitly_not_direct(self):
        doc = run_rmlui.report_template('adapted')
        self.assertTrue(doc['source']['css_modified'])
        self.assertTrue(doc['source']['dom_patched'])
        self.assertTrue(any('hand-adapted RCSS' in a for a in doc['source']['adaptations']))

    def test_fake_checkout_is_rejected_without_running(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'CMakeLists.txt').write_text('project(fake)')
            (p / 'LICENSE.txt').write_text('not a RmlUi checkout')
            verified, _ = run_rmlui.is_pinned_checkout(p)
            self.assertFalse(verified)

    def test_cmake_preflight_fails_closed_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            p = subprocess.run(['cmake', '-S', str(ROOT / 'native' / 'rmlui'), '-B', directory],
                               text=True, capture_output=True, timeout=20)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn('Missing RmlUi source', p.stdout + p.stderr)

    def test_runtime_is_native_backend_not_css_simulator(self):
        cpp = (ROOT / 'native' / 'rmlui' / 'probe.cpp').read_text()
        cmake = (ROOT / 'native' / 'rmlui' / 'CMakeLists.txt').read_text()
        self.assertIn('Backend::Initialize', cpp)
        self.assertIn('context->Render()', cpp)
        self.assertIn('glReadPixels', cpp)
        self.assertIn('GLFW_GL3', cmake)
        self.assertNotIn('WebView', cmake)
        self.assertIn('std::unique_ptr<ApplyListener>', cpp)

class RmlUiVerificationGuardTests(unittest.TestCase):
    """Runner-only negative tests. These don't certify an upstream RmlUi build."""

    def test_software_gl_cannot_be_called_hardware_gpu(self):
        self.assertEqual(run_rmlui.gl_renderer_class('llvmpipe (LLVM 17.0, 256 bits)'), 'software')
        self.assertEqual(run_rmlui.gl_renderer_class('Google SwiftShader Vulkan'), 'software')
        self.assertEqual(run_rmlui.gl_renderer_class('NVIDIA GeForce RTX 3060'), 'hardware')
        self.assertEqual(run_rmlui.gl_renderer_class('Apple M1 Max'), 'hardware')
        self.assertEqual(run_rmlui.gl_renderer_class('Generic OpenGL Renderer'), 'unknown')
        self.assertEqual(run_rmlui.gl_renderer_class(''), 'unknown')

    def test_exact_output_markers_required(self):
        logs = 'CALYRA_NATIVE_FRAME=1060x740\nCALYRA_GL_RENDERER=llvmpipe\n'
        self.assertIsNone(run_rmlui.marker(logs, 'CALYRA_NATIVE_RENDER_OK'))
        self.assertIsNone(run_rmlui.marker(logs, 'CALYRA_NATIVE_CLICK'))
        self.assertEqual(run_rmlui.marker(logs, 'CALYRA_GL_RENDERER'), 'llvmpipe')

    def test_stale_or_modified_build_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            src = d / 'upstream'
            src.mkdir()
            exe = d / 'calyra_rmlui_probe'
            exe.write_bytes(b'executable A')
            self.assertEqual(run_rmlui.read_provenance(d, src, exe)[0], False)
            (d / run_rmlui.PROVENANCE_FILE).write_text(json.dumps({
                'upstream_sha': run_rmlui.UPSTREAM_SHA,
                'source_root': str(src.resolve()),
                'binary_path': str(exe.resolve()),
                'binary_sha256': run_rmlui.hash_file(exe),
            }))
            self.assertTrue(run_rmlui.read_provenance(d, src, exe)[0])
            exe.write_bytes(b'executable B')
            self.assertFalse(run_rmlui.read_provenance(d, src, exe)[0])

    def test_multiconfig_executable_path_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)
            (build / 'Release').mkdir()
            binary = build / 'Release' / 'calyra_rmlui_probe'
            binary.write_bytes(b'test artifact')
            self.assertEqual(run_rmlui.find_built_executable(build), binary.resolve())

    def test_cpp_smoke_requires_real_rmlui_event_dispatch_and_gl_identity(self):
        cpp = (ROOT / 'native' / 'rmlui' / 'probe.cpp').read_text()
        self.assertIn('context->ProcessMouseButtonDown(0, 0)', cpp)
        self.assertIn('context->ProcessMouseButtonUp(0, 0)', cpp)
        self.assertIn('glGetString(GL_RENDERER)', cpp)
        self.assertIn('CALYRA_NATIVE_CLICK=1', cpp)

class RmlUiRunnerMockBoundaryTests(unittest.TestCase):
    """End-to-end runner state-machine tests using a FAKE binary.

    These prove report classification only, not real native rendering.
    """
    def run_mock(self, renderer, clicked=True, stale_frame=False):
        import argparse
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            src = d / 'fake-source'
            src.mkdir()
            binary = d / 'fake-probe'
            font = d / 'fake-font.ttf'
            font.write_bytes(b'fake font; never loaded')
            script = '''#!/usr/bin/env python3
import sys
from pathlib import Path
p = Path(sys.argv[4])
p.write_bytes(b'P6\\n800 500\\n255\\n' + b'\\x10\\x20\\x30' * 200000 + b'\\x80\\x70\\x60' * 200000)
print('CALYRA_NATIVE_FRAME=800x500')
print('CALYRA_GL_RENDERER=%s')
print('CALYRA_GL_VENDOR=MockVendor')
print('CALYRA_INPUT_SOURCE=synthetic_rmlui_event')
%s
print('CALYRA_NATIVE_RENDER_OK=1')
''' % (renderer, "print('CALYRA_NATIVE_CLICK=1')" if clicked else 'pass')
            binary.write_text(script)
            binary.chmod(0o755)
            (d / run_rmlui.PROVENANCE_FILE).write_text(json.dumps({
                'upstream_sha': run_rmlui.UPSTREAM_SHA,
                'source_root': str(src.resolve()),
                'binary_path': str(binary.resolve()),
                'binary_sha256': run_rmlui.hash_file(binary),
            }))
            if stale_frame:
                (d / 'rmlui-direct-frame.ppm').write_bytes(b'old bogus frame')
            args = argparse.Namespace(output=str(d), source=str(src), binary=str(binary),
                                      font=str(font), mode='direct', build=False)
            with patch.object(run_rmlui, 'is_pinned_checkout', return_value=(True, '')):
                result = run_rmlui.run(args)
            report = json.loads((d / 'rmlui-direct-result.json').read_text())
            return result, report

    def test_mocked_software_renderer_is_not_gpu(self):
        rc, report = self.run_mock('llvmpipe (LLVM 17.0)')
        self.assertEqual(rc, 0)
        self.assertEqual(report['eligibility'], 'restricted')
        self.assertEqual(report['adapter']['kind'], 'browserless-software')
        self.assertFalse(report['execution']['gpu_backed'])
        self.assertTrue(report['execution']['interactive'])
        self.assertTrue(report['capture']['success'])

    def test_mocked_success_without_click_must_fail_closed(self):
        rc, report = self.run_mock('NVIDIA GeForce RTX 3060', clicked=False)
        self.assertEqual(rc, 2)
        self.assertEqual(report['eligibility'], 'blocked')
        self.assertFalse(report['execution']['gpu_backed'])
        self.assertFalse(report['execution']['interactive'])
        self.assertFalse(report['capture']['success'])
        self.assertTrue(any('click' in x.lower() for x in report['limitations']))

    def test_unknown_renderer_rejected_even_with_valid_mocked_frame(self):
        rc, report = self.run_mock('Generic OpenGL Renderer')
        self.assertEqual(rc, 2)
        self.assertEqual(report['eligibility'], 'blocked')
        self.assertFalse(report['capture']['success'])
        self.assertTrue(any('unknown GL renderer' in x for x in report['limitations']))

    def test_stale_frame_cannot_rescue_missing_click(self):
        rc, report = self.run_mock('NVIDIA GeForce RTX 3060', clicked=False, stale_frame=True)
        self.assertEqual(rc, 2)
        self.assertFalse(report['capture']['success'])


if __name__ == '__main__':
    unittest.main()
