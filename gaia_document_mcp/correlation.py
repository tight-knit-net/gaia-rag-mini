"""Additive, synthetic-only P0/P1 correlation contracts.

No server identity, durable storage, deployment, approvals or external calls.
The observed scope/version are fixtures; authentication must happen elsewhere.
The existing DocumentSource and DocumentEvent v2 stay unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from .contracts import ContractViolation, DocumentEvent

_ID = re.compile(r"^[A-Za-z0-9_-]{5,100}$")
_SCOPE = re.compile(r"^[A-Za-z0-9_.:-]{3,120}$")
_REF = re.compile(r"^[A-Za-z0-9_.:/-]{1,200}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_KEY = re.compile(r"^[A-Za-z0-9_-]{12,100}$")

def check(v, pattern, message):
    if not isinstance(v, str) or pattern.fullmatch(v) is None:
        raise ContractViolation(message)

def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(data.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class LogicalDocument:
    document_id: str
    client_scope: str
    client_id: str
    process_id: str

    def __post_init__(self):
        check(self.document_id, _ID, "DOCUMENT_ID_INVALID")
        check(self.client_scope, _SCOPE, "CLIENT_SCOPE_INVALID")
        if not isinstance(self.client_id, str) or re.fullmatch(r"[0-9]{3}", self.client_id) is None:
            raise ContractViolation("CLIENT_ID_INVALID")
        check(self.process_id, _REF, "PROCESS_ID_INVALID")

@dataclass(frozen=True)
class RevisionSnapshot:
    """One candidate document revision, never event_revision."""
    document_id: str
    revision_id: str
    parent_revision_id: str | None
    client_scope: str
    source_ref: str
    source_version: str
    original_sha256: str
    source_kind: str | None = None
    interop_state: str = "review_required"

    def __post_init__(self):
        check(self.document_id, _ID, "DOCUMENT_ID_INVALID")
        check(self.revision_id, _ID, "DOCUMENT_REVISION_ID_INVALID")
        if self.parent_revision_id is not None:
            check(self.parent_revision_id, _ID, "PARENT_REVISION_ID_INVALID")
            if self.parent_revision_id == self.revision_id:
                raise ContractViolation("REVISION_CYCLE")
        check(self.client_scope, _SCOPE, "CLIENT_SCOPE_INVALID")
        check(self.source_ref, _REF, "SOURCE_REF_INVALID")
        check(self.source_version, _REF, "SOURCE_VERSION_INVALID")
        check(self.original_sha256, _HASH, "SOURCE_HASH_INVALID")
        if self.source_kind not in (None, "odt", "gdl_ds"):
            raise ContractViolation("SOURCE_KIND_INVALID")
        if self.interop_state not in ("native", "review_required", "verified"):
            raise ContractViolation("INTEROP_STATE_INVALID")
        if self.source_kind is None and self.interop_state != "review_required":
            raise ContractViolation("IMPORTED_NOT_EDITABLE")

@dataclass(frozen=True)
class ObservedRevision:
    """Untrusted simulation of a backend readback, not an authorization token."""
    document_id: str
    current_revision_id: str
    client_scope: str
    source_ref: str
    source_version: str

    def __post_init__(self):
        check(self.document_id, _ID, "DOCUMENT_ID_INVALID")
        check(self.current_revision_id, _ID, "REVISION_ID_INVALID")
        check(self.client_scope, _SCOPE, "CLIENT_SCOPE_INVALID")
        check(self.source_ref, _REF, "SOURCE_REF_INVALID")
        check(self.source_version, _REF, "SOURCE_VERSION_INVALID")

class CorrelationPreview:
    """Pure preview. The server must verify the scope and observation in reality."""

    @staticmethod
    def evaluate(*, document: LogicalDocument, revision: RevisionSnapshot,
                 observation: ObservedRevision, event: DocumentEvent,
                 allowed_scope: str, original_bytes: bytes) -> dict:
        if (not isinstance(document, LogicalDocument)
                or not isinstance(revision, RevisionSnapshot)
                or not isinstance(observation, ObservedRevision)
                or not isinstance(event, DocumentEvent)
                or not isinstance(original_bytes, bytes)):
            raise ContractViolation("CORRELATION_INPUT_INVALID")
        if (allowed_scope != document.client_scope
                or revision.client_scope != document.client_scope
                or observation.client_scope != document.client_scope):
            raise ContractViolation("FORBIDDEN_CLIENT_SCOPE")
        if document.document_id != revision.document_id or document.document_id != observation.document_id:
            raise ContractViolation("DOCUMENT_ID_MISMATCH")
        if observation.current_revision_id != revision.revision_id:
            raise ContractViolation("REVISION_CONFLICT")
        if revision.source_ref != observation.source_ref or revision.source_ref != event.source.source_ref:
            raise ContractViolation("SOURCE_REF_MISMATCH")
        if revision.source_version != observation.source_version or revision.source_version != event.source.source_version:
            raise ContractViolation("REVISION_CONFLICT")
        if event.source.client_id != document.client_id or event.source.process_id != document.process_id:
            raise ContractViolation("CASE_BINDING_MISMATCH")
        if (event.source.sha256_original is None
                or event.source.sha256_original != revision.original_sha256
                or not event.source.matches_original(original_bytes)):
            raise ContractViolation("SOURCE_HASH_MISMATCH")
        if len(original_bytes) > 15 * 1024 * 1024:
            raise ContractViolation("ORIGINAL_TOO_LARGE")
        request_fingerprint = digest({
            "scope": document.client_scope,
            "document_id": document.document_id,
            "revision_id": revision.revision_id,
            "source_ref": revision.source_ref,
            "source_version": revision.source_version,
            "original_sha256": revision.original_sha256,
            "operation": event.operation,
            "rule_id": event.rule_id,
            "proposed_filename": event.proposed_filename,
        })
        return {
            "schema": "gaia.correlation-preview.v1",
            "document_id": document.document_id,
            "document_revision_id": revision.revision_id,
            "parent_revision_id": revision.parent_revision_id,
            "client_scope_digest": sha256(document.client_scope.encode("utf-8")).hexdigest(),
            "source_ref": event.source.source_ref,
            "source_sha256": revision.original_sha256,
            "event_key": event.fingerprint(),
            "request_fingerprint": request_fingerprint,
            "source_kind": revision.source_kind,
            "interop_state": revision.interop_state,
            "requires_authenticated_scope": True,
            "requires_document_approval": True,
            "requires_r06_memory_approval": True,
            "r07_comparison_pending": True,
            "is_preview": True,
            "persisted": False,
            "write_performed": False,
        }

class SyntheticIdempotencyLedger:
    """RAM-only simulation: unique request fingerprint per scope+request key."""

    def __init__(self):
        self._requests = {}

    def register(self, *, scope: str, idempotency_key: str, preview: dict) -> dict:
        check(scope, _SCOPE, "CLIENT_SCOPE_INVALID")
        check(idempotency_key, _KEY, "IDEMPOTENCY_KEY_INVALID")
        if (not isinstance(preview, dict)
                or preview.get("schema") != "gaia.correlation-preview.v1"
                or preview.get("is_preview") is not True
                or preview.get("persisted") is not False
                or preview.get("write_performed") is not False
                or preview.get("client_scope_digest") != sha256(scope.encode("utf-8")).hexdigest()):
            raise ContractViolation("UNTRUSTED_PREVIEW_OR_SCOPE")
        fingerprint = preview.get("request_fingerprint")
        check(fingerprint, _HASH, "REQUEST_FINGERPRINT_INVALID")
        key = (scope, idempotency_key)
        prior = self._requests.get(key)
        if prior is not None:
            if prior["request_fingerprint"] != fingerprint:
                raise ContractViolation("IDEMPOTENCY_CONFLICT")
            return {**prior, "replayed": True}
        receipt = {
            "schema": "gaia.synthetic-idempotency.v1",
            "client_scope_digest": preview["client_scope_digest"],
            "request_fingerprint": fingerprint,
            "synthetic_run_id": digest({"scope": scope, "key": idempotency_key, "fp": fingerprint})[:32],
            "replayed": False,
            "persisted": False,
            "write_performed": False,
        }
        self._requests[key] = dict(receipt)
        return dict(receipt)
