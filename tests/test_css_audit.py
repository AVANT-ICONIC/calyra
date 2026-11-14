"""CALYRA source-audit tests. No renderer execution is asserted."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harness.css_audit import audit,declarations,evidence

class CssSourceAuditTests(unittest.TestCase):
    def test_recursive_media_query(self):
        rows=declarations(".a{display:grid}@media(max-width:420px){.a{display:flex;gap:4px}}")
        self.assertEqual(len(rows),3)
        self.assertIn("@media",rows[-1]["condition"])
    def test_grid_is_not_directly_compatible(self):
        self.assertEqual(evidence("display","grid")[0],"documented-incompatible")
        self.assertEqual(evidence("grid-template-columns","1fr 2fr")[0],"documented-incompatible")
        self.assertEqual(evidence("display","flex")[0],"documented-property-only")
    def test_value_adaptations(self):
        self.assertEqual(evidence("background","radial-gradient(red,blue)")[0],"documented-difference")
        self.assertEqual(evidence("font-family","Inter,Arial")[0],"documented-difference")
        self.assertEqual(evidence("unknown","10px")[0],"unverified")
    def test_real_fixture_and_provenance(self):
        result=audit()
        self.assertGreater(result["declaration_count"],130)
        self.assertGreater(result["unique_property_count"],35)
        self.assertGreater(len(result["risks"]),3)
        self.assertIn("no backend was run",result["claim"])
    def test_unknown_is_not_fabricated(self):
        items=declarations(".a{display:grid;color:red;custom-xyz:3}")
        self.assertEqual(len(items),3)
        self.assertEqual(evidence(items[-1]["property"],items[-1]["value"])[0],"unverified")

if __name__=="__main__":
    unittest.main()
