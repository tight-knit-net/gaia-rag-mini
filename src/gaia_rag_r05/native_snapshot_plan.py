"""S8 native Qdrant snapshot decision plan; pure validation, NO network or writes.

Qdrant collection snapshot creates and upload recovery are distinct actions,
and restoration into a new collection needs priority='snapshot'. This function
only reviews synthetic or already obtained metadata and never executes either.
"""
from __future__ import annotations

import re

_SHA = re.compile(r"^[0-9a-f]{64}$")
_NAME = re.compile(r"^[a-zA-Z0-9_.-]{5,100}$")


def preflight(manifest: dict) -> dict:
    """Fail closed unless the independent snapshot/ledger inventories reconcile.

    Fields must be operator-produced in an independently authorized gate.
    This function never marks an operation as actually homologated.
    """
    if not isinstance(manifest, dict):
        raise ValueError("SNAPSHOT_MANIFEST_REQUIRED")
    keys = ("source_collection", "restore_collection", "snapshot_name",
            "snapshot_sha256", "source_approved_count", "restored_approved_count",
            "source_point_count", "restored_point_count", "ledger_pending_count",
            "ledger_approved_count", "inventory_complete", "checksum_verified",
            "priority", "restore_target_was_absent", "ledger_backup_verified")
    if not all(k in manifest for k in keys):
        raise ValueError("SNAPSHOT_MANIFEST_INCOMPLETE")
    source, target = manifest["source_collection"], manifest["restore_collection"]
    if (not all(isinstance(v, str) and _NAME.fullmatch(v)
                for v in (source, target))
            or source == target):
        raise ValueError("OVERWRITE_OR_UNSAFE_COLLECTION")
    if (not isinstance(manifest["snapshot_name"], str)
            or "/" in manifest["snapshot_name"]
            or "\\" in manifest["snapshot_name"]
            or not manifest["snapshot_name"].endswith(".snapshot")):
        raise ValueError("UNSAFE_SNAPSHOT_FILENAME")
    if (not isinstance(manifest["snapshot_sha256"], str)
            or not _SHA.fullmatch(manifest["snapshot_sha256"])):
        raise ValueError("SNAPSHOT_HASH_MISSING")
    count_names = ("source_approved_count", "restored_approved_count",
                   "source_point_count", "restored_point_count",
                   "ledger_pending_count", "ledger_approved_count")
    if any(type(manifest[k]) is not int or manifest[k] < 0 for k in count_names):
        raise ValueError("INVALID_INVENTORY_COUNTS")
    controls = ("inventory_complete", "checksum_verified",
                "restore_target_was_absent", "ledger_backup_verified")
    if not all(manifest[k] is True for k in controls):
        raise ValueError("SNAPSHOT_EVIDENCE_NOT_COMPLETE")
    if manifest["priority"] != "snapshot":
        raise ValueError("SNAPSHOT_PRIORITY_NOT_SAFE")
    if (manifest["source_approved_count"] != manifest["source_point_count"]
            or manifest["restored_approved_count"] != manifest["restored_point_count"]
            or manifest["source_point_count"] != manifest["restored_point_count"]):
        raise ValueError("APPROVED_POINT_RESTORE_MISMATCH")
    return {
        "synthetic_manifest_passed": True,
        "approved_points_verified_count": manifest["source_approved_count"],
        "legacy_pending_count_kept_separate": manifest["ledger_pending_count"],
        "ledger_approved_count_separate_from_qdrant": manifest["ledger_approved_count"],
        "checks_only": True,
        "network_requests": 0,
        "writes": 0,
        "qdrant_native_snapshot_recovery_executed": False,
        "host_identity_verified": False,
        "production_homologated": False,
        "migration_authorized": False,
        "legacy_cutover_authorized": False,
    }
