"""G14-I: disposable OCR R02 event interoperability/lease lab.

Synthetic metadata only. No OCR engine, network, provider, R06, R07, Qdrant,
real authentication, customer data, or approved memory persistence.
Ticks are manually supplied logical test ticks; SQLite lives in TemporaryDirectory.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from tempfile import TemporaryDirectory

from .contracts import ContractViolation, DocumentEvent
from .g14g_isolated import G14GDisposableGate
from .g14h_ocr_r02_contract import preview_ocr_r02_contract
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly

_REF = re.compile(r"^[A-Za-z0-9_.:-]{8,100}$")
_FAILURES = frozenset({"PROVIDER_FAILURE_SYNTHETIC", "LEASE_WORKER_FAILED", "PAGE_METADATA_REJECTED"})
_SCHEMA = """
CREATE TABLE IF NOT EXISTS g14i_clock (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    tick INTEGER NOT NULL
);
INSERT OR IGNORE INTO g14i_clock VALUES (1,0);
CREATE TABLE IF NOT EXISTS g14i_tasks (
    process_key TEXT NOT NULL,
    process_id TEXT NOT NULL,
    task_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    document_id TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_version TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    document_quality TEXT NOT NULL,
    ocr_job_state TEXT NOT NULL,
    quality_counts_json TEXT NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL,
    lease_worker TEXT,
    lease_token TEXT,
    lease_until INTEGER,
    candidate_id TEXT,
    failure_code TEXT,
    PRIMARY KEY(process_key,task_key)
);
CREATE INDEX IF NOT EXISTS g14i_queue_select
ON g14i_tasks (state,lease_until,task_key);
CREATE TABLE IF NOT EXISTS g14i_task_history (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    process_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    prior_state TEXT,
    next_state TEXT NOT NULL,
    tick INTEGER NOT NULL
);
"""

def _strict_tick(tick: int) -> None:
    if isinstance(tick, bool) or not isinstance(tick, int) or tick < 0:
        raise ContractViolation("SYNTHETIC_TICK_INVALID")

def _ref(value: str) -> None:
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise ContractViolation("SYNTHETIC_TASK_REFERENCE_INVALID")

def _digest(value: object) -> str:
    return sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()

class G14IEventLab(G14GDisposableGate):
    """One-worker-at-a-time synthetic claim and evidence-only staging.

    A two-transaction finalization models the UNKNOWN state explicitly:
    no automatic replay if a crash occurs after the finalization barrier.
    """

    def __init__(self, workspace: TemporaryDirectory, owner: SyntheticOwnerOnly):
        super().__init__(workspace, owner)
        with self._conn() as db:
            db.executescript(_SCHEMA)

    @staticmethod
    def _advance_clock(db, now_tick: int) -> None:
        _strict_tick(now_tick)
        row = db.execute("SELECT tick FROM g14i_clock WHERE singleton=1").fetchone()
        if row is None or now_tick < row["tick"]:
            raise ContractViolation("SYNTHETIC_TIME_REGRESSION")
        db.execute("UPDATE g14i_clock SET tick=? WHERE singleton=1", (now_tick,))

    @staticmethod
    def _history(db, row, name: str, destination: str, tick: int) -> None:
        db.execute(
            "INSERT INTO g14i_task_history "
            "(process_key,task_key,event_kind,prior_state,next_state,tick) "
            "VALUES (?,?,?,?,?,?)",
            (row["process_key"],row["task_key"],name,row["state"],destination,tick),
        )

    def enqueue(
        self, *, claimed_owner: str, process: AdministrativeProcess,
        task_key: str, document_id: str, source_ref: str, source_version: str,
        source_sha256: str, format_kind: str, execution_state: str,
        total_pages: int, chunks: tuple, pages: tuple[dict, ...],
        exceptions: tuple[str, ...] = (), max_attempts: int = 3,
        now_tick: int = 0,
    ) -> dict:
        self._owner.require(claimed_owner)
        _ref(task_key)
        if (isinstance(max_attempts, bool) or not isinstance(max_attempts,int)
                or not 1 <= max_attempts <= 3):
            raise ContractViolation("MAX_ATTEMPTS_INVALID")
        preview = preview_ocr_r02_contract(
            owner=self._owner,claimed_owner=claimed_owner,process=process,
            document_id=document_id,source_ref=source_ref,
            source_version=source_version,source_sha256=source_sha256,
            format_kind=format_kind,execution_state=execution_state,
            total_pages=total_pages,chunks=chunks,pages=pages,exceptions=exceptions,
        )
        if preview["format_kind"] != "PDF":
            raise ContractViolation("NON_OCR_JOB_NOT_QUEUED")
        fingerprint = _digest([
            preview["safe_preview_fingerprint"],process.process_key,
            process.process_id,task_key,max_attempts,
        ])
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            binding = db.execute(
                "SELECT process_id FROM process_registry WHERE process_key=?",
                (process.process_key,),
            ).fetchone()
            if binding is None or binding["process_id"] != process.process_id:
                raise ContractViolation("PROCESS_BINDING_NOT_REGISTERED")
            observed = db.execute(
                "SELECT original_sha256,process_id FROM g14g_source_observations "
                "WHERE process_key=? AND source_ref=? AND source_version=?",
                (process.process_key,source_ref,source_version),
            ).fetchone()
            if (observed is None or observed["original_sha256"] != source_sha256
                    or observed["process_id"] != process.process_id):
                raise ContractViolation("OBSERVED_SOURCE_REQUIRED")
            existing = db.execute(
                "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            if existing is not None:
                if existing["fingerprint"] != fingerprint:
                    raise ContractViolation("OCR_JOB_IDEMPOTENCY_CONFLICT")
                return {
                    "task_key":task_key,"process_key":process.process_key,
                    "state":existing["state"],"replayed":True,
                    "attempts":existing["attempts"],"memory_approved":False,
                }
            state = "PENDING_SYNTHETIC"
            db.execute(
                "INSERT INTO g14i_tasks "
                "(process_key,process_id,task_key,fingerprint,document_id,source_ref,"
                "source_version,source_sha256,document_quality,ocr_job_state,"
                "quality_counts_json,state,max_attempts) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (process.process_key,process.process_id,task_key,fingerprint,
                 document_id,source_ref,source_version,source_sha256,
                 preview["document_quality"],preview["job_state"],
                 json.dumps(preview["quality_counts"],sort_keys=True),state,max_attempts),
            )
            row = db.execute(
                "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            self._history(db,{**row,"state":None},"ENQUEUED_SYNTHETIC",state,now_tick)
        return {
            "task_key":task_key,"process_key":process.process_key,
            "state":state,"replayed":False,"attempts":0,
            "quality":preview["document_quality"],"memory_approved":False,
            "actual_ocr_performed":False,
        }

    def claim(self, *, claimed_owner: str, worker: str,
              now_tick: int, lease_ticks: int = 3) -> dict | None:
        self._owner.require(claimed_owner)
        _ref(worker)
        if (isinstance(lease_ticks,bool) or not isinstance(lease_ticks,int)
                or not 1 <= lease_ticks <= 10):
            raise ContractViolation("LEASE_DURATION_INVALID")
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            exhausted=db.execute(
                "SELECT * FROM g14i_tasks WHERE state='LEASED_SYNTHETIC' "
                "AND lease_until<=? AND attempts>=max_attempts",
                (now_tick,),
            ).fetchall()
            for row in exhausted:
                self._history(db,row,"LEASE_EXHAUSTED","FAILED_SYNTHETIC",now_tick)
                db.execute(
                    "UPDATE g14i_tasks SET state='FAILED_SYNTHETIC',"
                    "lease_token=NULL,lease_worker=NULL,lease_until=NULL,"
                    "failure_code='LEASE_WORKER_FAILED' "
                    "WHERE process_key=? AND task_key=?",
                    (row["process_key"],row["task_key"]),
                )
            row=db.execute(
                "SELECT * FROM g14i_tasks WHERE "
                "state IN ('PENDING_SYNTHETIC','RETRY_PENDING_SYNTHETIC') "
                "OR (state='LEASED_SYNTHETIC' AND lease_until<=? "
                "AND attempts<max_attempts) "
                "ORDER BY task_key,process_key LIMIT 1",
                (now_tick,),
            ).fetchone()
            if row is None:
                return None
            attempt=row["attempts"]+1
            token=_digest([row["process_key"],row["task_key"],worker,attempt,now_tick])
            self._history(db,row,"CLAIM_OR_RECLAIM","LEASED_SYNTHETIC",now_tick)
            db.execute(
                "UPDATE g14i_tasks SET state='LEASED_SYNTHETIC',attempts=?,"
                "lease_worker=?,lease_token=?,lease_until=? "
                "WHERE process_key=? AND task_key=?",
                (attempt,worker,token,now_tick+lease_ticks,
                 row["process_key"],row["task_key"]),
            )
        return {
            "task_key":row["task_key"],"process_key":row["process_key"],
            "worker":worker,"lease_token":token,"attempt":attempt,
            "lease_until_tick":now_tick+lease_ticks,
            "no_external_task_claimed":True,
        }

    def _leased(self,db,*,process:AdministrativeProcess,task_key:str,
                worker:str,lease_token:str,now_tick:int):
        row=db.execute(
            "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
            (process.process_key,task_key),
        ).fetchone()
        if (row is None or row["process_id"] != process.process_id
                or row["state"]!="LEASED_SYNTHETIC"
                or row["lease_worker"]!=worker or row["lease_token"]!=lease_token
                or now_tick>=row["lease_until"]):
            raise ContractViolation("LEASE_NOT_CURRENT")
        return row

    def fail(self, *, claimed_owner:str,process:AdministrativeProcess,task_key:str,
             worker:str,lease_token:str,now_tick:int,error_code:str)->dict:
        self._owner.require(claimed_owner)
        if error_code not in _FAILURES:
            raise ContractViolation("UNSAFE_FAILURE_DETAIL")
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            row=self._leased(db,process=process,task_key=task_key,
                             worker=worker,lease_token=lease_token,now_tick=now_tick)
            next_state=("RETRY_PENDING_SYNTHETIC"
                        if row["attempts"]<row["max_attempts"]
                        else "FAILED_SYNTHETIC")
            self._history(db,row,"FAILURE_SYNTHETIC",next_state,now_tick)
            db.execute(
                "UPDATE g14i_tasks SET state=?,lease_worker=NULL,"
                "lease_token=NULL,lease_until=NULL,failure_code=? "
                "WHERE process_key=? AND task_key=?",
                (next_state,error_code,process.process_key,task_key),
            )
        return {"state":next_state,"attempts":row["attempts"],
                "retry_automatic_external":False,"memory_approved":False}

    def finish(
        self, *, claimed_owner:str,process:AdministrativeProcess,
        task_key:str,worker:str,lease_token:str,now_tick:int,
        event:DocumentEvent,original:bytes,
        simulate_crash_before_capture:bool=False,
    )->dict:
        self._owner.require(claimed_owner)
        if not isinstance(event,DocumentEvent) or not isinstance(original,bytes):
            raise ContractViolation("SYNTHETIC_EVENT_INVALID")
        if not isinstance(simulate_crash_before_capture,bool):
            raise ContractViolation("INVALID_CRASH_FLAG")
        if event.status!="completed" or event.operation!="ocr":
            raise ContractViolation("OCR_COMPLETION_EVENT_INVALID")
        if event.source.process_id!=process.process_id:
            raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
        if event.provider.lower()=="mock":
            raise ContractViolation("MOCK_OCR_NOT_EVIDENCE")
        if not event.source.matches_original(original):
            raise ContractViolation("SOURCE_HASH_MISMATCH")
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            row=self._leased(db,process=process,task_key=task_key,
                             worker=worker,lease_token=lease_token,now_tick=now_tick)
            if (row["source_ref"]!=event.source.source_ref
                    or row["source_version"]!=event.source.source_version
                    or row["source_sha256"]!=event.source.sha256_original):
                raise ContractViolation("OCR_EVENT_SOURCE_MISMATCH")
            quality=row["document_quality"]
            if row["ocr_job_state"]!="COMPLETED" or quality!="LEGIBLE_ALL_PAGES":
                state="REVIEW_NEEDED_SYNTHETIC"
            else:
                state="FINALIZING_UNKNOWN_SYNTHETIC"
            self._history(db,row,"COMPLETE_METADATA_SYNTHETIC",state,now_tick)
            db.execute(
                "UPDATE g14i_tasks SET state=?,lease_worker=NULL,"
                "lease_token=NULL,lease_until=NULL WHERE process_key=? AND task_key=?",
                (state,process.process_key,task_key),
            )
        if state=="REVIEW_NEEDED_SYNTHETIC":
            return {"state":state,"candidate_id":None,
                    "memory_approved":False,"qdrant_written":False}
        if simulate_crash_before_capture:
            return {"state":state,"candidate_id":None,
                    "requires_manual_reconciliation":True,
                    "automatic_retry":False,"memory_approved":False}
        # Deliberate transaction boundary: unknown is durable if capture fails.
        result=self.capture_observed_demo(
            claimed_owner=claimed_owner,process=process,event=event,original=original,
        )
        with self._tx() as db:
            current=db.execute(
                "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            if current is None or current["state"]!="FINALIZING_UNKNOWN_SYNTHETIC":
                raise ContractViolation("FINALIZATION_STATE_CHANGED")
            self._history(db,current,"CANDIDATE_CAPTURED_SYNTHETIC",
                          "CAPTURED_SYNTHETIC",now_tick)
            db.execute(
                "UPDATE g14i_tasks SET state='CAPTURED_SYNTHETIC',candidate_id=? "
                "WHERE process_key=? AND task_key=?",
                (result["candidate_id"],process.process_key,task_key),
            )
        return {"state":"CAPTURED_SYNTHETIC","candidate_id":result["candidate_id"],
                "source_count":result["source_count"],"memory_approved":False,
                "qdrant_written":False,"requires_authenticated_review":True}

    def receipt(self,*,claimed_owner:str,process:AdministrativeProcess,task_key:str)->dict:
        self._owner.require(claimed_owner)
        with self._conn() as db:
            row=db.execute(
                "SELECT process_id,state,attempts,max_attempts,candidate_id,"
                "document_quality,ocr_job_state,failure_code "
                "FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
        if row is None or row["process_id"]!=process.process_id:
            raise ContractViolation("TASK_NOT_FOUND_IN_PROCESS")
        return {**dict(row),"task_key":task_key,"process_key":process.process_key,
                "memory_approved":False,"qdrant_written":False,
                "real_provider_authenticated":False,
                "requires_manual_reconciliation":
                    row["state"]=="FINALIZING_UNKNOWN_SYNTHETIC"}

    def history(self,*,claimed_owner:str,process:AdministrativeProcess,task_key:str)->list[dict]:
        self._owner.require(claimed_owner)
        self.receipt(claimed_owner=claimed_owner,process=process,task_key=task_key)
        with self._conn() as db:
            rows=db.execute(
                "SELECT event_kind,prior_state,next_state,tick "
                "FROM g14i_task_history WHERE process_key=? AND task_key=? ORDER BY seq",
                (process.process_key,task_key),
            ).fetchall()
        return [dict(row) for row in rows]

    def preview_grouped_review(self,*,claimed_owner:str,process:AdministrativeProcess)->dict:
        """Groups pending candidates in one case; no permission or actual approval."""
        self._owner.require(claimed_owner)
        batches=self.preview_batches(claimed_owner=claimed_owner)
        groups=[b for b in batches if b["process_key"]==process.process_key]
        if not groups:
            return {"process_key":process.process_key,"batch_id":None,
                    "items":[],"requires_human_review":True,
                    "memory_approved":False,"qdrant_written":False}
        group=groups[0]
        return {"process_key":process.process_key,"batch_id":group["batch_id"],
                "items":[{"candidate_id":c["candidate_id"],
                           "candidate_revision":c["candidate_revision"],
                           "proposal_state":"PENDING_HUMAN_REVIEW"}
                          for c in group["candidates"]],
                "requires_human_review":True,"memory_approved":False,
                "qdrant_written":False,
                "authenticated_r06_review_performed":False}
