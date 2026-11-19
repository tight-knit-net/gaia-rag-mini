"""G14-J independent synthetic UNKNOWN, readback, concurrency and review tests.

Only invented source bytes, SQLite TemporaryDirectory, ticks, no services.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation,DocumentEvent,DocumentSource
from gaia_document_mcp.process_learning import AdministrativeProcess,SyntheticOwnerOnly
from gaia_document_mcp.g14j_reconciliation import G14JReconcileLab

OWNER="GAIA_OWNER_DEMO"
RAW=b"%PDF-1.4\nDEMO G14J SYNTHETIC ONLY\n%%EOF"
DIGEST=sha256(RAW).hexdigest()
TEXT_SHA=sha256(b"DEMO PAGE").hexdigest()
TASK="DEMO_TASK_G14J_01"
WORKER="DEMO_WORKER_01"

def process(*,number="000123/2026",pid="DEMO_PROC_000123"):
    return AdministrativeProcess(
        process_id=pid,agency_code="PREF_DEMO",
        jurisdiction="BR-SC-FLN",official_number=number,
    )

def event(p=None,*,summary="DEMO: requerimento administrativo",
          file_id="FILE_DEMO_G14J_001"):
    p=p or process()
    return DocumentEvent(
        source=DocumentSource(
            drive_id="DRIVE_DEMO_001",file_id=file_id,
            client_id="009",process_id=p.process_id,
            source_version="DEMO_VER_01",sha256_original=DIGEST,
        ),
        operation="ocr",status="completed",provider="tesseract",
        source_verified=False,operation_id="DEMO_OP_001",summary=summary,
    )

def page():
    return {"page":1,"quality":"OCR_READABLE","confidence":0.91,
            "attempts":1,"text_sha256":TEXT_SHA}

class G14JUnknownReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix="gaia-g14j-test-")
        self.addCleanup(self.tmp.cleanup)
        self.owner=SyntheticOwnerOnly(OWNER)
        self.lab=G14JReconcileLab(self.tmp,self.owner)
        self.p=process()
        self.ev=event(self.p)
        self.lab.seed(claimed_owner=OWNER,process=self.p,revision="DEMO_REV_01")
        self.lab.observe_demo_source(
            claimed_owner=OWNER,process=self.p,
            source_ref=self.ev.source.source_ref,
            source_version=self.ev.source.source_version,original=RAW,
        )

    def enqueue(self, *,task=TASK,process_obj=None,ev=None,
                now_tick=0,pages=None):
        p=process_obj or self.p
        ev=ev or self.ev
        return self.lab.enqueue(
            claimed_owner=OWNER,process=p,task_key=task,
            document_id="DOC_DEMO_G14J_01",source_ref=ev.source.source_ref,
            source_version=ev.source.source_version,
            source_sha256=DIGEST,format_kind="PDF",execution_state="completed",
            total_pages=1,chunks=((1,1),),
            pages=(page(),) if pages is None else pages,
            now_tick=now_tick,
        )

    def claim(self,*,tick=1,worker=WORKER):
        return self.lab.claim(claimed_owner=OWNER,worker=worker,now_tick=tick)

    def begin(self,claim,*,tick=2,task=TASK,ev=None,p=None,original=RAW):
        return self.lab.begin_unknown(
            claimed_owner=OWNER,process=p or self.p,task_key=task,
            worker=claim["worker"],lease_token=claim["lease_token"],
            now_tick=tick,event=ev or self.ev,original=original,
        )

    def effect(self,*,task=TASK,p=None,ev=None,original=RAW,lab=None):
        return (lab or self.lab).simulate_effect_receipt(
            claimed_owner=OWNER,process=p or self.p,task_key=task,
            event=ev or self.ev,original=original,
        )

    def reconcile(self,*,task=TASK,tick=3,p=None,lab=None):
        return (lab or self.lab).reconcile_unknown(
            claimed_owner=OWNER,process=p or self.p,
            task_key=task,now_tick=tick,
        )

    def receipt(self,*,task=TASK,p=None):
        return self.lab.receipt(claimed_owner=OWNER,process=p or self.p,task_key=task)

    def ready(self):
        self.enqueue()
        c=self.claim()
        return self.begin(c)

    def test_intent_atomic_unknown_persists_without_capture(self):
        r=self.ready()
        self.assertEqual(r["state"],"FINALIZING_UNKNOWN_SYNTHETIC")
        self.assertFalse(r["automatic_retry"])
        self.assertIsNone(self.receipt()["candidate_id"])

    def test_no_proof_retains_unknown_and_never_recaptures(self):
        self.ready()
        r=self.reconcile()
        self.assertEqual(r["state"],"RECONCILIATION_PENDING_SYNTHETIC")
        self.assertFalse(r["proof_verified"])
        self.assertFalse(r["automatic_retry"])
        self.assertEqual(self.receipt()["state"],"FINALIZING_UNKNOWN_SYNTHETIC")
        self.assertEqual(self.lab.preview_grouped_review(
            claimed_owner=OWNER,process=self.p)["items"],[])

    def test_repeated_no_proof_readback_does_not_increment_history(self):
        self.ready()
        before=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.reconcile()
        self.reconcile(tick=3)
        after=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.assertEqual(len(before),len(after))

    def test_matching_effect_receipt_allows_reconciliation(self):
        self.ready()
        r=self.effect()
        self.assertEqual(r["state"],"EFFECT_RECEIPT_SYNTHETIC")
        done=self.reconcile()
        self.assertEqual(done["state"],"CAPTURED_SYNTHETIC")
        self.assertTrue(done["proof_verified_in_disposable_sqlite"])
        self.assertFalse(done["qdrant_written"])
        self.assertEqual(self.receipt()["candidate_id"],r["candidate_id"])

    def test_reconciliation_replay_does_not_duplicate_history(self):
        self.ready()
        self.effect()
        first=self.reconcile()
        before=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        second=self.reconcile(tick=4)
        after=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.assertFalse(first["replayed"])
        self.assertTrue(second["replayed"])
        self.assertEqual(before,after)

    def test_effect_receipt_replay_is_idempotent_without_recapture(self):
        self.ready()
        a=self.effect()
        before=self.lab.candidate_history_readback(
            claimed_owner=OWNER,candidate_id=a["candidate_id"],
        )
        b=self.effect()
        after=self.lab.candidate_history_readback(
            claimed_owner=OWNER,candidate_id=a["candidate_id"],
        )
        self.assertTrue(b["replayed"])
        self.assertEqual(before,after)

    def test_crash_after_capture_but_before_proof_is_fail_closed(self):
        self.ready()
        self.lab.capture_observed_demo(
            claimed_owner=OWNER,process=self.p,event=self.ev,original=RAW,
        )
        r=self.reconcile()
        self.assertEqual(r["state"],"RECONCILIATION_PENDING_SYNTHETIC")
        with self.assertRaisesRegex(ContractViolation,"AMBIGUOUS_PRIOR_CAPTURE"):
            self.effect()

    def test_prior_same_event_from_other_task_is_not_effect_proof(self):
        self.lab.capture_observed_demo(
            claimed_owner=OWNER,process=self.p,event=self.ev,original=RAW,
        )
        self.ready()
        with self.assertRaisesRegex(ContractViolation,"AMBIGUOUS_PRIOR_CAPTURE"):
            self.effect()
        self.assertEqual(self.reconcile()["state"],"RECONCILIATION_PENDING_SYNTHETIC")

    def test_no_old_worker_can_finalize_after_intent(self):
        self.enqueue()
        c=self.claim()
        self.begin(c)
        with self.assertRaisesRegex(ContractViolation,"LEASE_NOT_CURRENT"):
            self.lab.finish(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
                worker=c["worker"],lease_token=c["lease_token"],
                now_tick=3,event=self.ev,original=RAW,
            )

    def test_unknown_not_claimable_after_expired_lease(self):
        self.ready()
        self.assertIsNone(self.claim(tick=10,worker="DEMO_WORKER_02"))

    def test_wrong_document_bytes_are_rejected_before_intent(self):
        self.enqueue()
        c=self.claim()
        with self.assertRaisesRegex(ContractViolation,"SOURCE_HASH_MISMATCH_OR_NONDEMO"):
            self.begin(c,original=RAW+b"changed")
        self.assertEqual(self.receipt()["state"],"LEASED_SYNTHETIC")

    def test_source_identity_mismatch_is_rejected_before_intent(self):
        self.enqueue()
        c=self.claim()
        other=event(self.p,file_id="FILE_DEMO_G14J_999")
        with self.assertRaisesRegex(ContractViolation,"OBSERVATION_REQUIRED"):
            self.begin(c,ev=other)
        self.assertEqual(self.receipt()["state"],"LEASED_SYNTHETIC")

    def test_task_alias_process_number_cannot_reconcile(self):
        self.ready()
        p=process(pid="DEMO_OTHER_INTERNAL_ID")
        with self.assertRaisesRegex(ContractViolation,"TASK_NOT_FOUND_IN_PROCESS"):
            self.reconcile(p=p)

    def test_wrong_event_fingerprint_cannot_record_effect(self):
        self.ready()
        changed=event(self.p,summary="DEMO: documento alterado")
        with self.assertRaisesRegex(ContractViolation,"FINALIZATION_INTENT_MISMATCH"):
            self.effect(ev=changed)
        self.assertEqual(self.reconcile()["state"],"RECONCILIATION_PENDING_SYNTHETIC")

    def test_changed_capture_receipt_candidate_is_not_accepted(self):
        self.ready()
        self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14j_effect_receipts SET candidate_id=? WHERE task_key=?",
                ("a"*64,TASK),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()
        self.assertEqual(self.receipt()["state"],"FINALIZING_UNKNOWN_SYNTHETIC")

    def test_changed_capture_receipt_event_is_not_accepted(self):
        self.ready()
        self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14j_effect_receipts SET event_key=? WHERE task_key=?",
                ("a"*64,TASK),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_changed_candidate_event_history_is_not_accepted(self):
        self.ready()
        out=self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE candidate_history SET event_key=? WHERE candidate_id=?",
                ("a"*64,out["candidate_id"]),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_changed_candidate_revision_is_not_accepted(self):
        self.ready()
        out=self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE candidates SET candidate_revision=candidate_revision+1 "
                "WHERE candidate_id=?",
                (out["candidate_id"],),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_deleted_candidate_cannot_be_reconstructed_by_reconcile(self):
        self.ready()
        out=self.effect()
        with self.lab._tx() as db:
            db.execute("DELETE FROM candidates WHERE candidate_id=?",(out["candidate_id"],))
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_changed_intent_source_version_invalidates_proof(self):
        self.ready()
        self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14j_finalization_intents SET source_version=? "
                "WHERE task_key=?",("ALTERED_VERSION",TASK),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_changed_intent_digest_invalidates_receipt(self):
        self.ready()
        self.effect()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14j_finalization_intents SET event_key=? WHERE task_key=?",
                ("b"*64,TASK),
            )
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_PROOF_MISMATCH"):
            self.reconcile()

    def test_repeated_reconcile_is_serialized_between_threads(self):
        self.ready()
        self.effect()
        def attempt(_):
            return self.reconcile(tick=3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,range(2)))
        self.assertEqual(sum(not x["replayed"] for x in results),1)
        self.assertEqual(sum(x["replayed"] for x in results),1)
        h=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.assertEqual(sum(x["event_kind"]=="G14J_RECONCILED_SYNTHETIC" for x in h),1)

    def test_concurrent_unknown_without_receipt_never_captures(self):
        self.ready()
        with ThreadPoolExecutor(max_workers=2) as pool:
            r=list(pool.map(lambda _:self.reconcile(tick=3),range(2)))
        self.assertTrue(all(x["state"]=="RECONCILIATION_PENDING_SYNTHETIC" for x in r))
        self.assertEqual(self.receipt()["state"],"FINALIZING_UNKNOWN_SYNTHETIC")

    def test_proof_survives_reopening_disposable_connection(self):
        self.ready()
        self.effect()
        reopened=G14JReconcileLab(self.tmp,self.owner)
        r=self.reconcile(lab=reopened)
        self.assertEqual(r["state"],"CAPTURED_SYNTHETIC")
        self.assertFalse(r["real_provider_readback"])

    def test_history_chain_has_correct_terminal_readback(self):
        self.ready()
        self.effect()
        self.reconcile()
        audit=self.lab.audit_task_history(
            claimed_owner=OWNER,process=self.p,task_key=TASK,
        )
        self.assertEqual(audit["transitions"],4)
        self.assertEqual(audit["terminal_state"],"CAPTURED_SYNTHETIC")
        self.assertFalse(audit["real_audit_log_authenticated"])

    def test_broken_history_transition_is_detected(self):
        self.ready()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14i_task_history SET prior_state='FORGED' "
                "WHERE task_key=? AND event_kind='G14J_INTENT_DURABLE_SYNTHETIC'",
                (TASK,),
            )
        with self.assertRaisesRegex(ContractViolation,"TASK_HISTORY_INTEGRITY_ERROR"):
            self.lab.audit_task_history(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
            )

    def test_backward_history_tick_is_detected(self):
        self.ready()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14i_task_history SET tick=0 "
                "WHERE task_key=? AND event_kind='G14J_INTENT_DURABLE_SYNTHETIC'",
                (TASK,),
            )
        with self.assertRaisesRegex(ContractViolation,"TASK_HISTORY_INTEGRITY_ERROR"):
            self.lab.audit_task_history(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
            )

    def test_history_terminal_state_change_is_detected(self):
        self.ready()
        with self.lab._tx() as db:
            db.execute(
                "UPDATE g14i_tasks SET state='FAILED_SYNTHETIC' WHERE task_key=?",
                (TASK,),
            )
        with self.assertRaisesRegex(ContractViolation,"TASK_HISTORY_TERMINAL_MISMATCH"):
            self.lab.audit_task_history(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
            )

    def test_grouped_preview_is_blocked_while_unknown_no_effect(self):
        self.ready()
        group=self.lab.review_preview_after_reconciliation(
            claimed_owner=OWNER,process=self.p,
        )
        self.assertEqual(group["state"],"BLOCKED_UNKNOWN_SYNTHETIC")
        self.assertIsNone(group["batch_id"])
        self.assertFalse(group["memory_approved"])

    def test_grouped_preview_is_blocked_even_after_unreconciled_effect(self):
        self.ready()
        self.effect()
        group=self.lab.review_preview_after_reconciliation(
            claimed_owner=OWNER,process=self.p,
        )
        self.assertEqual(group["state"],"BLOCKED_UNKNOWN_SYNTHETIC")
        self.assertEqual(group["items"],[])

    def test_grouped_preview_after_verified_reconciliation_is_unapproved(self):
        self.ready()
        self.effect()
        self.reconcile()
        group=self.lab.review_preview_after_reconciliation(
            claimed_owner=OWNER,process=self.p,
        )
        self.assertEqual(group["state"],"PREVIEW_ONLY_SYNTHETIC")
        self.assertEqual(len(group["items"]),1)
        self.assertFalse(group["authenticated_r06_review_performed"])
        self.assertFalse(group["qdrant_written"])

    def test_batch_prepare_proposal_never_approves_qdrant(self):
        self.ready()
        self.effect()
        self.reconcile()
        group=self.lab.review_preview_after_reconciliation(
            claimed_owner=OWNER,process=self.p,
        )
        item=group["items"][0]["candidate_id"]
        reviewed=self.lab.review_batch_items(
            claimed_owner=OWNER,process_key=self.p.process_key,
            batch_id=group["batch_id"],decisions={item:"prepare_proposals"},
        )
        self.assertFalse(reviewed["memory_approved"])
        self.assertFalse(reviewed["real_human_review_verified"])
        self.assertTrue(reviewed["requires_authenticated_r06_batch_review"])

    def test_other_operator_cannot_reconcile_synthetic_fixture(self):
        self.ready()
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            self.lab.reconcile_unknown(
                claimed_owner="OTHER_USER",process=self.p,task_key=TASK,now_tick=3,
            )

    def test_wrong_case_process_cannot_see_pending_review(self):
        self.ready()
        alias=process(pid="ANOTHER_INTERNAL_ID")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_ID_COLLISION"):
            self.lab.review_preview_after_reconciliation(
                claimed_owner=OWNER,process=alias,
            )

    def test_no_approval_flag_in_reconciliation_readback(self):
        self.ready()
        self.effect()
        result=self.reconcile()
        self.assertFalse(result["memory_approved"])
        self.assertFalse(result["qdrant_written"])
        self.assertTrue(result["requires_authenticated_review"])

if __name__=="__main__":
    unittest.main()
