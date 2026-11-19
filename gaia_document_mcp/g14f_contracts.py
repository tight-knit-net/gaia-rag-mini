"""G14-F independent synthetic boundary contracts; NO live integrations.

These pure helpers prepare an event/approval design for operator-only GAIA.
The observations, pages and R06 readbacks below are *untrusted fixtures*.
No actual authentication, provider inspection, DB, Qdrant or memory write.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from .contracts import ContractViolation, DocumentEvent
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly

_SHA = re.compile(r"^[a-f0-9]{64}$")
_REF = re.compile(r"^[A-Za-z0-9_.:/-]{3,200}$")

def _expect(value: str, pattern: re.Pattern, message: str) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractViolation(message)

def _fingerprint(obj) -> str:
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class SyntheticSourceObservation:
    """Explicit synthetic readback, never an authority or source of permission."""
    process_id: str
    process_key: str
    source_ref: str
    source_version: str
    original_sha256: str

    def __post_init__(self):
        for item in (self.process_id, self.process_key,
                     self.source_ref, self.source_version):
            _expect(item, _REF, "INVALID_SOURCE_OBSERVATION")
        _expect(self.original_sha256, _SHA, "INVALID_SOURCE_OBSERVATION")

def event_contract_preview(*, owner: SyntheticOwnerOnly, claimed_owner: str,
                           process: AdministrativeProcess, event: DocumentEvent,
                           observation: SyntheticSourceObservation,
                           original: bytes) -> dict:
    """Pure OCR/NOM/document-event envelope to candidate staging, not capture."""
    if not isinstance(owner, SyntheticOwnerOnly):
        raise ContractViolation("OWNER_FIXTURE_REQUIRED")
    owner.require(claimed_owner)
    if (not isinstance(process, AdministrativeProcess)
            or not isinstance(event, DocumentEvent)
            or not isinstance(observation, SyntheticSourceObservation)
            or not isinstance(original, bytes)):
        raise ContractViolation("INVALID_BOUNDARY_INPUT")
    if event.source.process_id != process.process_id:
        raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
    if (observation.process_id != process.process_id
            or observation.process_key != process.process_key):
        raise ContractViolation("OBSERVATION_PROCESS_MISMATCH")
    if (observation.source_ref != event.source.source_ref
            or observation.source_version != event.source.source_version):
        raise ContractViolation("SOURCE_VERSION_MISMATCH")
    if (observation.original_sha256 != event.source.sha256_original
            or not event.source.matches_original(original)):
        raise ContractViolation("SOURCE_HASH_MISMATCH")
    if event.status not in ("completed", "review_required"):
        raise ContractViolation("EVENT_NOT_ELIGIBLE")
    if event.operation == "ocr" and event.provider.lower() == "mock":
        raise ContractViolation("MOCK_OCR_NOT_EVIDENCE")
    if (not event.source.file_id.startswith("FILE_DEMO_")
            or not event.summary.startswith("DEMO: ")):
        raise ContractViolation("SYNTHETIC_FIXTURE_REQUIRED")
    envelope = event.envelope()
    return {
        "schema": "gaia.g14f-event-preview.v1",
        "event_key": envelope["event_key"],
        "process_key": process.process_key,
        "process_id": process.process_id,
        "source_ref": envelope["source_ref"],
        "source_version": envelope["source_version"],
        "source_sha256": observation.original_sha256,
        "evidence_sha256": envelope["evidence_sha256"],
        "operation": envelope["operation"],
        "candidate_fingerprint": _fingerprint({
            "process_key": process.process_key, "process_id": process.process_id,
            "source_ref": observation.source_ref,
            "source_version": observation.source_version,
            "source_sha256": observation.original_sha256,
            "operation": event.operation, "event_revision": event.event_revision,
            "summary_sha256": envelope["summary_sha256"],
            "evidence_sha256": envelope["evidence_sha256"],
            "rule_id": event.rule_id,
        }),
        "source_authentication": "NOT_VERIFIED_IN_SYNTHETIC_GATE",
        "proposal_state": "PENDING_EVIDENCE_AND_HUMAN_REVIEW",
        "memory_approved": False,
        "qdrant_written": False,
        "document_write_performed": False,
    }

def _flatten(batches: tuple[dict, ...]) -> list[dict]:
    if not isinstance(batches, tuple):
        raise ContractViolation("INVALID_SYNTHETIC_BATCHES")
    items: list[dict] = []
    unique = set()
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("process_key"), str):
            raise ContractViolation("INVALID_SYNTHETIC_BATCHES")
        _expect(batch["process_key"], _REF, "INVALID_SYNTHETIC_BATCHES")
        if not isinstance(batch.get("candidates"), list):
            raise ContractViolation("INVALID_SYNTHETIC_BATCHES")
        for candidate in batch["candidates"]:
            if not isinstance(candidate, dict):
                raise ContractViolation("INVALID_SYNTHETIC_CANDIDATE")
            cid, summary = candidate.get("candidate_id"), candidate.get("summary")
            _expect(cid, _SHA, "INVALID_SYNTHETIC_CANDIDATE")
            if not isinstance(summary, str) or not summary.startswith("DEMO: "):
                raise ContractViolation("INVALID_SYNTHETIC_CANDIDATE")
            if (isinstance(candidate.get("candidate_revision", 1), bool)
                    or not isinstance(candidate.get("candidate_revision", 1), int)
                    or not 1 <= candidate.get("candidate_revision", 1) <= 1_000_000
                    or isinstance(candidate.get("source_count", 1), bool)
                    or not isinstance(candidate.get("source_count", 1), int)
                    or not 1 <= candidate.get("source_count", 1) <= 1_000_000):
                raise ContractViolation("INVALID_SYNTHETIC_CANDIDATE")
            key = (batch["process_key"], cid)
            if key in unique:
                raise ContractViolation("DUPLICATE_CANDIDATE")
            unique.add(key)
            items.append({
                "process_key": batch["process_key"],
                "candidate_id": cid,
                "candidate_revision": candidate.get("candidate_revision", 1),
                "summary_digest": _fingerprint(summary),
                "source_count": candidate.get("source_count", 1),
            })
    return sorted(items, key=lambda x: (x["process_key"], x["candidate_id"]))

def synthetic_batch_page(*, batches: tuple[dict, ...],
                         limit: int, offset: int = 0) -> dict:
    """Paginate a synthetic snapshot; DOES NOT query/limit a real database."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 25:
        raise ContractViolation("PAGE_LIMIT_INVALID")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ContractViolation("PAGE_OFFSET_INVALID")
    rows = _flatten(batches)
    if offset > len(rows):
        raise ContractViolation("PAGE_OFFSET_INVALID")
    snapshot = _fingerprint(rows)
    chosen = rows[offset:offset+limit]
    next_offset = offset + len(chosen)
    return {
        "schema": "gaia.g14f-page.v1",
        "snapshot": snapshot,
        "offset": offset,
        "total": len(rows),
        "items": chosen,
        "next_offset": None if next_offset == len(rows) else next_offset,
        "page_complete": next_offset == len(rows),
        "full_coverage_verified": False,
        "real_database_paginated": False,
    }

def verify_synthetic_coverage(pages: tuple[dict, ...]) -> dict:
    """Require every page, in order, from a single immutable snapshot."""
    if not isinstance(pages, tuple) or not pages:
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    prior = pages[0]
    if not isinstance(prior, dict) or prior.get("offset") != 0:
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    snapshot, total = prior.get("snapshot"), prior.get("total")
    _expect(snapshot, _SHA, "PAGE_SNAPSHOT_MISMATCH")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    expected_offset, seen, rows = 0, set(), []
    for i, page in enumerate(pages):
        if (not isinstance(page, dict) or page.get("snapshot") != snapshot
                or page.get("total") != total
                or page.get("offset") != expected_offset):
            raise ContractViolation("PAGE_SNAPSHOT_MISMATCH")
        items = page.get("items")
        if not isinstance(items, list) or (not items and total != 0):
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
        for item in items:
            if not isinstance(item, dict):
                raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
            key = (item.get("process_key"), item.get("candidate_id"))
            if key in seen:
                raise ContractViolation("PAGE_DUPLICATE")
            seen.add(key)
            rows.append(item)
        expected_offset += len(items)
        if i < len(pages)-1 and page.get("next_offset") != expected_offset:
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    if (expected_offset != total or pages[-1].get("next_offset") is not None
            or _fingerprint(rows) != snapshot):
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    return {
        "schema": "gaia.g14f-synthetic-coverage.v1",
        "snapshot": snapshot, "coverage_verified_for_fixture": True,
        "count": total, "real_database_coverage_verified": False,
        "review_authorized": False,
    }

def synthetic_readback_contract(*, expected: dict, observed: dict) -> dict:
    """Compare one fictional R06 point, NOT a Qdrant read or approval."""
    required = ("point_id", "namespace", "process_id", "source_ref",
                "document_sha256", "document_approval_ref",
                "proposal_id", "approved_by", "approval_event_ref")
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        raise ContractViolation("READBACK_INCOMPLETE")
    if any(not isinstance(expected.get(k), str) or not expected[k].strip()
           for k in required):
        raise ContractViolation("READBACK_INCOMPLETE")
    _expect(expected["document_sha256"], _SHA, "READBACK_INCOMPLETE")
    if observed.get("approved") is not True:
        raise ContractViolation("READBACK_NOT_APPROVED")
    for field in required:
        if observed.get(field) != expected[field]:
            raise ContractViolation("READBACK_MISMATCH:" + field)
    return {
        "schema": "gaia.g14f-synthetic-readback.v1",
        "point_id": expected["point_id"],
        "match_in_test_fixture": True,
        "real_qdrant_readback": False,
        "real_human_approval_verified": False,
        "memory_write_performed": False,
    }

def synthetic_unknown_decision(state: str) -> dict:
    if state not in ("UNKNOWN_SYNTHETIC", "RESERVED_SYNTHETIC",
                     "CONFLICT_SYNTHETIC", "COMMITTED_SYNTHETIC"):
        raise ContractViolation("UNKNOWN_STATE_INVALID")
    return {
        "state": state,
        "safe_action": "READBACK_AND_RECONCILE" if state == "UNKNOWN_SYNTHETIC"
                       else "NO_AUTOMATIC_EXTERNAL_RETRY",
        "automatically_retried": False,
        "external_effect_verified": False,
    }
