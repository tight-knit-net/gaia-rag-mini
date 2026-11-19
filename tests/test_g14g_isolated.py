"""G14-G disposable source and SQL pagination negative tests.

All examples are invented; the database is created in TemporaryDirectory.
No REST, cloud identity, Qdrant, actual OCR, customer data or memory save.
"""
from dataclasses import replace
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest

from gaia_document_mcp.contracts import ContractViolation, DocumentSource, DocumentEvent
from gaia_document_mcp.process_learning import AdministrativeProcess, SyntheticOwnerOnly
from gaia_document_mcp.owner_concurrency import SyntheticRequest
from gaia_document_mcp.g14g_isolated import (
    G14GDisposableGate, verify_disposable_page_sequence,
)

OWNER = "GAIA_OWNER_DEMO"
RAW = b"%PDF-1.4\nDEMO SYNTHETIC PROCESS ONLY\n%%EOF"
HASH = sha256(RAW).hexdigest()
KEY = "G14G_REQUEST_DEMO_0001"
REV = "DEMO_REV_0001"


def process(number="000123/2026", pid="DEMO_PROC_000123"):
    return AdministrativeProcess(
        process_id=pid, jurisdiction="BR-SC-FLN",
        agency_code="PREF_DEMO", official_number=number,
    )


def event(proc=None, *, summary="DEMO: requerimento administrativo municipal",
          file_id="FILE_DEMO_0001", version="DEMO_SOURCE_VERSION_1",
          original_hash=HASH, operation_id="OP_DEMO_0001"):
    proc = proc or process()
    return DocumentEvent(
        source=DocumentSource(
            drive_id="DRIVE_DEMO_001", file_id=file_id, client_id="009",
            process_id=proc.process_id, source_version=version,
            sha256_original=original_hash,
        ),
        operation="ocr", status="completed", provider="tesseract",
        source_verified=False, operation_id=operation_id, summary=summary,
    )


class G14GDisposableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="gaia-g14g-test-")
        self.addCleanup(self.tmp.cleanup)
        self.owner = SyntheticOwnerOnly(OWNER)
        self.gate = G14GDisposableGate(self.tmp, self.owner)
        self.proc = process()

    def seed(self, proc=None):
        proc = proc or self.proc
        self.gate.seed(claimed_owner=OWNER, process=proc, revision=REV)

    def capture(self, proc=None, ev=None, *, gate=None):
        proc = proc or self.proc
        ev = ev or event(proc)
        return (gate or self.gate).capture(
            claimed_owner=OWNER, process=proc, event=ev,
        )

    def observe(self, proc=None, ev=None, data=RAW):
        proc = proc or self.proc
        ev = ev or event(proc)
        return self.gate.observe_demo_source(
            claimed_owner=OWNER, process=proc,
            source_ref=ev.source.source_ref,
            source_version=ev.source.source_version,
            original=data,
        )

    def reserve(self, *, expected=REV, key=KEY, fingerprint="a"*64):
        return self.gate.reserve(
            claimed_owner=OWNER, request=SyntheticRequest(
                process_key=self.proc.process_key, idempotency_key=key,
                expected_revision=expected, request_fingerprint=fingerprint,
            ),
        )

    def paginate(self, *, process_filter=None, page_size=1):
        pages = []
        cursor = None
        for _ in range(30):
            page = self.gate.page_pending(
                claimed_owner=OWNER, page_size=page_size,
                process=process_filter, cursor=cursor,
            )
            pages.append(page)
            if page["next_cursor"] is None:
                return tuple(pages)
            cursor = page["next_cursor"]
        self.fail("PAGE_LOOP")

    # Replay is a versioned conditional action, even after a commit.
    def test_replay_same_key_and_expected_revision_is_idempotent(self):
        self.seed()
        first = self.reserve()
        again = self.reserve()
        self.assertEqual(first["run_id"], again["run_id"])
        self.assertEqual(again["expected_revision"], REV)
        self.assertTrue(again["replayed"])

    def test_replay_new_expected_revision_is_conflict_even_with_same_payload(self):
        self.seed()
        self.reserve()
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_REVISION_CONFLICT"):
            self.reserve(expected="DEMO_REV_0002")
        self.assertEqual(
            self.gate.current_revision(claimed_owner=OWNER, process_key=self.proc.process_key),
            REV,
        )

    def test_replay_new_expected_revision_is_conflict_after_commit(self):
        self.seed()
        self.reserve()
        self.gate.commit_revision(
            claimed_owner=OWNER, process_key=self.proc.process_key,
            request_key=KEY, new_revision="DEMO_REV_0002",
        )
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_REVISION_CONFLICT"):
            self.reserve(expected="DEMO_REV_0002")

    def test_same_key_same_revision_changed_payload_is_conflict(self):
        self.seed()
        self.reserve()
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_CONFLICT"):
            self.reserve(fingerprint="b"*64)

    def test_new_key_stale_revision_is_cas_conflict(self):
        self.seed()
        self.reserve()
        self.gate.commit_revision(
            claimed_owner=OWNER, process_key=self.proc.process_key,
            request_key=KEY, new_revision="DEMO_REV_0002",
        )
        with self.assertRaisesRegex(ContractViolation, "REVISION_CONFLICT"):
            self.reserve(key="G14G_REQUEST_DEMO_0002")

    def test_bound_event_reservation_rejects_changed_expected_revision(self):
        self.seed()
        e = event()
        kwargs=dict(
            claimed_owner=OWNER, process=self.proc, event=e,
            original_bytes=RAW, idempotency_key=KEY,
        )
        original=self.gate.reserve_from_event(**kwargs, expected_revision=REV)
        self.assertFalse(original["replayed"])
        with self.assertRaisesRegex(ContractViolation, "IDEMPOTENCY_REVISION_CONFLICT"):
            self.gate.reserve_from_event(**kwargs, expected_revision="DEMO_REV_0002")

    def test_revision_expected_is_exposed_in_readback(self):
        self.seed()
        self.reserve()
        self.assertEqual(
            self.gate.readback(
                claimed_owner=OWNER, process_key=self.proc.process_key,
                request_key=KEY,
            )["expected_revision"], REV
        )

    # Observation comes from a separate synthetic fixture receipt.
    def test_observation_requires_registered_administrative_process(self):
        with self.assertRaisesRegex(ContractViolation, "PROCESS_BINDING_NOT_REGISTERED"):
            self.observe()

    def test_observation_retains_sha_and_is_not_provider_auth(self):
        self.seed()
        o=self.observe()
        self.assertEqual(o["original_sha256"], HASH)
        self.assertFalse(o["provider_origin_authenticated"])
        self.assertTrue(o["observed_only_in_disposable_fixture"])

    def test_identical_observation_is_idempotent(self):
        self.seed()
        a=self.observe()
        b=self.observe()
        self.assertTrue(b["replayed"])
        self.assertEqual(a["observation_id"], b["observation_id"])

    def test_same_source_version_different_bytes_fails(self):
        self.seed()
        self.observe()
        with self.assertRaisesRegex(ContractViolation, "OBSERVATION_CONFLICT"):
            self.observe(data=RAW+b"DEMO CHANGED")

    def test_non_demo_bytes_are_rejected(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "SYNTHETIC_OBSERVATION_ONLY"):
            self.observe(data=b"%PDF confidential content")

    def test_oversized_demo_fixture_is_rejected(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "SYNTHETIC_OBSERVATION_ONLY"):
            self.observe(data=b"DEMO"+b"0"*65536)

    def test_alternate_process_id_with_same_number_is_rejected(self):
        self.seed()
        p=process(pid="DEMO_ALTERNATIVE_PROC")
        with self.assertRaisesRegex(ContractViolation, "PROCESS_BINDING_NOT_REGISTERED"):
            self.observe(proc=p,ev=event(p))

    def test_observed_capture_requires_observation(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "OBSERVATION_REQUIRED"):
            self.gate.capture_observed_demo(
                claimed_owner=OWNER, process=self.proc, event=event(),
                original=RAW,
            )

    def test_observed_capture_checks_original_bytes(self):
        self.seed()
        self.observe()
        with self.assertRaisesRegex(ContractViolation, "SOURCE_HASH_MISMATCH"):
            self.gate.capture_observed_demo(
                claimed_owner=OWNER, process=self.proc,
                event=event(), original=RAW+b"TAMPER",
            )

    def test_observed_capture_checks_version(self):
        self.seed()
        self.observe()
        with self.assertRaisesRegex(ContractViolation, "OBSERVATION_REQUIRED"):
            self.gate.capture_observed_demo(
                claimed_owner=OWNER, process=self.proc,
                event=event(version="DEMO_SOURCE_VERSION_2"), original=RAW,
            )

    def test_observed_capture_rejects_wrong_declared_original_hash(self):
        self.seed()
        self.observe()
        with self.assertRaisesRegex(ContractViolation, "SOURCE_HASH_MISMATCH"):
            self.gate.capture_observed_demo(
                claimed_owner=OWNER, process=self.proc,
                event=event(original_hash="f"*64), original=RAW,
            )

    def test_observed_capture_creates_only_pending_candidate(self):
        self.seed()
        self.observe()
        result=self.gate.capture_observed_demo(
            claimed_owner=OWNER, process=self.proc, event=event(), original=RAW,
        )
        self.assertEqual(result["status"], "PENDING_HUMAN_REVIEW")
        self.assertFalse(result["provider_origin_authenticated"])
        self.assertFalse(result["derived_quality_attested"])
        self.assertFalse(result["memory_approved"])
        self.assertFalse(result["qdrant_write_performed"])
        self.assertEqual(len(self.gate.working_context(
            claimed_owner=OWNER, process=self.proc,
        )), 1)

    def test_owner_other_subject_cannot_observe_or_capture(self):
        self.seed()
        with self.assertRaisesRegex(ContractViolation, "OWNER_REQUIRED"):
            self.gate.observe_demo_source(
                claimed_owner="NOT_OWNER", process=self.proc,
                source_ref=event().source.source_ref,
                source_version=event().source.source_version,
                original=RAW,
            )

    # Transactional SQL page snapshots, not flattened in-memory fixtures.
    def test_empty_table_is_complete_with_zero_items(self):
        p=self.gate.page_pending(claimed_owner=OWNER, page_size=5)
        self.assertEqual(p["total"],0)
        self.assertTrue(p["page_complete"])
        self.assertEqual(p["items"],[])
        self.assertTrue(self.gate.confirm_current_coverage(
            claimed_owner=OWNER, pages=(p,),
        )["currently_matches_disposable_sqlite"])

    def test_two_page_sql_cursor_reaches_full_coverage(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        pages=self.paginate(page_size=1)
        self.assertEqual(len(pages),2)
        proof=self.gate.confirm_current_coverage(claimed_owner=OWNER, pages=pages)
        self.assertEqual(proof["count"],2)
        self.assertFalse(proof["real_provider_coverage_verified"])
        self.assertTrue(pages[0]["disposable_sqlite_paginated"])
        self.assertFalse(pages[0]["real_database_paginated"])

    def test_page_limit_capped_at_25(self):
        for bad in (0,26,-1,True,"20"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ContractViolation, "PAGE_LIMIT_INVALID"):
                    self.gate.page_pending(claimed_owner=OWNER,page_size=bad)

    def test_page_cursor_rejects_malformed_values(self):
        for bad in ("abc","g14g:zz:1","g14g:"+"a"*64+":-1",1):
            with self.subTest(cursor=bad):
                with self.assertRaisesRegex(ContractViolation,"PAGE_CURSOR_INVALID"):
                    self.gate.page_pending(claimed_owner=OWNER,cursor=bad)

    def test_new_candidate_invalidates_cursor(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        p=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        self.capture(ev=event(summary="DEMO: processo de consulta ambiental"))
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.page_pending(
                claimed_owner=OWNER, page_size=1, cursor=p["next_cursor"],
            )

    def test_new_evidence_update_invalidates_cursor(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        p=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        self.capture(ev=event(file_id="FILE_DEMO_0002"))
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.page_pending(
                claimed_owner=OWNER, page_size=1,cursor=p["next_cursor"],
            )

    def test_reviewed_candidate_invalidates_cursor(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        p=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        preview=self.gate.preview_batches(claimed_owner=OWNER)[0]
        self.gate.review_batch_items(
            claimed_owner=OWNER, process_key=self.proc.process_key,
            batch_id=preview["batch_id"],
            decisions={preview["candidates"][0]["candidate_id"]:"prepare_proposals"},
        )
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.page_pending(
                claimed_owner=OWNER,page_size=1,cursor=p["next_cursor"],
            )

    def test_sql_direct_update_invalidation_trigger(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        p=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        with self.gate._tx() as db:
            db.execute(
                "UPDATE candidates SET summary='DEMO: updated for test' "
                "WHERE summary='DEMO: requerimento administrativo municipal'",
            )
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.page_pending(
                claimed_owner=OWNER,page_size=1,cursor=p["next_cursor"],
            )

    def test_cursor_persists_across_reopened_sqlite_connection(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        first=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        reopened=G14GDisposableGate(self.tmp,self.owner)
        following=reopened.page_pending(
            claimed_owner=OWNER,page_size=1,cursor=first["next_cursor"],
        )
        proof=reopened.confirm_current_coverage(
            claimed_owner=OWNER,pages=(first,following),
        )
        self.assertEqual(proof["count"],2)

    def test_cross_process_query_is_context_filter_not_acl(self):
        self.seed()
        self.capture()
        other=process(number="000124/2026",pid="DEMO_PROC_000124")
        self.gate.seed(claimed_owner=OWNER,process=other,revision=REV)
        self.capture(proc=other,ev=event(other))
        one=self.gate.page_pending(
            claimed_owner=OWNER,process=self.proc,page_size=5,
        )
        allp=self.gate.page_pending(claimed_owner=OWNER,page_size=5)
        self.assertEqual(one["total"],1)
        self.assertEqual(allp["total"],2)

    def test_scope_specific_cursor_cannot_apply_globally(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        scoped=self.gate.page_pending(
            claimed_owner=OWNER,process=self.proc,page_size=1,
        )
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.page_pending(
                claimed_owner=OWNER,page_size=1,
                cursor=scoped["next_cursor"],
            )

    def test_coverage_rejects_missing_final_page(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        first=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        with self.assertRaisesRegex(ContractViolation,"PAGE_COVERAGE_INCOMPLETE"):
            verify_disposable_page_sequence((first,))

    def test_coverage_rejects_duplicate_page(self):
        self.seed()
        self.capture()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        first=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        with self.assertRaisesRegex(ContractViolation,"PAGE_COVERAGE_INCOMPLETE"):
            verify_disposable_page_sequence((first,first))

    def test_coverage_recheck_after_insertion_rejects_stale(self):
        self.seed()
        self.capture()
        pages=self.paginate()
        self.capture(ev=event(summary="DEMO: despacho de alvara municipal"))
        with self.assertRaisesRegex(ContractViolation,"PAGE_SNAPSHOT_STALE"):
            self.gate.confirm_current_coverage(
                claimed_owner=OWNER,pages=pages,
            )

    def test_coverage_owner_required(self):
        pages=self.paginate()
        with self.assertRaisesRegex(ContractViolation,"OWNER_REQUIRED"):
            self.gate.confirm_current_coverage(
                claimed_owner="OTHER",pages=pages,
            )

    def test_bad_scope_on_coverage_rejected(self):
        pages=self.paginate()
        with self.assertRaisesRegex(ContractViolation,"PAGE_SCOPE_MISMATCH"):
            self.gate.confirm_current_coverage(
                claimed_owner=OWNER,pages=pages,process=self.proc,
            )

    def test_candidate_pagination_does_not_create_memory(self):
        self.seed()
        self.capture()
        p=self.gate.page_pending(claimed_owner=OWNER,page_size=1)
        self.assertFalse(p["items"][0]["memory_approved"])
        proof=self.gate.confirm_current_coverage(
            claimed_owner=OWNER,pages=(p,),
        )
        self.assertFalse(proof["memory_approved"])
        self.assertFalse(proof["real_provider_coverage_verified"])


if __name__=="__main__":
    unittest.main()
