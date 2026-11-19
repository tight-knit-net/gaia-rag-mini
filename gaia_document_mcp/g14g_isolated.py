"""G14-G: purely disposable SQLite pagination and observed-source fixtures.

This is NOT an authenticated OCR adapter, source attestation, archival
retention system, human-review interface, or approved-memory writer.
Every source must use DEMO bytes, synthetic identifiers and temporary storage.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from tempfile import TemporaryDirectory

from .contracts import ContractViolation, DocumentEvent
from .g14c_disposable import DisposableGate, _sha
from .g14f_contracts import SyntheticSourceObservation, event_contract_preview
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly

_PAGE_TOKEN = re.compile(r"^g14g:([a-f0-9]{64}):([0-9]{1,12})$")
_SOURCE = re.compile(r"^[A-Za-z0-9_.:/-]{3,200}$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_POLICY = "g14g-disposable-pending-v1"
_MAX_DEMO_BYTES = 65536

_G14G_SCHEMA = """
CREATE TABLE IF NOT EXISTS g14g_pending_generation (
    id INTEGER PRIMARY KEY CHECK (id=1),
    generation INTEGER NOT NULL
);
INSERT OR IGNORE INTO g14g_pending_generation VALUES (1, 0);
CREATE TRIGGER IF NOT EXISTS g14g_candidate_insert AFTER INSERT ON candidates
BEGIN
    UPDATE g14g_pending_generation SET generation=generation+1 WHERE id=1;
END;
CREATE TRIGGER IF NOT EXISTS g14g_candidate_update AFTER UPDATE ON candidates
BEGIN
    UPDATE g14g_pending_generation SET generation=generation+1 WHERE id=1;
END;
CREATE TRIGGER IF NOT EXISTS g14g_candidate_delete AFTER DELETE ON candidates
BEGIN
    UPDATE g14g_pending_generation SET generation=generation+1 WHERE id=1;
END;
CREATE INDEX IF NOT EXISTS g14g_pending_by_process
    ON candidates (review_status, process_key, candidate_id);
CREATE TABLE IF NOT EXISTS g14g_source_observations (
    process_key TEXT NOT NULL,
    process_id TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_version TEXT NOT NULL,
    original_sha256 TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    PRIMARY KEY (process_key, source_ref, source_version)
);
"""

def _require_ref(value: str) -> None:
    if not isinstance(value, str) or not _SOURCE.fullmatch(value):
        raise ContractViolation("OBSERVATION_IDENTIFIER_INVALID")

def _snapshot(generation: int, total: int, scope: str | None) -> str:
    return _sha(json.dumps([_POLICY, generation, total, scope],
                           separators=(",", ":"), ensure_ascii=False))

def _page_token(snapshot: str, offset: int) -> str:
    return f"g14g:{snapshot}:{offset}"

def verify_disposable_page_sequence(pages: tuple[dict, ...]) -> dict:
    """Validate an entire series returned by G14GDisposableGate.

    This is a fixture-only consistency check; remote or authenticated
    database coverage is not claimed by the output.
    """
    if not isinstance(pages, tuple) or not pages:
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    first = pages[0]
    if not isinstance(first, dict):
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    snapshot, total, scope = (
        first.get("snapshot"), first.get("total"), first.get("process_key")
    )
    if (not isinstance(snapshot, str) or not _SHA.fullmatch(snapshot)
            or isinstance(total, bool) or not isinstance(total, int) or total < 0):
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    expected_offset = 0
    observed_ids: set[str] = set()
    for index, page in enumerate(pages):
        if (not isinstance(page, dict) or page.get("schema") != "gaia.g14g-sqlite-page.v1"
                or page.get("snapshot") != snapshot
                or page.get("total") != total
                or page.get("process_key") != scope
                or page.get("offset") != expected_offset):
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
        items = page.get("items")
        limit = page.get("limit")
        if (isinstance(limit, bool) or not isinstance(limit, int)
                or not 1 <= limit <= 25
                or not isinstance(items, list)
                or len(items) > limit
                or (not items and total > 0)):
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("candidate_id"), str):
                raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
            cid = item["candidate_id"]
            if cid in observed_ids:
                raise ContractViolation("PAGE_DUPLICATE")
            if scope is not None and item.get("process_key") != scope:
                raise ContractViolation("PAGE_SCOPE_MISMATCH")
            observed_ids.add(cid)
        expected_offset += len(items)
        nxt = None if expected_offset == total else _page_token(snapshot, expected_offset)
        if page.get("next_cursor") != nxt:
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
        if index < len(pages)-1 and nxt is None:
            raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    if expected_offset != total or pages[-1].get("next_cursor") is not None:
        raise ContractViolation("PAGE_COVERAGE_INCOMPLETE")
    return {
        "snapshot": snapshot,
        "process_key": scope,
        "count": total,
        "coverage_verified_in_disposable_sqlite_fixture": True,
        "real_provider_coverage_verified": False,
        "memory_approved": False,
    }


class G14GDisposableGate(DisposableGate):
    """Additive synthetic lab; existing G14-C contracts remain unchanged."""

    def __init__(self, workspace: TemporaryDirectory, owner: SyntheticOwnerOnly):
        super().__init__(workspace, owner)
        with self._conn() as db:
            db.executescript(_G14G_SCHEMA)

    def observe_demo_source(
        self, *, claimed_owner: str, process: AdministrativeProcess,
        source_ref: str, source_version: str, original: bytes,
    ) -> dict:
        """Independently store *test-fixture* bytes' digest once per version.

        This does not authenticate a provider and cannot handle real files.
        Caller must seed the official process binding before observing.
        """
        self._owner.require(claimed_owner)
        if not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        _require_ref(source_ref)
        _require_ref(source_version)
        if ("FILE_DEMO_" not in source_ref
                or not isinstance(original, bytes)
                or len(original) > _MAX_DEMO_BYTES
                or b"DEMO" not in original[:512]):
            raise ContractViolation("SYNTHETIC_OBSERVATION_ONLY")
        digest = sha256(original).hexdigest()
        obs_id = _sha(json.dumps(
            [process.process_key, process.process_id, source_ref, source_version, digest],
            separators=(",", ":"),
        ))
        with self._tx() as db:
            binding = db.execute(
                "SELECT process_id FROM process_registry WHERE process_key=?",
                (process.process_key,),
            ).fetchone()
            if binding is None or binding["process_id"] != process.process_id:
                raise ContractViolation("PROCESS_BINDING_NOT_REGISTERED")
            row = db.execute(
                "SELECT * FROM g14g_source_observations "
                "WHERE process_key=? AND source_ref=? AND source_version=?",
                (process.process_key, source_ref, source_version),
            ).fetchone()
            if row:
                if row["original_sha256"] != digest or row["process_id"] != process.process_id:
                    raise ContractViolation("OBSERVATION_CONFLICT")
                replayed = True
            else:
                db.execute(
                    "INSERT INTO g14g_source_observations VALUES (?,?,?,?,?,?)",
                    (process.process_key, process.process_id, source_ref,
                     source_version, digest, obs_id),
                )
                replayed = False
        return {
            "observation_id": obs_id,
            "process_key": process.process_key,
            "source_ref": source_ref,
            "source_version": source_version,
            "original_sha256": digest,
            "replayed": replayed,
            "provider_origin_authenticated": False,
            "observed_only_in_disposable_fixture": True,
        }

    def capture_observed_demo(
        self, *, claimed_owner: str, process: AdministrativeProcess,
        event: DocumentEvent, original: bytes,
    ) -> dict:
        """Compare event with independently stored demo-source observation.

        Capture is an automatic *candidate*; no R06 approval or Qdrant write.
        """
        self._owner.require(claimed_owner)
        if not isinstance(event, DocumentEvent) or not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_CAPTURE_INPUT")
        with self._conn() as db:
            row = db.execute(
                "SELECT * FROM g14g_source_observations WHERE "
                "process_key=? AND source_ref=? AND source_version=?",
                (process.process_key, event.source.source_ref,
                 event.source.source_version),
            ).fetchone()
        if row is None:
            raise ContractViolation("OBSERVATION_REQUIRED")
        observation = SyntheticSourceObservation(
            process_id=row["process_id"], process_key=process.process_key,
            source_ref=row["source_ref"], source_version=row["source_version"],
            original_sha256=row["original_sha256"],
        )
        preview = event_contract_preview(
            owner=self._owner, claimed_owner=claimed_owner,
            process=process, event=event,
            observation=observation, original=original,
        )
        candidate = self.capture(
            claimed_owner=claimed_owner, process=process, event=event,
        )
        return {
            **candidate,
            "observation_id": row["observation_id"],
            "event_key": preview["event_key"],
            "source_observed_in_disposable_fixture": True,
            "provider_origin_authenticated": False,
            "derived_quality_attested": False,
            "memory_approved": False,
            "qdrant_write_performed": False,
        }

    def page_pending(
        self, *, claimed_owner: str, page_size: int = 10,
        cursor: str | None = None, process: AdministrativeProcess | None = None,
    ) -> dict:
        """Bounded LIMIT/OFFSET SQL in a consistent SQLite read transaction.

        On any insert/update/delete of candidates, a persisted generation
        counter invalidates old cursors. No table-wide fetchall occurs here.
        """
        self._owner.require(claimed_owner)
        if (isinstance(page_size, bool) or not isinstance(page_size, int)
                or not 1 <= page_size <= 25):
            raise ContractViolation("PAGE_LIMIT_INVALID")
        if process is not None and not isinstance(process, AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        scope = None if process is None else process.process_key
        offset = 0
        supplied_snapshot = None
        if cursor is not None:
            if not isinstance(cursor, str):
                raise ContractViolation("PAGE_CURSOR_INVALID")
            parsed = _PAGE_TOKEN.fullmatch(cursor)
            if parsed is None:
                raise ContractViolation("PAGE_CURSOR_INVALID")
            supplied_snapshot, offset_string = parsed.groups()
            offset = int(offset_string)
        conditions = " WHERE review_status='PENDING_HUMAN_REVIEW'"
        params: tuple[str, ...] = ()
        if scope is not None:
            conditions += " AND process_key=?"
            params = (scope,)
        with self._conn() as db:
            db.execute("BEGIN")
            try:
                if process is not None:
                    binding = db.execute(
                        "SELECT process_id FROM process_registry WHERE process_key=?",
                        (process.process_key,),
                    ).fetchone()
                    if binding is None:
                        raise ContractViolation("PROCESS_BINDING_NOT_REGISTERED")
                    if binding["process_id"] != process.process_id:
                        raise ContractViolation("PROCESS_ID_COLLISION")
                row = db.execute(
                    "SELECT generation FROM g14g_pending_generation WHERE id=1"
                ).fetchone()
                if row is None:
                    raise ContractViolation("PAGINATION_GENERATION_MISSING")
                count = db.execute(
                    "SELECT COUNT(*) AS n FROM candidates"+conditions, params,
                ).fetchone()["n"]
                snapshot = _snapshot(row["generation"], count, scope)
                if supplied_snapshot is not None and supplied_snapshot != snapshot:
                    raise ContractViolation("PAGE_SNAPSHOT_STALE")
                if offset > count:
                    raise ContractViolation("PAGE_OFFSET_INVALID")
                selected = db.execute(
                    "SELECT candidate_id,process_key,process_id,"
                    "candidate_revision,summary,source_refs_json "
                    "FROM candidates"+conditions+
                    " ORDER BY process_key,candidate_id LIMIT ? OFFSET ?",
                    (*params, page_size, offset),
                ).fetchall()  # LIMIT <= 25, never a whole-table fetch.
                items = [{
                    "candidate_id": item["candidate_id"],
                    "process_key": item["process_key"],
                    "process_id": item["process_id"],
                    "candidate_revision": item["candidate_revision"],
                    "summary_digest": sha256(item["summary"].encode()).hexdigest(),
                    "source_count": len(json.loads(item["source_refs_json"])),
                    "memory_approved": False,
                } for item in selected]
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        next_offset = offset + len(items)
        return {
            "schema": "gaia.g14g-sqlite-page.v1",
            "process_key": scope,
            "snapshot": snapshot,
            "offset": offset,
            "total": count,
            "limit": page_size,
            "items": items,
            "next_cursor": None if next_offset == count
                           else _page_token(snapshot, next_offset),
            "page_complete": next_offset == count,
            "real_database_paginated": False,
            "disposable_sqlite_paginated": True,
        }

    def confirm_current_coverage(
        self, *, claimed_owner: str, pages: tuple[dict, ...],
        process: AdministrativeProcess | None = None,
    ) -> dict:
        """Readback *each displayed item* inside one SQLite read snapshot.

        The pagination generation guards mutations but does NOT prove the
        caller returned the actual unmodified page payload. Compare every
        bounded LIMIT/OFFSET read with the supplied pages before claiming
        synthetic coverage. No remote authenticity or memory approval.
        """
        self._owner.require(claimed_owner)
        validated = verify_disposable_page_sequence(pages)
        scope = None if process is None else process.process_key
        if validated["process_key"] != scope:
            raise ContractViolation("PAGE_SCOPE_MISMATCH")
        with self._conn() as db:
            db.execute("BEGIN")
            try:
                if process is not None:
                    binding = db.execute(
                        "SELECT process_id FROM process_registry WHERE process_key=?",
                        (scope,),
                    ).fetchone()
                    if binding is None:
                        raise ContractViolation("PROCESS_BINDING_NOT_REGISTERED")
                    if binding["process_id"] != process.process_id:
                        raise ContractViolation("PROCESS_ID_COLLISION")
                generation = db.execute(
                    "SELECT generation FROM g14g_pending_generation WHERE id=1"
                ).fetchone()
                if generation is None:
                    raise ContractViolation("PAGINATION_GENERATION_MISSING")
                where = " WHERE review_status='PENDING_HUMAN_REVIEW'"
                params: tuple[str, ...] = ()
                if scope is not None:
                    where += " AND process_key=?"
                    params = (scope,)
                count = db.execute(
                    "SELECT COUNT(*) AS n FROM candidates" + where, params,
                ).fetchone()["n"]
                if _snapshot(generation["generation"], count, scope) != validated["snapshot"]:
                    raise ContractViolation("PAGE_SNAPSHOT_STALE")
                for page in pages:
                    rows = db.execute(
                        "SELECT candidate_id,process_key,process_id,"
                        "candidate_revision,summary,source_refs_json "
                        "FROM candidates" + where +
                        " ORDER BY process_key,candidate_id LIMIT ? OFFSET ?",
                        (*params, page["limit"], page["offset"]),
                    ).fetchall()
                    expected = [{
                        "candidate_id": row["candidate_id"],
                        "process_key": row["process_key"],
                        "process_id": row["process_id"],
                        "candidate_revision": row["candidate_revision"],
                        "summary_digest": sha256(row["summary"].encode()).hexdigest(),
                        "source_count": len(json.loads(row["source_refs_json"])),
                        "memory_approved": False,
                    } for row in rows]
                    if page["items"] != expected:
                        raise ContractViolation("PAGE_CONTENT_MISMATCH")
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return {
            **validated, "currently_matches_disposable_sqlite": True,
            "page_content_readback_verified": True,
            "real_qdrant_or_r06_readback": False,
            "requires_human_review": True,
        }
