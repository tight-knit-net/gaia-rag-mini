"""S9 synthetic OS CycloneDX and security scan tests; no network."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from r07_s9_os_audit import installed_os_inventory, build_os_sbom, inspect_os_scan

PACKAGES = "\n".join(
    f"demo-pkg-{i:02d}\t1.{i}-1\tamd64" for i in range(1, 28)
)


def scan(findings=None):
    return {
        "ArtifactType": "container_image",
        "Results": [
            {"Target": "gaia-r07-demo (debian 12)", "Class": "os-pkgs",
             "Type": "debian", "Vulnerabilities": findings or []}
        ],
    }


class OSScanTests(unittest.TestCase):
    def test_os_inventory_requires_multiple_os_packages(self):
        packages = installed_os_inventory(PACKAGES)
        self.assertEqual(len(packages), 27)

    def test_os_sbom_deterministic_and_honest(self):
        sbom = build_os_sbom(PACKAGES)
        self.assertEqual(sbom, build_os_sbom(PACKAGES))
        self.assertEqual(sbom["specVersion"], "1.6")
        self.assertEqual(len(sbom["components"]), 27)
        self.assertEqual(sbom["metadata"]["component"]["properties"][1]["value"],
                         "installed-debian-packages-only")

    def test_malformed_dpkg_inventory_fail_closed(self):
        with self.assertRaises(ValueError):
            installed_os_inventory(PACKAGES + "\nmalformed")

    def test_duplicate_os_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OS_PACKAGE"):
            installed_os_inventory(PACKAGES + "\ndemo-pkg-01\t1.1-1\tamd64")

    def test_empty_and_non_container_reports_rejected(self):
        for payload in ({}, {"ArtifactType": "repository", "Results": []}):
            with self.assertRaises(ValueError):
                inspect_os_scan(payload)

    def test_report_without_actual_os_results_rejected(self):
        with self.assertRaisesRegex(ValueError, "OS_SCAN_NO_OS_COVERAGE"):
            inspect_os_scan({"ArtifactType": "container_image",
                             "Results": [{"Class": "lang-pkgs"}]})

    def test_zero_os_vulnerabilities_is_eligible_only_for_ci(self):
        result = inspect_os_scan(scan())
        self.assertTrue(result["ready_for_supply_chain_gate"])
        self.assertFalse(result["production_homologated"])

    def test_high_os_vulnerability_causes_no_go(self):
        findings = [{"VulnerabilityID": "DEMO-CVE-2026-999",
                     "Severity": "HIGH", "PkgName": "libc6",
                     "InstalledVersion": "demo", "FixedVersion": "fixed"}]
        result = inspect_os_scan(scan(findings))
        self.assertFalse(result["ready_for_supply_chain_gate"])
        self.assertEqual(result["os_blocking_findings"], 1)


if __name__ == "__main__":
    unittest.main()
