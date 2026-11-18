"""Synthetic R07 lifecycle tests; no network, clients, remote writes or keys."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05 import lifecycle_read as mod

PROC = "DEMO-CLIENT-009-TEST"
NS = "chatgpt"


class Reader:
    def __init__(self, entries):
        self.entries = entries
        self.calls = []

    def list_process(self, capability, limit=30, offset=None):
        self.calls.append((capability, limit, offset))
        idx = int(offset or 0)
        page = self.entries[idx:idx + limit]
        end = idx + len(page)
        return {"items": page, "next_offset": str(end) if end < len(self.entries) else None}


def point(i, at=None):
    return {"id": f"id-{i}", "process_id": PROC, "namespace": NS,
            "approved": True, "title": f"DEMO {i}",
            "text": f"Texto fictício {i}", "source_ref": f"DEMO-SOURCE-{i}",
            "approved_at": at}


class LifecycleReadTests(unittest.TestCase):
    def test_all_pages_covered(self):
        r = Reader([point(i) for i in range(4)])
        x = mod.collect_process(r, object(), max_items=5, page_size=2)
        self.assertTrue(x["complete"])
        self.assertEqual(len(x["items"]), 4)
        self.assertEqual(len(r.calls), 2)

    def test_partial_coverage_cursor(self):
        r = Reader([point(i) for i in range(4)])
        x = mod.collect_process(r, object(), max_items=3, page_size=2)
        self.assertFalse(x["complete"])
        self.assertEqual(x["next_offset"], "3")
        self.assertEqual(len(x["items"]), 3)

    def test_repeated_point_is_rejected(self):
        r = Reader([point(1), point(1)])
        with self.assertRaisesRegex(RuntimeError, "REPEATED_POINT"):
            mod.collect_process(r, object())

    def test_timeline_sorts_and_marks_missing_date(self):
        r = Reader([point(1, 400), point(2, None), point(3, 800)])
        a = mod.process_timeline(r, object())
        self.assertEqual([x["point_id"] for x in a["items"]],
                         ["id-3", "id-1", "id-2"])
        self.assertFalse(a["truncated"])

    def test_export_hash_reproducible_and_partial(self):
        r = Reader([point(i) for i in range(3)])
        a = mod.process_export(r, object(), max_items=2)
        self.assertTrue(a["truncated"])
        self.assertEqual(a["next_offset"], "2")
        b = mod.process_export(Reader([point(i) for i in range(3)]),
                               object(), max_items=2, offset=a["next_offset"])
        self.assertEqual(b["count"], 1)
        self.assertFalse(b["truncated"])
        self.assertEqual([x["id"] for x in b["entries"]], ["id-2"])
        self.assertEqual(a["sha256"], mod.process_export(Reader([point(i) for i in range(3)]),
                                                        object(), max_items=2)["sha256"])
        self.assertEqual(a["format"], "gaia-approved-memory-json-v1")

    def test_index_preview_has_no_write_or_external_call(self):
        x = mod.index_candidate_preview(
            process_id=PROC, title="Triagem documental",
            summary="Fluxo de conferencia de contratos e procurações, pendência de assinatura.",
            source_ref="DEMO-SOURCE-1")
        self.assertFalse(x["automatic_save"])
        self.assertFalse(x["persisted"])
        self.assertFalse(x["external_llm_used"])
        self.assertEqual(x["suggested_kind"], "procedimento")
        self.assertTrue(x["human_memory_approval_required"])
        self.assertTrue(x["suggested_tags"])

    def test_index_blocks_unverified_facts(self):
        x = mod.index_candidate_preview(
            process_id=PROC, title="Alegação", summary="Hipótese não comprovada.",
            source_ref="DEMO-SOURCE-1", evidence_status="alegada")
        self.assertFalse(x["recommend_review"])
        with self.assertRaisesRegex(ValueError, "INVALID_EVIDENCE_STATUS"):
            mod.index_candidate_preview(
                process_id=PROC, title="A", summary="B", source_ref="S",
                evidence_status="confirmada_pela_IA")

    def test_absent_review_db_is_not_zero_statistic(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "missing.sqlite"
            with patch.dict(os.environ, {"GAIA_RAG_REVIEW_DB": str(path)}):
                self.assertFalse(mod.proposal_statistics(NS)["storage_available"])
                self.assertIsNone(mod.proposal_statistics(NS)["proposal_counts"])
                self.assertFalse(mod.pending_reviews(NS, PROC)["storage_available"])
                self.assertFalse(mod.approval_events(NS)["storage_available"])
                self.assertFalse(path.exists())

    def test_pending_audit_and_stats_are_read_only(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "reviews.sqlite"
            with sqlite3.connect(db) as c:
                c.executescript("""
                CREATE TABLE proposals (
                    id TEXT PRIMARY KEY, title TEXT, status TEXT, namespace TEXT,
                    process_id TEXT, created_at INTEGER, expires_at INTEGER);
                CREATE TABLE audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER,
                    proposal_id TEXT, event TEXT, actor TEXT);
                INSERT INTO proposals VALUES
                  ('p1','Pending','pending','chatgpt','DEMO-CLIENT-009-TEST',100,200),
                  ('p2','Approved','approved','chatgpt','DEMO-CLIENT-009-TEST',101,201),
                  ('p3','Other case','pending','chatgpt','DEMO-OTHER',102,202);
                INSERT INTO audit(at,proposal_id,event,actor)
                  VALUES (103,'p1','proposal_prepared','DEMO-ACTOR');
                """)
            before = db.read_bytes()
            with patch.dict(os.environ, {"GAIA_RAG_REVIEW_DB": str(db)}):
                pending = mod.pending_reviews(NS, PROC)
                stats = mod.proposal_statistics(NS, process_id=PROC)
                audit = mod.approval_events(NS, process_id=PROC)
            self.assertEqual([p["id"] for p in pending["proposals"]], ["p1"])
            self.assertTrue(pending["storage_available"])
            self.assertEqual(stats["proposal_counts"]["pending"], 1)
            self.assertEqual(stats["proposal_counts"]["approved"], 1)
            self.assertEqual(len(audit["events"]), 1)
            self.assertEqual(db.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
