"""S6 security regression for proposal review and legacy SQLite compatibility.

Synthetic-only: no Cloudflare, no real Qdrant, no external provider or TestLab.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
import uuid
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05 import review
from gaia_rag_r05.authz import OwnerAuthorizer, Principal, Scope, AccessDenied

NS = "gaia-demo"
PROC = "S6-FAKE-ADMIN-PROCESS"
ACTOR = "owner@example.invalid"
ISSUER = "https://gaia-demo.cloudflareaccess.com"
AUD = "DEMO-R07-S6-AUDIENCE"
SECRET = "S6-SYNTHETIC-LONG-CSRF-SECRET-DO-NOT-USE-IN-PRODUCTION-1234"


class ReviewS6Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "synthetic-reviews.sqlite"
        self.env = patch.dict(os.environ, {
            "GAIA_RAG_REVIEW_DB": str(self.db),
            "GAIA_RAG_CSRF_SECRET": SECRET,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        principal = Principal(ACTOR, ISSUER, AUD)
        authorizer = OwnerAuthorizer(
            [ACTOR], expected_issuer=ISSUER, expected_audience=AUD)
        self.authorize = lambda namespace, tenant, process: authorizer.require(
            principal, Scope(namespace, "owner-all", process))

    def _insert(self, db: sqlite3.Connection, *, expired: bool = False) -> str:
        ident = str(uuid.uuid4())
        now = review._now()
        db.execute(
            """INSERT INTO proposals(
                id,identity_key,namespace,tenant_id,process_id,created_by,title,
                summary,source_ref,document_approval_ref,document_sha256,
                point_id,status,created_at,expires_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ident, "test-" + ident, NS, "FAKE-CLIENT-001", PROC, ACTOR,
                "DEMO checklist", "Somente dados fictícios",
                "DEMO-SOURCE", "DEMO-DOC-APPROVED", "a"*64, str(uuid.uuid4()),
                "pending", now - 120, now - 1 if expired else now + 3600
            ),
        )
        return ident

    def test_fresh_schema_discard_is_human_csrf_and_idempotent(self):
        with closing(review._connect()) as db:
            self.assertTrue(review._ledger_supports_discard(db))
            ident = self._insert(db)
            result = review.discard(
                ident, ACTOR, self.authorize, review.csrf_token(ident, ACTOR))
            self.assertTrue(result["discarded"])
            self.assertFalse(result["replayed"])
            with closing(sqlite3.connect(self.db)) as check:
                state = check.execute("SELECT status FROM proposals WHERE id=?",
                                      (ident,)).fetchone()[0]
                events = check.execute(
                    "SELECT event FROM audit WHERE proposal_id=?", (ident,)
                ).fetchall()
            self.assertEqual(state, "discarded")
            self.assertEqual(events, [("human_discarded",)])
            replay = review.discard(
                ident, ACTOR, self.authorize, review.csrf_token(ident, ACTOR))
            self.assertTrue(replay["replayed"])
            with closing(sqlite3.connect(self.db)) as check:
                count = check.execute(
                    "SELECT COUNT(*) FROM audit WHERE proposal_id=?",
                    (ident,)).fetchone()[0]
            self.assertEqual(count, 1)

    def test_expired_proposal_rejected_even_with_fresh_csrf(self):
        with closing(review._connect()) as db:
            ident = self._insert(db, expired=True)
        with self.assertRaisesRegex(AccessDenied, "DISCARD_NOT_PENDING"):
            review.discard(
                ident, ACTOR, self.authorize, review.csrf_token(ident, ACTOR))
        with closing(sqlite3.connect(self.db)) as check:
            status = check.execute(
                "SELECT status FROM proposals WHERE id=?", (ident,)).fetchone()[0]
        self.assertEqual(status, "pending")

    def test_legacy_schema_requires_separate_migration_without_mutation(self):
        with closing(sqlite3.connect(self.db)) as db:
            db.executescript("""
                CREATE TABLE proposals (
                    id TEXT PRIMARY KEY, identity_key TEXT UNIQUE,
                    namespace TEXT, tenant_id TEXT, process_id TEXT,
                    created_by TEXT, title TEXT, summary TEXT,
                    source_ref TEXT, document_approval_ref TEXT,
                    document_sha256 TEXT, point_id TEXT UNIQUE,
                    status TEXT CHECK(status IN ('pending','approving','approved')),
                    created_at INTEGER, expires_at INTEGER,
                    approved_by TEXT, approved_at INTEGER
                );
                CREATE TABLE audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER,
                    proposal_id TEXT, event TEXT, actor TEXT
                );
            """)
            ident = self._insert(db)
        with closing(review._connect()) as read:
            self.assertFalse(review._ledger_supports_discard(read))
        with self.assertRaisesRegex(AccessDenied, "DISCARD_SCHEMA_MIGRATION_REQUIRED"):
            review.discard(
                ident, ACTOR, self.authorize, review.csrf_token(ident, ACTOR))
        with closing(sqlite3.connect(self.db)) as check:
            status = check.execute(
                "SELECT status FROM proposals WHERE id=?", (ident,)).fetchone()[0]
            schema = check.execute(
                "SELECT sql FROM sqlite_master WHERE name='proposals'"
            ).fetchone()[0]
            count = check.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
        self.assertEqual(status, "pending")
        self.assertEqual(count, 0)
        self.assertNotIn("'discarded'", schema)

    def test_nonowner_denied_by_authoritative_registry(self):
        outsider = Principal("outsider@example.invalid", ISSUER, AUD)
        owners = OwnerAuthorizer(
            [ACTOR], expected_issuer=ISSUER, expected_audience=AUD)
        with self.assertRaisesRegex(AccessDenied, "ACCESS_DENIED"):
            owners.require(outsider, Scope(NS, "owner-all", PROC))

    def test_review_csrf_forgery_is_rejected(self):
        with closing(review._connect()) as db:
            ident = self._insert(db)
        with self.assertRaisesRegex(AccessDenied, "CSRF_DENIED"):
            review.discard(ident, ACTOR, self.authorize, "forged")
        with closing(sqlite3.connect(self.db)) as check:
            status = check.execute(
                "SELECT status FROM proposals WHERE id=?", (ident,)).fetchone()[0]
        self.assertEqual(status, "pending")


if __name__ == "__main__":
    unittest.main()
