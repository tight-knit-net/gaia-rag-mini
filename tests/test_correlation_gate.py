"""P0/P1 synthetic correlation, revision and scope regression tests.

No real documents, server auth, external APIs, databases or runtime effects.
"""
from dataclasses import replace
from hashlib import sha256
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentSource, DocumentEvent
from gaia_document_mcp.correlation import (
    LogicalDocument, RevisionSnapshot, ObservedRevision, CorrelationPreview,
    SyntheticIdempotencyLedger,
)

RAW = b"%PDF-1.4\nSYNTHETIC NO CUSTOMER DATA\n%%EOF"
HASH = sha256(RAW).hexdigest()
SCOPE = "scope-demo-009"
KEY = "synthetic_request_001"

def fixtures(*, scope=SCOPE, client_id="009", document_id="DOC_DEMO_0001",
             file_id="FILE_DEMO_0001", process_id="PROCESS_DEMO_0001"):
    src = DocumentSource(
        drive_id="DRIVE_DEMO_0001", file_id=file_id,
        client_id=client_id, process_id=process_id,
        source_version="OBS_DEMO_0001", sha256_original=HASH,
    )
    doc = LogicalDocument(document_id, scope, client_id, process_id)
    rev = RevisionSnapshot(
        document_id, "REV_DEMO_0001", None, scope, src.source_ref,
        src.source_version, HASH,
    )
    obs = ObservedRevision(
        document_id, rev.revision_id, scope, src.source_ref, src.source_version,
    )
    event = DocumentEvent(
        source=src, operation="ocr", status="review_required",
        provider="tesseract", source_verified=False,
        operation_id="OP_DEMO_000001", rule_id="NOM-002",
    )
    return doc, rev, obs, event

def preview(doc=None, rev=None, obs=None, event=None, *, allowed_scope=SCOPE, raw=RAW):
    default = fixtures()
    return CorrelationPreview.evaluate(
        document=default[0] if doc is None else doc,
        revision=default[1] if rev is None else rev,
        observation=default[2] if obs is None else obs,
        event=default[3] if event is None else event,
        allowed_scope=allowed_scope, original_bytes=raw,
    )

class CorrelationGateTests(unittest.TestCase):
    def assert_denied(self, code, *, doc=None, rev=None, obs=None, event=None,
                      allowed_scope=SCOPE, raw=RAW):
        with self.assertRaises(ContractViolation) as ctx:
            preview(doc, rev, obs, event, allowed_scope=allowed_scope, raw=raw)
        self.assertEqual(str(ctx.exception), code)

    def test_valid_synthetic_preview(self):
        result = preview()
        self.assertEqual(result["schema"], "gaia.correlation-preview.v1")
        self.assertEqual(result["document_id"], "DOC_DEMO_0001")
        self.assertEqual(result["document_revision_id"], "REV_DEMO_0001")

    def test_preview_never_persists_or_approves(self):
        r = preview()
        self.assertFalse(r["persisted"])
        self.assertFalse(r["write_performed"])
        self.assertTrue(r["requires_authenticated_scope"])
        self.assertTrue(r["requires_document_approval"])
        self.assertTrue(r["requires_r06_memory_approval"])
        self.assertTrue(r["r07_comparison_pending"])

    def test_preview_does_not_expose_original_or_ocr(self):
        self.assertNotIn("SYNTHETIC NO CUSTOMER DATA", str(preview()))
        self.assertNotIn("original_bytes", preview())

    def test_logical_document_id_is_not_file_id(self):
        d, _, _, e = fixtures()
        self.assertNotEqual(d.document_id, e.source.file_id)
        self.assertEqual(e.source.source_ref, "drive:DRIVE_DEMO_0001:FILE_DEMO_0001")

    def test_document_revision_is_distinct_from_event_revision(self):
        _, rev, _, e = fixtures()
        self.assertEqual(rev.revision_id, "REV_DEMO_0001")
        self.assertEqual(e.event_revision, 1)

    def test_same_source_different_logical_document_has_distinct_fingerprint(self):
        d, r, o, e = fixtures()
        original = preview(d, r, o, e)
        d2 = replace(d, document_id="DOC_DEMO_0002")
        r2 = replace(r, document_id=d2.document_id)
        o2 = replace(o, document_id=d2.document_id)
        self.assertNotEqual(original["request_fingerprint"],
                            preview(d2, r2, o2, e)["request_fingerprint"])

    def test_unauthorized_scope_fails_closed(self):
        self.assert_denied("FORBIDDEN_CLIENT_SCOPE", allowed_scope="scope-demo-999")

    def test_foreign_revision_scope_fails_closed(self):
        d, r, o, e = fixtures()
        self.assert_denied("FORBIDDEN_CLIENT_SCOPE", doc=d,
                           rev=replace(r, client_scope="scope-demo-999"), obs=o, event=e)

    def test_foreign_observation_scope_fails_closed(self):
        d, r, o, e = fixtures()
        self.assert_denied("FORBIDDEN_CLIENT_SCOPE", doc=d, rev=r,
                           obs=replace(o, client_scope="scope-demo-999"), event=e)

    def test_document_id_mismatch_fails(self):
        d, r, o, e = fixtures()
        self.assert_denied("DOCUMENT_ID_MISMATCH", doc=d,
                           rev=replace(r, document_id="DOC_DEMO_9999"), obs=o, event=e)

    def test_observation_document_id_mismatch_fails(self):
        d, r, o, e = fixtures()
        self.assert_denied("DOCUMENT_ID_MISMATCH", doc=d, rev=r,
                           obs=replace(o, document_id="DOC_DEMO_9999"), event=e)

    def test_stale_document_revision_returns_conflict(self):
        d, r, o, e = fixtures()
        self.assert_denied("REVISION_CONFLICT", doc=d, rev=r,
                           obs=replace(o, current_revision_id="REV_DEMO_9999"), event=e)

    def test_stale_source_version_returns_conflict(self):
        d, r, o, e = fixtures()
        self.assert_denied("REVISION_CONFLICT", doc=d, rev=r,
                           obs=replace(o, source_version="OBS_DEMO_9999"), event=e)

    def test_event_stale_source_version_returns_conflict(self):
        d, r, o, e = fixtures()
        stale = replace(e, source=replace(e.source, source_version="OBS_DEMO_9999"))
        self.assert_denied("REVISION_CONFLICT", doc=d, rev=r, obs=o, event=stale)

    def test_mismatched_file_ref_fails(self):
        d, r, o, e = fixtures()
        self.assert_denied("SOURCE_REF_MISMATCH", doc=d,
                           rev=replace(r, source_ref="drive:OTHER_DRIVE:FILE_DEMO_0001"),
                           obs=o, event=e)

    def test_mismatched_event_ref_fails(self):
        d, r, o, e = fixtures()
        changed = replace(e, source=replace(e.source, file_id="FILE_DEMO_9999"))
        self.assert_denied("SOURCE_REF_MISMATCH", doc=d, rev=r, obs=o, event=changed)

    def test_revision_sha_mismatch_fails(self):
        d, r, o, e = fixtures()
        self.assert_denied("SOURCE_HASH_MISMATCH", doc=d,
                           rev=replace(r, original_sha256="f"*64), obs=o, event=e)

    def test_modified_pdf_bytes_fail(self):
        self.assert_denied("SOURCE_HASH_MISMATCH", raw=RAW + b"MALICIOUS")

    def test_null_source_hash_fails(self):
        d, r, o, e = fixtures()
        e2 = replace(e, source=replace(e.source, sha256_original=None))
        self.assert_denied("SOURCE_HASH_MISMATCH", doc=d, rev=r, obs=o, event=e2)

    def test_cross_client_binding_fails(self):
        d, r, o, e = fixtures()
        e2 = replace(e, source=replace(e.source, client_id="010"))
        self.assert_denied("CASE_BINDING_MISMATCH", doc=d, rev=r, obs=o, event=e2)

    def test_cross_process_binding_fails(self):
        d, r, o, e = fixtures()
        e2 = replace(e, source=replace(e.source, process_id="PROCESS_DEMO_9999"))
        self.assert_denied("CASE_BINDING_MISMATCH", doc=d, rev=r, obs=o, event=e2)

    def test_parent_revision_self_cycle_fails(self):
        _, r, _, _ = fixtures()
        with self.assertRaisesRegex(ContractViolation, "REVISION_CYCLE"):
            replace(r, parent_revision_id=r.revision_id)

    def test_valid_parent_revision_preserved_in_preview(self):
        d, r, o, e = fixtures()
        r2 = replace(r, parent_revision_id="REV_DEMO_0000")
        self.assertEqual(preview(d, r2, o, e)["parent_revision_id"], "REV_DEMO_0000")

    def test_unverified_imported_is_not_editable(self):
        _, r, _, _ = fixtures()
        with self.assertRaisesRegex(ContractViolation, "IMPORTED_NOT_EDITABLE"):
            replace(r, interop_state="verified")

    def test_editable_revision_requires_known_kind(self):
        _, r, _, _ = fixtures()
        with self.assertRaisesRegex(ContractViolation, "SOURCE_KIND_INVALID"):
            replace(r, source_kind="drive")

    def test_editable_odt_kind_can_be_described_not_approved(self):
        d, r, o, e = fixtures()
        r2 = replace(r, source_kind="odt", interop_state="native")
        self.assertEqual(preview(d, r2, o, e)["source_kind"], "odt")
        self.assertTrue(preview(d, r2, o, e)["requires_document_approval"])

    def test_request_fingerprint_independent_of_event_attempt_id(self):
        d, r, o, e = fixtures()
        e2 = replace(e, operation_id="OP_DEMO_000002")
        self.assertNotEqual(e.fingerprint(), e2.fingerprint())
        self.assertEqual(preview(d, r, o, e)["request_fingerprint"],
                         preview(d, r, o, e2)["request_fingerprint"])

    def test_request_fingerprint_sensitive_to_nomenclature_rule(self):
        d, r, o, e = fixtures()
        e2 = replace(e, rule_id="NOM-003")
        self.assertNotEqual(preview(d, r, o, e)["request_fingerprint"],
                            preview(d, r, o, e2)["request_fingerprint"])

    def test_request_fingerprint_sensitive_to_filename(self):
        d, r, o, e = fixtures()
        e2 = replace(e, proposed_filename="009_SYNTHETIC.pdf")
        self.assertNotEqual(preview(d, r, o, e)["request_fingerprint"],
                            preview(d, r, o, e2)["request_fingerprint"])

    def test_first_idempotency_register_is_no_write(self):
        r = SyntheticIdempotencyLedger().register(
            scope=SCOPE, idempotency_key=KEY, preview=preview())
        self.assertEqual(r["schema"], "gaia.synthetic-idempotency.v1")
        self.assertFalse(r["persisted"])
        self.assertFalse(r["replayed"])
        self.assertFalse(r["write_performed"])

    def test_same_key_same_request_replayed_without_duplicate_run(self):
        ledger = SyntheticIdempotencyLedger()
        first = ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        second = ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        self.assertEqual(first["synthetic_run_id"], second["synthetic_run_id"])
        self.assertTrue(second["replayed"])
        self.assertEqual(len(ledger._requests), 1)

    def test_same_key_different_payload_conflicts(self):
        d, r, o, e = fixtures()
        ledger = SyntheticIdempotencyLedger()
        ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_CONFLICT"):
            ledger.register(scope=SCOPE, idempotency_key=KEY,
                            preview=preview(d, r, o, replace(e, rule_id="NOM-003")))

    def test_same_key_different_scope_independent(self):
        ledger = SyntheticIdempotencyLedger()
        x = ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        d, r, o, e = fixtures(scope="scope-demo-010", client_id="010")
        y = ledger.register(scope="scope-demo-010", idempotency_key=KEY,
                            preview=preview(d, r, o, e, allowed_scope="scope-demo-010"))
        self.assertNotEqual(x["synthetic_run_id"], y["synthetic_run_id"])
        self.assertEqual(len(ledger._requests), 2)

    def test_preview_scope_forgery_rejected_by_ledger(self):
        with self.assertRaisesRegex(ContractViolation, "UNTRUSTED_PREVIEW_OR_SCOPE"):
            SyntheticIdempotencyLedger().register(
                scope="scope-demo-010", idempotency_key=KEY, preview=preview())

    def test_changed_preview_flags_are_not_accepted(self):
        p = preview()
        p["persisted"] = True
        with self.assertRaisesRegex(ContractViolation, "UNTRUSTED_PREVIEW_OR_SCOPE"):
            SyntheticIdempotencyLedger().register(scope=SCOPE, idempotency_key=KEY, preview=p)

    def test_invalid_idempotency_key_rejected(self):
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_KEY_INVALID"):
            SyntheticIdempotencyLedger().register(
                scope=SCOPE, idempotency_key="x", preview=preview())

    def test_result_mutation_does_not_change_ledger(self):
        ledger = SyntheticIdempotencyLedger()
        r = ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        r["synthetic_run_id"] = "tampered"
        replay = ledger.register(scope=SCOPE, idempotency_key=KEY, preview=preview())
        self.assertNotEqual(r["synthetic_run_id"], replay["synthetic_run_id"])

    def test_invalid_revision_id_rejected(self):
        _, rev, _, _ = fixtures()
        with self.assertRaisesRegex(ContractViolation, "DOCUMENT_REVISION_ID_INVALID"):
            replace(rev, revision_id="x")

    def test_no_direct_memory_or_drive_operation(self):
        r = preview()
        self.assertFalse(r["persisted"])
        self.assertFalse(r["write_performed"])
        self.assertNotIn("qdrant_point_id", r)
        self.assertNotIn("drive_write_performed", r)

if __name__ == "__main__":
    unittest.main()
