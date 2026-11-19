"""G14-H independent review tests: G14-G readback and OCR R02 metadata.

All payloads are synthetic, and no OCR engine, R06, R07, provider or
customer document is read. SQLite is confined to TemporaryDirectory.
"""
from copy import deepcopy
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentEvent, DocumentSource
from gaia_document_mcp.process_learning import AdministrativeProcess, SyntheticOwnerOnly
from gaia_document_mcp.g14g_isolated import G14GDisposableGate
from gaia_document_mcp.g14h_ocr_r02_contract import preview_ocr_r02_contract

OWNER = "SYNTHETIC_GAIA_OWNER"
BYTES = b"%PDF-1.4\nDEMO SYNTHETIC ADMINISTRATIVE DOCUMENT\n%%EOF"
HASH = sha256(BYTES).hexdigest()
TXT = sha256(b"DEMO PAGE TEXT").hexdigest()


def process(number="000123/2026", process_id="DEMO_PROC_000123"):
    return AdministrativeProcess(
        process_id=process_id, jurisdiction="BR-SC-FLN",
        agency_code="PREF_DEMO", official_number=number,
    )


def source_event(proc, summary="DEMO: requerimento municipal de funcionamento"):
    return DocumentEvent(
        source=DocumentSource(
            drive_id="DRIVE_DEMO_001", file_id="FILE_DEMO_001",
            client_id="009", process_id=proc.process_id,
            source_version="DEMO_SOURCE_01", sha256_original=HASH,
        ),
        operation="ocr", status="completed", provider="tesseract",
        source_verified=False, operation_id="DEMO_OP_001",
        summary=summary,
    )


def page(number, quality="OCR_READABLE", confidence=0.91,
         attempts=1, digest=TXT):
    return {"page":number, "quality":quality, "confidence":confidence,
            "attempts":attempts, "text_sha256":digest}


def check_ocr(*, proc=None, format_kind="PDF", execution_state="completed",
              total_pages=1, chunks=((1,1),), pages=None, exceptions=(),
              source_sha256=HASH, document_id="DOC_DEMO_001",
              source_ref="drive:DRIVE_DEMO_001:FILE_DEMO_001"):
    proc = proc or process()
    if pages is None:
        pages=(page(1),)
    return preview_ocr_r02_contract(
        owner=SyntheticOwnerOnly(OWNER), claimed_owner=OWNER,
        process=proc, document_id=document_id,
        source_ref=source_ref, source_version="DEMO_SOURCE_01",
        source_sha256=source_sha256, format_kind=format_kind,
        execution_state=execution_state, total_pages=total_pages,
        chunks=chunks, pages=pages, exceptions=exceptions,
    )


class IndependentPaginationReview(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix="gaia-g14h-demo-")
        self.addCleanup(self.tmp.cleanup)
        self.owner=SyntheticOwnerOnly(OWNER)
        self.gate=G14GDisposableGate(self.tmp,self.owner)
        self.proc=process()
        self.gate.seed(claimed_owner=OWNER,process=self.proc,revision="DEMO_REV_1")
        self.gate.capture(claimed_owner=OWNER,process=self.proc,
                          event=source_event(self.proc))
        self.gate.capture(claimed_owner=OWNER,process=self.proc,
                          event=source_event(self.proc,"DEMO: despacho administrativo municipal"))

    def pages(self):
        first=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        second=self.gate.page_pending(
            claimed_owner=OWNER,page_size=1,cursor=first["next_cursor"])
        return first,second

    def test_unchanged_pages_have_current_sqlite_readback(self):
        p=self.pages()
        r=self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=p)
        self.assertEqual(r["count"],2)
        self.assertTrue(r["page_content_readback_verified"])
        self.assertFalse(r["real_qdrant_or_r06_readback"])

    def test_forged_summary_digest_is_rejected_at_readback(self):
        pages=list(deepcopy(self.pages()))
        pages[1]["items"][0]["summary_digest"]="f"*64
        with self.assertRaisesRegex(ContractViolation,"PAGE_CONTENT_MISMATCH"):
            self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=tuple(pages))

    def test_forged_process_id_is_rejected_at_readback(self):
        pages=list(deepcopy(self.pages()))
        pages[0]["items"][0]["process_id"]="DEMO_OTHER_PROCESS"
        with self.assertRaisesRegex(ContractViolation,"PAGE_CONTENT_MISMATCH"):
            self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=tuple(pages))

    def test_forged_source_count_is_rejected_at_readback(self):
        pages=list(deepcopy(self.pages()))
        pages[0]["items"][0]["source_count"]=999
        with self.assertRaisesRegex(ContractViolation,"PAGE_CONTENT_MISMATCH"):
            self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=tuple(pages))

    def test_forged_memory_approval_is_rejected_at_readback(self):
        pages=list(deepcopy(self.pages()))
        pages[0]["items"][0]["memory_approved"]=True
        with self.assertRaisesRegex(ContractViolation,"PAGE_CONTENT_MISMATCH"):
            self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=tuple(pages))

    def test_bad_page_limit_type_is_controlled_failure(self):
        from gaia_document_mcp.g14g_isolated import verify_disposable_page_sequence
        pages=list(deepcopy(self.pages()))
        pages[0]["limit"]="1"
        with self.assertRaisesRegex(ContractViolation,"PAGE_COVERAGE_INCOMPLETE"):
            verify_disposable_page_sequence(tuple(pages))

    def test_scope_with_same_number_and_another_internal_process_is_rejected(self):
        alias=process(process_id="DEMO_NOT_THE_REGISTERED_ID")
        with self.assertRaisesRegex(ContractViolation,"PROCESS_ID_COLLISION"):
            self.gate.page_pending(claimed_owner=OWNER,process=alias)

    def test_source_change_invalidates_prior_page_before_readback(self):
        p=self.pages()
        self.gate.capture(
            claimed_owner=OWNER,process=self.proc,
            event=source_event(self.proc,"DEMO: parecer tecnico municipal"),
        )
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.confirm_current_coverage(claimed_owner=OWNER,pages=p)


class OCRR02MetadataContract(unittest.TestCase):
    def test_one_page_complete_and_legible_is_only_candidate_preview(self):
        a=check_ocr()
        self.assertTrue(a["all_pages_accounted"])
        self.assertEqual(a["document_quality"],"LEGIBLE_ALL_PAGES")
        self.assertEqual(a["job_state"],"COMPLETED")
        self.assertFalse(a["eligible_for_verified_document_evidence"])
        self.assertFalse(a["qdrant_written"])

    def test_ten_page_document_has_no_implicit_ten_page_limit(self):
        a=check_ocr(total_pages=10,chunks=((1,8),(9,10)),
                    pages=tuple(page(i) for i in range(1,11)))
        self.assertEqual(a["pages_accounted"],10)

    def test_seventeen_pages_in_eight_eight_one_chunks(self):
        a=check_ocr(total_pages=17,chunks=((1,8),(9,16),(17,17)),
                    pages=tuple(page(i) for i in range(1,18)))
        self.assertEqual(a["pages_accounted"],17)

    def test_oversized_page_count_is_blocked_in_fixture(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_PAGE_LIMIT_INVALID"):
            check_ocr(total_pages=65,chunks=(),pages=())

    def test_completed_job_with_only_three_pages_of_ten_is_blocked(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_PAGE_COVERAGE_INCOMPLETE"):
            check_ocr(total_pages=10,chunks=((1,3),),
                      pages=tuple(page(i) for i in range(1,4)))

    def test_partial_job_with_three_pages_is_not_legible_document(self):
        a=check_ocr(total_pages=10,chunks=((1,3),),
                    pages=tuple(page(i) for i in range(1,4)),
                    execution_state="partial")
        self.assertEqual(a["document_quality"],"INCOMPLETE")
        self.assertFalse(a["all_pages_accounted"])

    def test_mixed_native_ocr_and_blank_document_requires_review(self):
        items=(
            page(1,"NATIVE",None,0,TXT),
            page(2,"OCR_READABLE",0.95,1,TXT),
            page(3,"EMPTY",None,1,None),
        )
        a=check_ocr(total_pages=3,chunks=((1,3),),pages=items)
        self.assertEqual(a["job_state"],"COMPLETED")
        self.assertEqual(a["document_quality"],"NEEDS_DOCUMENT_REVIEW")
        self.assertEqual(a["quality_counts"]["EMPTY"],1)

    def test_ocr_low_confidence_cannot_be_disguised_as_legible(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_QUALITY_CONTRADICTION"):
            check_ocr(pages=(page(1,"OCR_READABLE",0.25,1,TXT),))

    def test_ocr_retries_are_capped(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_ATTEMPTS_INVALID"):
            check_ocr(pages=(page(1,"OCR_READABLE",0.8,4,TXT),))

    def test_retry_with_rotation_low_confidence_remains_reviewable(self):
        a=check_ocr(pages=(page(1,"LOW_CONFIDENCE",0.41,3,None),),
                    exceptions=("ROTATION_RETRY_EXHAUSTED",))
        self.assertEqual(a["document_quality"],"NEEDS_DOCUMENT_REVIEW")
        self.assertFalse(a["memory_approved"])

    def test_kml_service_exception_is_invalid_export_no_ocr(self):
        a=check_ocr(format_kind="KML",execution_state="routed",total_pages=0,
                    chunks=(),pages=(),exceptions=("SERVICE_EXCEPTION_REPORT",))
        self.assertEqual(a["route"],"INVALID_EXPORT_NO_OCR")

    def test_kml_encoding_requires_derived_utf8_copy(self):
        a=check_ocr(format_kind="KML",execution_state="routed",total_pages=0,
                    chunks=(),pages=(),exceptions=("KML_ENCODING_CONVERSION_REQUIRED",))
        self.assertEqual(a["route"],"DERIVED_UTF8_COPY_REQUIRED")

    def test_missing_dbf_shapefile_is_incomplete(self):
        a=check_ocr(format_kind="SHP",execution_state="routed",total_pages=0,
                    chunks=(),pages=(),exceptions=("SHAPESET_MISSING_DBF",))
        self.assertEqual(a["route"],"INCOMPLETE_SHAPESET")

    def test_dwg_is_routed_to_cad_without_ocr(self):
        a=check_ocr(format_kind="DWG",execution_state="routed",total_pages=0,
                    chunks=(),pages=())
        self.assertEqual(a["route"],"CAD_ANALYZER_REQUIRED")
        self.assertFalse(a["actual_ocr_performed"])

    def test_geojson_is_only_structural_route(self):
        a=check_ocr(format_kind="GEOJSON",execution_state="routed",total_pages=0,
                    chunks=(),pages=())
        self.assertEqual(a["route"],"GEOJSON_STRUCTURAL_VALIDATION_REQUIRED")
        self.assertFalse(a["provider_connected"])

    def test_duplicate_page_number_fails(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_PAGE_NUMBER_INVALID"):
            check_ocr(total_pages=2,chunks=((1,2),),
                      pages=(page(1),page(1)))

    def test_out_of_order_or_overlapping_chunks_fail(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_CHUNK_CONTRACT_INVALID"):
            check_ocr(total_pages=4,chunks=((1,2),(2,4)),
                      pages=tuple(page(i) for i in range(1,5)))

    def test_arbitrary_raw_extracted_text_is_rejected(self):
        bad=page(1)
        bad["raw_text"]="DEMO content that must not be in metadata"
        with self.assertRaisesRegex(ContractViolation,"OCR_PAGE_METADATA_INVALID"):
            check_ocr(pages=(bad,))

    def test_page_text_digest_is_required_for_legible_ocr(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_TEXT_DIGEST_REQUIRED"):
            check_ocr(pages=(page(1,digest=None),))

    def test_failure_event_does_not_claim_document_readiness(self):
        a=check_ocr(execution_state="failed",chunks=(),pages=(),
                    exceptions=("PROVIDER_FAILURE_SYNTHETIC",))
        self.assertEqual(a["document_quality"],"INCOMPLETE")
        self.assertFalse(a["eligible_for_verified_document_evidence"])

    def test_changed_process_context_changes_fingerprint(self):
        a=check_ocr()
        p2=process(number="000124/2026",process_id="DEMO_PROC_000124")
        b=check_ocr(proc=p2)
        self.assertNotEqual(a["safe_preview_fingerprint"],b["safe_preview_fingerprint"])

    def test_source_revision_changes_fingerprint(self):
        a=check_ocr()
        b=check_ocr(source_sha256="f"*64)
        self.assertNotEqual(a["safe_preview_fingerprint"],b["safe_preview_fingerprint"])

    def test_non_ocr_event_with_pdf_pages_is_not_accepted(self):
        with self.assertRaisesRegex(ContractViolation,"NON_OCR_ROUTING_REQUIRED"):
            check_ocr(format_kind="DWG",execution_state="routed")

    def test_wrong_source_identifier_not_demo_is_blocked(self):
        with self.assertRaisesRegex(ContractViolation,"SYNTHETIC_DOCUMENT_ONLY"):
            check_ocr(source_ref="drive:REAL_CLIENT_FILE")

    def test_uncontrolled_exception_text_is_blocked(self):
        with self.assertRaisesRegex(ContractViolation,"OCR_EXCEPTION_CODE_INVALID"):
            check_ocr(exceptions=("Provider token sk-secret",))


if __name__=="__main__":
    unittest.main()
