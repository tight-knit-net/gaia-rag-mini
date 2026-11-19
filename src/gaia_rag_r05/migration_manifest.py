"""R07 deterministic reconciliation of two APPROVED-memory snapshots.

This module creates a plan, NEVER imports, upserts, deletes or approves data.
The default case is that old and candidate readers share the same Qdrant
collection, so copy is unnecessary and could duplicate records.
"""
from __future__ import annotations

import hashlib
import json
import uuid


def _fingerprint(item: dict) -> str:
    relevant = {key: item.get(key) for key in (
        "namespace", "process_id", "approved", "title", "text",
        "source_ref", "source_type", "document_sha256", "approved_at",
        "approved_by", "kind")}
    blob = json.dumps(relevant, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _by_id(items):
    found = {}
    for item in items:
        if not isinstance(item, dict) or item.get("approved") is not True:
            raise ValueError("UNAPPROVED_OR_INVALID_RECORD")
        ident = item.get("id")
        try:
            ident = str(uuid.UUID(str(ident)))
        except (ValueError, TypeError, AttributeError):
            raise ValueError("INVALID_POINT_ID") from None
        if not isinstance(item.get("namespace"), str) or not item.get("process_id"):
            raise ValueError("MISSING_SCOPE_METADATA")
        if ident in found:
            raise ValueError("DUPLICATE_POINT_ID")
        found[ident] = _fingerprint(item)
    return found


def compare_approved_snapshots(legacy_items: list[dict], candidate_items: list[dict],
                               *, legacy_complete: bool, candidate_complete: bool):
    """No GO if either inventory is incomplete; never expose memory text."""
    old, new = _by_id(legacy_items), _by_id(candidate_items)
    missing = sorted(set(old) - set(new))
    extra = sorted(set(new) - set(old))
    inconsistent = sorted(k for k in set(old) & set(new) if old[k] != new[k])
    complete = legacy_complete is True and candidate_complete is True
    return {
        "legacy_approved_count": len(old), "candidate_approved_count": len(new),
        "missing_in_candidate_ids": missing,
        "extra_in_candidate_ids": extra,
        "content_mismatch_ids": inconsistent,
        "inventories_complete": complete,
        "copy_required": bool(missing) if complete else None,
        "candidate_read_parity": complete and not (missing or extra or inconsistent),
        "migration_authorized": False, "writes_performed": 0,
        "next_step": (
            "NO_COPY_REQUIRED_VERIFY_SHARED_STORAGE"
            if complete and not (missing or extra or inconsistent)
            else "HUMAN_RECONCILIATION_AND_SEPARATE_APPROVAL_REQUIRED"
        ),
    }


def classify_legacy_pending(proposals: list[dict]):
    """Legacy proposals are not valid R07 approvals without document evidence."""
    counts = {"pending": 0, "approved": 0, "discarded": 0, "other": 0}
    for proposal in proposals:
        if not isinstance(proposal, dict) or not isinstance(proposal.get("id"), str):
            raise ValueError("INVALID_LEGACY_PROPOSAL")
        status = proposal.get("status")
        counts[status if status in counts else "other"] += 1
    return {
        "counts": counts, "auto_import": False,
        "manual_review_required": counts["pending"],
        "unverified_document_approvals": True,
        "reason": "R07 requires source_ref, exact process, document_approval_ref and SHA256",
        "writes_performed": 0,
    }
