"""Synthetic owner-operated, process-aware hybrid learning.

Captures candidate context automatically on document events, retrieves approved
knowledge across processes as labeled analogies, and leaves all candidates
pending human review. No Qdrant, persistence, auth server, or external calls.
This module receives test fixtures, not authenticated production data.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
import unicodedata

from .contracts import ContractViolation, DocumentEvent

_ID = re.compile(r"^[A-Za-z0-9_.:/-]{3,150}$")
_NUMBER = re.compile(r"^[0-9][0-9./-]{2,79}$")
_WORDS = re.compile(r"[a-z0-9]+")
_NOISE = {"a", "o", "e", "de", "da", "do", "das", "dos", "para", "em",
          "no", "na", "com", "ao", "um", "uma", "por", "que"}


def _check(value: str, pattern: re.Pattern, reason: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractViolation(reason)


def _tokens(value: str) -> set[str]:
    if not isinstance(value, str):
        raise ContractViolation("INVALID_QUERY")
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return set(_WORDS.findall(normalized)) - _NOISE


def _similarity(a: str, b: str) -> float:
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


@dataclass(frozen=True)
class AdministrativeProcess:
    """Official number has literal significance, including leading zeros."""
    process_id: str
    agency_code: str
    jurisdiction: str
    official_number: str

    def __post_init__(self) -> None:
        _check(self.process_id, _ID, "INVALID_PROCESS_ID")
        _check(self.agency_code, _ID, "INVALID_AGENCY")
        _check(self.jurisdiction, _ID, "INVALID_JURISDICTION")
        _check(self.official_number, _NUMBER, "INVALID_OFFICIAL_NUMBER")

    @property
    def process_key(self) -> str:
        return f"{self.jurisdiction.upper()}:{self.agency_code.upper()}:{self.official_number}"


@dataclass(frozen=True)
class ApprovedKnowledgeFixture:
    """Synthetic stand-in for a result from a trusted APPROVED-only RAG read.

    A caller-supplied approved flag is NOT proof that a Qdrant point is approved.
    A real connector must enforce approved=true, identity and source integrity.
    """
    point_id: str
    process_key: str
    process_id: str
    source_ref: str
    summary: str
    approval_ref: str
    approved: bool = True

    def __post_init__(self) -> None:
        for value in (self.point_id, self.process_key, self.process_id,
                      self.source_ref, self.approval_ref):
            _check(value, _ID, "INVALID_APPROVED_MEMORY_FIXTURE")
        if not isinstance(self.summary, str) or not 1 <= len(self.summary.strip()) <= 500:
            raise ContractViolation("INVALID_APPROVED_SUMMARY")
        if not isinstance(self.approved, bool):
            raise ContractViolation("INVALID_APPROVED_FLAG")


class SyntheticOwnerOnly:
    """One operator; client IDs and process IDs are not permission boundaries."""

    def __init__(self, expected_owner: str) -> None:
        _check(expected_owner, _ID, "INVALID_OWNER")
        self._expected = expected_owner

    def require(self, claimed_owner: str) -> None:
        if not isinstance(claimed_owner, str) or claimed_owner != self._expected:
            raise ContractViolation("OWNER_REQUIRED")


class HybridLearningPreview:
    """In-memory automatic candidate staging and context-aware search only."""

    def __init__(self, owner: SyntheticOwnerOnly) -> None:
        if not isinstance(owner, SyntheticOwnerOnly):
            raise ContractViolation("OWNER_GATE_REQUIRED")
        self._owner = owner
        self._pending: dict[tuple[str, str], dict] = {}

    def observe(self, *, event: DocumentEvent, process: AdministrativeProcess,
                claimed_owner: str) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(event, DocumentEvent) or not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_EVENT_OR_PROCESS")
        if event.source.process_id != process.process_id:
            raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
        if event.status not in ("completed", "review_required"):
            raise ContractViolation("INELIGIBLE_EVENT")
        if event.operation == "ocr" and event.provider.lower() == "mock":
            raise ContractViolation("MOCK_OCR_NOT_EVIDENCE")
        if not event.summary.strip() or not _tokens(event.summary):
            return {"status": "INSUFFICIENT_CONTEXT", "candidate_created": False,
                    "memory_persisted": False}
        # Staged text is untrusted and must be minimized/redacted by a future
        # trusted ingest service before durable storage or external AI.
        summary = event.summary.strip()[:500]
        signature = sha256((" ".join(sorted(_tokens(summary)))).encode()).hexdigest()
        key = (process.process_key, signature)
        existing = self._pending.get(key)
        if existing is None:
            existing = {
                "status": "PENDING_HUMAN_REVIEW",
                "candidate_id": sha256((process.process_key + ":" + signature).encode()).hexdigest(),
                "process_key": process.process_key,
                "process_id": process.process_id,
                "official_process_number": process.official_number,
                "summary": summary,
                "source_refs": [],
                "event_keys": [],
                "source_quality": "UNVERIFIED_AUTOMATIC",
                "document_approval_required": True,
                "memory_approval_required": True,
                "memory_persisted": False,
                "write_performed": False,
            }
            self._pending[key] = existing
        if event.source.source_ref not in existing["source_refs"]:
            existing["source_refs"].append(event.source.source_ref)
        fingerprint = event.fingerprint()
        if fingerprint not in existing["event_keys"]:
            existing["event_keys"].append(fingerprint)
        return {
            "status": "PENDING_HUMAN_REVIEW",
            "candidate_id": existing["candidate_id"],
            "process_key": process.process_key,
            "source_count": len(existing["source_refs"]),
            "memory_persisted": False,
            "write_performed": False,
        }

    def retrieve(self, *, process: AdministrativeProcess, query: str,
                 claimed_owner: str,
                 approved_records: tuple[ApprovedKnowledgeFixture, ...] = ()) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        if not isinstance(approved_records, tuple) or any(
                not isinstance(x, ApprovedKnowledgeFixture) for x in approved_records):
            raise ContractViolation("UNTRUSTED_APPROVED_RECORD_LIST")
        if not _tokens(query):
            return {"working_context": [], "approved_context": [],
                    "cross_process_analogies": []}
        working = []
        for item in self._pending.values():
            if item["process_key"] != process.process_key:
                continue
            score = _similarity(query, item["summary"])
            if score >= 0.3:
                working.append({
                    "candidate_id": item["candidate_id"],
                    "process_key": item["process_key"],
                    "process_id": item["process_id"],
                    "summary": item["summary"],
                    "review_status": "PENDING_HUMAN_REVIEW",
                    "score": round(score, 4),
                    "is_authoritative": False,
                })
        approved_context, analogies = [], []
        for record in approved_records:
            if not record.approved or not record.approval_ref:
                continue
            score = _similarity(query, record.summary)
            if score < 0.3:
                continue
            match = {
                "point_id": record.point_id,
                "process_key": record.process_key,
                "process_id": record.process_id,
                "source_ref": record.source_ref,
                "approval_ref": record.approval_ref,
                "summary": record.summary,
                "score": round(score, 4),
                "origin_approved": True,
                "use_as_current_process_fact": record.process_key == process.process_key,
            }
            if record.process_key == process.process_key:
                approved_context.append(match)
            else:
                match["relation"] = "ANALOGY_ONLY"
                match["use_as_current_process_fact"] = False
                analogies.append(match)
        sorter = lambda x: (-x["score"], x.get("point_id", x.get("candidate_id", "")))
        return {
            "working_context": sorted(working, key=sorter),
            "approved_context": sorted(approved_context, key=sorter),
            "cross_process_analogies": sorted(analogies, key=sorter),
            "approved_records_are_synthetic_fixtures": True,
            "qdrant_written": False,
        }

    def pending_count(self) -> int:
        return len(self._pending)
