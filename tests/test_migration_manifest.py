"""R07 read-only simulated cutover planning; intentionally no connectors."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05.migration_manifest import (
    compare_approved_snapshots, classify_legacy_pending,
)

A = "11111111-1111-4111-8111-111111111111"
B = "22222222-2222-4222-8222-222222222222"


def approved(ident, text="Resumo sintético"):
    return {"id": ident, "namespace": "chatgpt", "process_id": "DEMO-PROCESS",
            "approved": True, "text": text, "source_ref": "DEMO-SOURCE",
            "title": "Síntese DEMO", "approved_by": "DEMO-OWNER"}


class MigrationManifestTests(unittest.TestCase):
    def test_identical_snapshots_require_no_copy(self):
        old = [approved(A), approved(B)]
        result = compare_approved_snapshots(old, old, legacy_complete=True,
                                            candidate_complete=True)
        self.assertTrue(result["candidate_read_parity"])
        self.assertFalse(result["copy_required"])
        self.assertEqual(result["next_step"], "NO_COPY_REQUIRED_VERIFY_SHARED_STORAGE")
        self.assertEqual(result["writes_performed"], 0)

    def test_missing_point_requires_review_not_automatic_import(self):
        result = compare_approved_snapshots([approved(A), approved(B)], [approved(A)],
                                            legacy_complete=True, candidate_complete=True)
        self.assertEqual(result["missing_in_candidate_ids"], [B])
        self.assertTrue(result["copy_required"])
        self.assertFalse(result["migration_authorized"])

    def test_mismatch_report_only_identifier(self):
        result = compare_approved_snapshots([approved(A)], [approved(A, text="Outro")],
                                            legacy_complete=True, candidate_complete=True)
        self.assertEqual(result["content_mismatch_ids"], [A])
        self.assertNotIn("Outro", str(result))

    def test_partial_inventory_blocks_complete_claim(self):
        result = compare_approved_snapshots([approved(A)], [approved(A)],
                                            legacy_complete=True, candidate_complete=False)
        self.assertFalse(result["candidate_read_parity"])
        self.assertIsNone(result["copy_required"])

    def test_reject_unapproved_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_OR_INVALID"):
            compare_approved_snapshots([dict(approved(A), approved=False)], [],
                                       legacy_complete=True, candidate_complete=True)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_POINT_ID"):
            compare_approved_snapshots([approved(A), approved(A)], [],
                                       legacy_complete=True, candidate_complete=True)

    def test_pending_legacy_never_imports_as_approved(self):
        x = classify_legacy_pending([{"id": "demo-proposal", "status": "pending"},
                                     {"id": "demo-approved", "status": "approved"}])
        self.assertEqual(x["manual_review_required"], 1)
        self.assertFalse(x["auto_import"])
        self.assertEqual(x["writes_performed"], 0)


if __name__ == "__main__":
    unittest.main()
