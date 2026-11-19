"""Versioned metadata-only documentary contracts; no external effects (v2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re

class ContractViolation(ValueError):
    """Invalid or unverifiable contract structure. Not an authorization decision."""

_HASH = re.compile(r"^[0-9a-f]{64}$")
_REF = re.compile(r"^[A-Za-z0-9_.:/-]{1,200}$")
_ID = re.compile(r"^[A-Za-z0-9_-]{5,150}$")
_OP_ID = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
_PROVIDERS = frozenset({"drive", "dropbox", "local", "generated", "notion"})
_KINDS = frozenset({
    "ocr", "pdf_transform", "catalog", "nomenclature",
    "document_create", "signature", "workspace",
})
_STATES = frozenset({"completed", "review_required", "blocked", "failed"})

def _safe_str(value: str, pattern: re.Pattern, name: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractViolation("INVALID_" + name)

def _digest(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class DocumentSource:
    """Origin identity independently of case assignment. Never certifies origin."""
    drive_id: str | None
    file_id: str
    client_id: str | None
    process_id: str | None
    source_version: str
    sha256_original: str | None
    source_provider: str = "drive"

    def __post_init__(self) -> None:
        if self.source_provider not in _PROVIDERS:
            raise ContractViolation("INVALID_SOURCE_PROVIDER")
        _safe_str(self.file_id, _ID, "FILE_ID")
        if self.source_provider == "drive":
            _safe_str(self.drive_id, _ID, "DRIVE_ID")
        elif self.drive_id is not None:
            raise ContractViolation("UNEXPECTED_DRIVE_ID")
        if self.client_id is not None:
            if not isinstance(self.client_id, str) or not re.fullmatch(r"[0-9]{3}", self.client_id):
                raise ContractViolation("INVALID_CLIENT_ID")
        if self.process_id is not None:
            _safe_str(self.process_id, _REF, "PROCESS_ID")
        _safe_str(self.source_version, _REF, "SOURCE_VERSION")
        if self.sha256_original is not None:
            _safe_str(self.sha256_original, _HASH, "SOURCE_HASH")
        # Fail early; do not postpone source_ref failure until an audit/write.
        _safe_str(self.source_ref, _REF, "SOURCE_REF")

    @property
    def source_ref(self) -> str:
        if self.source_provider == "drive":
            return f"drive:{self.drive_id}:{self.file_id}"
        return f"{self.source_provider}:{self.file_id}"

    @property
    def bound_to_case(self) -> bool:
        return self.client_id is not None and self.process_id is not None

    def matches_original(self, raw: bytes) -> bool:
        """Actual byte equality; a supplied SHA string alone is not evidence."""
        return (isinstance(raw, bytes) and self.sha256_original is not None
                and sha256(raw).hexdigest() == self.sha256_original)

@dataclass(frozen=True)
class Evidence:
    """Untrusted review claim with locator; authorization is server-controlled."""
    source_file_id: str
    locator: str
    reviewer_verified: bool = False

    def __post_init__(self) -> None:
        _safe_str(self.source_file_id, _ID, "EVIDENCE_SOURCE")
        if (not isinstance(self.locator, str) or not self.locator.strip()
                or len(self.locator) > 160
                or any(ord(c) < 32 for c in self.locator)):
            raise ContractViolation("INVALID_EVIDENCE_LOCATOR")
        if not isinstance(self.reviewer_verified, bool):
            raise ContractViolation("INVALID_EVIDENCE_VERIFICATION")

@dataclass(frozen=True)
class DocumentEvent:
    """One versioned operation event. Not a permission to write or to approve."""
    source: DocumentSource
    operation: str
    status: str
    provider: str
    source_verified: bool
    operation_id: str
    event_revision: int = 1
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
        if not isinstance(self.source, DocumentSource):
            raise ContractViolation("INVALID_SOURCE")
        if self.operation not in _KINDS or self.status not in _STATES:
            raise ContractViolation("INVALID_OPERATION_OR_STATUS")
        _safe_str(self.operation_id, _OP_ID, "OPERATION_ID")
        if isinstance(self.event_revision, bool) or not isinstance(self.event_revision, int) or not 1 <= self.event_revision <= 1_000_000:
            raise ContractViolation("INVALID_EVENT_REVISION")
        if not isinstance(self.provider, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", self.provider):
            raise ContractViolation("INVALID_PROVIDER")
        for name in ("source_verified", "fields_verified", "client_verified", "ocr_reviewed", "external_llm_used"):
            if not isinstance(getattr(self, name), bool):
                raise ContractViolation("INVALID_" + name.upper())
        if not isinstance(self.summary, str) or len(self.summary) > 4000:
            raise ContractViolation("INVALID_SUMMARY")
        if self.derived_sha256 is not None:
            _safe_str(self.derived_sha256, _HASH, "DERIVED_HASH")
        if self.rule_id is not None and not re.fullmatch(r"NOM-[0-9]{3}", self.rule_id):
            raise ContractViolation("INVALID_RULE")
        if self.proposed_filename is not None:
            n = self.proposed_filename
            if (self.source.client_id is None or not isinstance(n, str)
                    or not n.startswith(self.source.client_id + "_")
                    or len(n.encode("utf-8")) > 240 or n.endswith((".", " "))
                    or ".." in n or any(c in n for c in "\\/:*?\"<>|")
                    or any(ord(c) < 32 for c in n)):
                raise ContractViolation("INVALID_FILENAME")
        if (not isinstance(self.evidence, tuple) or
                any(not isinstance(x, Evidence) or x.source_file_id != self.source.file_id
                    for x in self.evidence)):
            raise ContractViolation("INVALID_EVIDENCE")

    def evidence_digest(self) -> str:
        """Hash locators/review claims without exposing raw text in a receipt."""
        parts = sorted((x.source_file_id, x.locator, x.reviewer_verified) for x in self.evidence)
        return _digest(parts)

    def fingerprint(self) -> str:
        """Identity of an exact event revision, including all review-relevant claims.

        operation_id is assigned by an orchestrator (same on retries); changing
        status/summary/evidence/revision changes the event_key.
        """
        return _digest({
            "schema": "gaia.document-event.v2",
            "source_ref": self.source.source_ref,
            "source_provider": self.source.source_provider,
            "client_id": self.source.client_id,
            "process_id": self.source.process_id,
            "source_version": self.source.source_version,
            "source_hash": self.source.sha256_original,
            "operation_id": self.operation_id,
            "event_revision": self.event_revision,
            "operation": self.operation,
            "status": self.status,
            "provider": self.provider,
            "claims": [self.source_verified, self.fields_verified,
                       self.client_verified, self.ocr_reviewed, self.external_llm_used],
            "summary_sha256": sha256(self.summary.encode("utf-8")).hexdigest(),
            "evidence_digest": self.evidence_digest(),
            "derived_hash": self.derived_sha256,
            "rule_id": self.rule_id,
            "proposed_filename": self.proposed_filename,
        })

    def envelope(self) -> dict:
        """Metadata-only event envelope. No raw OCR, summary, or direct writes."""
        return {
            "schema": "gaia.document-event.v2",
            "event_key": self.fingerprint(),
            "operation_id": self.operation_id,
            "event_revision": self.event_revision,
            "source_ref": self.source.source_ref,
            "source_provider": self.source.source_provider,
            "source_version": self.source.source_version,
            "document_sha256": self.source.sha256_original,
            "derived_sha256": self.derived_sha256,
            "client_id": self.source.client_id,
            "process_id": self.source.process_id,
            "operation": self.operation,
            "status": self.status,
            "provider": self.provider,
            "evidence_sha256": self.evidence_digest(),
            "summary_sha256": sha256(self.summary.encode("utf-8")).hexdigest(),
        }

