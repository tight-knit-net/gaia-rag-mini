"""Lean OCR/NOM adapter contract tests: synthetic PDFs and mocked dependencies."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock
import json
import subprocess

from gaia_document_mcp.contracts import ContractViolation, DocumentSource
from gaia_document_mcp.hybrid import (
    LegacyOcrRecord, InternalOcrReader, ExistingNomPreview, HybridOcrNom,
)

PDF = b"%PDF-1.4\nsynthetic-test-only\n%%EOF"
DOCUMENT_ID = "11111111-1111-4111-8111-111111111111"

def source(**kwargs):
    p = dict(
        drive_id="DEMO_DRIVE_001", file_id="DEMO_FILE_001",
        client_id="009", process_id="DEMO-PROCESSO-001",
        source_version="TEST_REV_001", sha256_original=sha256(PDF).hexdigest(),
    )
    p.update(kwargs)
    return DocumentSource(**p)

def record(**kwargs):
    p = dict(
        document_id=DOCUMENT_ID, tenant="test", sha256=sha256(PDF).hexdigest(),
        provider="tesseract", status="processed",
        text="COMPROVANTE DE INSCRICAO E SITUACAO CADASTRAL - DEMO",
    )
    p.update(kwargs)
    return LegacyOcrRecord(**p)

class StubNom:
    def __init__(self):
        self.calls = []
    def preview(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "OK", "rule_id": kwargs["rule_id"],
            "finalFilename": kwargs["client_id"] + "_DEMO.pdf",
            "mode": "PREVIEW_ONLY", "write_performed": False,
        }

class HybridTest(TestCase):
    def test_ocr_record_parses_legacy_test_tenant(self):
        data = dict(id=DOCUMENT_ID,tenant="test",sha256=sha256(PDF).hexdigest(),
                    provider="tesseract",status="processed",text="some text")
        self.assertEqual(LegacyOcrRecord.parse(data).tenant,"test")

    def test_ocr_record_blocks_unknown_provider(self):
        with self.assertRaises(ContractViolation):
            LegacyOcrRecord.parse(dict(
                id=DOCUMENT_ID,tenant="test",sha256=sha256(PDF).hexdigest(),
                provider="untrusted",status="processed",text="some text"))

    def test_loopback_only(self):
        for url in ("https://api.ilovepdf.com:443/", "http://169.254.169.254:80/",
                    "http://example.org:1234/", "http://localhost:18788/path"):
            with self.subTest(url=url):
                with self.assertRaises(ContractViolation):
                    InternalOcrReader(url,"synthetic-bearer-only")
        InternalOcrReader("http://127.0.0.1:18788/","synthetic-bearer-only")

    def test_mock_ocr_never_flows_to_nom(self):
        n=StubNom()
        x=HybridOcrNom(n).preview(source=source(),original_bytes=PDF,
            record=record(provider="mock"),operation_id="DEMO_OPERATION_001",
            expected_tenant="test",rule_id="NOM-002",reviewed_fields={"DATA":"01-01-2026"})
        self.assertEqual(x["status"],"BLOCKED")
        self.assertEqual(len(n.calls),0)

    def test_sha_mismatch_blocks_nom(self):
        n=StubNom()
        with self.assertRaises(ContractViolation):
            HybridOcrNom(n).preview(source=source(),original_bytes=PDF,
                record=record(sha256="f"*64),operation_id="DEMO_OPERATION_001",
                expected_tenant="test",rule_id="NOM-002",reviewed_fields={})
        self.assertEqual(len(n.calls),0)

    def test_tenant_mismatch_blocks_nom(self):
        with self.assertRaises(ContractViolation):
            HybridOcrNom(StubNom()).preview(source=source(),original_bytes=PDF,
                record=record(),operation_id="DEMO_OPERATION_001",
                expected_tenant="other")

    def test_no_case_binding_blocks_nom(self):
        n=StubNom()
        x=HybridOcrNom(n).preview(source=source(client_id=None),original_bytes=PDF,
            record=record(),operation_id="DEMO_OPERATION_001",
            expected_tenant="test",rule_id="NOM-002",reviewed_fields={})
        self.assertEqual(x["reason"],"CLIENT_PROCESS_BINDING_PENDING")
        self.assertEqual(n.calls,[])

    def test_nom_not_called_without_reviewed_variables(self):
        n=StubNom()
        x=HybridOcrNom(n).preview(source=source(),original_bytes=PDF,
            record=record(),operation_id="DEMO_OPERATION_001",
            expected_tenant="test")
        self.assertEqual(x["status"],"OCR_REVIEW_REQUIRED")
        self.assertIsNone(x["nom_preview"])
        self.assertEqual(n.calls,[])
        self.assertFalse(x["memory_persisted"])

    def test_synthetic_ocr_to_nom_preview(self):
        n=StubNom()
        x=HybridOcrNom(n).preview(source=source(),original_bytes=PDF,
            record=record(),operation_id="DEMO_OPERATION_001",
            expected_tenant="test",rule_id="NOM-002",
            reviewed_fields={"DATA":"01-01-2026"})
        self.assertEqual(x["status"],"OCR_NOM_PREVIEW_REQUIRES_APPROVAL")
        self.assertEqual(x["nom_preview"]["finalFilename"],"009_DEMO.pdf")
        self.assertEqual(n.calls[0]["rule_id"],"NOM-002")
        self.assertFalse(x["write_performed"])
        self.assertTrue(x["R07_preview_pending"])

    def test_nom_adapter_must_be_preview_only(self):
        class WrongNom:
            def preview(self,**kw):
                return {"status":"OK","rule_id":"NOM-002","write_performed":True,
                        "mode":"PREVIEW_ONLY","finalFilename":"009_TEST.pdf"}
        with self.assertRaises(ContractViolation):
            HybridOcrNom(WrongNom()).preview(source=source(),original_bytes=PDF,
                record=record(),operation_id="DEMO_OPERATION_001",
                expected_tenant="test",rule_id="NOM-002",reviewed_fields={})

    def test_node_nom_response_must_use_own_rule(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.js"
            path.write_text("module.exports={}",encoding="utf-8")
            n=ExistingNomPreview(path)
            res = json.dumps({
                "status":"OK","rule_id":"NOM-003","mode":"PREVIEW_ONLY",
                "write_performed":False,"finalFilename":"009_TEST.pdf",
            })
            with mock.patch("gaia_document_mcp.hybrid.subprocess.run",
                            return_value=subprocess.CompletedProcess([],0,stdout=res,stderr="")):
                with self.assertRaises(ContractViolation):
                    n.preview(rule_id="NOM-002",client_id="009",provided={"DATA":"01-01-2026"})

    def test_node_nom_response_does_not_allow_path_traversal(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.js"
            path.write_text("module.exports={}",encoding="utf-8")
            n=ExistingNomPreview(path)
            res=json.dumps({"status":"OK","rule_id":"NOM-002","mode":"PREVIEW_ONLY",
                            "write_performed":False,"finalFilename":"009_../file.pdf"})
            with mock.patch("gaia_document_mcp.hybrid.subprocess.run",
                            return_value=subprocess.CompletedProcess([],0,stdout=res,stderr="")):
                with self.assertRaises(ContractViolation):
                    n.preview(rule_id="NOM-002",client_id="009",provided={})

    def test_bad_nom_fields_rejected(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.js"
            path.write_text("module.exports={}",encoding="utf-8")
            n=ExistingNomPreview(path)
            with self.assertRaises(ContractViolation):
                n.preview(rule_id="NOM-002",client_id="009",provided={"DATA":object()})

