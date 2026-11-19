"""S8: strict simulated native-snapshot gate, without calling Qdrant."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05.native_snapshot_plan import preflight


def synthetic():
    return {
        "source_collection": "s8_source_demo",
        "restore_collection": "s8_restore_demo",
        "snapshot_name": "qdrant-demo.snapshot",
        "snapshot_sha256": "a"*64,
        "source_approved_count": 3, "restored_approved_count": 3,
        "source_point_count": 3, "restored_point_count": 3,
        "ledger_pending_count": 2, "ledger_approved_count": 3,
        "inventory_complete": True, "checksum_verified": True,
        "restore_target_was_absent": True,
        "ledger_backup_verified": True,
        "priority": "snapshot",
    }


class SnapshotContractTests(unittest.TestCase):
    def test_complete_synthetic_evidence_does_not_claim_real_execution(self):
        result = preflight(synthetic())
        self.assertTrue(result["synthetic_manifest_passed"])
        self.assertFalse(result["production_homologated"])
        self.assertFalse(result["migration_authorized"])
        self.assertEqual(result["writes"], 0)
        self.assertEqual(result["legacy_pending_count_kept_separate"], 2)

    def test_default_replica_priority_denied(self):
        data = synthetic()
        data["priority"] = "replica"
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_PRIORITY_NOT_SAFE"):
            preflight(data)

    def test_recovery_into_existing_collection_denied(self):
        data = synthetic()
        data["restore_collection"] = data["source_collection"]
        with self.assertRaisesRegex(ValueError, "OVERWRITE_OR_UNSAFE_COLLECTION"):
            preflight(data)
        data = synthetic()
        data["restore_target_was_absent"] = False
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_EVIDENCE_NOT_COMPLETE"):
            preflight(data)

    def test_partial_inventory_and_checksum_failure_block(self):
        for key in ("inventory_complete", "checksum_verified",
                    "ledger_backup_verified"):
            data = synthetic()
            data[key] = False
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "SNAPSHOT_EVIDENCE_NOT_COMPLETE"):
                    preflight(data)

    def test_mixed_unapproved_points_fail(self):
        data = synthetic()
        data["source_point_count"] = 4
        with self.assertRaisesRegex(ValueError, "APPROVED_POINT_RESTORE_MISMATCH"):
            preflight(data)

    def test_incomplete_restore_fails(self):
        data = synthetic()
        data["restored_approved_count"] = 2
        with self.assertRaisesRegex(ValueError, "APPROVED_POINT_RESTORE_MISMATCH"):
            preflight(data)

    def test_no_path_traversal_or_missing_hash(self):
        data = synthetic()
        data["snapshot_name"] = "../qdrant-demo.snapshot"
        with self.assertRaisesRegex(ValueError, "UNSAFE_SNAPSHOT_FILENAME"):
            preflight(data)
        data = synthetic()
        data["snapshot_sha256"] = ""
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_HASH_MISSING"):
            preflight(data)

    def test_boolean_counts_and_partial_manifest_fail(self):
        data = synthetic()
        data["source_approved_count"] = True
        with self.assertRaisesRegex(ValueError, "INVALID_INVENTORY_COUNTS"):
            preflight(data)
        data = synthetic()
        del data["checksum_verified"]
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_MANIFEST_INCOMPLETE"):
            preflight(data)


if __name__ == "__main__":
    unittest.main()
