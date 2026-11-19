"""S9.3 fail-closed Debian image minimization controls; fictional artifacts only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from r07_s93_minimization import temporary_minimal_dockerfile, compare

DOCKER=(Path(__file__).resolve().parents[1]/"Dockerfile").read_text(encoding="utf-8")
PKGS="\n".join(f"demo-{i:02d}\t1.0\tamd64" for i in range(30))+"\n"


def finding(ident, severity="High", pkg="demo-01"):
    return {"artifact":{"type":"deb","name":pkg,"version":"1.0"},
            "vulnerability":{"id":ident,"severity":severity}}


def scan(issues=None):
    return {"descriptor":{"name":"grype"},
            "source":{"type":"image"},
            "distro":{"name":"debian","version":"13"},
            "matches":issues or []}


def probe(observed=None):
    return {"runtime_imports_ok":True,
            "loaded_module_paths":{
                "python":"/usr/local/bin/python",
                "_ssl":"/usr/local/lib/python3.12/lib-dynload/_ssl.so",
                "_sqlite3":"/usr/local/lib/python3.12/lib-dynload/_sqlite3.so",
                "zlib":"/usr/local/lib/python3.12/lib-dynload/zlib.so",
                "_ctypes":"/usr/local/lib/python3.12/lib-dynload/_ctypes.so",
                "_bz2":"/usr/local/lib/python3.12/lib-dynload/_bz2.so",
                "_lzma":"/usr/local/lib/python3.12/lib-dynload/_lzma.so"},
            "observed_os_packages":observed or ["demo-01"],"network_requests":0}


class MinimizationContractTests(unittest.TestCase):
    def test_only_dockerfile_trial_layer_and_hashes_preserved(self):
        output=temporary_minimal_dockerfile(DOCKER)
        self.assertIn("apt-get autoremove --purge -y",output)
        self.assertIn("--require-hashes --only-binary=:all:",output)
        self.assertIn("zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1",output)
        self.assertTrue(output.startswith(DOCKER.splitlines()[0]))
        self.assertEqual(output.count("COPY requirements.lock ./"),1)

    def test_bad_base_or_floating_install_rejected(self):
        with self.assertRaisesRegex(ValueError,"IMMUTABLE"):
            temporary_minimal_dockerfile(DOCKER.replace("@sha256:",":latest@sha256:",1))
        with self.assertRaisesRegex(ValueError,"WHEEL_SHA256"):
            temporary_minimal_dockerfile(DOCKER.replace("--require-hashes ","",1))

    def test_official_zlib_patch_is_mandatory(self):
        with self.assertRaisesRegex(ValueError,"OFFICIAL_ZLIB"):
            temporary_minimal_dockerfile(DOCKER.replace("1:1.3.dfsg+really1.3.1-1+deb13u1","0.0"))

    def test_identical_images_are_not_claimed_as_remediation(self):
        data=compare(PKGS,PKGS,scan([finding("DEMO-CVE-A")]),
                     scan([finding("DEMO-CVE-A")]),probe(),probe())
        self.assertFalse(data["candidate_eligible"])
        self.assertEqual(data["trial_unique_blockers"],1)
        self.assertEqual(data["removed_os_packages"],[])
        self.assertFalse(data["publish_approved"])

    def test_auto_removed_unobserved_package_is_identified(self):
        modified="\n".join(line for line in PKGS.splitlines()
                           if not line.startswith("demo-30\t"))+"\n"
        data=compare(PKGS,modified,scan([finding("DEMO-CVE-A")]),
                     scan([]),probe(),probe())
        self.assertEqual(data["removed_os_packages"][0]["name"],"demo-30")
        self.assertEqual(data["resolved_blockers"],["DEMO-CVE-A"])
        self.assertFalse(data["publish_approved"])

    def test_removing_observed_system_library_is_refused(self):
        modified="\n".join(line for line in PKGS.splitlines()
                           if not line.startswith("demo-01\t"))+"\n"
        with self.assertRaisesRegex(ValueError,"REMOVED_OBSERVED_RUNTIME_PACKAGE"):
            compare(PKGS,modified,scan(),scan(),probe(),probe())

    def test_new_cve_severity_unknown_is_blocking(self):
        data=compare(PKGS,PKGS,scan(),scan([finding("DEMO-UNKNOWN","Unknown")]),
                     probe(),probe())
        self.assertFalse(data["candidate_eligible"])
        self.assertEqual(data["new_blockers"],["DEMO-UNKNOWN"])
        self.assertEqual(data["scanner_waivers"],0)

    def test_modified_os_version_is_not_minimization(self):
        updated=PKGS.replace("demo-01\t1.0\t","demo-01\t2.0\t")
        with self.assertRaisesRegex(ValueError,"MINIMIZATION_CANNOT_UPGRADE"):
            compare(PKGS,updated,scan(),scan(),probe(),probe())

    def test_incomplete_probe_or_scan_fails(self):
        data=probe()
        data["runtime_imports_ok"]=False
        with self.assertRaisesRegex(ValueError,"RUNTIME_IMPORTS_FAILED"):
            compare(PKGS,PKGS,scan(),scan(),data,probe())
        with self.assertRaises(ValueError):
            compare(PKGS,PKGS,{},scan(),probe(),probe())

    def test_no_network_leak_in_runtime_probe(self):
        data=probe()
        data["network_requests"]=1
        with self.assertRaisesRegex(ValueError,"NETWORK_GUARD"):
            compare(PKGS,PKGS,scan(),scan(),probe(),data)


if __name__=="__main__":
    unittest.main()
