"""Only *verifies* trusted server attestations; it never signs or approves them.

The issuing service (not implemented) MUST authenticate the human reviewer,
verify file bytes and evidence, authorize the case and sign with a server-only
key. These signatures are NOT R06 documentary or memory approvals.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import time
from .contracts import DocumentEvent, ContractViolation

@dataclass(frozen=True)
class ReviewAttestation:
    event_key: str
    evidence_sha256: str
    review_id: str
    reviewer_subject: str
    issued_at: int
    expires_at: int
    mac: str

    def __post_init__(self) -> None:
        if (not isinstance(self.event_key, str) or not re.fullmatch(r"[0-9a-f]{64}", self.event_key)
                or not isinstance(self.evidence_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.evidence_sha256)
                or not isinstance(self.mac, str) or not re.fullmatch(r"[0-9a-f]{64}", self.mac)
                or not isinstance(self.review_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", self.review_id)
                or not isinstance(self.reviewer_subject, str) or
                not re.fullmatch(r"[A-Za-z0-9_.:@-]{3,150}", self.reviewer_subject)
                or isinstance(self.issued_at, bool) or not isinstance(self.issued_at, int)
                or isinstance(self.expires_at, bool) or not isinstance(self.expires_at, int)
                or self.issued_at <= 0 or self.expires_at <= self.issued_at):
            raise ContractViolation("INVALID_ATTESTATION")

    def signing_bytes(self) -> bytes:
        data = ["gaia.document-review.v1", self.event_key,
                self.evidence_sha256, self.review_id, self.reviewer_subject,
                self.issued_at, self.expires_at]
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

class ReviewProofVerifier:
    """An HMAC verifier for synthetic contract tests and later trusted backend.

    Possession of the secret is NOT equivalent to verified authorization.
    The issuing server, registry and actor authentication are future gates.
    """

    def __init__(self, secret: bytes) -> None:
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ContractViolation("REVIEW_VERIFIER_KEY_REQUIRED")
        self._secret = secret

    def verify(self, event: DocumentEvent, proof: ReviewAttestation | None,
               *, now: int | None = None) -> bool:
        if not isinstance(event, DocumentEvent) or not isinstance(proof, ReviewAttestation):
            return False
        current = int(time.time()) if now is None else now
        if (isinstance(current, bool) or not isinstance(current, int) or
                proof.issued_at > current + 30 or proof.expires_at < current or
                proof.expires_at > proof.issued_at + 900):
            return False
        if not hmac.compare_digest(proof.event_key, event.fingerprint()):
            return False
        if not hmac.compare_digest(proof.evidence_sha256, event.evidence_digest()):
            return False
        expected = hmac.new(self._secret, proof.signing_bytes(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, proof.mac)

