"""Deterministic ownership semantics; no macOS required for classification QA."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from macos_webkit_attribution import classify  # noqa: E402

WEB = "/System/Library/Frameworks/WebKit.framework/.../com.apple.WebKit.WebContent"
NET = "/System/Library/Frameworks/WebKit.framework/.../com.apple.WebKit.Networking"


def row(pid, parent, name="app"):
    return {
        "pid": pid, "ppid": parent, "comm": name,
        "rss_kib": 100, "vsz_kib": 500,
        "ps_cpu_percent_instantaneous": 0.0,
    }


class AttributionTests(unittest.TestCase):
    def test_launchd_helper_confirmed_only_by_responsibility(self):
        before = [row(1, 0), row(3, 1, WEB)]
        during = before + [row(100, 1, "calyra-tauri-reference"),
                           row(105, 1, WEB), row(106, 1, NET)]
        results = classify(before, during, 100, {
            105: {"responsible_pid": 100}, 106: {"responsible_pid": None}
        })
        self.assertEqual([x["pid"] for x in results["confirmed"]], [105])
        self.assertEqual([x["pid"] for x in results["new_unconfirmed"]], [106])
        self.assertEqual([x["pid"] for x in results["preexisting_unassigned"]], [3])

    def test_real_child_confirmed_without_private_api(self):
        before = [row(1, 0)]
        during = before + [row(200, 1), row(201, 200, WEB)]
        results = classify(before, during, 200, {})
        self.assertEqual(results["confirmed"][0]["classification"],
                         "confirmed_parent_lineage")

    def test_preexisting_webkit_process_never_assigned(self):
        before = [row(1, 0), row(300, 1, WEB)]
        during = before + [row(400, 1)]
        results = classify(before, during, 400, {
            300: {"responsible_pid": 400}
        })
        self.assertEqual(results["confirmed"], [])
        self.assertEqual(results["preexisting_unassigned"][0]["pid"], 300)

    def test_new_other_application_webkit_process_is_not_claimed(self):
        before = [row(1, 0)]
        during = before + [row(501, 1), row(502, 1, WEB)]
        results = classify(before, during, 501, {
            502: {"responsible_pid": 111}
        })
        self.assertEqual(results["confirmed"], [])
        self.assertEqual(results["new_unconfirmed"][0]["pid"], 502)

    def test_existing_target_process_fails_closed(self):
        with self.assertRaises(AssertionError):
            classify([row(3, 1)], [row(3, 1)], 3, {})


if __name__ == "__main__":
    unittest.main()
