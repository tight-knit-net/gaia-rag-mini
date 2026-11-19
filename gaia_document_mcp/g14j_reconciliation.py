"""G14-J disposable UNKNOWN finalization reconciliation laboratory.

Only DEMO sources and temporary SQLite. No real OCR, external I/O, R06,
Qdrant, authentication, memory approval, provider writes or deployment.
Reconciliation requires a durable synthetic intent, effect receipt and
candidate/history readback; similarity is NEVER proof of a task effect.
"""
from __future__ import annotations

from hashlib import sha256
import json
from tempfile import TemporaryDirectory

from .contracts import ContractViolation, DocumentEvent
from .g14i_event_lab import G14IEventLab
from .g14c_disposable import _sha, _source_evidence_marker
from .g14f_contracts import SyntheticSourceObservation, event_contract_preview
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly, _canonical_summary

_SCHEMA_J = """
CREATE TABLE IF NOT EXISTS g14j_finalization_intents (
    process_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    process_id TEXT NOT NULL,
    event_key TEXT NOT NULL,
    expected_candidate_id TEXT NOT NULL,
    evidence_marker TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_version TEXT NOT NULL,
    original_sha256 TEXT NOT NULL,
    intent_tick INTEGER NOT NULL,
    PRIMARY KEY(process_key,task_key)
);
CREATE TABLE IF NOT EXISTS g14j_effect_receipts (
    process_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    event_key TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    candidate_revision INTEGER NOT NULL,
    proof_marker TEXT NOT NULL,
    PRIMARY KEY(process_key,task_key)
);
"""

class G14JReconcileLab(G14IEventLab):
    """Additive versioned synthetic readback; leaves G14-I behavior intact."""

    def __init__(self, workspace: TemporaryDirectory, owner: SyntheticOwnerOnly):
        super().__init__(workspace, owner)
        with self._conn() as db:
            db.executescript(_SCHEMA_J)

    def _require_event(self, *, claimed_owner: str,
                       process: AdministrativeProcess,
                       event: DocumentEvent, original: bytes) -> tuple[str,str,str]:
        self._owner.require(claimed_owner)
        if (not isinstance(process,AdministrativeProcess)
                or not isinstance(event,DocumentEvent)
                or not isinstance(original,bytes)
                or not original.startswith(b"%PDF-")
                or b"DEMO" not in original[:512]
                or event.status!="completed" or event.operation!="ocr"
                or event.provider.lower()=="mock"):
            raise ContractViolation("SYNTHETIC_COMPLETION_EVENT_INVALID")
        if event.source.process_id!=process.process_id:
            raise ContractViolation("PROCESS_CONTEXT_MISMATCH")
        if (not event.summary.startswith("DEMO: ")
                or not event.source.matches_original(original)):
            raise ContractViolation("SOURCE_HASH_MISMATCH_OR_NONDEMO")
        with self._conn() as db:
            observed=db.execute(
                "SELECT * FROM g14g_source_observations "
                "WHERE process_key=? AND source_ref=? AND source_version=?",
                (process.process_key,event.source.source_ref,event.source.source_version),
            ).fetchone()
        if observed is None:
            raise ContractViolation("OBSERVATION_REQUIRED")
        observation=SyntheticSourceObservation(
            process_id=observed["process_id"],process_key=process.process_key,
            source_ref=observed["source_ref"],source_version=observed["source_version"],
            original_sha256=observed["original_sha256"],
        )
        event_contract_preview(
            owner=self._owner,claimed_owner=claimed_owner,process=process,
            event=event,observation=observation,original=original,
        )
        topic_hash=_sha(_canonical_summary(event.summary.strip()))
        expected_id=_sha(process.process_key+":"+topic_hash)
        return event.fingerprint(),expected_id,_source_evidence_marker(event)

    def begin_unknown(self, *, claimed_owner: str,
                      process: AdministrativeProcess,task_key: str,worker: str,
                      lease_token: str,now_tick: int,event: DocumentEvent,
                      original: bytes) -> dict:
        """Atomically persist intent + UNKNOWN before any candidate side effect."""
        event_key,expected_id,evidence_marker=self._require_event(
            claimed_owner=claimed_owner,process=process,event=event,original=original,
        )
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            row=self._leased(
                db,process=process,task_key=task_key,worker=worker,
                lease_token=lease_token,now_tick=now_tick,
            )
            if (row["source_ref"]!=event.source.source_ref
                    or row["source_version"]!=event.source.source_version
                    or row["source_sha256"]!=event.source.sha256_original
                    or row["ocr_job_state"]!="COMPLETED"
                    or row["document_quality"]!="LEGIBLE_ALL_PAGES"):
                raise ContractViolation("NOT_ELIGIBLE_FOR_FINALIZATION")
            if db.execute(
                "SELECT 1 FROM g14j_finalization_intents WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone():
                raise ContractViolation("FINALIZATION_INTENT_CONFLICT")
            db.execute(
                "INSERT INTO g14j_finalization_intents VALUES(?,?,?,?,?,?,?,?,?,?)",
                (process.process_key,task_key,process.process_id,event_key,
                 expected_id,evidence_marker,event.source.source_ref,
                 event.source.source_version,event.source.sha256_original,now_tick),
            )
            self._history(db,row,"G14J_INTENT_DURABLE_SYNTHETIC",
                          "FINALIZING_UNKNOWN_SYNTHETIC",now_tick)
            db.execute(
                "UPDATE g14i_tasks SET state='FINALIZING_UNKNOWN_SYNTHETIC',"
                "lease_worker=NULL,lease_token=NULL,lease_until=NULL "
                "WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            )
        return {"state":"FINALIZING_UNKNOWN_SYNTHETIC",
                "intent_event_key":event_key,"candidate_id":None,
                "automatic_retry":False,"memory_approved":False,
                "requires_manual_reconciliation":True}

    def simulate_effect_receipt(
        self, *, claimed_owner: str,process: AdministrativeProcess,
        task_key: str,event: DocumentEvent,original: bytes,
    ) -> dict:
        """Controlled post-intent DEMO capture with a separate durable receipt.

        Crash *between* candidate capture and receipt is intentionally
        unrecoverable automatically: absent independent receipt => NO-GO.
        """
        event_key,expected_id,marker=self._require_event(
            claimed_owner=claimed_owner,process=process,event=event,original=original,
        )
        with self._conn() as db:
            task=db.execute(
                "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            intent=db.execute(
                "SELECT * FROM g14j_finalization_intents WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            effect=db.execute(
                "SELECT * FROM g14j_effect_receipts WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            prior=db.execute(
                "SELECT 1 FROM candidate_history WHERE candidate_id=? AND event_key=? "
                "AND event_name IN ('CAPTURED_SYNTHETIC','EVIDENCE_ADDED_SYNTHETIC')",
                (expected_id,event_key),
            ).fetchone()
        if (task is None or task["process_id"]!=process.process_id
                or task["state"]!="FINALIZING_UNKNOWN_SYNTHETIC"
                or intent is None or intent["process_id"]!=process.process_id
                or intent["event_key"]!=event_key
                or intent["expected_candidate_id"]!=expected_id
                or intent["evidence_marker"]!=marker):
            raise ContractViolation("FINALIZATION_INTENT_MISMATCH")
        if effect is not None:
            if effect["candidate_id"]!=expected_id or effect["event_key"]!=event_key:
                raise ContractViolation("EFFECT_RECEIPT_CONFLICT")
            return {"state":"RECEIPT_ALREADY_PRESENT_SYNTHETIC",
                    "candidate_id":expected_id,"replayed":True,
                    "memory_approved":False}
        if prior is not None:
            # Matching older candidate history cannot be attributed to this task.
            raise ContractViolation("AMBIGUOUS_PRIOR_CAPTURE")
        result=self.capture_observed_demo(
            claimed_owner=claimed_owner,process=process,event=event,original=original,
        )
        if result["candidate_id"]!=expected_id:
            raise ContractViolation("CAPTURE_ID_MISMATCH")
        with self._tx() as db:
            task=db.execute(
                "SELECT state FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            candidate=db.execute(
                "SELECT * FROM candidates WHERE candidate_id=? AND process_key=?",
                (expected_id,process.process_key),
            ).fetchone()
            evidence=db.execute(
                "SELECT 1 FROM candidate_history WHERE candidate_id=? AND event_key=? "
                "AND event_name IN ('CAPTURED_SYNTHETIC','EVIDENCE_ADDED_SYNTHETIC')",
                (expected_id,event_key),
            ).fetchone()
            if (task is None or task["state"]!="FINALIZING_UNKNOWN_SYNTHETIC"
                    or candidate is None or candidate["process_id"]!=process.process_id
                    or evidence is None
                    or event_key not in json.loads(candidate["event_keys_json"])
                    or marker not in json.loads(candidate["evidence_markers_json"])):
                raise ContractViolation("CAPTURE_EFFECT_NOT_VERIFIED")
            db.execute(
                "INSERT INTO g14j_effect_receipts VALUES(?,?,?,?,?,?)",
                (process.process_key,task_key,event_key,expected_id,
                 candidate["candidate_revision"],marker),
            )
        return {"state":"EFFECT_RECEIPT_SYNTHETIC","candidate_id":expected_id,
                "replayed":False,"requires_manual_reconciliation":True,
                "memory_approved":False,"qdrant_written":False}

    @staticmethod
    def _verify_proof(db,task,intent,effect) -> bool:
        if intent is None or effect is None:
            return False
        candidate=db.execute(
            "SELECT * FROM candidates WHERE candidate_id=? AND process_key=?",
            (intent["expected_candidate_id"],intent["process_key"]),
        ).fetchone()
        history=db.execute(
            "SELECT 1 FROM candidate_history WHERE candidate_id=? AND event_key=? "
            "AND event_name IN ('CAPTURED_SYNTHETIC','EVIDENCE_ADDED_SYNTHETIC')",
            (intent["expected_candidate_id"],intent["event_key"]),
        ).fetchone()
        return bool(
            candidate is not None and history is not None
            and task["process_id"]==intent["process_id"]
            and task["source_ref"]==intent["source_ref"]
            and task["source_version"]==intent["source_version"]
            and task["source_sha256"]==intent["original_sha256"]
            and candidate["process_id"]==intent["process_id"]
            and candidate["review_status"]=="PENDING_HUMAN_REVIEW"
            and effect["candidate_id"]==intent["expected_candidate_id"]
            and effect["event_key"]==intent["event_key"]
            and effect["proof_marker"]==intent["evidence_marker"]
            and effect["candidate_revision"]==candidate["candidate_revision"]
            and intent["source_ref"] in json.loads(candidate["source_refs_json"])
            and intent["event_key"] in json.loads(candidate["event_keys_json"])
            and intent["evidence_marker"] in json.loads(candidate["evidence_markers_json"])
        )

    def reconcile_unknown(self, *, claimed_owner: str,
                          process:AdministrativeProcess,task_key:str,
                          now_tick:int) -> dict:
        """Single CAS-like tx: no evidence => pending; proven => captured.

        A second concurrent caller receives an idempotent readback, not
        another candidate capture or second history transition.
        """
        self._owner.require(claimed_owner)
        if not isinstance(process,AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        with self._tx() as db:
            self._advance_clock(db,now_tick)
            task=db.execute(
                "SELECT * FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            if task is None or task["process_id"]!=process.process_id:
                raise ContractViolation("TASK_NOT_FOUND_IN_PROCESS")
            if task["state"] not in ("FINALIZING_UNKNOWN_SYNTHETIC","CAPTURED_SYNTHETIC"):
                raise ContractViolation("RECONCILIATION_STATE_INVALID")
            intent=db.execute(
                "SELECT * FROM g14j_finalization_intents WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            effect=db.execute(
                "SELECT * FROM g14j_effect_receipts WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
            if effect is None:
                if task["state"]=="CAPTURED_SYNTHETIC":
                    raise ContractViolation("RECONCILIATION_PROOF_MISSING")
                return {"state":"RECONCILIATION_PENDING_SYNTHETIC",
                        "candidate_id":None,"proof_verified":False,
                        "automatic_retry":False,"memory_approved":False,
                        "qdrant_written":False}
            if not self._verify_proof(db,task,intent,effect):
                raise ContractViolation("RECONCILIATION_PROOF_MISMATCH")
            if task["state"]=="CAPTURED_SYNTHETIC":
                if task["candidate_id"]!=effect["candidate_id"]:
                    raise ContractViolation("RECONCILIATION_PROOF_MISMATCH")
                replayed=True
            else:
                self._history(db,task,"G14J_RECONCILED_SYNTHETIC",
                              "CAPTURED_SYNTHETIC",now_tick)
                db.execute(
                    "UPDATE g14i_tasks SET state='CAPTURED_SYNTHETIC',candidate_id=? "
                    "WHERE process_key=? AND task_key=? AND state='FINALIZING_UNKNOWN_SYNTHETIC'",
                    (effect["candidate_id"],process.process_key,task_key),
                )
                replayed=False
        return {"state":"CAPTURED_SYNTHETIC","candidate_id":effect["candidate_id"],
                "proof_verified_in_disposable_sqlite":True,
                "replayed":replayed,"memory_approved":False,
                "qdrant_written":False,"real_provider_readback":False,
                "requires_authenticated_review":True}

    def audit_task_history(self, *, claimed_owner:str,
                           process:AdministrativeProcess,task_key:str) -> dict:
        """History chain, monotonic ticks, terminal task readback."""
        self._owner.require(claimed_owner)
        self.receipt(claimed_owner=claimed_owner,process=process,task_key=task_key)
        with self._conn() as db:
            entries=db.execute(
                "SELECT prior_state,next_state,event_kind,tick FROM g14i_task_history "
                "WHERE process_key=? AND task_key=? ORDER BY seq",
                (process.process_key,task_key),
            ).fetchall()
            task=db.execute(
                "SELECT state FROM g14i_tasks WHERE process_key=? AND task_key=?",
                (process.process_key,task_key),
            ).fetchone()
        if not entries or task is None:
            raise ContractViolation("TASK_HISTORY_INCOMPLETE")
        prior=None
        last_tick=-1
        for entry in entries:
            if (entry["prior_state"]!=prior
                    or not isinstance(entry["tick"],int)
                    or entry["tick"]<last_tick):
                raise ContractViolation("TASK_HISTORY_INTEGRITY_ERROR")
            prior=entry["next_state"]
            last_tick=entry["tick"]
        if task["state"]!=prior:
            raise ContractViolation("TASK_HISTORY_TERMINAL_MISMATCH")
        return {"history_valid_in_disposable_sqlite":True,
                "transitions":len(entries),"terminal_state":prior,
                "real_audit_log_authenticated":False}

    def review_preview_after_reconciliation(self, *, claimed_owner:str,
                                            process:AdministrativeProcess) -> dict:
        """Block all synthetic grouped review while any task is UNKNOWN."""
        self._owner.require(claimed_owner)
        if not isinstance(process,AdministrativeProcess):
            raise ContractViolation("INVALID_PROCESS")
        with self._conn() as db:
            reg=db.execute(
                "SELECT process_id FROM process_registry WHERE process_key=?",
                (process.process_key,),
            ).fetchone()
            if reg is None or reg["process_id"]!=process.process_id:
                raise ContractViolation("PROCESS_ID_COLLISION")
            pending=db.execute(
                "SELECT COUNT(*) AS n FROM g14i_tasks WHERE process_key=? "
                "AND state='FINALIZING_UNKNOWN_SYNTHETIC'",
                (process.process_key,),
            ).fetchone()["n"]
        if pending:
            return {"state":"BLOCKED_UNKNOWN_SYNTHETIC","batch_id":None,
                    "items":[],"unknown_task_count":pending,
                    "requires_manual_reconciliation":True,
                    "memory_approved":False,"qdrant_written":False}
        preview=self.preview_grouped_review(
            claimed_owner=claimed_owner,process=process,
        )
        return {**preview,"state":"PREVIEW_ONLY_SYNTHETIC",
                "authenticated_r06_review_performed":False,
                "memory_approved":False,"qdrant_written":False}
