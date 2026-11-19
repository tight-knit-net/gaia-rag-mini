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
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly, _tokens, _canonical_summary
from .owner_concurrency import SyntheticRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS process_heads (
    process_key TEXT PRIMARY KEY,
    revision TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS process_registry (
    process_key TEXT PRIMARY KEY,
    process_id TEXT NOT NULL,
    agency_code TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    official_number TEXT NOT NULL
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
    evidence_markers_json TEXT NOT NULL DEFAULT '[]',
    review_status TEXT NOT NULL,
    batch_id TEXT,
    candidate_revision INTEGER NOT NULL DEFAULT 1,
    UNIQUE (process_key, topic_digest)
);
CREATE TABLE IF NOT EXISTS batch_receipts (
    batch_id TEXT PRIMARY KEY,
    process_key TEXT NOT NULL,
    decision TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    operator_ref TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batch_review_items (
    batch_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    candidate_revision INTEGER NOT NULL,
    decision TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (batch_id, candidate_id)
);
CREATE TABLE IF NOT EXISTS candidate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    candidate_revision INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_key TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL
);
"""

def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()

def _batch_id(process_key: str, snapshots: list[str]) -> str:
    return _sha(json.dumps([process_key, *sorted(snapshots)], separators=(",", ":")))

def _candidate_snapshot(row) -> str:
    """Canonical hash of every displayed/effective candidate field."""
    return _sha(json.dumps([
        row["candidate_id"], row["process_key"], row["process_id"],
        row["topic_digest"], row["summary"], row["review_status"],
        row["candidate_revision"],
        sorted(json.loads(row["source_refs_json"])),
        sorted(json.loads(row["event_keys_json"])),
        sorted(json.loads(row["evidence_markers_json"])),
        "g14e-synthetic-policy.v1",
    ], ensure_ascii=False, separators=(",", ":")))


def _source_evidence_marker(event: DocumentEvent) -> str:
    """Changes in attempt ID alone are not a new source/evidence version."""
    return _sha(json.dumps([
        event.source.source_ref, event.source.source_version,
        event.source.sha256_original, event.evidence_digest(),
        event.derived_sha256,
    ], separators=(",", ":")))


def _register_process(db, process: AdministrativeProcess) -> None:
    """Bind official process identity; not a client ACL."""
    row = db.execute(
        "SELECT * FROM process_registry WHERE process_key=?", (process.process_key,)
    ).fetchone()
    values = (process.process_key, process.process_id, process.agency_code,
              process.jurisdiction, process.official_number)
    if row is None:
        db.execute("INSERT INTO process_registry VALUES (?,?,?,?,?)", values)
    elif any(row[field] != actual for field, actual in zip(
            ("process_key", "process_id", "agency_code", "jurisdiction", "official_number"),
            values)):
        raise ContractViolation("PROCESS_ID_COLLISION")


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
            _register_process(db, process)
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

    def reserve_from_event(self, *, claimed_owner: str, process: AdministrativeProcess,
                           event: DocumentEvent, original_bytes: bytes,
                           idempotency_key: str, expected_revision: str) -> dict:
        """Generate a synthetic fingerprint from observed bytes and event fields.

        Caller-supplied request_fingerprint is NOT trusted in this path.
        Still no authenticated provider origin or external write.
        """
        self._owner.require(claimed_owner)
        if (not isinstance(process, AdministrativeProcess)
                or not isinstance(event, DocumentEvent)
                or event.source.process_id != process.process_id):
            raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
        if (not isinstance(original_bytes, bytes)
                or not event.source.matches_original(original_bytes)):
            raise ContractViolation("SOURCE_HASH_MISMATCH")
        if (not event.source.file_id.startswith("FILE_DEMO_")
                or not event.summary.startswith("DEMO: ")):
            raise ContractViolation("SYNTHETIC_DATA_REQUIRED")
        with self._conn() as db:
            observed = db.execute(
                "SELECT * FROM process_registry WHERE process_key=?",
                (process.process_key,),
            ).fetchone()
            if observed is None or observed["process_id"] != process.process_id:
                raise ContractViolation("PROCESS_BINDING_NOT_REGISTERED")
        fingerprint = _sha(json.dumps({
            "process_key": process.process_key, "process_id": process.process_id,
            "source_ref": event.source.source_ref,
            "source_version": event.source.source_version,
            "document_sha256": event.source.sha256_original,
            "operation": event.operation, "provider": event.provider,
            "summary": _canonical_summary(event.summary),
            "rule_id": event.rule_id, "proposed_filename": event.proposed_filename,
        }, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        return self.reserve(claimed_owner=claimed_owner, request=SyntheticRequest(
            process_key=process.process_key,
            idempotency_key=idempotency_key,
            expected_revision=expected_revision,
            request_fingerprint=fingerprint,
        ))

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
        topic_digest = _sha(_canonical_summary(summary))
        candidate_id = _sha(process.process_key + ":" + topic_digest)
        evidence_marker = _source_evidence_marker(event)
        with self._tx() as db:
            _register_process(db, process)
            found = db.execute(
                "SELECT * FROM candidates WHERE process_key=? AND topic_digest=?",
                (process.process_key, topic_digest),
            ).fetchone()
            if found is None:
                db.execute(
                    "INSERT INTO candidates "
                    "(candidate_id,process_key,process_id,topic_digest,summary,"
                    "source_refs_json,event_keys_json,evidence_markers_json,"
                    "review_status,batch_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (candidate_id, process.process_key, process.process_id,
                     topic_digest, summary, json.dumps([event.source.source_ref]),
                     json.dumps([event.fingerprint()]),json.dumps([evidence_marker]),
                     "PENDING_HUMAN_REVIEW", None),
                )
                db.execute(
                    "INSERT INTO candidate_history "
                    "(candidate_id,candidate_revision,event_name,event_key,"
                    "previous_status,new_status) VALUES (?,?,?,?,?,?)",
                    (candidate_id, 1, "CAPTURED_SYNTHETIC", event.fingerprint(),
                     None, "PENDING_HUMAN_REVIEW"),
                )
                count = 1
                revision = 1
            else:
                if found["process_id"] != process.process_id:
                    raise ContractViolation("PROCESS_ID_COLLISION")
                old_status = found["review_status"]
                if old_status not in (
                    "PENDING_HUMAN_REVIEW", "MORE_EVIDENCE_NEEDED_SYNTHETIC"
                ):
                    # A prepared proposal cannot be silently changed.
                    raise ContractViolation("REVIEWED_CANDIDATE_CANNOT_CHANGE")
                srcs = json.loads(found["source_refs_json"])
                keys = json.loads(found["event_keys_json"])
                markers = json.loads(found["evidence_markers_json"])
                event_key = event.fingerprint()
                new_evidence = evidence_marker not in markers
                if old_status == "MORE_EVIDENCE_NEEDED_SYNTHETIC" and not new_evidence:
                    raise ContractViolation("NEW_EVIDENCE_REQUIRED")
                if event.source.source_ref not in srcs:
                    srcs.append(event.source.source_ref)
                if event_key not in keys:
                    keys.append(event_key)
                if evidence_marker not in markers:
                    markers.append(evidence_marker)
                revision = found["candidate_revision"] + (1 if new_evidence else 0)
                db.execute(
                    "UPDATE candidates SET source_refs_json=?, event_keys_json=?,"
                    "evidence_markers_json=?,review_status='PENDING_HUMAN_REVIEW',"
                    "batch_id=NULL,candidate_revision=? WHERE candidate_id=?",
                    (json.dumps(srcs), json.dumps(keys),json.dumps(markers),
                     revision, candidate_id),
                )
                if new_evidence:
                    db.execute(
                        "INSERT INTO candidate_history "
                        "(candidate_id,candidate_revision,event_name,event_key,"
                        "previous_status,new_status) VALUES (?,?,?,?,?,?)",
                        (candidate_id, revision,
                         "EVIDENCE_ADDED_SYNTHETIC", event_key,
                         old_status, "PENDING_HUMAN_REVIEW"),
                    )
                count = len(srcs)
        return {
            "status": "PENDING_HUMAN_REVIEW", "candidate_id": candidate_id,
            "process_key": process.process_key, "source_count": count,
            "candidate_revision": revision,
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
                "SELECT * FROM candidates "
                "WHERE review_status='PENDING_HUMAN_REVIEW' ORDER BY process_key,candidate_id"
            ).fetchall()
        groups: dict[str, list[dict]] = {}
        snapshots: dict[str, list[str]] = {}
        for row in rows:
            snapshots.setdefault(row["process_key"], []).append(_candidate_snapshot(row))
            groups.setdefault(row["process_key"], []).append({
                "candidate_id": row["candidate_id"],
                "summary": row["summary"],
                "candidate_revision": row["candidate_revision"],
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
        """Legacy all-pending batch action; preserved for G14-C callers."""
        if decision not in ("prepare_proposals", "needs_more_evidence"):
            raise ContractViolation("INVALID_REVIEW_DECISION")
        if (not isinstance(candidate_ids, tuple) or not candidate_ids
                or len(set(candidate_ids)) != len(candidate_ids)):
            raise ContractViolation("INVALID_REVIEW_MEMBERS")
        return self.review_batch_items(
            claimed_owner=claimed_owner, process_key=process_key,
            batch_id=batch_id, decisions={cid: decision for cid in candidate_ids},
            require_all=True,
        )

    def review_batch_items(self, *, claimed_owner: str, process_key: str,
                           batch_id: str, decisions: dict[str, str],
                           require_all: bool = False) -> dict:
        """Review selected synthetic items; never authorizes R06/Qdrant.

        The batch digest always covers *all* pending candidates, even when
        only a subset is selected, so any new evidence invalidates it.
        """
        self._owner.require(claimed_owner)
        if (not isinstance(decisions, dict) or not decisions
                or any(not isinstance(cid, str) or not cid for cid in decisions)):
            raise ContractViolation("INVALID_REVIEW_MEMBERS")
        if any(decision not in ("prepare_proposals", "needs_more_evidence")
               for decision in decisions.values()):
            raise ContractViolation("INVALID_REVIEW_DECISION")
        if not isinstance(batch_id, str) or len(batch_id) != 64:
            raise ContractViolation("INVALID_BATCH_ID")
        if not isinstance(process_key, str) or not process_key:
            raise ContractViolation("PROCESS_KEY_INVALID")
        with self._tx() as db:
            rows = db.execute(
                "SELECT * FROM candidates "
                "WHERE process_key=? AND review_status='PENDING_HUMAN_REVIEW'",
                (process_key,),
            ).fetchall()
            pending = {row["candidate_id"]: row for row in rows}
            if (not pending or not set(decisions).issubset(pending)
                    or (require_all and set(decisions) != set(pending))
                    or _batch_id(process_key, [
                        _candidate_snapshot(row) for row in rows
                    ]) != batch_id):
                raise ContractViolation("BATCH_STALE_OR_PROCESS_MISMATCH")
            items = []
            for cid in sorted(decisions):
                decision = decisions[cid]
                status = ("REVIEWED_FOR_PROPOSAL_SYNTHETIC"
                          if decision == "prepare_proposals"
                          else "MORE_EVIDENCE_NEEDED_SYNTHETIC")
                db.execute(
                    "UPDATE candidates SET review_status=?,batch_id=? "
                    "WHERE candidate_id=? AND review_status='PENDING_HUMAN_REVIEW'",
                    (status, batch_id, cid),
                )
                db.execute(
                    "INSERT INTO batch_review_items "
                    "(batch_id,candidate_id,candidate_revision,decision,status) "
                    "VALUES (?,?,?,?,?)",
                    (batch_id, cid, pending[cid]["candidate_revision"], decision, status),
                )
                db.execute(
                    "INSERT INTO candidate_history "
                    "(candidate_id,candidate_revision,event_name,event_key,"
                    "previous_status,new_status) VALUES (?,?,?,?,?,?)",
                    (cid, pending[cid]["candidate_revision"],
                     "BATCH_REVIEW_SYNTHETIC", "batch:" + batch_id,
                     "PENDING_HUMAN_REVIEW", status),
                )
                items.append({
                    "candidate_id": cid,
                    "candidate_revision": pending[cid]["candidate_revision"],
                    "decision": decision,
                    "status": status,
                    "memory_approved": False,
                    "qdrant_written": False,
                })
            choices = set(decisions.values())
            group_decision = next(iter(choices)) if len(choices) == 1 else "mixed"
            db.execute(
                "INSERT INTO batch_receipts VALUES (?,?,?,?,?)",
                (batch_id, process_key, group_decision, len(items), claimed_owner),
            )
        status_values = {item["status"] for item in items}
        return {
            "batch_id": batch_id,
            "process_key": process_key,
            "candidate_count": len(items),
            "review_status": next(iter(status_values)) if len(status_values) == 1
                             else "MIXED_SYNTHETIC",
            "items": items,
            "document_approval": False,
            "memory_approved": False,
            "qdrant_written": False,
            "real_human_review_verified": False,
            "requires_authenticated_r06_batch_review": True,
        }

    def candidate_history_readback(self, *, claimed_owner: str,
                                   candidate_id: str) -> list[dict]:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            rows = db.execute(
                "SELECT candidate_revision,event_name,event_key,previous_status,"
                "new_status FROM candidate_history WHERE candidate_id=? ORDER BY id",
                (candidate_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def batch_readback(self, *, claimed_owner: str, batch_id: str) -> dict:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            row = db.execute("SELECT * FROM batch_receipts WHERE batch_id=?",
                             (batch_id,)).fetchone()
        if not row:
            raise ContractViolation("BATCH_NOT_FOUND")
        with self._conn() as db:
            details = db.execute(
                "SELECT candidate_id,candidate_revision,decision,status "
                "FROM batch_review_items WHERE batch_id=? ORDER BY candidate_id",
                (batch_id,),
            ).fetchall()
        return {
            "batch_id": row["batch_id"], "process_key": row["process_key"],
            "candidate_count": row["candidate_count"], "decision": row["decision"],
            "items": [dict(item) for item in details],
            "memory_approved": False, "qdrant_written": False,
        }
