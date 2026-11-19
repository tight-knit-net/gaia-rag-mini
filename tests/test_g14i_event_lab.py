"""G14-I synthetic queue/lease/OCR event interoperability regressions.

No actual OCR, tenant auth, DB service, network, R06, R07 or Qdrant.
Every fixture uses TemporaryDirectory and fake administrative identifiers.
"""
from dataclasses import replace
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentEvent, DocumentSource
from gaia_document_mcp.process_learning import AdministrativeProcess, SyntheticOwnerOnly
from gaia_document_mcp.g14i_event_lab import G14IEventLab

OWNER="GAIA_OWNER_DEMO"
RAW=b"%PDF-1.4\nDEMO SYNTHETIC TEST DOCUMENT\n%%EOF"
HASH=sha256(RAW).hexdigest()
TEXT=sha256(b"DEMO SYNTHETIC PAGE").hexdigest()
TASK="DEMO_TASK_00000001"
WORKER="DEMO_WORKER_ALPHA"

def process(*,number="000123/2026",pid="DEMO_PROC_000123"):
    return AdministrativeProcess(
        process_id=pid,agency_code="PREF_DEMO",
        jurisdiction="BR-SC-FLN",official_number=number,
    )

def event(p=None,*,summary="DEMO: requerimento administrativo",
          source_version="DEMO_VER_01",file_id="FILE_DEMO_001"):
    p=p or process()
    return DocumentEvent(
        source=DocumentSource(
            drive_id="DRIVE_DEMO_001",file_id=file_id,client_id="009",
            process_id=p.process_id,source_version=source_version,
            sha256_original=HASH,
        ),
        operation="ocr",status="completed",provider="tesseract",
        source_verified=False,operation_id="DEMO_OP_001",
        summary=summary,
    )

def page(i,kind="OCR_READABLE",confidence=.90,attempts=1,text_hash=TEXT):
    return {"page":i,"quality":kind,"confidence":confidence,
            "attempts":attempts,"text_sha256":text_hash}

class G14IEventQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix="gaia-g14i-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.owner=SyntheticOwnerOnly(OWNER)
        self.lab=G14IEventLab(self.tmp,self.owner)
        self.p=process()
        self.lab.seed(claimed_owner=OWNER,process=self.p,revision="DEMO_REV_01")
        self.ev=event(self.p)
        self.lab.observe_demo_source(
            claimed_owner=OWNER,process=self.p,source_ref=self.ev.source.source_ref,
            source_version=self.ev.source.source_version,original=RAW,
        )

    def submit(self,*,p=None,ev=None,task=TASK,kind="OCR_READABLE",
               quality_conf=.90,max_attempts=3,now=0,pages=None,source_sha=HASH,
               format_kind="PDF",state="completed",chunks=((1,1),),
               total_pages=None):
        p=p or self.p
        ev=ev or self.ev
        if pages is None:
            pages=(page(1,kind,quality_conf,1 if kind!="NATIVE" else 0,
                        None if kind in ("EMPTY","LOW_CONFIDENCE") else TEXT),)
        return self.lab.enqueue(
            claimed_owner=OWNER,process=p,task_key=task,
            document_id="DOC_DEMO_001",source_ref=ev.source.source_ref,
            source_version=ev.source.source_version,source_sha256=source_sha,
            format_kind=format_kind,execution_state=state,
            total_pages=(len(pages) if total_pages is None else total_pages),
            chunks=chunks,pages=pages,max_attempts=max_attempts,now_tick=now,
        )

    def claim(self,*,worker=WORKER,tick=1,lease_ticks=3):
        return self.lab.claim(claimed_owner=OWNER,worker=worker,
                              now_tick=tick,lease_ticks=lease_ticks)

    def finish(self,claim,*,tick=2,ev=None,original=RAW,crash=False,task=TASK,p=None):
        return self.lab.finish(
            claimed_owner=OWNER,process=p or self.p,task_key=task,
            worker=claim["worker"],lease_token=claim["lease_token"],
            now_tick=tick,event=ev or self.ev,original=original,
            simulate_crash_before_capture=crash,
        )

    def receipt(self,task=TASK,p=None):
        return self.lab.receipt(claimed_owner=OWNER,process=p or self.p,task_key=task)

    # Enqueue fingerprints, source observation and administrative case context
    def test_enqueue_preserves_metadata_and_is_not_real_ocr(self):
        a=self.submit()
        self.assertEqual(a["state"],"PENDING_SYNTHETIC")
        self.assertFalse(a["actual_ocr_performed"])
        self.assertFalse(a["memory_approved"])
        self.assertEqual(a["quality"],"LEGIBLE_ALL_PAGES")

    def test_reenqueue_same_task_is_idempotent_without_duplicate(self):
        self.submit()
        replay=self.submit()
        self.assertTrue(replay["replayed"])
        self.assertEqual(self.receipt()["attempts"],0)

    def test_same_task_with_changed_page_quality_conflicts(self):
        self.submit()
        with self.assertRaisesRegex(ContractViolation,"OCR_JOB_IDEMPOTENCY_CONFLICT"):
            self.submit(kind="LOW_CONFIDENCE",quality_conf=.4)

    def test_same_key_other_process_is_separate_not_acl(self):
        self.submit()
        other=process(number="000124/2026",pid="DEMO_PROC_000124")
        ev=event(other)
        self.lab.seed(claimed_owner=OWNER,process=other,revision="DEMO_REV_01")
        self.lab.observe_demo_source(
            claimed_owner=OWNER,process=other,source_ref=ev.source.source_ref,
            source_version=ev.source.source_version,original=RAW,
        )
        r=self.submit(p=other,ev=ev)
        self.assertNotEqual(r["process_key"],self.p.process_key)
        self.assertEqual(self.receipt(p=other)["state"],"PENDING_SYNTHETIC")

    def test_missing_observation_does_not_enqueue(self):
        ev=event(self.p,source_version="DEMO_VER_02")
        with self.assertRaisesRegex(ContractViolation,"OBSERVED_SOURCE_REQUIRED"):
            self.submit(ev=ev)

    def test_false_original_hash_does_not_enqueue(self):
        with self.assertRaisesRegex(ContractViolation,"OBSERVED_SOURCE_REQUIRED"):
            self.submit(source_sha="f"*64)

    def test_task_requires_registered_process(self):
        alias=process(pid="DEMO_ALIASED_ID")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_BINDING_NOT_REGISTERED"):
            self.submit(p=alias,ev=event(alias))

    def test_failed_ocr_metadata_is_not_legible(self):
        a=self.submit(state="failed",chunks=(),pages=(),total_pages=1)
        self.assertEqual(a["quality"],"INCOMPLETE")

    def test_non_ocr_route_does_not_claim_ocr_queue(self):
        with self.assertRaisesRegex(ContractViolation,"NON_OCR_JOB_NOT_QUEUED"):
            self.lab.enqueue(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
                document_id="DOC_DEMO_001",source_ref=self.ev.source.source_ref,
                source_version=self.ev.source.source_version,source_sha256=HASH,
                format_kind="DWG",execution_state="routed",
                total_pages=0,chunks=(),pages=(),
            )

    def test_seventeen_page_metadata_is_accepted_in_chunks(self):
        a=self.submit(pages=tuple(page(i) for i in range(1,18)),
                      chunks=((1,8),(9,16),(17,17)))
        self.assertEqual(a["quality"],"LEGIBLE_ALL_PAGES")

    def test_missing_page_in_completed_job_is_rejected(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_PAGE_COVERAGE_INCOMPLETE"):
            self.submit(pages=tuple(page(i) for i in range(1,4)),
                        chunks=((1,2),))

    # Single claim, expiry, CAS and bounded retries; no real workers
    def test_one_worker_claims_other_worker_gets_none(self):
        self.submit()
        c=self.claim()
        self.assertIsNotNone(c)
        self.assertIsNone(self.claim(worker="DEMO_WORKER_BRAVO",tick=1))
        self.assertEqual(self.receipt()["attempts"],1)

    def test_expired_lease_reclaimed_and_old_token_rejected(self):
        self.submit()
        a=self.claim(tick=1,lease_ticks=2)
        b=self.claim(worker="DEMO_WORKER_BRAVO",tick=3,lease_ticks=2)
        self.assertEqual(b["attempt"],2)
        self.assertNotEqual(a["lease_token"],b["lease_token"])
        with self.assertRaisesRegex(ContractViolation,"LEASE_NOT_CURRENT"):
            self.finish(a,tick=3)

    def test_failure_retry_is_explicit_and_bounded(self):
        self.submit(max_attempts=2)
        first=self.claim(tick=1)
        r=self.lab.fail(
            claimed_owner=OWNER,process=self.p,task_key=TASK,
            worker=first["worker"],lease_token=first["lease_token"],
            now_tick=2,error_code="PROVIDER_FAILURE_SYNTHETIC",
        )
        self.assertEqual(r["state"],"RETRY_PENDING_SYNTHETIC")
        self.assertFalse(r["retry_automatic_external"])
        second=self.claim(tick=2)
        self.assertEqual(second["attempt"],2)
        r2=self.lab.fail(
            claimed_owner=OWNER,process=self.p,task_key=TASK,
            worker=second["worker"],lease_token=second["lease_token"],
            now_tick=3,error_code="LEASE_WORKER_FAILED",
        )
        self.assertEqual(r2["state"],"FAILED_SYNTHETIC")
        self.assertIsNone(self.claim(tick=3))

    def test_expired_last_lease_fails_closed(self):
        self.submit(max_attempts=1)
        self.claim(tick=1,lease_ticks=1)
        self.assertIsNone(self.claim(tick=2))
        self.assertEqual(self.receipt()["state"],"FAILED_SYNTHETIC")

    def test_not_expired_lease_cannot_be_reclaimed(self):
        self.submit()
        a=self.claim(tick=1,lease_ticks=5)
        self.assertIsNone(self.claim(tick=5))
        self.assertEqual(self.receipt()["attempts"],1)

    def test_invalid_failure_details_rejected_no_secret_recorded(self):
        self.submit()
        c=self.claim()
        with self.assertRaisesRegex(ContractViolation,"UNSAFE_FAILURE_DETAIL"):
            self.lab.fail(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
                worker=c["worker"],lease_token=c["lease_token"],
                now_tick=2,error_code="TOKEN_SECRET_EXPOSED_SYNTHETIC",
            )
        self.assertIsNone(self.receipt()["failure_code"])

    def test_clock_cannot_go_backward(self):
        self.submit(now=5)
        with self.assertRaisesRegex(ContractViolation,"SYNTHETIC_TIME_REGRESSION"):
            self.claim(tick=4)

    def test_invalid_lease_duration_rejected(self):
        self.submit()
        for bad in (0,11,True):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ContractViolation,"LEASE_DURATION_INVALID"):
                    self.claim(lease_ticks=bad)

    def test_wrong_worker_cannot_finish(self):
        self.submit()
        claim=self.claim()
        with self.assertRaisesRegex(ContractViolation,"LEASE_NOT_CURRENT"):
            self.lab.finish(
                claimed_owner=OWNER,process=self.p,task_key=TASK,
                worker="DEMO_WORKER_BRAVO",lease_token=claim["lease_token"],
                now_tick=2,event=self.ev,original=RAW,
            )

    # OCR quality is distinct from task execution; candidate is provisional.
    def test_legible_event_produces_only_pending_candidate(self):
        self.submit()
        c=self.claim()
        r=self.finish(c)
        self.assertEqual(r["state"],"CAPTURED_SYNTHETIC")
        self.assertFalse(r["memory_approved"])
        self.assertFalse(r["qdrant_written"])
        self.assertEqual(self.receipt()["state"],"CAPTURED_SYNTHETIC")
        group=self.lab.preview_grouped_review(claimed_owner=OWNER,process=self.p)
        self.assertEqual(len(group["items"]),1)
        self.assertTrue(group["requires_human_review"])
        self.assertFalse(group["authenticated_r06_review_performed"])

    def test_low_quality_completed_ocr_routes_to_review_no_candidate(self):
        self.submit(kind="LOW_CONFIDENCE",quality_conf=.4)
        c=self.claim()
        r=self.finish(c)
        self.assertEqual(r["state"],"REVIEW_NEEDED_SYNTHETIC")
        self.assertIsNone(r["candidate_id"])
        group=self.lab.preview_grouped_review(claimed_owner=OWNER,process=self.p)
        self.assertEqual(group["items"],[])

    def test_incomplete_job_does_not_capture_pending_memory(self):
        self.submit(state="partial",chunks=((1,1),),pages=(page(1),))
        c=self.claim()
        r=self.finish(c)
        self.assertEqual(r["state"],"REVIEW_NEEDED_SYNTHETIC")
        self.assertFalse(r["qdrant_written"])

    def test_wrong_source_version_does_not_complete(self):
        self.submit()
        c=self.claim()
        bad=event(self.p,source_version="DEMO_VER_02")
        with self.assertRaisesRegex(ContractViolation,"OCR_EVENT_SOURCE_MISMATCH"):
            self.finish(c,ev=bad)
        self.assertEqual(self.receipt()["state"],"LEASED_SYNTHETIC")

    def test_wrong_original_bytes_do_not_complete(self):
        self.submit()
        c=self.claim()
        with self.assertRaisesRegex(ContractViolation,"SOURCE_HASH_MISMATCH"):
            self.finish(c,original=RAW+b"TAMPER")
        self.assertEqual(self.receipt()["state"],"LEASED_SYNTHETIC")

    def test_simulated_crash_is_unknown_no_automatic_retry(self):
        self.submit()
        c=self.claim()
        r=self.finish(c,crash=True)
        self.assertEqual(r["state"],"FINALIZING_UNKNOWN_SYNTHETIC")
        self.assertTrue(r["requires_manual_reconciliation"])
        self.assertIsNone(self.claim(tick=4))
        receipt=self.receipt()
        self.assertTrue(receipt["requires_manual_reconciliation"])
        self.assertFalse(receipt["memory_approved"])

    def test_reenqueue_unknown_never_performs_capture(self):
        self.submit()
        c=self.claim()
        self.finish(c,crash=True)
        retry=self.submit(now=3)
        self.assertTrue(retry["replayed"])
        self.assertEqual(retry["state"],"FINALIZING_UNKNOWN_SYNTHETIC")
        self.assertIsNone(self.lab.preview_grouped_review(
            claimed_owner=OWNER,process=self.p)["batch_id"])

    def test_receipt_survives_sqlite_connection_reopen(self):
        self.submit()
        c=self.claim()
        self.finish(c)
        other=G14IEventLab(self.tmp,self.owner)
        rr=other.receipt(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.assertEqual(rr["state"],"CAPTURED_SYNTHETIC")
        self.assertEqual(rr["attempts"],1)

    def test_history_is_versioned_and_no_raw_document_logged(self):
        self.submit()
        c=self.claim()
        self.finish(c)
        history=self.lab.history(claimed_owner=OWNER,process=self.p,task_key=TASK)
        self.assertEqual([x["event_kind"] for x in history],
            ["ENQUEUED_SYNTHETIC","CLAIM_OR_RECLAIM",
             "COMPLETE_METADATA_SYNTHETIC","CANDIDATE_CAPTURED_SYNTHETIC"])
        self.assertNotIn("DEMO SYNTHETIC TEST DOCUMENT",str(history))

    def test_batch_group_stays_contextual_and_not_approved(self):
        self.submit()
        c=self.claim()
        self.finish(c)
        second="DEMO_TASK_00000002"
        self.submit(task=second,now=2)
        next_claim=self.claim(tick=3)
        new_event=event(self.p,summary="DEMO: despacho de processo administrativo")
        self.finish(next_claim,tick=4,ev=new_event,task=second)
        group=self.lab.preview_grouped_review(claimed_owner=OWNER,process=self.p)
        self.assertEqual(len(group["items"]),2)
        self.assertFalse(group["memory_approved"])
        self.assertFalse(group["qdrant_written"])

    def test_batch_decisions_only_prepare_proposal(self):
        self.submit()
        c=self.claim()
        self.finish(c)
        group=self.lab.preview_grouped_review(claimed_owner=OWNER,process=self.p)
        selected=group["items"][0]["candidate_id"]
        res=self.lab.review_batch_items(
            claimed_owner=OWNER,process_key=self.p.process_key,
            batch_id=group["batch_id"],
            decisions={selected:"prepare_proposals"},
        )
        self.assertFalse(res["memory_approved"])
        self.assertFalse(res["qdrant_written"])
        self.assertTrue(res["requires_authenticated_r06_batch_review"])

    def test_other_owner_fixture_cannot_claim_jobs(self):
        self.submit()
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            self.lab.claim(claimed_owner="OTHER_OWNER",worker=WORKER,now_tick=1)

    def test_no_recorded_memory_approval_in_queue(self):
        self.submit()
        c=self.claim()
        self.finish(c)
        r=self.receipt()
        self.assertFalse(r["memory_approved"])
        self.assertFalse(r["qdrant_written"])
        self.assertFalse(r["real_provider_authenticated"])

if __name__=="__main__":
    unittest.main()
