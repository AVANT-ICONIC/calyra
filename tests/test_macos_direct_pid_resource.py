"""Fail-closed direct macOS WKWebView PID-to-process metric verification."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from macos_direct_pid_resource_five_run import verify_and_sample

def row(pid, name):
    return {
        "pid":pid,"ppid":1,"rss_kib":128,"vsz_kib":900,
        "ps_cpu_percent_instantaneous":0.0,"comm":name
    }

APP="/private/tmp/calyra-tauri-reference"
WEB="/System/Library/.../com.apple.WebKit.WebContent"
NET="/System/Library/.../com.apple.WebKit.Networking"

def doc(web=11,network=12):
    return {
        "schema":"calyra.macos-native-wkwebview-pids.v1",
        "tauri_ui_process_pid":10,
        "webkit_webcontent_pid":web,
        "webkit_network_pid":network,
        "webkit_gpu_pid":None,
        "private_diagnostic_only":True,
        "canonical_html_css_js_unmodified":True,
    }

def fake_meta(_, pids):
    return {
        pid:{"responsible_pid":2,"resident_bytes":1000,
             "physical_footprint_bytes":500,"rusage_status":"ok"}
        for pid in pids
    }

class DirectPidTest(unittest.TestCase):
    def setUp(self):
        self.rows=[row(10,APP),row(11,WEB),row(12,NET)]
        self.patch=patch("macos_direct_pid_resource_five_run.probe_metadata",
                         side_effect=fake_meta)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_exact_real_webkit_process_names(self):
        got=verify_and_sample(doc(),10,self.rows,"unused")
        self.assertEqual(got["webcontent"]["direct_wkwebview_pid"],11)
        self.assertEqual(got["networking"]["direct_wkwebview_pid"],12)
        self.assertIsNone(got["gpu"])

    def test_networking_optional_without_fake_zero(self):
        got=verify_and_sample(doc(network=None),10,self.rows,"unused")
        self.assertIsNone(got["networking"])

    def test_pid_from_wrong_process_fails(self):
        bad=[row(10,APP),row(11,NET),row(12,NET)]
        with self.assertRaises(AssertionError):
            verify_and_sample(doc(),10,bad,"unused")

    def test_missing_webcontent_fails(self):
        with self.assertRaises(AssertionError):
            verify_and_sample(doc(web=None),10,self.rows,"unused")

    def test_foreign_ui_pid_fails(self):
        with self.assertRaises(AssertionError):
            verify_and_sample(doc(),999,self.rows,"unused")

    def test_duplicate_process_ids_fail(self):
        with self.assertRaises(AssertionError):
            verify_and_sample(doc(network=11),10,self.rows,"unused")

if __name__=="__main__":
    unittest.main()
