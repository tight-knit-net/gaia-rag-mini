"""Only RAM-based version/idempotency model for gate G14-B.

The records are disposable simulations. A successful synthetic revision is NOT
a document write or an external persistence guarantee. No database or network.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
import re
from .contracts import ContractViolation
from .process_learning import SyntheticOwnerOnly

_REF = re.compile(r"^[A-Za-z0-9_.:/-]{3,150}$")
_KEY = re.compile(r"^[A-Za-z0-9_-]{12,100}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


def _validate(value, pattern, reason):
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ContractViolation(reason)


@dataclass(frozen=True)
class SyntheticRequest:
    process_key: str
    idempotency_key: str
    expected_revision: str
    request_fingerprint: str

    def __post_init__(self):
        _validate(self.process_key, _REF, "PROCESS_KEY_INVALID")
        _validate(self.idempotency_key, _KEY, "IDEMPOTENCY_KEY_INVALID")
        _validate(self.expected_revision, _REF, "REVISION_INVALID")
        _validate(self.request_fingerprint, _HASH, "REQUEST_FINGERPRINT_INVALID")


class InMemoryRevisionCoordinator:
    """Atomically simulates two callers racing on the same revision."""

    def __init__(self, owner: SyntheticOwnerOnly):
        if not isinstance(owner, SyntheticOwnerOnly):
            raise ContractViolation("OWNER_GATE_REQUIRED")
        self._owner = owner
        self._lock = Lock()
        self._heads = {}
        self._runs = {}

    def seed(self, *, claimed_owner: str, process_key: str, revision: str) -> None:
        self._owner.require(claimed_owner)
        _validate(process_key, _REF, "PROCESS_KEY_INVALID")
        _validate(revision, _REF, "REVISION_INVALID")
        with self._lock:
            if process_key in self._heads:
                raise ContractViolation("PROCESS_ALREADY_SEEDED")
            self._heads[process_key] = revision

    def reserve(self, *, claimed_owner: str, request: SyntheticRequest) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(request, SyntheticRequest):
            raise ContractViolation("REQUEST_INVALID")
        key = (request.process_key, request.idempotency_key)
        with self._lock:
            old = self._runs.get(key)
            if old is not None:
                if old["request_fingerprint"] != request.request_fingerprint:
                    raise ContractViolation("IDEMPOTENCY_CONFLICT")
                return {**deepcopy(old), "replayed": True}
            if self._heads.get(request.process_key) != request.expected_revision:
                raise ContractViolation("REVISION_CONFLICT")
            rec = {
                "state": "RESERVED_SYNTHETIC",
                "process_key": request.process_key,
                "expected_revision": request.expected_revision,
                "request_fingerprint": request.request_fingerprint,
                "run_id": sha256(
                    (request.process_key + "|" + request.idempotency_key).encode()
                ).hexdigest()[:32],
                "replayed": False,
                "document_write_performed": False,
                "qdrant_write_performed": False,
                "durable": False,
            }
            self._runs[key] = rec
            return deepcopy(rec)

    def simulate_commit(self, *, claimed_owner: str, process_key: str,
                        idempotency_key: str, new_revision: str) -> dict:
        """Advance a RAM string only; NOT a provider commit."""
        self._owner.require(claimed_owner)
        _validate(process_key, _REF, "PROCESS_KEY_INVALID")
        _validate(idempotency_key, _KEY, "IDEMPOTENCY_KEY_INVALID")
        _validate(new_revision, _REF, "REVISION_INVALID")
        key = (process_key, idempotency_key)
        with self._lock:
            rec = self._runs.get(key)
            if rec is None:
                raise ContractViolation("RUN_NOT_FOUND")
            if rec["state"] == "UNKNOWN_SYNTHETIC":
                raise ContractViolation("RECONCILIATION_REQUIRED")
            if rec["state"] == "COMMITTED_SYNTHETIC":
                if rec["new_revision"] != new_revision:
                    raise ContractViolation("REPLAY_REVISION_MISMATCH")
                return deepcopy(rec)
            if self._heads.get(process_key) != rec["expected_revision"]:
                rec["state"] = "CONFLICT_SYNTHETIC"
                raise ContractViolation("REVISION_CONFLICT")
            if new_revision == rec["expected_revision"]:
                raise ContractViolation("REVISION_NOT_ADVANCED")
            self._heads[process_key] = new_revision
            rec["new_revision"] = new_revision
            rec["state"] = "COMMITTED_SYNTHETIC"
            return deepcopy(rec)

    def mark_unknown(self, *, claimed_owner: str, process_key: str,
                     idempotency_key: str) -> dict:
        self._owner.require(claimed_owner)
        with self._lock:
            rec = self._runs.get((process_key, idempotency_key))
            if rec is None or rec["state"] != "RESERVED_SYNTHETIC":
                raise ContractViolation("UNKNOWN_STATE_TRANSITION")
            rec["state"] = "UNKNOWN_SYNTHETIC"
            return deepcopy(rec)

    def readback(self, *, claimed_owner: str, process_key: str,
                 idempotency_key: str) -> dict:
        self._owner.require(claimed_owner)
        with self._lock:
            rec = self._runs.get((process_key, idempotency_key))
            if rec is None:
                raise ContractViolation("RUN_NOT_FOUND")
            return deepcopy(rec)

    def current_revision(self, *, claimed_owner: str, process_key: str) -> str | None:
        self._owner.require(claimed_owner)
        with self._lock:
            return self._heads.get(process_key)

    def synthetic_snapshot(self, *, claimed_owner: str) -> dict:
        """Copy of ephemeral state; does not establish durability or backup."""
        self._owner.require(claimed_owner)
        with self._lock:
            return deepcopy({"heads": self._heads, "runs": [
                {"key": list(k), "value": v} for k, v in self._runs.items()
            ]})
