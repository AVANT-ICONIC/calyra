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


if __name__ == '__main__':
    unittest.main()

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
