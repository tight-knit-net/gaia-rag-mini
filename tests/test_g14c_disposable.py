"""G14-C: disposable SQLite transactions, process context and grouped review.

All fixtures are invented. No APIs, Qdrant, client documents or production DB.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentEvent, DocumentSource
from gaia_document_mcp.process_learning import AdministrativeProcess, SyntheticOwnerOnly
from gaia_document_mcp.owner_concurrency import SyntheticRequest
from gaia_document_mcp.g14c_disposable import DisposableGate

OWNER = "synthetic_gaia_owner"
PDF = b"%PDF-1.4\nDEMO DOCUMENT ONLY\n%%EOF"
HASH = sha256(PDF).hexdigest()
KEY1 = "DEMO_IDEMP_REQUEST_01"
KEY2 = "DEMO_IDEMP_REQUEST_02"
SUMMARY = "DEMO: requerimento autorizacao funcionamento comercio municipal"

def process(number="000123/2026", process_id="ADM_DEMO_000123"):
    return AdministrativeProcess(
        process_id=process_id, jurisdiction="BR-SC-FLN",
        agency_code="PREF_DEMO", official_number=number,
    )

def event(p=None, summary=SUMMARY, file_id="FILE_DEMO_0001",
          status="completed", provider="tesseract"):
    p = p or process()
    src = DocumentSource(
        drive_id="DRIVE_DEMO_001", file_id=file_id, client_id="009",
        process_id=p.process_id, source_version="REV_DEMO_V1",
        sha256_original=HASH,
    )
    return DocumentEvent(
        source=src, operation="ocr", status=status, provider=provider,
        source_verified=False, operation_id="OP_DEMO_G14C_001",
        summary=summary,
    )

def request(p=None, key=KEY1, revision="REV_DEMO_0001", fingerprint="a"*64):
    p = p or process()
    return SyntheticRequest(
        process_key=p.process_key, idempotency_key=key,
        expected_revision=revision, request_fingerprint=fingerprint,
    )

class DisposableLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="test-gaia-g14c-")
        self.addCleanup(self.temp.cleanup)
        self.owner = SyntheticOwnerOnly(OWNER)
        self.gate = DisposableGate(self.temp, self.owner)
        self.p = process()

    def seed(self, p=None):
        p = p or self.p
        self.gate.seed(claimed_owner=OWNER, process=p, revision="REV_DEMO_0001")

    def reserve(self, req=None, *, gate=None):
        return (gate or self.gate).reserve(claimed_owner=OWNER,
                                           request=req or request())

    def capture(self, p=None, ev=None):
        p = p or self.p
        return self.gate.capture(claimed_owner=OWNER, process=p,
                                 event=ev or event(p))

    def test_requires_disposable_workspace_object(self):
        with self.assertRaisesRegex(ContractViolation, "DISPOSABLE_WORKSPACE_REQUIRED"):
            DisposableGate("/data/production.sqlite", self.owner)

    def test_closed_temp_workspace_rejected(self):
        other = TemporaryDirectory()
        other.cleanup()
        with self.assertRaisesRegex(ContractViolation, "DISPOSABLE_WORKSPACE_CLOSED"):
            DisposableGate(other, self.owner)

    def test_seed_owner_required(self):
        with self.assertRaisesRegex(ContractViolation, "OWNER_REQUIRED"):
            self.gate.seed(claimed_owner="someone_else", process=self.p,
                           revision="REV_DEMO_0001")

    def test_seed_creates_revision(self):
        self.seed()
        self.assertEqual(self.gate.current_revision(
            claimed_owner=OWNER, process_key=self.p.process_key), "REV_DEMO_0001")

    def test_duplicate_seed_fails(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "PROCESS_ALREADY_SEEDED"):
            self.seed()

    def test_reserve_is_synthetic_and_no_external_write(self):
        self.seed()
        r = self.reserve()
        self.assertEqual(r["state"], "RESERVED_SYNTHETIC")
        self.assertTrue(r["persisted_only_in_disposable_sqlite"])
        self.assertFalse(r["production_durable"])
        self.assertFalse(r["provider_write_performed"])
        self.assertFalse(r["qdrant_write_performed"])

    def test_same_key_same_request_replays(self):
        self.seed()
        a = self.reserve()
        b = self.reserve()
        self.assertEqual(a["run_id"], b["run_id"])
        self.assertTrue(b["replayed"])

    def test_same_key_new_payload_conflicts(self):
        self.seed()
        self.reserve()
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_CONFLICT"):
            self.reserve(request(fingerprint="b"*64))

    def test_revision_conflict_before_reservation(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "REVISION_CONFLICT"):
            self.reserve(request(revision="REV_DEMO_9999"))

    def test_crash_before_reservation_commit_rolls_back(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "SIMULATED_CRASH_BEFORE_COMMIT"):
            self.gate.reserve(claimed_owner=OWNER, request=request(),
                              fail_before_commit=True)
        with self.assertRaisesRegex(ContractViolation, "RUN_NOT_FOUND"):
            self.gate.readback(claimed_owner=OWNER,process_key=self.p.process_key,
                               request_key=KEY1)
        self.assertFalse(self.reserve()["replayed"])

    def test_state_survives_reopening_disposable_connection(self):
        self.seed()
        run = self.reserve()
        reopened = DisposableGate(self.temp, self.owner)
        replay = reopened.reserve(claimed_owner=OWNER, request=request())
        self.assertEqual(replay["run_id"], run["run_id"])
        self.assertTrue(replay["replayed"])

    def test_commit_revision_is_only_local_string(self):
        self.seed()
        self.reserve()
        r = self.gate.commit_revision(
            claimed_owner=OWNER,process_key=self.p.process_key,
            request_key=KEY1,new_revision="REV_DEMO_0002",
        )
        self.assertEqual(r["state"], "COMMITTED_SYNTHETIC")
        self.assertFalse(r["provider_write_performed"])
        self.assertEqual(self.gate.current_revision(
            claimed_owner=OWNER,process_key=self.p.process_key), "REV_DEMO_0002")

    def test_commit_readback_after_reopen(self):
        self.seed()
        self.reserve()
        self.gate.commit_revision(claimed_owner=OWNER,process_key=self.p.process_key,
                                  request_key=KEY1,new_revision="REV_DEMO_0002")
        reopened = DisposableGate(self.temp, self.owner)
        got = reopened.readback(claimed_owner=OWNER,process_key=self.p.process_key,
                                request_key=KEY1)
        self.assertEqual(got["state"], "COMMITTED_SYNTHETIC")
        self.assertEqual(got["new_revision"], "REV_DEMO_0002")

    def test_commit_retry_same_revision_replays(self):
        self.seed()
        self.reserve()
        args=dict(claimed_owner=OWNER,process_key=self.p.process_key,
                  request_key=KEY1,new_revision="REV_DEMO_0002")
        self.gate.commit_revision(**args)
        self.assertTrue(self.gate.commit_revision(**args)["replayed"])

    def test_commit_retry_other_revision_fails(self):
        self.seed()
        self.reserve()
        self.gate.commit_revision(claimed_owner=OWNER,process_key=self.p.process_key,
                                  request_key=KEY1,new_revision="REV_DEMO_0002")
        with self.assertRaisesRegex(ContractViolation, "REPLAY_REVISION_MISMATCH"):
            self.gate.commit_revision(claimed_owner=OWNER,process_key=self.p.process_key,
                                      request_key=KEY1,new_revision="REV_DEMO_0003")

    def test_parallel_reservations_with_same_key_produce_one_run(self):
        self.seed()
        other = DisposableGate(self.temp, self.owner)
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda gate: gate.reserve(
                claimed_owner=OWNER, request=request()
            )["run_id"], [self.gate, other]))
        self.assertEqual(ids[0], ids[1])

    def test_parallel_commits_one_wins_on_same_revision(self):
        self.seed()
        self.reserve(request(key=KEY1))
        self.reserve(request(key=KEY2))
        second = DisposableGate(self.temp, self.owner)
        def attempt(gate, key, rev):
            try:
                gate.commit_revision(claimed_owner=OWNER,process_key=self.p.process_key,
                                     request_key=key,new_revision=rev)
                return "OK"
            except ContractViolation as ex:
                return str(ex)
        with ThreadPoolExecutor(max_workers=2) as pool:
            res = list(pool.map(lambda args: attempt(*args),[
                (self.gate,KEY1,"REV_DEMO_0002"),
                (second,KEY2,"REV_DEMO_0003"),
            ]))
        self.assertCountEqual(res,["OK","REVISION_CONFLICT"])

    def test_unknown_after_timeout_is_not_committed(self):
        self.seed()
        self.reserve()
        self.gate.mark_unknown(claimed_owner=OWNER,process_key=self.p.process_key,
                               request_key=KEY1)
        reopened=DisposableGate(self.temp,self.owner)
        self.assertEqual(reopened.readback(claimed_owner=OWNER,
                         process_key=self.p.process_key,request_key=KEY1)["state"],
                         "UNKNOWN_SYNTHETIC")
        with self.assertRaisesRegex(ContractViolation, "RECONCILIATION_REQUIRED"):
            reopened.commit_revision(claimed_owner=OWNER,process_key=self.p.process_key,
                                     request_key=KEY1,new_revision="REV_DEMO_0002")

    def test_same_idempotency_key_other_process_is_distinct(self):
        self.seed()
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        self.seed(p2)
        a=self.reserve()
        b=self.reserve(request(p2))
        self.assertNotEqual(a["run_id"],b["run_id"])

    def test_owner_required_for_readback(self):
        self.seed()
        self.reserve()
        with self.assertRaisesRegex(ContractViolation, "OWNER_REQUIRED"):
            self.gate.readback(claimed_owner="wrong",process_key=self.p.process_key,
                               request_key=KEY1)

    def test_process_number_with_leading_zeros_is_preserved(self):
        p2=process(number="00123/2026",process_id="ADM_DEMO_00123")
        self.assertNotEqual(self.p.process_key,p2.process_key)
        self.seed()
        self.seed(p2)

    def test_capture_creates_automatic_pending_candidate(self):
        receipt=self.capture()
        self.assertEqual(receipt["status"],"PENDING_HUMAN_REVIEW")
        self.assertFalse(receipt["qdrant_write_performed"])

    def test_capture_survives_disposable_database_reopen(self):
        self.capture()
        reopened=DisposableGate(self.temp,self.owner)
        got=reopened.working_context(claimed_owner=OWNER,process=self.p)
        self.assertEqual(len(got),1)
        self.assertFalse(got[0]["is_authoritative"])

    def test_capture_duplicate_deduplicates_in_process(self):
        a=self.capture()
        b=self.capture()
        self.assertEqual(a["candidate_id"],b["candidate_id"])
        self.assertEqual(b["source_count"],1)

    def test_capture_second_file_preserves_source_count(self):
        self.capture()
        b=self.capture(ev=event(file_id="FILE_DEMO_0002"))
        self.assertEqual(b["source_count"],2)

    def test_similar_requerimentos_other_process_not_merged(self):
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        a=self.capture()
        b=self.capture(p2,event(p2))
        self.assertNotEqual(a["candidate_id"],b["candidate_id"])
        self.assertEqual(len(self.gate.working_context(
            claimed_owner=OWNER,process=p2)),1)

    def test_working_context_does_not_include_other_process(self):
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        self.capture(p2,event(p2))
        self.assertEqual(self.gate.working_context(claimed_owner=OWNER,process=self.p),[])

    def test_process_link_mismatch_blocked(self):
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        with self.assertRaisesRegex(ContractViolation, "PROCESS_CONTEXT_MISMATCH"):
            self.capture(ev=event(p2))

    def test_mock_ocr_not_persisted(self):
        with self.assertRaisesRegex(ContractViolation, "MOCK_IS_NOT_EVIDENCE"):
            self.capture(ev=event(provider="mock"))
        self.assertEqual(self.gate.preview_batches(claimed_owner=OWNER),[])

    def test_failed_ocr_not_persisted(self):
        with self.assertRaisesRegex(ContractViolation, "EVENT_NOT_ELIGIBLE"):
            self.capture(ev=event(status="failed"))

    def test_real_looking_file_id_blocked(self):
        with self.assertRaisesRegex(ContractViolation, "SYNTHETIC_DOCUMENT_ONLY"):
            self.capture(ev=event(file_id="CLIENTFILE_0001"))

    def test_non_demo_summary_blocked(self):
        with self.assertRaisesRegex(ContractViolation, "SYNTHETIC_SUMMARY_REQUIRED"):
            self.capture(ev=event(summary="Dados pessoais de cliente"))

    def test_process_id_collision_with_same_official_number_blocked(self):
        self.capture()
        p_alt=process(process_id="ADM_DEMO_ALT_ID")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_ID_COLLISION"):
            self.capture(p_alt,event(p_alt))

    def test_review_batches_group_by_process(self):
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        self.capture()
        self.capture(p2,event(p2))
        batches=self.gate.preview_batches(claimed_owner=OWNER)
        self.assertEqual(len(batches),2)
        self.assertEqual({b["process_key"] for b in batches},
                         {self.p.process_key,p2.process_key})
        self.assertTrue(all(b["qdrant_written"] is False for b in batches))

    def test_two_topics_same_process_one_batch(self):
        self.capture()
        self.capture(ev=event(summary="DEMO: vistoria municipal de alvara sanitario"))
        batches=self.gate.preview_batches(claimed_owner=OWNER)
        self.assertEqual(len(batches),1)
        self.assertEqual(batches[0]["candidate_count"],2)

    def test_group_review_marks_proposals_not_approved(self):
        self.capture()
        batch=self.gate.preview_batches(claimed_owner=OWNER)[0]
        ids=tuple(x["candidate_id"] for x in batch["candidates"])
        result=self.gate.review_batch(claimed_owner=OWNER,
            process_key=self.p.process_key,batch_id=batch["batch_id"],
            candidate_ids=ids,decision="prepare_proposals")
        self.assertEqual(result["review_status"],"REVIEWED_FOR_PROPOSAL_SYNTHETIC")
        self.assertFalse(result["memory_approved"])
        self.assertFalse(result["document_approval"])
        self.assertFalse(result["qdrant_written"])
        self.assertTrue(result["requires_authenticated_r06_batch_review"])

    def test_batch_receipt_readback_survives_reopen(self):
        self.capture()
        batch=self.gate.preview_batches(claimed_owner=OWNER)[0]
        self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
            batch_id=batch["batch_id"],candidate_ids=(batch["candidates"][0]["candidate_id"],),
            decision="needs_more_evidence")
        reopened=DisposableGate(self.temp,self.owner)
        r=reopened.batch_readback(claimed_owner=OWNER,batch_id=batch["batch_id"])
        self.assertEqual(r["candidate_count"],1)
        self.assertFalse(r["qdrant_written"])

    def test_group_review_rejects_other_process_member(self):
        p2=process(number="000124/2026",process_id="ADM_DEMO_000124")
        self.capture()
        self.capture(p2,event(p2))
        batches=self.gate.preview_batches(claimed_owner=OWNER)
        own=next(b for b in batches if b["process_key"]==self.p.process_key)
        other=next(b for b in batches if b["process_key"]==p2.process_key)
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=own["batch_id"],
                candidate_ids=(other["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    def test_stale_group_after_new_candidate_rejected(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        self.capture(ev=event(summary="DEMO: vistoria de outra atividade"))
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=b["batch_id"],
                candidate_ids=(b["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    def test_stale_group_after_new_source_evidence_rejected(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        self.capture(ev=event(file_id="FILE_DEMO_0002"))
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=b["batch_id"],
                candidate_ids=(b["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    def test_group_requires_exact_members_without_duplicates(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        with self.assertRaisesRegex(ContractViolation, "INVALID_REVIEW_MEMBERS"):
            self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=b["batch_id"],
                candidate_ids=(b["candidates"][0]["candidate_id"],)*2,
                decision="prepare_proposals")

    def test_invalid_group_decision_rejected(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        with self.assertRaisesRegex(ContractViolation,"INVALID_REVIEW_DECISION"):
            self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=b["batch_id"],
                candidate_ids=(b["candidates"][0]["candidate_id"],),
                decision="approve_in_qdrant")

    def test_reviewer_cannot_reapprove_stale_batch(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        ids=tuple(x["candidate_id"] for x in b["candidates"])
        kw=dict(claimed_owner=OWNER,process_key=self.p.process_key,
                batch_id=b["batch_id"],candidate_ids=ids,decision="prepare_proposals")
        self.gate.review_batch(**kw)
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(**kw)

    def test_reviewed_candidate_cannot_change_silently(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        self.gate.review_batch(claimed_owner=OWNER,process_key=self.p.process_key,
            batch_id=b["batch_id"],candidate_ids=(b["candidates"][0]["candidate_id"],),
            decision="prepare_proposals")
        with self.assertRaisesRegex(ContractViolation,"REVIEWED_CANDIDATE_CANNOT_CHANGE"):
            self.capture(ev=event(file_id="FILE_DEMO_0002"))

    def test_group_review_wrong_owner_blocked(self):
        self.capture()
        b=self.gate.preview_batches(claimed_owner=OWNER)[0]
        with self.assertRaisesRegex(ContractViolation, "OWNER_REQUIRED"):
            self.gate.review_batch(claimed_owner="not_owner",process_key=self.p.process_key,
                batch_id=b["batch_id"],
                candidate_ids=(b["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    def test_group_preview_has_no_memory_writes(self):
        self.capture()
        out=self.gate.preview_batches(claimed_owner=OWNER)
        self.assertFalse(out[0]["qdrant_written"])
        self.assertEqual(out[0]["status"],"PENDING_GROUPED_REVIEW")

if __name__=="__main__":
    unittest.main()
