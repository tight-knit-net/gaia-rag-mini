"""Contract-v2 and negative security tests, entirely synthetic/offline."""
from dataclasses import replace
from hashlib import sha256
import hmac
import json
from pathlib import Path
import time
import unittest

from gaia_document_mcp.contracts import (
    ContractViolation, DocumentEvent, DocumentSource, Evidence,
)
from gaia_document_mcp.pipeline import KnowledgeCapture, TOOL_CATALOG
from gaia_document_mcp.settings import GateSettings
from gaia_document_mcp.trust import ReviewAttestation, ReviewProofVerifier

D = "f" * 64
KEY = b"synthetic-review-key-that-is-never-used-in-production-0001"
OP = "DEMO_OPERATION_001"

def source(**kwargs):
    p = {
        "drive_id": "DRIVE_DEMO_001", "file_id": "FILE_DEMO_001",
        "client_id": "009", "process_id": "DEMO-PROCESSO-001",
        "source_version": "OBS_SYNTH_0001", "sha256_original": D,
    }
    p.update(kwargs)
    return DocumentSource(**p)

def event(**kwargs):
    p = {
        "source": source(), "operation": "ocr", "status": "completed",
        "provider": "tesseract", "source_verified": True,
        "operation_id": OP,
        "fields_verified": True, "client_verified": True,
        "ocr_reviewed": True, "summary": "Procedimento sintetico de conferencia de anexos.",
        "evidence": (Evidence("FILE_DEMO_001", "p1:lines1-3", True),)
    }
    p.update(kwargs)
    return DocumentEvent(**p)

def attestation(e, *, key=KEY, issued_at=None):
    now = int(time.time()) if issued_at is None else issued_at
    p = ReviewAttestation(
        event_key=e.fingerprint(), evidence_sha256=e.evidence_digest(),
        review_id="SYNTH_REVIEW_001", reviewer_subject="synthetic.actor",
        issued_at=now, expires_at=now + 300, mac="0" * 64,
    )
    return replace(p, mac=hmac.new(key, p.signing_bytes(), "sha256").hexdigest())

class ContractV2Tests(unittest.TestCase):
    def test_all_flags_default_off(self):
        self.assertEqual(GateSettings.from_env({}), GateSettings())

    def test_direct_qdrant_always_forbidden(self):
        self.assertFalse(GateSettings(real_documents=True, memory_writes=True).may_execute("direct_qdrant_write"))

    def test_unknown_capability_denied(self):
        self.assertFalse(GateSettings().may_execute("god_mode"))

    def test_env_gates_fail_closed(self):
        self.assertFalse(GateSettings.from_env({"GAIA_DOC_GOOGLE_WRITES": "1"}).may_execute("google_write"))

    def test_event_receipt_is_idempotent(self):
        store = KnowledgeCapture()
        self.assertEqual(store.capture(event()), store.capture(event()))
        self.assertEqual(len(store._receipts), 1)

    def test_receipt_has_no_side_effect(self):
        r = KnowledgeCapture().capture(event())
        self.assertFalse(r["persisted"] or r["drive_write_performed"] or r["memory_write_performed"])

    def test_receipt_is_metadata_only(self):
        result = KnowledgeCapture().capture(event(summary="CONFIDENTIAL_SYNTHETIC_MARKER"))
        self.assertNotIn("CONFIDENTIAL_SYNTHETIC_MARKER", json.dumps(result))
        self.assertNotIn("summary", result)
        self.assertEqual(result["schema"], "gaia.document-receipt.v2")

    def test_candidate_requires_trusted_review_even_when_flags_true(self):
        r = KnowledgeCapture().memory_preview(event())
        self.assertFalse(r["candidate"])
        self.assertIn("TRUSTED_REVIEW_ATTESTATION_MISSING_OR_INVALID", r["blockers"])
        self.assertIsNone(r["summary"])

    def test_attested_editorial_candidate_never_persists(self):
        e = event()
        r = KnowledgeCapture().memory_preview(
            e, proof=attestation(e), verifier=ReviewProofVerifier(KEY))
        self.assertTrue(r["candidate"])
        self.assertFalse(r["persisted"])
        self.assertTrue(r["r07_comparison_pending"])
        self.assertTrue(r["requires_r06_human_approval"])
        self.assertTrue(r["requires_document_registry_approval"])
        self.assertIsNone(r["document_approval_ref"])

    def test_attestation_alone_does_not_override_ocr_review(self):
        e = event(ocr_reviewed=False)
        r = KnowledgeCapture().memory_preview(e, proof=attestation(e), verifier=ReviewProofVerifier(KEY))
        self.assertIn("OCR_NOT_REVIEWED", r["blockers"])

    def test_unverified_client_is_blocked(self):
        e = event(client_verified=False)
        r = KnowledgeCapture().memory_preview(e)
        self.assertIn("CLIENT_NOT_VERIFIED", r["blockers"])

    def test_external_llm_requires_policy_review(self):
        e = event(external_llm_used=True)
        r = KnowledgeCapture().memory_preview(e, proof=attestation(e), verifier=ReviewProofVerifier(KEY))
        self.assertIn("EXTERNAL_LLM_DATA_POLICY_REVIEW_REQUIRED", r["blockers"])

    def test_no_summary_is_blocked(self):
        self.assertIn("NO_DURABLE_KNOWLEDGE_SUMMARY", KnowledgeCapture().memory_preview(event(summary=" "))["blockers"])

    def test_missing_field_evidence_is_blocked(self):
        self.assertIn("EVIDENCE_NOT_REVIEWED", KnowledgeCapture().memory_preview(event(evidence=()))["blockers"])

    def test_wrong_source_evidence_is_rejected(self):
        with self.assertRaises(ContractViolation):
            event(evidence=(Evidence("FILE_DEMO_999", "p1", True),))

    def test_client_prefix_mandatory(self):
        with self.assertRaises(ContractViolation):
            event(proposed_filename="CNPJ.pdf")

    def test_client_3_digits(self):
        with self.assertRaises(ContractViolation):
            source(client_id="9D")

    def test_invalid_hash_rejected(self):
        with self.assertRaises(ContractViolation):
            source(sha256_original="x" * 64)

    def test_tool_catalog_no_direct_write(self):
        names = [x.name for x in TOOL_CATALOG]
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn("document.qdrant_write", names)
        self.assertTrue(next(x for x in TOOL_CATALOG if x.name == "document.send_signature").requires_approval)

    def test_noncompleted_cannot_be_promoted(self):
        self.assertIn("OPERATION_NOT_COMPLETED", KnowledgeCapture().memory_preview(event(status="blocked"))["blockers"])

    def test_mock_ocr_can_never_be_promoted(self):
        e = event(provider="mock")
        r = KnowledgeCapture().memory_preview(e, proof=attestation(e), verifier=ReviewProofVerifier(KEY))
        self.assertIn("OCR_MOCK_NOT_EVIDENCE", r["blockers"])

    def test_source_ref_within_r06_ref_contract(self):
        s = source()
        self.assertLessEqual(len(s.source_ref), 200)
        self.assertTrue(s.source_ref.startswith("drive:"))

    def test_source_ref_checked_at_construction(self):
        with self.assertRaises(ContractViolation):
            source(drive_id="D"*140, file_id="F"*140)

    def test_generated_document_without_case_or_hash_allowed(self):
        s = source(
            source_provider="generated", drive_id=None,
            client_id=None, process_id=None,
            sha256_original=None,
        )
        self.assertEqual(s.source_ref, "generated:FILE_DEMO_001")
        e = event(source=s)
        r = KnowledgeCapture().memory_preview(e)
        self.assertIn("CASE_BINDING_PENDING", r["blockers"])
        self.assertIn("SOURCE_HASH_UNKNOWN", r["blockers"])

    def test_dropbox_document_without_drive_id(self):
        s = source(source_provider="dropbox", drive_id=None)
        self.assertEqual(s.source_ref, "dropbox:FILE_DEMO_001")

    def test_drive_id_required_for_drive(self):
        with self.assertRaises(ContractViolation):
            source(drive_id=None)

    def test_non_drive_rejects_drive_id(self):
        with self.assertRaises(ContractViolation):
            source(source_provider="local")

    def test_unsupported_provider_rejected(self):
        with self.assertRaises(ContractViolation):
            source(source_provider="https")

    def test_unknown_case_cannot_propose_filename(self):
        s = source(client_id=None)
        with self.assertRaises(ContractViolation):
            event(source=s, proposed_filename="009_CNPJ.pdf")

    def test_original_hash_can_be_checked_against_bytes(self):
        raw = b"synthetic bytes only"
        s = source(sha256_original=sha256(raw).hexdigest())
        self.assertTrue(s.matches_original(raw))
        self.assertFalse(s.matches_original(b"different bytes"))
        self.assertFalse(source(sha256_original=None).matches_original(raw))

    def test_fingerprint_is_sensitive_to_drive_identity(self):
        a=event()
        b=event(source=source(drive_id="DRIVE_DEMO_999"))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_fingerprint_is_sensitive_to_client_identity(self):
        self.assertNotEqual(event().fingerprint(), event(source=source(client_id="010")).fingerprint())

    def test_fingerprint_is_sensitive_to_operation_id(self):
        self.assertNotEqual(event().fingerprint(), event(operation_id="DEMO_OPERATION_002").fingerprint())

    def test_fingerprint_is_sensitive_to_event_revision(self):
        self.assertNotEqual(event().fingerprint(), event(event_revision=2).fingerprint())

    def test_fingerprint_is_sensitive_to_review_claims(self):
        self.assertNotEqual(event().fingerprint(), event(fields_verified=False).fingerprint())

    def test_fingerprint_is_sensitive_to_summary(self):
        self.assertNotEqual(event().fingerprint(), event(summary="Outra revisao sintetica").fingerprint())

    def test_fingerprint_is_sensitive_to_evidence(self):
        self.assertNotEqual(event().fingerprint(),
            event(evidence=(Evidence("FILE_DEMO_001", "p2:lines1-3", True),)).fingerprint())

    def test_fingerprint_is_sensitive_to_status(self):
        self.assertNotEqual(event().fingerprint(), event(status="review_required").fingerprint())

    def test_same_op_retry_is_idempotent_but_revision_is_distinct(self):
        store=KnowledgeCapture()
        store.capture(event())
        store.capture(event())
        store.capture(event(event_revision=2))
        self.assertEqual(len(store._receipts), 2)

    def test_attestation_from_other_event_is_invalid(self):
        a=event()
        b=event(event_revision=2)
        r=KnowledgeCapture().memory_preview(
            b, proof=attestation(a), verifier=ReviewProofVerifier(KEY))
        self.assertIn("TRUSTED_REVIEW_ATTESTATION_MISSING_OR_INVALID", r["blockers"])

    def test_attestation_from_other_key_is_invalid(self):
        a=event()
        r=KnowledgeCapture().memory_preview(
            a, proof=attestation(a,key=b"x"*32), verifier=ReviewProofVerifier(KEY))
        self.assertFalse(r["candidate"])

    def test_expired_attestation_is_invalid(self):
        a=event()
        proof=attestation(a,issued_at=int(time.time())-900)
        r=KnowledgeCapture().memory_preview(a, proof=proof, verifier=ReviewProofVerifier(KEY))
        self.assertFalse(r["candidate"])

    def test_review_proof_verifier_requires_secret(self):
        with self.assertRaises(ContractViolation):
            ReviewProofVerifier(b"short")

    def test_attestation_invalid_id_is_rejected(self):
        p=attestation(event())
        with self.assertRaises(ContractViolation):
            replace(p, review_id="../escape")

    def test_no_provenance_attestation_in_receipt(self):
        e=event()
        r=KnowledgeCapture().capture(e)
        self.assertNotIn("mac",r)
        self.assertNotIn("reviewer_subject",r)

    def test_operation_id_and_event_revision_checked(self):
        with self.assertRaises(ContractViolation):
            event(operation_id="short")
        with self.assertRaises(ContractViolation):
            event(event_revision=0)
        with self.assertRaises(ContractViolation):
            event(event_revision=True)

    def test_filename_rejects_unsafe_paths(self):
        for name in ("009_../a.pdf","009_bad:.pdf","009_end.", "009_evil\t.pdf"):
            with self.subTest(name=name):
                with self.assertRaises(ContractViolation):
                    event(proposed_filename=name)

    def test_event_and_receipt_schemas_structurally_match(self):
        e=event()
        envelope=e.envelope()
        receipt=KnowledgeCapture().capture(e)
        self.assertEqual(envelope["schema"],"gaia.document-event.v2")
        for name, data in [
            ("schemas/gaia.document-event.v2.schema.json", envelope),
            ("schemas/gaia.document-receipt.v2.schema.json", receipt),
        ]:
            s=json.loads(Path(name).read_text())
            self.assertEqual(set(data),set(s["required"]))
            self.assertEqual(set(data),set(s["properties"]))
            self.assertEqual(data["schema"],s["properties"]["schema"]["const"])

    def test_v1_schema_is_kept_for_historical_readers(self):
        s=json.loads(Path("schemas/gaia.document-event.v1.schema.json").read_text())
        self.assertEqual(s["properties"]["schema"]["const"],"gaia.document-event.v1")

if __name__ == "__main__":
    unittest.main()

