"""S8: public Python dependency SBOM/advisory validation, entirely offline."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from r07_s8_supplychain import (
    create_sbom, validate_public_audit, validate_sbom
)
LOCK = (Path(__file__).resolve().parents[1] / "requirements.lock").read_bytes()
SBOM = create_sbom(LOCK)


def audit_fixture():
    return {"dependencies": [
        {"name": c["name"], "version": c["version"], "vulns": []}
        for c in SBOM["components"]
    ]}


class SupplyChainTests(unittest.TestCase):
    def test_cyclonedx_is_deterministic_29_components(self):
        self.assertEqual(SBOM, create_sbom(LOCK))
        status = validate_sbom(SBOM, LOCK)
        self.assertEqual(status["python_components"], 29)
        self.assertFalse(status["wheel_hashes_verified"])
        self.assertFalse(status["base_image_os_components_included"])

    def test_sbom_tampered_package_is_rejected(self):
        other = json.loads(json.dumps(SBOM))
        other["components"][0]["version"] = "0.0.0"
        with self.assertRaisesRegex(ValueError, "SBOM_DRIFT"):
            validate_sbom(other, LOCK)

    def test_sbom_cannot_mask_lock_drift(self):
        with self.assertRaises(ValueError):
            validate_sbom(SBOM, LOCK + b"\n# synthetic drift\n")

    def test_all_pinned_packages_are_required_to_claim_clean(self):
        verdict = validate_public_audit(audit_fixture(), LOCK)
        self.assertTrue(verdict["clean"])
        self.assertEqual(verdict["analyzed_count"], 29)
        self.assertEqual(verdict["vulnerability_count"], 0)

    def test_incomplete_scan_must_fail_closed(self):
        report = audit_fixture()
        report["dependencies"].pop()
        with self.assertRaisesRegex(ValueError, "ADVISORY_AUDIT_INCOMPLETE"):
            validate_public_audit(report, LOCK)

    def test_duplicate_or_version_mismatch_must_fail_closed(self):
        report = audit_fixture()
        report["dependencies"][0] = report["dependencies"][1].copy()
        with self.assertRaisesRegex(ValueError, "ADVISORY_AUDIT_VERSION_OR_DUPLICATE"):
            validate_public_audit(report, LOCK)
        report = audit_fixture()
        report["dependencies"][0]["version"] = "0.0.0"
        with self.assertRaisesRegex(ValueError, "ADVISORY_AUDIT_VERSION_OR_DUPLICATE"):
            validate_public_audit(report, LOCK)

    def test_known_vulnerability_is_no_go(self):
        report = audit_fixture()
        report["dependencies"][0]["vulns"] = [
            {"id": "DEMO-VULNERABILITY-000", "fix_versions": ["99.0"]}
        ]
        verdict = validate_public_audit(report, LOCK)
        self.assertFalse(verdict["clean"])
        self.assertEqual(verdict["vulnerability_count"], 1)
        self.assertEqual(verdict["vulnerabilities"][0]["vulnerability_id"],
                         "DEMO-VULNERABILITY-000")

    def test_unknown_or_malformed_report_must_not_be_clean(self):
        with self.assertRaisesRegex(ValueError, "ADVISORY_AUDIT_INVALID"):
            validate_public_audit({}, LOCK)
        report = audit_fixture()
        del report["dependencies"][0]["vulns"]
        with self.assertRaisesRegex(ValueError, "ADVISORY_AUDIT_MISSING_VULNS"):
            validate_public_audit(report, LOCK)


if __name__ == "__main__":
    unittest.main()
