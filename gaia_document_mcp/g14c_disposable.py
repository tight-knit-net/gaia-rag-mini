"""G14-C disposable SQLite lab for owner-operated document workflows.

Explicit tempfile.TemporaryDirectory workspace only. Never connect to production.
No approved memory, actual document write, or Qdrant integration occurs here.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from .contracts import ContractViolation, DocumentEvent
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly, _tokens
from .owner_concurrency import SyntheticRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS process_heads (
    process_key TEXT PRIMARY KEY,
    revision TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requests (
    process_key TEXT NOT NULL,
    request_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    expected_revision TEXT NOT NULL,
    run_id TEXT NOT NULL,
    state TEXT NOT NULL,
    new_revision TEXT,
    PRIMARY KEY (process_key, request_key)
);
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    process_key TEXT NOT NULL,
    process_id TEXT NOT NULL,
    topic_digest TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_refs_json TEXT NOT NULL,
    event_keys_json TEXT NOT NULL,
    review_status TEXT NOT NULL,
    batch_id TEXT,
    UNIQUE (process_key, topic_digest)
);
CREATE TABLE IF NOT EXISTS batch_receipts (
    batch_id TEXT PRIMARY KEY,
    process_key TEXT NOT NULL,
    decision TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    operator_ref TEXT NOT NULL
);
"""

def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()

def _batch_id(process_key: str, snapshots: list[str]) -> str:
    return _sha(json.dumps([process_key, *sorted(snapshots)], separators=(",", ":")))

def _candidate_snapshot(row) -> str:
    return _sha(json.dumps([
        row["candidate_id"], row["source_refs_json"], row["event_keys_json"]
    ], separators=(",", ":")))

class DisposableGate:
    """SQLite transactions with real file reopen, constrained to a temp workspace.

    Caller must own a live TemporaryDirectory; its cleanup deletes the DB.
    SyntheticOwnerOnly is just a comparison fixture, not real identity proof.
    """

    def __init__(self, workspace: TemporaryDirectory, owner: SyntheticOwnerOnly):
        if not isinstance(workspace, TemporaryDirectory):
            raise ContractViolation("DISPOSABLE_WORKSPACE_REQUIRED")
        if not isinstance(owner, SyntheticOwnerOnly):
            raise ContractViolation("OWNER_FIXTURE_REQUIRED")
        root = Path(workspace.name)
        if not root.is_dir() or root.is_symlink():
            raise ContractViolation("DISPOSABLE_WORKSPACE_CLOSED")
        self._db = root / "g14c-fixture-only.sqlite3"
        self._owner = owner
        with self._conn() as db:
            db.executescript(SCHEMA)
            db.execute("PRAGMA user_version = 1")

    @contextmanager
    def _conn(self):
        db = sqlite3.connect(str(self._db), timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA foreign_keys=ON")
            yield db
        finally:
            db.close()

    @contextmanager
    def _tx(self):
        with self._conn() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def seed(self, *, claimed_owner: str, process: AdministrativeProcess,
             revision: str):
        self._owner.require(claimed_owner)
        if not isinstance(process, AdministrativeProcess) or not isinstance(revision, str) or not revision:
            raise ContractViolation("INVALID_PROCESS_OR_REVISION")
        with self._tx() as db:
            if db.execute("SELECT 1 FROM process_heads WHERE process_key=?",
                          (process.process_key,)).fetchone():
                raise ContractViolation("PROCESS_ALREADY_SEEDED")
            db.execute("INSERT INTO process_heads VALUES (?,?)", (process.process_key, revision))

    def current_revision(self, *, claimed_owner: str, process_key: str) -> str | None:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            row = db.execute("SELECT revision FROM process_heads WHERE process_key=?",
                             (process_key,)).fetchone()
        return row["revision"] if row else None

    def reserve(self, *, claimed_owner: str, request: SyntheticRequest,
                fail_before_commit: bool = False) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(request, SyntheticRequest):
            raise ContractViolation("INVALID_REQUEST")
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM requests WHERE process_key=? AND request_key=?",
                (request.process_key, request.idempotency_key),
            ).fetchone()
            if row:
                if row["fingerprint"] != request.request_fingerprint:
                    raise ContractViolation("IDEMPOTENCY_CONFLICT")
                return self._receipt(dict(row), replayed=True)
            head = db.execute("SELECT revision FROM process_heads WHERE process_key=?",
                              (request.process_key,)).fetchone()
            if not head or head["revision"] != request.expected_revision:
                raise ContractViolation("REVISION_CONFLICT")
            run_id = _sha(request.process_key + ":" + request.idempotency_key)[:32]
            db.execute(
                "INSERT INTO requests VALUES (?,?,?,?,?,?,?)",
                (request.process_key, request.idempotency_key,
                 request.request_fingerprint, request.expected_revision,
                 run_id, "RESERVED_SYNTHETIC", None),
            )
            if fail_before_commit:
                raise ContractViolation("SIMULATED_CRASH_BEFORE_COMMIT")
            return self._receipt({
                "process_key": request.process_key, "request_key": request.idempotency_key,
                "fingerprint": request.request_fingerprint, "expected_revision": request.expected_revision,
                "run_id": run_id, "state": "RESERVED_SYNTHETIC", "new_revision": None,
            }, replayed=False)

    def commit_revision(self, *, claimed_owner: str, process_key: str,
                        request_key: str, new_revision: str) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(new_revision, str) or not new_revision:
            raise ContractViolation("INVALID_REVISION")
        with self._tx() as db:
            row = db.execute(
                "SELECT * FROM requests WHERE process_key=? AND request_key=?",
                (process_key, request_key),
            ).fetchone()
            if row is None:
                raise ContractViolation("RUN_NOT_FOUND")
            record = dict(row)
            if record["state"] == "UNKNOWN_SYNTHETIC":
                raise ContractViolation("RECONCILIATION_REQUIRED")
            if record["state"] == "COMMITTED_SYNTHETIC":
                if record["new_revision"] != new_revision:
                    raise ContractViolation("REPLAY_REVISION_MISMATCH")
                return self._receipt(record, replayed=True)
            if record["state"] != "RESERVED_SYNTHETIC":
                raise ContractViolation("RUN_NOT_COMMITTABLE")
            if new_revision == record["expected_revision"]:
                raise ContractViolation("REVISION_NOT_ADVANCED")
            changed = db.execute(
                "UPDATE process_heads SET revision=? WHERE process_key=? AND revision=?",
                (new_revision, process_key, record["expected_revision"]),
            ).rowcount
            if changed != 1:
                db.execute(
                    "UPDATE requests SET state='CONFLICT_SYNTHETIC' WHERE process_key=? AND request_key=?",
                    (process_key, request_key),
                )
                # Raise after transaction so the conflict marker remains as evidence.
                conflict = True
            else:
                db.execute(
                    "UPDATE requests SET state='COMMITTED_SYNTHETIC', new_revision=? "
                    "WHERE process_key=? AND request_key=?",
                    (new_revision, process_key, request_key),
                )
                conflict = False
        if conflict:
            raise ContractViolation("REVISION_CONFLICT")
        record.update(state="COMMITTED_SYNTHETIC", new_revision=new_revision)
        return self._receipt(record, replayed=False)

    def mark_unknown(self, *, claimed_owner: str, process_key: str,
                     request_key: str) -> dict:
        self._owner.require(claimed_owner)
        with self._tx() as db:
            changed = db.execute(
                "UPDATE requests SET state='UNKNOWN_SYNTHETIC' "
                "WHERE process_key=? AND request_key=? AND state='RESERVED_SYNTHETIC'",
                (process_key, request_key),
            ).rowcount
            if changed != 1:
                raise ContractViolation("UNKNOWN_STATE_TRANSITION")
            row = db.execute(
                "SELECT * FROM requests WHERE process_key=? AND request_key=?",
                (process_key, request_key),
            ).fetchone()
        return self._receipt(dict(row), replayed=False)

    def readback(self, *, claimed_owner: str, process_key: str,
                 request_key: str) -> dict:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            row = db.execute(
                "SELECT * FROM requests WHERE process_key=? AND request_key=?",
                (process_key, request_key),
            ).fetchone()
        if row is None:
            raise ContractViolation("RUN_NOT_FOUND")
        return self._receipt(dict(row), replayed=False)

    @staticmethod
    def _receipt(rec: dict, *, replayed: bool) -> dict:
        return {
            "schema": "gaia.g14c-synthetic-receipt.v1",
            "process_key": rec["process_key"],
            "run_id": rec["run_id"],
            "request_fingerprint": rec["fingerprint"],
            "state": rec["state"],
            "new_revision": rec["new_revision"],
            "replayed": replayed,
            "persisted_only_in_disposable_sqlite": True,
            "provider_write_performed": False,
            "qdrant_write_performed": False,
            "production_durable": False,
        }

    def capture(self, *, claimed_owner: str, process: AdministrativeProcess,
                event: DocumentEvent) -> dict:
        self._owner.require(claimed_owner)
        if not isinstance(process, AdministrativeProcess) or not isinstance(event, DocumentEvent):
            raise ContractViolation("INVALID_CAPTURE_INPUT")
        if event.source.process_id != process.process_id:
            raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
        if event.status not in ("completed", "review_required"):
            raise ContractViolation("EVENT_NOT_ELIGIBLE")
        if event.operation == "ocr" and event.provider.lower() == "mock":
            raise ContractViolation("MOCK_IS_NOT_EVIDENCE")
        # Explicitly refuse normal document identifiers: this lab must not hold
        # real client data, even accidentally.
        if not event.source.file_id.startswith("FILE_DEMO_"):
            raise ContractViolation("SYNTHETIC_DOCUMENT_ONLY")
        summary = event.summary.strip()
        if not summary.startswith("DEMO: ") or len(summary) > 240 or not _tokens(summary):
            raise ContractViolation("SYNTHETIC_SUMMARY_REQUIRED")
        topic_digest = _sha(" ".join(sorted(_tokens(summary))))
        candidate_id = _sha(process.process_key + ":" + topic_digest)
        with self._tx() as db:
            found = db.execute(
                "SELECT * FROM candidates WHERE process_key=? AND topic_digest=?",
                (process.process_key, topic_digest),
            ).fetchone()
            if found is None:
                db.execute(
                    "INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?,?)",
                    (candidate_id, process.process_key, process.process_id,
                     topic_digest, summary, json.dumps([event.source.source_ref]),
                     json.dumps([event.fingerprint()]), "PENDING_HUMAN_REVIEW", None),
                )
                count = 1
            else:
                if found["process_id"] != process.process_id:
                    raise ContractViolation("PROCESS_ID_COLLISION")
                if found["review_status"] != "PENDING_HUMAN_REVIEW":
                    # New evidence after review needs a fresh review event,
                    # not implicit mutation of a sealed batch.
                    raise ContractViolation("REVIEWED_CANDIDATE_CANNOT_CHANGE")
                srcs = json.loads(found["source_refs_json"])
                keys = json.loads(found["event_keys_json"])
                if event.source.source_ref not in srcs:
                    srcs.append(event.source.source_ref)
                if event.fingerprint() not in keys:
                    keys.append(event.fingerprint())
                db.execute(
                    "UPDATE candidates SET source_refs_json=?, event_keys_json=? "
                    "WHERE candidate_id=?",
                    (json.dumps(srcs), json.dumps(keys), candidate_id),
                )
                count = len(srcs)
        return {
            "status": "PENDING_HUMAN_REVIEW", "candidate_id": candidate_id,
            "process_key": process.process_key, "source_count": count,
            "qdrant_write_performed": False, "production_durable": False,
        }

    def working_context(self, *, claimed_owner: str, process: AdministrativeProcess) -> list[dict]:
        self._owner.require(claimed_owner)
        if not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        with self._conn() as db:
            rows = db.execute(
                "SELECT candidate_id,process_key,summary,review_status FROM candidates "
                "WHERE process_key=? ORDER BY candidate_id",
                (process.process_key,),
            ).fetchall()
        return [
            {"candidate_id": row["candidate_id"],
             "process_key": row["process_key"],
             "summary": row["summary"],
             "review_status": row["review_status"],
             "is_authoritative": False}
            for row in rows
        ]

    def preview_batches(self, *, claimed_owner: str) -> list[dict]:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            rows = db.execute(
                "SELECT candidate_id,process_key,summary,source_refs_json,event_keys_json FROM candidates "
                "WHERE review_status='PENDING_HUMAN_REVIEW' ORDER BY process_key,candidate_id"
            ).fetchall()
        groups: dict[str, list[dict]] = {}
        snapshots: dict[str, list[str]] = {}
        for row in rows:
            snapshots.setdefault(row["process_key"], []).append(_candidate_snapshot(row))
            groups.setdefault(row["process_key"], []).append({
                "candidate_id": row["candidate_id"],
                "summary": row["summary"],
                "source_count": len(json.loads(row["source_refs_json"])),
            })
        return [{
            "process_key": process_key,
            "batch_id": _batch_id(process_key, snapshots[process_key]),
            "candidates": items,
            "candidate_count": len(items),
            "status": "PENDING_GROUPED_REVIEW",
            "qdrant_written": False,
        } for process_key, items in sorted(groups.items())]

    def review_batch(self, *, claimed_owner: str, process_key: str,
                     batch_id: str, candidate_ids: tuple[str, ...],
                     decision: str) -> dict:
        self._owner.require(claimed_owner)
        if decision not in ("prepare_proposals", "needs_more_evidence"):
            raise ContractViolation("INVALID_REVIEW_DECISION")
        if not isinstance(candidate_ids, tuple) or not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
            raise ContractViolation("INVALID_REVIEW_MEMBERS")
        if not isinstance(batch_id, str) or len(batch_id) != 64:
            raise ContractViolation("INVALID_BATCH_ID")
        with self._tx() as db:
            rows = db.execute(
                "SELECT candidate_id,source_refs_json,event_keys_json FROM candidates "
                "WHERE process_key=? AND review_status='PENDING_HUMAN_REVIEW'",
                (process_key,),
            ).fetchall()
            actual = sorted(row["candidate_id"] for row in rows)
            if actual != sorted(candidate_ids) or not actual or _batch_id(
                    process_key, [_candidate_snapshot(row) for row in rows]
            ) != batch_id:
                raise ContractViolation("BATCH_STALE_OR_PROCESS_MISMATCH")
            status = ("REVIEWED_FOR_PROPOSAL_SYNTHETIC"
                      if decision == "prepare_proposals" else "MORE_EVIDENCE_NEEDED_SYNTHETIC")
            db.executemany(
                "UPDATE candidates SET review_status=?,batch_id=? WHERE candidate_id=?",
                [(status, batch_id, candidate_id) for candidate_id in actual],
            )
            db.execute(
                "INSERT INTO batch_receipts VALUES (?,?,?,?,?)",
                (batch_id, process_key, decision, len(actual), claimed_owner),
            )
        return {
            "batch_id": batch_id, "process_key": process_key,
            "candidate_count": len(actual), "review_status": status,
            "document_approval": False, "memory_approved": False,
            "qdrant_written": False, "real_human_review_verified": False,
            "requires_authenticated_r06_batch_review": True,
        }

    def batch_readback(self, *, claimed_owner: str, batch_id: str) -> dict:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            row = db.execute("SELECT * FROM batch_receipts WHERE batch_id=?",
                             (batch_id,)).fetchone()
        if not row:
            raise ContractViolation("BATCH_NOT_FOUND")
        return {
            "batch_id": row["batch_id"], "process_key": row["process_key"],
            "candidate_count": row["candidate_count"], "decision": row["decision"],
            "memory_approved": False, "qdrant_written": False,
        }
