"""Versioned documentary provenance contracts. No I/O, external LLM or Qdrant writes."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re

class ContractViolation(ValueError):
    """Reject an unverified or malformed documentary envelope."""

_HASH = re.compile(r"^[0-9a-f]{64}$")
_REF = re.compile(r"^[A-Za-z0-9_.:/-]{1,200}$")
_ID = re.compile(r"^[A-Za-z0-9_-]{5,150}$")
_KINDS = frozenset({"ocr", "pdf_transform", "catalog", "nomenclature", "document_create", "signature", "workspace"})
_STATES = frozenset({"completed", "review_required", "blocked", "failed"})

def _safe_str(value: str, pattern: re.Pattern, name: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractViolation("INVALID_" + name)

def _digest(obj: dict) -> str:
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

@dataclass(frozen=True)
class DocumentSource:
    """Immutable reference. The original file remains authoritative in Drive."""
    drive_id: str
    file_id: str
    client_id: str
    process_id: str
    source_version: str
    sha256_original: str

    def __post_init__(self) -> None:
        _safe_str(self.drive_id, _ID, "DRIVE_ID")
        _safe_str(self.file_id, _ID, "FILE_ID")
        if not isinstance(self.client_id, str) or not re.fullmatch(r"\d{3}", self.client_id):
            raise ContractViolation("INVALID_CLIENT_ID")
        _safe_str(self.process_id, _REF, "PROCESS_ID")
        _safe_str(self.source_version, _REF, "SOURCE_VERSION")
        _safe_str(self.sha256_original, _HASH, "SOURCE_HASH")

    @property
    def source_ref(self) -> str:
        # Canonical stable key; no raw file path or PII. Source version is checked separately.
        value = "drive:" + self.drive_id + ":" + self.file_id
        _safe_str(value, _REF, "SOURCE_REF")
        return value

@dataclass(frozen=True)
class Evidence:
    """Evidence locator only; never put a full OCR transcript here."""
    source_file_id: str
    locator: str
    reviewer_verified: bool = False

    def __post_init__(self) -> None:
        _safe_str(self.source_file_id, _ID, "EVIDENCE_SOURCE")
        if (not isinstance(self.locator, str) or not self.locator.strip()
                or len(self.locator) > 160 or any(ord(c) < 32 for c in self.locator)):
            raise ContractViolation("INVALID_EVIDENCE_LOCATOR")
        if not isinstance(self.reviewer_verified, bool):
            raise ContractViolation("INVALID_EVIDENCE_VERIFICATION")

@dataclass(frozen=True)
class DocumentEvent:
    """Output of one tool operation, not permission to modify Drive or the RAG."""
    source: DocumentSource
    operation: str
    status: str
    provider: str
    source_verified: bool
    fields_verified: bool = False
    client_verified: bool = False
    ocr_reviewed: bool = False
    summary: str = ""
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    derived_sha256: str | None = None
    rule_id: str | None = None
    proposed_filename: str | None = None
    external_llm_used: bool = False

    def __post_init__(self) -> None:
        if self.operation not in _KINDS or self.status not in _STATES:
            raise ContractViolation("INVALID_OPERATION_OR_STATUS")
        if not isinstance(self.provider, str) or not 1 <= len(self.provider) <= 50 or not re.fullmatch(r"[a-zA-Z0-9_-]+", self.provider):
            raise ContractViolation("INVALID_PROVIDER")
        for name in ("source_verified", "fields_verified", "client_verified", "ocr_reviewed", "external_llm_used"):
            if not isinstance(getattr(self, name), bool):
                raise ContractViolation("INVALID_" + name.upper())
        if not isinstance(self.summary, str) or len(self.summary) > 4000:
            raise ContractViolation("INVALID_SUMMARY")
        if self.derived_sha256 is not None:
            _safe_str(self.derived_sha256, _HASH, "DERIVED_HASH")
        if self.rule_id is not None and not re.fullmatch(r"NOM-\d{3}", self.rule_id):
            raise ContractViolation("INVALID_RULE")
        if self.proposed_filename is not None and (len(self.proposed_filename) > 240 or
                not self.proposed_filename.startswith(self.source.client_id + "_") or
                any(x in self.proposed_filename for x in ("/", "\\", "\n", "\r"))):
            raise ContractViolation("INVALID_FILENAME")
        if not isinstance(self.evidence, tuple) or any(not isinstance(x, Evidence) or x.source_file_id != self.source.file_id for x in self.evidence):
            raise ContractViolation("INVALID_EVIDENCE")

    def fingerprint(self) -> str:
        return _digest({
            "schema": "gaia.document-event.v1",
            "file_id": self.source.file_id,
            "process_id": self.source.process_id,
            "source_version": self.source.source_version,
            "source_hash": self.source.sha256_original,
            "operation": self.operation,
            "status": self.status,
            "provider": self.provider,
            "derived_hash": self.derived_sha256,
            "rule_id": self.rule_id,
            "proposed_filename": self.proposed_filename,
        })

