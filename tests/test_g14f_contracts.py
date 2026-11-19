"""G14-F independent negative contract tests; fictional data only."""
from dataclasses import replace
from hashlib import sha256
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentSource, DocumentEvent
from gaia_document_mcp.process_learning import AdministrativeProcess, SyntheticOwnerOnly
from gaia_document_mcp.g14f_contracts import (
    SyntheticSourceObservation, event_contract_preview,
    synthetic_batch_page, verify_synthetic_coverage,
    synthetic_readback_contract, synthetic_unknown_decision,
)

OWNER = "GAIA_OWNER_DEMO"
PDF = b"%PDF-1.4\nFAKE G14F\n%%EOF"
SHA = sha256(PDF).hexdigest()

def process(number="000123/2026", pid="ADM_DEMO_000123"):
    return AdministrativeProcess(
        process_id=pid, agency_code="PREF_DEMO",
        jurisdiction="BR-SC-FLN", official_number=number,
    )

def event(p=None, status="completed", provider="tesseract", summary="DEMO: requerimento municipal"):
    p=p or process()
    source=DocumentSource(
        drive_id="DRIVE_DEMO_01",file_id="FILE_DEMO_001",
        client_id="009",process_id=p.process_id,source_version="VERSION_DEMO_1",
        sha256_original=SHA,
    )
    return DocumentEvent(
        source=source,operation="ocr",status=status,provider=provider,
        source_verified=False,operation_id="OP_G14F_DEMO_01",
        summary=summary,
    )

def observation(e, p=None):
    p=p or process()
    return SyntheticSourceObservation(
        process_id=p.process_id,process_key=p.process_key,
        source_ref=e.source.source_ref,source_version=e.source.source_version,
        original_sha256=SHA,
    )

def candidate(ch, summary, revision=1):
    return {
        "candidate_id":ch * 64,
        "candidate_revision":revision,
        "summary":summary,
        "source_count":1,
    }

def batches():
    a=process()
    b=process("000124/2026","ADM_DEMO_000124")
    return (
        {"process_key":a.process_key,"candidates":[
            candidate("a","DEMO: requerimento de funcionamento"),
            candidate("b","DEMO: despacho municipal"),
        ]},
        {"process_key":b.process_key,"candidates":[
            candidate("c","DEMO: requerimento de funcionamento"),
        ]},
    )

def receipt():
    return {
        "point_id":"point_synthetic_001",
        "namespace":"chatgpt",
        "process_id":"ADM_DEMO_000123",
        "source_ref":"drive:DRIVE_DEMO_01:FILE_DEMO_001",
        "document_sha256":SHA,
        "document_approval_ref":"DOC_APPROVAL_DEMO_01",
        "proposal_id":"proposal_synthetic_01",
        "approved_by":"GAIA_OWNER_DEMO",
        "approval_event_ref":"REVIEW_DEMO_001",
    }

class SyntheticEventContractTests(unittest.TestCase):
    def evaluate(self, e=None, p=None, observed=None, content=PDF, claimed_owner=OWNER):
        e=e or event()
        p=p or process()
        observed=observed or observation(e,p)
        return event_contract_preview(
            owner=SyntheticOwnerOnly(OWNER),claimed_owner=claimed_owner,
            process=p,event=e,observation=observed,original=content,
        )

    def test_matching_event_is_only_preview(self):
        out=self.evaluate()
        self.assertEqual(out["proposal_state"],"PENDING_EVIDENCE_AND_HUMAN_REVIEW")
        self.assertFalse(out["memory_approved"])
        self.assertFalse(out["qdrant_written"])
        self.assertFalse(out["document_write_performed"])

    def test_metadata_only_no_document_or_raw_summary(self):
        result=self.evaluate()
        self.assertNotIn("DEMO: requerimento",str(result))
        self.assertNotIn("FAKE G14F",str(result))
        self.assertIn("source_sha256",result)

    def test_owner_fixture_rejects_other_subject(self):
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            self.evaluate(claimed_owner="OTHER")

    def test_event_with_different_process_rejected(self):
        p2=process("000124/2026","ADM_DEMO_000124")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_CONTEXT_MISMATCH"):
            self.evaluate(e=event(p2))

    def test_observation_with_other_process_rejected(self):
        obs=observation(event())
        alt=replace(obs,process_key=process("000124/2026","ADM_DEMO_000124").process_key)
        with self.assertRaisesRegex(ContractViolation,"OBSERVATION_PROCESS_MISMATCH"):
            self.evaluate(observed=alt)

    def test_observation_wrong_source_ref_rejected(self):
        obs=replace(observation(event()),source_ref="drive:DRIVE_DEMO_02:FILE_DEMO_001")
        with self.assertRaisesRegex(ContractViolation,"SOURCE_VERSION_MISMATCH"):
            self.evaluate(observed=obs)

    def test_observation_old_version_rejected(self):
        obs=replace(observation(event()),source_version="OLD_DEMO")
        with self.assertRaisesRegex(ContractViolation,"SOURCE_VERSION_MISMATCH"):
            self.evaluate(observed=obs)

    def test_observation_different_hash_rejected(self):
        obs=replace(observation(event()),original_sha256="f"*64)
        with self.assertRaisesRegex(ContractViolation,"SOURCE_HASH_MISMATCH"):
            self.evaluate(observed=obs)

    def test_original_modified_bytes_rejected(self):
        with self.assertRaisesRegex(ContractViolation,"SOURCE_HASH_MISMATCH"):
            self.evaluate(content=PDF+b"changed")

    def test_mock_ocr_does_not_create_candidate_preview(self):
        with self.assertRaisesRegex(ContractViolation,"MOCK_OCR_NOT_EVIDENCE"):
            self.evaluate(e=event(provider="mock"))

    def test_failed_event_does_not_create_candidate_preview(self):
        with self.assertRaisesRegex(ContractViolation,"EVENT_NOT_ELIGIBLE"):
            self.evaluate(e=event(status="failed"))

    def test_real_looking_text_not_accepted_in_demo_lab(self):
        with self.assertRaisesRegex(ContractViolation,"SYNTHETIC_FIXTURE_REQUIRED"):
            self.evaluate(e=event(summary="Possível documento de cliente"))

    def test_other_process_with_similar_topic_yields_distinct_fingerprint(self):
        p2=process("000124/2026","ADM_DEMO_000124")
        e2=event(p2)
        a=self.evaluate()["candidate_fingerprint"]
        b=self.evaluate(e=e2,p=p2,observed=observation(e2,p2))["candidate_fingerprint"]
        self.assertNotEqual(a,b)

    def test_changed_event_revision_changes_fingerprint(self):
        e=event()
        a=self.evaluate(e=e)["candidate_fingerprint"]
        b=self.evaluate(e=replace(e,event_revision=2))["candidate_fingerprint"]
        self.assertNotEqual(a,b)

class SyntheticPaginationTests(unittest.TestCase):
    def test_page_limit_rejects_unbounded(self):
        for limit in (0,26,False,-1):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ContractViolation,"PAGE_LIMIT_INVALID"):
                    synthetic_batch_page(batches=batches(),limit=limit)

    def test_all_pages_cover_three_candidates(self):
        a=synthetic_batch_page(batches=batches(),limit=1,offset=0)
        b=synthetic_batch_page(batches=batches(),limit=1,offset=a["next_offset"])
        c=synthetic_batch_page(batches=batches(),limit=1,offset=b["next_offset"])
        cov=verify_synthetic_coverage((a,b,c))
        self.assertEqual(cov["count"],3)
        self.assertTrue(cov["coverage_verified_for_fixture"])
        self.assertFalse(cov["review_authorized"])
        self.assertFalse(cov["real_database_coverage_verified"])

    def test_early_final_page_is_not_complete_coverage(self):
        first=synthetic_batch_page(batches=batches(),limit=1)
        with self.assertRaisesRegex(ContractViolation,"PAGE_COVERAGE_INCOMPLETE"):
            verify_synthetic_coverage((first,))

    def test_repeat_page_is_detected(self):
        first=synthetic_batch_page(batches=batches(),limit=1)
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_MISMATCH"):
            verify_synthetic_coverage((first,first))

    def test_snapshot_changes_with_new_candidate(self):
        before=batches()
        after=({"process_key":before[0]["process_key"],
                "candidates":before[0]["candidates"]+[candidate("d","DEMO: outro requerimento")]},
               before[1])
        first=synthetic_batch_page(batches=before,limit=1)
        next_from_new=synthetic_batch_page(batches=after,limit=3,offset=1)
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_MISMATCH"):
            verify_synthetic_coverage((first,next_from_new))

    def test_duplicate_candidate_in_fixture_rejected(self):
        p=process()
        d=candidate("a","DEMO: repetido")
        with self.assertRaisesRegex(ContractViolation,"DUPLICATE_CANDIDATE"):
            synthetic_batch_page(batches=(
                {"process_key":p.process_key,"candidates":[d,d]},
            ),limit=1)

    def test_unverified_summary_rejected(self):
        p=process()
        with self.assertRaisesRegex(ContractViolation,"INVALID_SYNTHETIC_CANDIDATE"):
            synthetic_batch_page(batches=(
                {"process_key":p.process_key,
                 "candidates":[candidate("a","Cliente 111 dados")]},
            ),limit=1)

    def test_snapshot_includes_revision(self):
        data=batches()
        newer=({"process_key":data[0]["process_key"],
                "candidates":[{**data[0]["candidates"][0],"candidate_revision":2},
                              data[0]["candidates"][1]]},data[1])
        a=synthetic_batch_page(batches=data,limit=2)
        b=synthetic_batch_page(batches=newer,limit=2)
        self.assertNotEqual(a["snapshot"],b["snapshot"])

    def test_out_of_range_offset_rejected(self):
        with self.assertRaisesRegex(ContractViolation,"PAGE_OFFSET_INVALID"):
            synthetic_batch_page(batches=batches(),limit=2,offset=7)

class SyntheticReadbackTests(unittest.TestCase):
    def test_full_fixture_readback_is_not_real_approval(self):
        x=receipt()
        result=synthetic_readback_contract(expected=x,observed={**x,"approved":True})
        self.assertTrue(result["match_in_test_fixture"])
        self.assertFalse(result["real_qdrant_readback"])
        self.assertFalse(result["real_human_approval_verified"])

    def test_missing_provenance_not_accepted(self):
        x=receipt()
        observed={**x,"approved":True}
        del observed["document_approval_ref"]
        with self.assertRaisesRegex(ContractViolation,"READBACK_MISMATCH"):
            synthetic_readback_contract(expected=x,observed=observed)

    def test_cross_process_point_cannot_validate_other_process(self):
        x=receipt()
        observed={**x,"approved":True,"process_id":"ADM_DEMO_999999"}
        with self.assertRaisesRegex(ContractViolation,"READBACK_MISMATCH:process_id"):
            synthetic_readback_contract(expected=x,observed=observed)

    def test_wrong_namespace_not_accepted(self):
        x=receipt()
        with self.assertRaisesRegex(ContractViolation,"READBACK_MISMATCH:namespace"):
            synthetic_readback_contract(expected=x,observed={**x,"approved":True,"namespace":"other"})

    def test_pending_proposal_must_not_be_marked_approved(self):
        x=receipt()
        with self.assertRaisesRegex(ContractViolation,"READBACK_NOT_APPROVED"):
            synthetic_readback_contract(expected=x,observed={**x,"approved":False})

    def test_readback_missing_expected_document_hash_rejected(self):
        x=receipt()
        x["document_sha256"]=""
        with self.assertRaisesRegex(ContractViolation,"READBACK_INCOMPLETE"):
            synthetic_readback_contract(expected=x,observed={**x,"approved":True})

    def test_other_source_ref_does_not_validate(self):
        x=receipt()
        with self.assertRaisesRegex(ContractViolation,"READBACK_MISMATCH:source_ref"):
            synthetic_readback_contract(
                expected=x,observed={**x,"approved":True,"source_ref":"drive:OTHER:FILE"}
            )

    def test_unknown_state_never_retries_automatically(self):
        x=synthetic_unknown_decision("UNKNOWN_SYNTHETIC")
        self.assertEqual(x["safe_action"],"READBACK_AND_RECONCILE")
        self.assertFalse(x["automatically_retried"])
        self.assertFalse(x["external_effect_verified"])

    def test_committed_synthetic_does_not_claim_external_write(self):
        x=synthetic_unknown_decision("COMMITTED_SYNTHETIC")
        self.assertEqual(x["safe_action"],"NO_AUTOMATIC_EXTERNAL_RETRY")
        self.assertFalse(x["external_effect_verified"])

if __name__=="__main__":
    unittest.main()
