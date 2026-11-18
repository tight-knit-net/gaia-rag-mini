"""Deterministic synthetic tests; no real documents, network or persistence."""
import json
from hashlib import sha256
import unittest
from pathlib import Path

from gaia_document_mcp.contracts import ContractViolation, DocumentEvent, DocumentSource, Evidence
from gaia_document_mcp.pipeline import KnowledgeCapture, TOOL_CATALOG
from gaia_document_mcp.settings import GateSettings

D = "f" * 64

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
        "fields_verified": True, "client_verified": True,
        "ocr_reviewed": True, "summary": "Procedimento hipotetico de conferencia de anexos.",
        "evidence": (Evidence("FILE_DEMO_001", "p1:lines1-3", True),)
    }
    p.update(kwargs)
    return DocumentEvent(**p)

class DocumentMcpTests(unittest.TestCase):
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
    def test_valid_candidate_never_persists(self):
        r = KnowledgeCapture().memory_preview(event())
        self.assertTrue(r["candidate"])
        self.assertFalse(r["persisted"])
        self.assertIsNone(r["document_approval_ref"])
        self.assertTrue(r["requires_r06_human_approval"])
    def test_unverified_ocr_is_blocked(self):
        r = KnowledgeCapture().memory_preview(event(ocr_reviewed=False))
        self.assertIn("OCR_NOT_REVIEWED", r["blockers"])
    def test_unverified_client_is_blocked(self):
        r = KnowledgeCapture().memory_preview(event(client_verified=False))
        self.assertIn("CLIENT_NOT_VERIFIED", r["blockers"])
    def test_external_llm_requires_policy_check(self):
        r = KnowledgeCapture().memory_preview(event(external_llm_used=True))
        self.assertIn("EXTERNAL_LLM_DATA_POLICY_REVIEW_REQUIRED", r["blockers"])
    def test_no_summary_is_blocked(self):
        r = KnowledgeCapture().memory_preview(event(summary=" "))
        self.assertIn("NO_DURABLE_KNOWLEDGE_SUMMARY", r["blockers"])
    def test_missing_field_evidence_is_blocked(self):
        r = KnowledgeCapture().memory_preview(event(evidence=()))
        self.assertIn("EVIDENCE_NOT_REVIEWED", r["blockers"])
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
            source(sha256_original="x"*64)
    def test_no_raw_text_in_receipt(self):
        result = KnowledgeCapture().capture(event(summary="CONFIDENTIAL_SYNTHETIC_MARKER"))
        self.assertNotIn("CONFIDENTIAL_SYNTHETIC_MARKER", json.dumps(result))
    def test_tool_catalog_has_no_unsafe_direct_tool(self):
        names = [x.name for x in TOOL_CATALOG]
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn("document.qdrant_write", names)
        self.assertTrue(next(x for x in TOOL_CATALOG if x.name == "document.send_signature").requires_approval)
    def test_json_schema_exists(self):
        j = json.loads(Path("schemas/gaia.document-event.v1.schema.json").read_text())
        self.assertEqual(j["properties"]["schema"]["const"], "gaia.document-event.v1")
    def test_source_ref_is_within_r06_ref_contract(self):
        s=source()
        self.assertLessEqual(len(s.source_ref), 200)
        self.assertTrue(s.source_ref.startswith("drive:"))
    def test_noncompleted_cannot_be_promoted(self):
        r=KnowledgeCapture().memory_preview(event(status="blocked"))
        self.assertIn("OPERATION_NOT_COMPLETED",r["blockers"])

if __name__ == "__main__":
    unittest.main()

