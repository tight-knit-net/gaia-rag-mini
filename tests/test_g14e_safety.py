"""G14-E negative synthetic regression tests, no production services.

Every datum is invented. SQLite must be in TemporaryDirectory; no Qdrant,
Cloudflare, Drive, Linear, GitLab, or R06/R07 interaction is authorized.
"""
from dataclasses import replace
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentEvent, DocumentSource
from gaia_document_mcp.process_learning import (
    AdministrativeProcess, HybridLearningPreview, SyntheticOwnerOnly,
)
from gaia_document_mcp.g14c_disposable import DisposableGate

OWNER = "GAIA_DEMO_OWNER"
RAW = b"%PDF-1.4\nSYNTHETIC G14E\n%%EOF"
HASH = sha256(RAW).hexdigest()
TITLE = "DEMO: requerimento de funcionamento comercio local"
OTHER = "DEMO: vistoria sanitaria requerida pela prefeitura"
KEY = "G14E_REQUEST_000001"

def process(*, number="000123/2026", process_id="DEMO_PROC_000123", agency="PREF_DEMO"):
    return AdministrativeProcess(
        process_id=process_id, agency_code=agency,
        jurisdiction="BR-SC-FLN", official_number=number,
    )

def event(p=None, *, summary=TITLE, file_id="FILE_DEMO_0001", operation_id="DEMO_OPERATION_001"):
    p = p or process()
    src = DocumentSource(
        drive_id="DRIVE_DEMO_01", file_id=file_id, client_id="009",
        process_id=p.process_id, source_version="DEMO_V1",
        sha256_original=HASH,
    )
    return DocumentEvent(
        source=src, operation="ocr", status="completed",
        provider="tesseract", source_verified=False,
        operation_id=operation_id, summary=summary,
    )

class G14ENegatives(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="gaia-g14e-demo-")
        self.addCleanup(self.tmp.cleanup)
        self.owner = SyntheticOwnerOnly(OWNER)
        self.gate = DisposableGate(self.tmp, self.owner)
        self.proc = process()

    def capture(self, *, p=None, e=None):
        p = p or self.proc
        return self.gate.capture(claimed_owner=OWNER, process=p, event=e or event(p))

    def preview(self):
        return self.gate.preview_batches(claimed_owner=OWNER)[0]

    def review_all(self, decision):
        batch = self.preview()
        receipt = self.gate.review_batch(
            claimed_owner=OWNER, process_key=self.proc.process_key,
            batch_id=batch["batch_id"],
            candidate_ids=tuple(x["candidate_id"] for x in batch["candidates"]),
            decision=decision,
        )
        return batch, receipt

    def seed(self):
        self.gate.seed(claimed_owner=OWNER, process=self.proc,
                       revision="DEMO_REV_01")

    def reserve_bound(self, *, e=None, data=RAW, key=KEY):
        return self.gate.reserve_from_event(
            claimed_owner=OWNER, process=self.proc,
            event=e or event(), original_bytes=data,
            idempotency_key=key, expected_revision="DEMO_REV_01",
        )

    # Official-process identity: a process number is provenance, not ACL.
    def test_process_binding_rejects_different_id_for_distinct_topic(self):
        self.capture()
        alias = process(process_id="DEMO_PROC_OTHER")
        with self.assertRaisesRegex(ContractViolation, "PROCESS_ID_COLLISION"):
            self.capture(p=alias, e=event(alias, summary=OTHER))

    def test_process_binding_rejects_alias_after_seed(self):
        self.seed()
        alias = process(process_id="DEMO_PROC_OTHER")
        with self.assertRaisesRegex(ContractViolation, "PROCESS_ID_COLLISION"):
            self.capture(p=alias, e=event(alias, summary=OTHER))

    def test_same_number_different_agency_remains_separate(self):
        self.capture()
        p2 = process(process_id="DEMO_PROC_AGENCY", agency="PREF_OTHER")
        r = self.capture(p=p2, e=event(p2))
        self.assertNotEqual(self.preview()["process_key"], r["process_key"])
        self.assertEqual(len(self.gate.preview_batches(claimed_owner=OWNER)), 2)

    def test_process_id_is_not_permission_boundary(self):
        self.capture()
        p2 = process(number="000124/2026", process_id="DEMO_PROC_000124")
        self.capture(p=p2, e=event(p2))
        b = self.gate.preview_batches(claimed_owner=OWNER)
        self.assertEqual(len(b), 2)

    # Exact deduplication must preserve word order, negations and event lineage.
    def test_reordered_words_never_collapsed_as_same_fact(self):
        a = self.capture(e=event(summary="DEMO: prefeitura deferiu requerimento"))
        b = self.capture(e=event(summary="DEMO: requerimento deferiu prefeitura"))
        self.assertNotEqual(a["candidate_id"], b["candidate_id"])
        self.assertEqual(self.preview()["candidate_count"], 2)

    def test_negation_changes_candidate_identity(self):
        a = self.capture(e=event(summary="DEMO: prefeitura deferiu requerimento"))
        b = self.capture(e=event(summary="DEMO: prefeitura nao deferiu requerimento"))
        self.assertNotEqual(a["candidate_id"], b["candidate_id"])

    def test_whitespace_and_case_only_are_duplicate(self):
        a = self.capture(e=event(summary="DEMO: requerimento autorizado"))
        b = self.capture(e=event(summary="demo:   requerimento   AUTORIZADO"))
        self.assertEqual(a["candidate_id"], b["candidate_id"])
        self.assertEqual(self.preview()["candidate_count"], 1)

    def test_same_text_other_process_stays_distinct(self):
        a = self.capture()
        p2 = process(number="000124/2026", process_id="DEMO_PROC_000124")
        b = self.capture(p=p2,e=event(p2))
        self.assertNotEqual(a["candidate_id"],b["candidate_id"])

    def test_lexical_similarity_stays_non_authoritative(self):
        learning = HybridLearningPreview(self.owner)
        p = self.proc
        r = learning.observe(event=event(p),process=p,claimed_owner=OWNER)
        self.assertFalse(r["memory_persisted"])

    # More-evidence transitions: prior sealed batch stays as audit history.
    def test_new_evidence_reopens_needs_more_without_approval(self):
        first = self.capture()
        old_batch, _ = self.review_all("needs_more_evidence")
        changed = self.capture(e=event(file_id="FILE_DEMO_0002"))
        self.assertEqual(changed["candidate_id"], first["candidate_id"])
        self.assertEqual(changed["candidate_revision"], 2)
        self.assertEqual(changed["source_count"], 2)
        new_batch = self.preview()
        self.assertNotEqual(old_batch["batch_id"], new_batch["batch_id"])
        self.assertEqual(new_batch["candidates"][0]["candidate_revision"], 2)
        hist = self.gate.candidate_history_readback(
            claimed_owner=OWNER, candidate_id=first["candidate_id"])
        self.assertEqual(hist[-1]["previous_status"], "MORE_EVIDENCE_NEEDED_SYNTHETIC")
        self.assertEqual(hist[-1]["new_status"], "PENDING_HUMAN_REVIEW")

    def test_replay_without_new_evidence_does_not_reopen(self):
        self.capture()
        self.review_all("needs_more_evidence")
        with self.assertRaisesRegex(ContractViolation,"NEW_EVIDENCE_REQUIRED"):
            self.capture()

    def test_new_event_fingerprint_reopens_same_file(self):
        self.capture()
        self.review_all("needs_more_evidence")
        r = self.capture(e=event(operation_id="DEMO_OPERATION_002"))
        self.assertEqual(r["candidate_revision"],2)

    def test_history_survives_connection_reopen(self):
        c = self.capture()
        self.review_all("needs_more_evidence")
        self.capture(e=event(file_id="FILE_DEMO_0002"))
        second = DisposableGate(self.tmp,self.owner)
        hist = second.candidate_history_readback(
            claimed_owner=OWNER,candidate_id=c["candidate_id"])
        self.assertEqual([h["event_name"] for h in hist],
                         ["CAPTURED_SYNTHETIC","BATCH_REVIEW_SYNTHETIC",
                          "EVIDENCE_ADDED_SYNTHETIC"])

    def test_prepared_proposal_cannot_be_mutated(self):
        self.capture()
        self.review_all("prepare_proposals")
        with self.assertRaisesRegex(ContractViolation,"REVIEWED_CANDIDATE_CANNOT_CHANGE"):
            self.capture(e=event(file_id="FILE_DEMO_0002"))

    def test_new_evidence_invalidates_old_batch_digest(self):
        self.capture()
        old = self.preview()
        self.capture(e=event(file_id="FILE_DEMO_0002"))
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(
                claimed_owner=OWNER,process_key=self.proc.process_key,
                batch_id=old["batch_id"],
                candidate_ids=(old["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    def test_mutating_displayed_summary_invalidates_snapshot(self):
        self.capture()
        old = self.preview()
        with self.gate._tx() as db:
            db.execute("UPDATE candidates SET summary=?",
                       ("DEMO: documento alterado",))
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch(
                claimed_owner=OWNER,process_key=self.proc.process_key,
                batch_id=old["batch_id"],
                candidate_ids=(old["candidates"][0]["candidate_id"],),
                decision="prepare_proposals")

    # Select individual candidates, but snapshot entire pending set.
    def test_one_candidate_selected_does_not_approve_other(self):
        self.capture()
        self.capture(e=event(summary=OTHER))
        batch=self.preview()
        chosen=batch["candidates"][0]["candidate_id"]
        result=self.gate.review_batch_items(
            claimed_owner=OWNER,process_key=self.proc.process_key,
            batch_id=batch["batch_id"],decisions={chosen:"prepare_proposals"})
        self.assertEqual(result["candidate_count"],1)
        self.assertFalse(result["memory_approved"])
        remaining=self.preview()
        self.assertEqual(remaining["candidate_count"],1)
        self.assertNotEqual(remaining["candidates"][0]["candidate_id"],chosen)

    def test_mixed_decisions_have_per_item_receipts(self):
        self.capture()
        self.capture(e=event(summary=OTHER))
        b=self.preview()
        ids=[x["candidate_id"] for x in b["candidates"]]
        decisions={ids[0]:"prepare_proposals",ids[1]:"needs_more_evidence"}
        r=self.gate.review_batch_items(
            claimed_owner=OWNER,process_key=self.proc.process_key,
            batch_id=b["batch_id"],decisions=decisions)
        self.assertEqual(r["review_status"],"MIXED_SYNTHETIC")
        self.assertEqual({x["decision"] for x in r["items"]},set(decisions.values()))
        self.assertFalse(r["memory_approved"])
        receipt=self.gate.batch_readback(claimed_owner=OWNER,batch_id=b["batch_id"])
        self.assertEqual(len(receipt["items"]),2)
        self.assertEqual(receipt["decision"],"mixed")

    def test_mixed_group_can_reopen_only_needs_more(self):
        self.capture()
        self.capture(e=event(summary=OTHER))
        b=self.preview()
        bysummary = {x["summary"]:x["candidate_id"] for x in b["candidates"]}
        self.gate.review_batch_items(
            claimed_owner=OWNER,process_key=self.proc.process_key,
            batch_id=b["batch_id"],
            decisions={bysummary[TITLE]:"needs_more_evidence",
                       bysummary[OTHER]:"prepare_proposals"})
        r=self.capture(e=event(summary=TITLE,file_id="FILE_DEMO_0002"))
        self.assertEqual(r["candidate_revision"],2)
        with self.assertRaisesRegex(ContractViolation,"REVIEWED_CANDIDATE_CANNOT_CHANGE"):
            self.capture(e=event(summary=OTHER,file_id="FILE_DEMO_0003"))

    def test_partial_review_rejects_foreign_candidate(self):
        self.capture()
        p2=process(number="000124/2026", process_id="DEMO_PROC_000124")
        other=self.capture(p=p2,e=event(p2))
        b=self.preview() # first process, alphabetical ordering not assumed
        all_batches=self.gate.preview_batches(claimed_owner=OWNER)
        ours=next(x for x in all_batches if x["process_key"]==self.proc.process_key)
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch_items(
                claimed_owner=OWNER,process_key=self.proc.process_key,
                batch_id=ours["batch_id"],
                decisions={other["candidate_id"]:"prepare_proposals"})

    def test_partial_review_rejects_stale_snapshot(self):
        self.capture()
        b=self.preview()
        self.capture(e=event(summary=OTHER))
        with self.assertRaisesRegex(ContractViolation,"BATCH_STALE_OR_PROCESS_MISMATCH"):
            self.gate.review_batch_items(
                claimed_owner=OWNER,process_key=self.proc.process_key,
                batch_id=b["batch_id"],
                decisions={b["candidates"][0]["candidate_id"]:"prepare_proposals"})

    def test_partial_review_rejects_implicit_approval(self):
        self.capture()
        b=self.preview()
        with self.assertRaisesRegex(ContractViolation,"INVALID_REVIEW_DECISION"):
            self.gate.review_batch_items(
                claimed_owner=OWNER,process_key=self.proc.process_key,
                batch_id=b["batch_id"],
                decisions={b["candidates"][0]["candidate_id"]:"approve_qdrant"})

    def test_remaining_items_get_new_batch_id(self):
        self.capture()
        self.capture(e=event(summary=OTHER))
        first=self.preview()
        self.gate.review_batch_items(
            claimed_owner=OWNER,process_key=self.proc.process_key,
            batch_id=first["batch_id"],
            decisions={first["candidates"][0]["candidate_id"]:"prepare_proposals"})
        second=self.preview()
        self.assertNotEqual(first["batch_id"],second["batch_id"])
        self.assertEqual(second["candidate_count"],1)

    # Never trust a raw fingerprint when observed bytes can be checked.
    def test_bound_reservation_fingerprint_computed_from_event(self):
        self.seed()
        r=self.reserve_bound()
        self.assertEqual(r["state"],"RESERVED_SYNTHETIC")
        self.assertEqual(len(r["request_fingerprint"]),64)

    def test_bound_reservation_retries_with_new_attempt_id(self):
        self.seed()
        a=self.reserve_bound()
        b=self.reserve_bound(e=event(operation_id="DEMO_OPERATION_002"))
        self.assertEqual(a["run_id"],b["run_id"])
        self.assertTrue(b["replayed"])

    def test_bound_reservation_changed_text_conflicts(self):
        self.seed()
        self.reserve_bound()
        with self.assertRaisesRegex(ContractViolation,"IDEMPOTENCY_CONFLICT"):
            self.reserve_bound(e=event(summary=OTHER))

    def test_bound_reservation_wrong_bytes_denied(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation,"SOURCE_HASH_MISMATCH"):
            self.reserve_bound(data=RAW+b"tamper")

    def test_bound_reservation_wrong_process_denied(self):
        self.seed()
        p2=process(number="000124/2026",process_id="DEMO_PROC_000124")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_CONTEXT_MISMATCH"):
            self.reserve_bound(e=event(p2))

    def test_bound_reservation_requires_registry(self):
        with self.assertRaisesRegex(ContractViolation,"PROCESS_BINDING_NOT_REGISTERED"):
            self.reserve_bound()

    def test_bound_reservation_wrong_owner_denied(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            self.gate.reserve_from_event(
                claimed_owner="NOT_OWNER",process=self.proc,event=event(),
                original_bytes=RAW,idempotency_key=KEY,
                expected_revision="DEMO_REV_01")

    def test_no_qdrant_or_r06_approval_in_batch(self):
        self.capture()
        b=self.preview()
        r=self.gate.review_batch_items(
            claimed_owner=OWNER,process_key=self.proc.process_key,
            batch_id=b["batch_id"],
            decisions={b["candidates"][0]["candidate_id"]:"prepare_proposals"})
        self.assertFalse(r["document_approval"])
        self.assertFalse(r["qdrant_written"])
        self.assertTrue(r["requires_authenticated_r06_batch_review"])

if __name__=="__main__":
    unittest.main()
