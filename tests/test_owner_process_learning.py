"""G14-B: owner-only and hybrid learning with wholly fictitious administrative cases."""
from dataclasses import replace
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentSource, DocumentEvent
from gaia_document_mcp.process_learning import (
    AdministrativeProcess, ApprovedKnowledgeFixture,
    SyntheticOwnerOnly, HybridLearningPreview,
)
from gaia_document_mcp.owner_concurrency import (
    SyntheticRequest, InMemoryRevisionCoordinator,
)

OWNER = "gaia_owner_demo"
TEXT = "Requerimento de autorizacao para funcionamento de comercio local"
PDF = b"%PDF-1.4\nDEMO DATA ONLY\n%%EOF"
HASH = sha256(PDF).hexdigest()
KEY = "REQUEST_IDEMP_0001"

def process(number="000123/2026", process_id="ADM-PMF-000123-2026",
            agency="PMF", jurisdiction="BR-SC-FLN"):
    return AdministrativeProcess(
        process_id=process_id, agency_code=agency,
        jurisdiction=jurisdiction, official_number=number,
    )

def event(proc=None, *, text=TEXT, operation="ocr", provider="tesseract",
          file_id="FILE_DEMO_0001", status="completed"):
    proc = proc or process()
    s = DocumentSource(
        drive_id="DRIVE_DEMO_0001", file_id=file_id,
        client_id="009", process_id=proc.process_id,
        source_version="SOURCE_VER_0001", sha256_original=HASH,
    )
    return DocumentEvent(
        source=s, operation=operation, status=status, provider=provider,
        source_verified=False, operation_id="OP_DEMO_000001",
        summary=text,
    )

def engine():
    return HybridLearningPreview(SyntheticOwnerOnly(OWNER))

def record(proc=None, *, approved=True, text=TEXT, point_id="POINT_DEMO_0001"):
    proc = proc or process()
    return ApprovedKnowledgeFixture(
        point_id=point_id, process_key=proc.process_key,
        process_id=proc.process_id, source_ref="drive:DEMO:FILE_DEMO_0001",
        summary=text, approval_ref="REVIEW_DEMO_0001", approved=approved,
    )

def request(proc=None, *, fingerprint=None, key=KEY, expected="REV_DEMO_0001"):
    return SyntheticRequest(
        process_key=(proc or process()).process_key, idempotency_key=key,
        expected_revision=expected, request_fingerprint=fingerprint or ("a" * 64),
    )

def coordinator():
    c = InMemoryRevisionCoordinator(SyntheticOwnerOnly(OWNER))
    c.seed(claimed_owner=OWNER, process_key=process().process_key,
           revision="REV_DEMO_0001")
    return c

class ProcessAwareLearningTests(unittest.TestCase):
    def test_only_owner_fixture_allowed(self):
        e = engine()
        with self.assertRaisesRegex(ContractViolation, "OWNER_REQUIRED"):
            e.observe(event=event(), process=process(), claimed_owner="other_user")
        self.assertEqual(e.pending_count(), 0)

    def test_owner_fixture_does_not_imply_real_authentication(self):
        result = engine().observe(event=event(), process=process(), claimed_owner=OWNER)
        self.assertEqual(result["status"], "PENDING_HUMAN_REVIEW")
        self.assertFalse(result["memory_persisted"])

    def test_process_number_preserves_leading_zeros(self):
        self.assertNotEqual(process().process_key,
                            process(number="00123/2026").process_key)

    def test_same_number_different_municipality_differs(self):
        self.assertNotEqual(process().process_key,
                            process(jurisdiction="BR-SC-ITA").process_key)

    def test_same_number_different_agency_differs(self):
        self.assertNotEqual(process().process_key,
                            process(agency="SEFAZ").process_key)

    def test_two_similar_requerimentos_do_not_merge_processes(self):
        p1 = process()
        p2 = process(number="000124/2026",process_id="ADM-PMF-000124-2026")
        e = engine()
        a = e.observe(event=event(p1),process=p1,claimed_owner=OWNER)
        b = e.observe(event=event(p2),process=p2,claimed_owner=OWNER)
        self.assertNotEqual(a["candidate_id"], b["candidate_id"])
        self.assertEqual(e.pending_count(), 2)

    def test_duplicate_candidate_in_same_process_is_deduplicated(self):
        e = engine()
        e.observe(event=event(), process=process(), claimed_owner=OWNER)
        r = e.observe(event=event(), process=process(), claimed_owner=OWNER)
        self.assertEqual(e.pending_count(), 1)
        self.assertEqual(r["source_count"], 1)

    def test_second_file_same_context_preserves_both_origins(self):
        e = engine()
        e.observe(event=event(),process=process(),claimed_owner=OWNER)
        r = e.observe(event=event(file_id="FILE_DEMO_0002"),
                      process=process(),claimed_owner=OWNER)
        self.assertEqual(r["source_count"], 2)
        self.assertEqual(e.pending_count(), 1)

    def test_mismatched_process_link_is_rejected(self):
        p2=process(number="000124/2026",process_id="ADM-PMF-000124-2026")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_CONTEXT_MISMATCH"):
            engine().observe(event=event(),process=p2,claimed_owner=OWNER)

    def test_mock_ocr_is_not_evidence(self):
        with self.assertRaisesRegex(ContractViolation,"MOCK_OCR_NOT_EVIDENCE"):
            engine().observe(event=event(provider="mock"),
                             process=process(),claimed_owner=OWNER)

    def test_failed_document_event_not_learned(self):
        with self.assertRaisesRegex(ContractViolation,"INELIGIBLE_EVENT"):
            engine().observe(event=event(status="failed"),
                             process=process(),claimed_owner=OWNER)

    def test_blank_summary_is_not_learned(self):
        e=engine()
        result=e.observe(event=event(text=""),process=process(),claimed_owner=OWNER)
        self.assertEqual(result["status"],"INSUFFICIENT_CONTEXT")
        self.assertEqual(e.pending_count(),0)

    def test_operational_actions_can_trigger_staging(self):
        e=engine()
        for k in ("pdf_transform","catalog","nomenclature","document_create","workspace"):
            ev=event(operation=k,provider="local")
            ev=replace(ev,summary=TEXT + " " + k)
            r=e.observe(event=ev,process=process(),claimed_owner=OWNER)
            self.assertEqual(r["status"],"PENDING_HUMAN_REVIEW")
        self.assertEqual(e.pending_count(),5)

    def test_capture_never_persists_qdrant_or_approves(self):
        e=engine()
        x=e.observe(event=event(),process=process(),claimed_owner=OWNER)
        self.assertFalse(x["memory_persisted"])
        self.assertFalse(x["write_performed"])
        self.assertNotIn("point_id",x)

    def test_pending_context_retrieved_only_same_process(self):
        p1=process()
        p2=process(number="000124/2026",process_id="ADM-PMF-000124-2026")
        e=engine()
        e.observe(event=event(p1),process=p1,claimed_owner=OWNER)
        self.assertEqual(len(e.retrieve(process=p1,query=TEXT,claimed_owner=OWNER)["working_context"]),1)
        self.assertEqual(e.retrieve(process=p2,query=TEXT,claimed_owner=OWNER)["working_context"],[])

    def test_unapproved_records_not_retrieved(self):
        e=engine()
        r=e.retrieve(process=process(),query=TEXT,claimed_owner=OWNER,
                     approved_records=(record(approved=False),))
        self.assertEqual(r["approved_context"],[])
        self.assertEqual(r["cross_process_analogies"],[])

    def test_approved_same_process_explicitly_labeled(self):
        e=engine()
        r=e.retrieve(process=process(),query=TEXT,claimed_owner=OWNER,
                     approved_records=(record(),))
        self.assertEqual(len(r["approved_context"]),1)
        self.assertTrue(r["approved_context"][0]["use_as_current_process_fact"])

    def test_other_process_approved_memory_is_only_analogy(self):
        p2=process(number="000124/2026",process_id="ADM-PMF-000124-2026")
        r=engine().retrieve(process=process(),query=TEXT,claimed_owner=OWNER,
                            approved_records=(record(p2),))
        self.assertEqual(r["approved_context"],[])
        self.assertEqual(len(r["cross_process_analogies"]),1)
        self.assertEqual(r["cross_process_analogies"][0]["process_key"],p2.process_key)
        self.assertEqual(r["cross_process_analogies"][0]["relation"],"ANALOGY_ONLY")
        self.assertFalse(r["cross_process_analogies"][0]["use_as_current_process_fact"])

    def test_dissimilar_approved_case_not_injected(self):
        r=engine().retrieve(process=process(),query=TEXT,claimed_owner=OWNER,
                            approved_records=(record(text="Fiscalizacao de ruído na praia"),))
        self.assertEqual(r["approved_context"],[])

    def test_query_similarity_accent_insensitive(self):
        r=engine().retrieve(process=process(),query="autorização de comércio local",
                            claimed_owner=OWNER,approved_records=(record(),))
        self.assertEqual(len(r["approved_context"]),1)

    def test_approved_lookup_only_owner(self):
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            engine().retrieve(process=process(),query=TEXT,claimed_owner="anyone",
                              approved_records=(record(),))

    def test_no_automatic_memory_write_after_retrieval(self):
        r=engine().retrieve(process=process(),query=TEXT,claimed_owner=OWNER,
                            approved_records=(record(),))
        self.assertFalse(r["qdrant_written"])
        self.assertTrue(r["approved_records_are_synthetic_fixtures"])

class OwnerConcurrencyTests(unittest.TestCase):
    def test_owner_required_for_seed(self):
        c=InMemoryRevisionCoordinator(SyntheticOwnerOnly(OWNER))
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            c.seed(claimed_owner="anyone",process_key=process().process_key,
                   revision="REV_DEMO_0001")

    def test_reserve_with_expected_revision(self):
        c=coordinator()
        r=c.reserve(claimed_owner=OWNER,request=request())
        self.assertEqual(r["state"],"RESERVED_SYNTHETIC")
        self.assertFalse(r["durable"])

    def test_same_request_key_replay(self):
        c=coordinator()
        first=c.reserve(claimed_owner=OWNER,request=request())
        second=c.reserve(claimed_owner=OWNER,request=request())
        self.assertEqual(first["run_id"],second["run_id"])
        self.assertTrue(second["replayed"])

    def test_same_key_changed_payload_conflicts(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        with self.assertRaisesRegex(ContractViolation,"IDEMPOTENCY_CONFLICT"):
            c.reserve(claimed_owner=OWNER,request=request(fingerprint="b"*64))

    def test_stale_revision_conflicts_before_reserve(self):
        c=coordinator()
        with self.assertRaisesRegex(ContractViolation,"REVISION_CONFLICT"):
            c.reserve(claimed_owner=OWNER,request=request(expected="REV_DEMO_0000"))

    def test_two_simultaneous_commit_attempts_only_one_advances(self):
        c=coordinator()
        r1=request(key="REQUEST_IDEMP_0001")
        r2=request(key="REQUEST_IDEMP_0002")
        c.reserve(claimed_owner=OWNER,request=r1)
        c.reserve(claimed_owner=OWNER,request=r2)
        def run(key,new_revision):
            try:
                c.simulate_commit(claimed_owner=OWNER,
                                  process_key=process().process_key,
                                  idempotency_key=key,new_revision=new_revision)
                return "OK"
            except ContractViolation as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as exe:
            results=list(exe.map(lambda p:run(*p),[
                ("REQUEST_IDEMP_0001","REV_DEMO_0002"),
                ("REQUEST_IDEMP_0002","REV_DEMO_0003"),
            ]))
        self.assertCountEqual(results,["OK","REVISION_CONFLICT"])

    def test_simulated_commit_returns_no_real_write(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        r=c.simulate_commit(claimed_owner=OWNER,
                            process_key=process().process_key,
                            idempotency_key=KEY,new_revision="REV_DEMO_0002")
        self.assertEqual(r["state"],"COMMITTED_SYNTHETIC")
        self.assertFalse(r["document_write_performed"])
        self.assertFalse(r["qdrant_write_performed"])
        self.assertFalse(r["durable"])

    def test_revision_advanced_only_in_ram(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                          idempotency_key=KEY,new_revision="REV_DEMO_0002")
        self.assertEqual(c.current_revision(claimed_owner=OWNER,
                          process_key=process().process_key),"REV_DEMO_0002")

    def test_same_commit_replayed_is_idempotent(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        a=c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                            idempotency_key=KEY,new_revision="REV_DEMO_0002")
        b=c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                            idempotency_key=KEY,new_revision="REV_DEMO_0002")
        self.assertEqual(a,b)

    def test_commit_different_revision_on_replay_rejected(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                          idempotency_key=KEY,new_revision="REV_DEMO_0002")
        with self.assertRaisesRegex(ContractViolation,"REPLAY_REVISION_MISMATCH"):
            c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                              idempotency_key=KEY,new_revision="REV_DEMO_0003")

    def test_unknown_after_timeout_needs_manual_reconciliation(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        c.mark_unknown(claimed_owner=OWNER,process_key=process().process_key,
                       idempotency_key=KEY)
        with self.assertRaisesRegex(ContractViolation,"RECONCILIATION_REQUIRED"):
            c.simulate_commit(claimed_owner=OWNER,process_key=process().process_key,
                              idempotency_key=KEY,new_revision="REV_DEMO_0002")

    def test_unknown_readback_does_not_claim_success(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        x=c.mark_unknown(claimed_owner=OWNER,process_key=process().process_key,
                         idempotency_key=KEY)
        self.assertEqual(x["state"],"UNKNOWN_SYNTHETIC")
        self.assertFalse(x["document_write_performed"])

    def test_snapshot_is_copied_not_durable(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        snap=c.synthetic_snapshot(claimed_owner=OWNER)
        snap["heads"][process().process_key]="TAMPERED"
        self.assertEqual(c.current_revision(claimed_owner=OWNER,
                         process_key=process().process_key),"REV_DEMO_0001")

    def test_readback_requires_owner(self):
        c=coordinator()
        c.reserve(claimed_owner=OWNER,request=request())
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            c.readback(claimed_owner="other",process_key=process().process_key,
                       idempotency_key=KEY)

    def test_other_process_is_independent(self):
        c=coordinator()
        p2=process(number="000124/2026",process_id="ADM-PMF-000124-2026")
        c.seed(claimed_owner=OWNER,process_key=p2.process_key,
               revision="REV_DEMO_0001")
        c.reserve(claimed_owner=OWNER,request=request())
        c.reserve(claimed_owner=OWNER,request=request(p2))
        self.assertEqual(len(c.synthetic_snapshot(claimed_owner=OWNER)["runs"]),2)

    def test_missing_run_cannot_commit(self):
        with self.assertRaisesRegex(ContractViolation,"RUN_NOT_FOUND"):
            coordinator().simulate_commit(claimed_owner=OWNER,
               process_key=process().process_key,idempotency_key=KEY,
               new_revision="REV_DEMO_0002")

    def test_duplicate_seed_fails(self):
        c=coordinator()
        with self.assertRaisesRegex(ContractViolation,"PROCESS_ALREADY_SEEDED"):
            c.seed(claimed_owner=OWNER,process_key=process().process_key,
                   revision="REV_DEMO_0001")

if __name__=="__main__":
    unittest.main()
