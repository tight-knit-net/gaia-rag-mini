"""S9.1 synthetic-only comparative OS scan contracts (no real CVE bypass)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from r07_s9_1_compare_os import compare

REF = "python@sha256:" + "a"*64
def demo(findings=None):
    return {
        "descriptor":{"name":"grype"},
        "source":{"type":"image"},
        "distro":{"name":"debian","version":"13"},
        "matches":findings or [],
    }
def finding(ident="CVE-2026-DEMO",sev="High",name="libssl3t64",fix=None):
    return {"artifact":{"type":"deb","name":name,"version":"1.0"},
            "vulnerability":{"id":ident,"severity":sev,"fix":{"versions":fix or []}}}


class ComparisonTests(unittest.TestCase):
    def test_good_scan_no_findings_stays_research_only(self):
        o=compare(demo(),REF,"slim-trixie")
        self.assertTrue(o["candidate_eligible"])
        self.assertTrue(o["CI_comparison_only"])
        self.assertFalse(o["production_deployed"])
        self.assertFalse(o["ignore_rules_used"])

    def test_blockers_are_distinct_per_cve_not_package(self):
        o=compare(demo([finding(name="openssl"),finding(name="libssl3t64")]),
                  REF,"slim-trixie")
        self.assertEqual(o["os_blocking_matches"],2)
        self.assertEqual(o["unique_blocking_cves"],1)
        self.assertFalse(o["candidate_eligible"])

    def test_fix_versions_are_reported_not_automatically_applied(self):
        o=compare(demo([finding(fix=["2.0"])]),REF,"slim-bookworm")
        self.assertEqual(o["cves"][0]["scanner_fix_versions"],["2.0"])
        self.assertFalse(o["wheel_hash_change_authorized"])

    def test_digest_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,"IMMUTABLE"):
            compare(demo(),"python:3.12-slim","slim-bookworm")

    def test_only_supported_variants(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED"):
            compare(demo(),REF,"alpine")

    def test_wrong_distro_or_missing_report_fails_closed(self):
        bad=demo()
        bad["distro"]["name"]="ubuntu"
        with self.assertRaisesRegex(ValueError,"OS_SCAN_WRONG"):
            compare(bad,REF,"slim-trixie")
        with self.assertRaises(ValueError):
            compare({},REF,"slim-bookworm")


if __name__=="__main__":
    unittest.main()
