"""S9.2 official stable-only upgrade trial contract tests, all synthetic."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from r07_s92_stable_update import trial_dockerfile, compare

ROOT = Path(__file__).resolve().parents[1]
DOCKER = (ROOT / "Dockerfile").read_text(encoding="utf-8")


def inventory(version="1.0"):
    return "\n".join(f"demo-pkg-{i:02d}\t{version}\tamd64"
                     for i in range(1, 28)) + "\n"


def finding(ident, severity="High", package="demo-pkg-01"):
    return {
        "artifact": {"type": "deb", "name": package, "version": "1.0"},
        "vulnerability": {"id": ident, "severity": severity},
    }


def grype(issues=None):
    return {"descriptor": {"name": "grype"},
            "source": {"type": "image"},
            "distro": {"name": "debian", "version": "13"},
            "matches": issues or []}


class StableUpgradeContractTests(unittest.TestCase):
    def test_trial_is_extra_layer_not_code_mutation(self):
        generated = trial_dockerfile(DOCKER)
        self.assertIn("apt-get upgrade -y --no-install-recommends", generated)
        self.assertIn("zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1", generated)
        self.assertIn("--require-hashes --only-binary=:all:", generated)
        self.assertEqual(generated.count("COPY requirements.lock ./"), 1)
        self.assertIn("if printf '%s", generated)
        self.assertNotEqual(generated, DOCKER)

    def test_floating_base_and_missing_hash_policy_rejected(self):
        with self.assertRaisesRegex(ValueError, "BASE_OR_LOCK"):
            trial_dockerfile(DOCKER.replace("@sha256:", ":latest@sha256:", 1))
        with self.assertRaisesRegex(ValueError, "WHEEL_HASH_POLICY"):
            trial_dockerfile(DOCKER.replace("--require-hashes ", "", 1))

    def test_distro_specific_zlib_patch_cannot_be_removed(self):
        with self.assertRaisesRegex(ValueError, "S91_SECURITY_PATCH_MISSING"):
            trial_dockerfile(DOCKER.replace(
                "1:1.3.dfsg+really1.3.1-1+deb13u1", "0.0.0"))

    def test_identical_scans_do_not_authorize_promotion(self):
        base = grype([finding("DEMO-CVE-1")])
        o = compare(base, base, inventory(), inventory())
        self.assertFalse(o["candidate_eligible"])
        self.assertFalse(o["promote_automatically"])
        self.assertEqual(o["baseline_unique_blocking_ids"], 1)
        self.assertEqual(o["trial_unique_blocking_ids"], 1)
        self.assertFalse(o["improvement_without_new_blockers"])

    def test_only_real_reduction_is_reported_not_promoted(self):
        a = grype([finding("DEMO-CVE-1"), finding("DEMO-CVE-2")])
        b = grype([finding("DEMO-CVE-2")])
        result = compare(a, b, inventory(), inventory("1.1"))
        self.assertEqual(result["removed_blocking_ids"], ["DEMO-CVE-1"])
        self.assertTrue(result["improvement_without_new_blockers"])
        self.assertFalse(result["candidate_eligible"])
        self.assertEqual(len(result["updated_or_removed_packages"]), 27)

    def test_new_high_is_detected(self):
        a = grype([finding("DEMO-CVE-1")])
        b = grype([finding("DEMO-CVE-2")])
        result = compare(a, b, inventory(), inventory())
        self.assertEqual(result["new_blocking_ids"], ["DEMO-CVE-2"])
        self.assertFalse(result["improvement_without_new_blockers"])

    def test_invalid_grype_or_incomplete_inventory_fails_closed(self):
        with self.assertRaises(ValueError):
            compare({}, grype(), inventory(), inventory())
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OS_PACKAGE"):
            compare(grype(), grype(), "pkg\t1\tamd64\n", inventory())

    def test_unknown_or_critical_finding_is_not_ignored(self):
        a = grype()
        b = grype([finding("DEMO-UNKNOWN","Unknown"),
                   finding("DEMO-CRITICAL","Critical")])
        r = compare(a, b, inventory(), inventory())
        self.assertEqual(r["trial_unique_blocking_ids"], 2)
        self.assertFalse(r["candidate_eligible"])
        self.assertEqual(r["scanner_waivers"], 0)


if __name__ == "__main__":
    unittest.main()
