"""Lean OCR -> NOM preview adapter using the existing engines, not replacements.

The adapters can point at the existing private OCR REST interface and at a
trusted, checked-out copy of the existing NOM JS engine. No provider writes,
no signature, no direct Qdrant connection, no approval by LLM.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import http.client
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, quote
from .contracts import ContractViolation, DocumentEvent, DocumentSource

_UUID = re.compile(r"^[0-9a-fA-F-]{32,36}$")
_TENANT = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_RULE = re.compile(r"^NOM-[0-9]{3}$")
_MAX_RESPONSE = 3 * 1024 * 1024
_MAX_INPUT = 32 * 1024
_MAX_FILE = 15 * 1024 * 1024

@dataclass(frozen=True)
class LegacyOcrRecord:
    document_id: str
    tenant: str
    sha256: str
    provider: str
    status: str
    text: str

    @classmethod
    def parse(cls, data: dict) -> "LegacyOcrRecord":
        if not isinstance(data, dict):
            raise ContractViolation("INVALID_OCR_RECORD")
        rec = cls(
            document_id=data.get("id"), tenant=data.get("tenant"),
            sha256=data.get("sha256"), provider=data.get("provider"),
            status=data.get("status"), text=data.get("text"),
        )
        if (not isinstance(rec.document_id, str) or not _UUID.fullmatch(rec.document_id)
                or not isinstance(rec.tenant, str) or not _TENANT.fullmatch(rec.tenant)
                or not isinstance(rec.sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", rec.sha256)
                or rec.provider not in ("tesseract", "iloveapi", "mock")
                or rec.status != "processed"
                or not isinstance(rec.text, str)
                or len(rec.text.encode("utf-8")) > _MAX_RESPONSE):
            raise ContractViolation("OCR_RECORD_NOT_VERIFIED")
        return rec

class InternalOcrReader:
    """Read-only REST adapter; only loopback is allowed in this milestone.

    Does not expose the OCR MCP itself or its unauthenticated tools.
    The token must be supplied by an authenticated backend secret manager.
    """
    def __init__(self, base_url: str, token: str):
        u = urlsplit(base_url)
        if (u.scheme != "http" or u.hostname not in ("127.0.0.1", "localhost")
                or not u.port or u.path not in ("", "/") or u.query or u.fragment
                or u.username or u.password):
            raise ContractViolation("OCR_URL_NOT_LOOPBACK")
        if not isinstance(token, str) or len(token) < 12:
            raise ContractViolation("OCR_TOKEN_NOT_CONFIGURED")
        self._port = u.port
        self._token = token

    def read(self, document_id: str, tenant: str) -> LegacyOcrRecord:
        if not isinstance(document_id, str) or not _UUID.fullmatch(document_id):
            raise ContractViolation("INVALID_OCR_DOCUMENT_ID")
        if not isinstance(tenant, str) or not _TENANT.fullmatch(tenant):
            raise ContractViolation("INVALID_OCR_TENANT")
        conn = http.client.HTTPConnection("127.0.0.1", self._port, timeout=8)
        try:
            path = "/v1/documents/" + quote(document_id, safe="") + "?tenant=" + quote(tenant, safe="")
            conn.request("GET", path, headers={
                "Authorization": "Bearer " + self._token, "Accept": "application/json"
            })
            response = conn.getresponse()
            if response.status != 200:
                raise ContractViolation("OCR_HTTP_READ_FAILED")
            payload = response.read(_MAX_RESPONSE + 1)
            if len(payload) > _MAX_RESPONSE:
                raise ContractViolation("OCR_RESPONSE_TOO_LARGE")
            try:
                record = LegacyOcrRecord.parse(json.loads(payload))
            except (ValueError, UnicodeDecodeError, TypeError) as exc:
                raise ContractViolation("OCR_RESPONSE_INVALID") from exc
        finally:
            conn.close()
        if record.document_id != document_id or record.tenant != tenant:
            raise ContractViolation("OCR_TENANT_DOCUMENT_MISMATCH")
        return record

class ExistingNomPreview:
    """Invoke the exact existing NOM index.js at a trusted admin-provided path.

    No copied nomenclature rules, no shell, no Drive interaction. Requires
    node installed and a checked-out NOM engine; never accepts a root from OCR.
    """
    _SCRIPT = (
        "const fs=require('node:fs');"
        "const nom=require(process.argv[1]);"
        "const d=JSON.parse(fs.readFileSync(0,'utf8'));"
        "process.stdout.write(JSON.stringify(nom.suggestDocumentName(d)));"
    )
    def __init__(self, index_path: Path):
        path = Path(index_path).resolve(strict=True)
        if path.name != "index.js" or not path.is_file():
            raise ContractViolation("NOM_ENGINE_PATH_INVALID")
        self._index = path

    def preview(self, *, rule_id: str, client_id: str,
                provided: dict, raw_fields: dict | None = None,
                signals: list[str] | None = None) -> dict:
        if not isinstance(rule_id, str) or not _RULE.fullmatch(rule_id):
            raise ContractViolation("NOM_RULE_INVALID")
        if not isinstance(client_id, str) or not re.fullmatch(r"[0-9]{3}", client_id):
            raise ContractViolation("NOM_CLIENT_INVALID")
        if not isinstance(provided, dict) or not all(
                isinstance(k, str) and isinstance(v, (str, bool, int)) for k, v in provided.items()):
            raise ContractViolation("NOM_FIELDS_INVALID")
        if raw_fields is not None and (not isinstance(raw_fields, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in raw_fields.items())):
            raise ContractViolation("NOM_RAW_FIELDS_INVALID")
        if signals is not None and (not isinstance(signals, list)
                                    or not all(isinstance(x, str) for x in signals)):
            raise ContractViolation("NOM_SIGNALS_INVALID")
        body = json.dumps({
            "rule_id": rule_id, "clientNNN": client_id,
            "provided": provided, "rawFields": raw_fields or {},
            "signals": signals or [],
        }, ensure_ascii=False)
        if len(body.encode("utf-8")) > _MAX_INPUT:
            raise ContractViolation("NOM_REQUEST_TOO_LARGE")
        try:
            p = subprocess.run(
                ["node", "-e", self._SCRIPT, str(self._index)],
                input=body, text=True, capture_output=True, timeout=5, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ContractViolation("NOM_BACKEND_UNAVAILABLE") from exc
        if p.returncode != 0 or len(p.stdout.encode("utf-8")) > _MAX_INPUT:
            raise ContractViolation("NOM_BACKEND_FAILED")
        try:
            response = json.loads(p.stdout)
        except ValueError as exc:
            raise ContractViolation("NOM_BAD_RESPONSE") from exc
        if not isinstance(response, dict):
            raise ContractViolation("NOM_BAD_RESPONSE")
        if response.get("status") == "OK" and (
                response.get("mode") != "PREVIEW_ONLY"
                or response.get("write_performed") is not False
                or response.get("rule_id") != rule_id):
            raise ContractViolation("NOM_UNSAFE_RESPONSE")
        if response.get("status") == "OK":
            name = response.get("finalFilename")
            if (not isinstance(name, str) or not name.startswith(client_id + "_")
                    or len(name.encode("utf-8")) > 240 or name.endswith((".", " "))
                    or ".." in name or any(c in name for c in "\\\\/:*?\\\"<>|")
                    or any(ord(c) < 32 for c in name)):
                raise ContractViolation("NOM_FILENAME_UNSAFE")
        return response

class HybridOcrNom:
    """Runnable locally with a reviewed OCR record and an installed NOM engine.

    PREVIEW_ONLY even for successfully named synthetic files. Caller-supplied
    fields are NOT server proof; future authenticated review is still required.
    """
    def __init__(self, nom):
        self._nom = nom

    def preview(self, *, source: DocumentSource, original_bytes: bytes,
                record: LegacyOcrRecord, operation_id: str, expected_tenant: str,
                rule_id: str | None = None, reviewed_fields: dict | None = None) -> dict:
        if (not isinstance(source, DocumentSource)
                or not isinstance(record, LegacyOcrRecord)
                or not isinstance(original_bytes, bytes)
                or len(original_bytes) < 5 or len(original_bytes) > _MAX_FILE):
            raise ContractViolation("INVALID_OCR_INPUT")
        if not isinstance(expected_tenant, str) or record.tenant != expected_tenant:
            raise ContractViolation("OCR_TENANT_MISMATCH")
        if source.source_provider != "drive" or not original_bytes.startswith(b"%PDF-"):
            raise ContractViolation("OCR_PDF_SOURCE_REQUIRED")
        if not source.matches_original(original_bytes) or record.sha256 != source.sha256_original:
            raise ContractViolation("OCR_SHA256_MISMATCH")
        if record.provider == "mock":
            return {"status": "BLOCKED", "reason": "MOCK_OCR_NOT_REAL",
                    "write_performed": False, "memory_persisted": False}
        if source.client_id is None or source.process_id is None:
            return {"status": "BLOCKED", "reason": "CLIENT_PROCESS_BINDING_PENDING",
                    "write_performed": False, "memory_persisted": False}
        if not record.text.strip():
            return {"status": "BLOCKED", "reason": "OCR_TEXT_EMPTY",
                    "write_performed": False, "memory_persisted": False}
        event = DocumentEvent(
            source=source, operation="ocr", status="review_required",
            provider=record.provider, source_verified=True,
            operation_id=operation_id, summary="", evidence=(),
            client_verified=False, fields_verified=False, ocr_reviewed=False,
        )
        result = {"status": "OCR_REVIEW_REQUIRED",
                  "schema": "gaia.hybrid-preview.v1",
                  "source_ref": source.source_ref,
                  "source_hash": source.sha256_original,
                  "text_sha256": hashlib.sha256(record.text.encode("utf-8")).hexdigest(),
                  "event_key": event.fingerprint(),
                  "nom_preview": None,
                  "write_performed": False, "memory_persisted": False,
                  "R07_preview_pending": True}
        # Reviewed_fields is a request for a NAME preview, never proof of
        # client affiliation or a review authorization for writes/memory.
        if rule_id and reviewed_fields is not None:
            nom = self._nom.preview(
                rule_id=rule_id, client_id=source.client_id,
                provided=reviewed_fields)
            if not isinstance(nom, dict) or nom.get("write_performed") is not False:
                raise ContractViolation("NOM_EFFECT_NOT_PROHIBITED")
            if nom.get("status") == "OK" and (
                    nom.get("mode") != "PREVIEW_ONLY"
                    or nom.get("rule_id") != rule_id
                    or not isinstance(nom.get("finalFilename"), str)
                    or not nom["finalFilename"].startswith(source.client_id + "_")):
                raise ContractViolation("NOM_UNSAFE_RESPONSE")
            result["nom_preview"] = nom
            result["status"] = (
                "OCR_NOM_PREVIEW_REQUIRES_APPROVAL"
                if nom.get("status") == "OK" else "NOM_PENDING_REVIEW"
            )
        return result

