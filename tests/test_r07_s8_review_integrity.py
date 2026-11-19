"""S8: approved memory replay must re-read actual synthetic Qdrant point."""
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
from gaia_rag_r05.authz import OwnerAuthorizer, Principal, Scope

OWNER = "owner@example.invalid"
ISS = "https://synthetic.cloudflareaccess.com"
AUD = "R07-DEMO-AUD-APPROVAL"
NS = "r07-demo"
PROC = "FAKE-ADMIN-REVIEW-PROCESS"
SHA = "a" * 64


class ApprovedReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "demo.sqlite3"
        self.env = patch.dict(os.environ, {
            "GAIA_RAG_REVIEW_DB": str(self.path),
            "GAIA_RAG_CSRF_SECRET": "R07-S8-FICTITIOUS-CSRF-SECRET-" + "X" * 40,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        authorizer = OwnerAuthorizer([OWNER], expected_issuer=ISS,
                                     expected_audience=AUD)
        actor = Principal(OWNER, ISS, AUD)
        self.authorize = lambda ns, tenant, proc: authorizer.require(
            actor, Scope(ns, "owner-all", proc))
        self.proposal = str(uuid.uuid4())
        self.point = str(uuid.uuid4())
        with closing(review._connect()) as db:
            now = review._now()
            db.execute("""INSERT INTO proposals
              (id,identity_key,namespace,tenant_id,process_id,created_by,title,
               summary,source_ref,document_approval_ref,document_sha256,
               point_id,status,created_at,expires_at,approved_by,approved_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (self.proposal, "DEMO-KEY-" + self.proposal, NS, "FAKE-CLIENT",
                 PROC, OWNER, "Title Demo", "Synthetic content",
                 "DEMO-SOURCE", "DEMO-APPROVAL", SHA, self.point,
                 "approved", now-3600, now+3600, OWNER, now-100))

    def verified(self):
        return {"found": True, "item": {
            "id": self.point, "namespace": NS,
            "process_id": PROC, "approved": True,
            "text": "Synthetic content", "source_ref": "DEMO-SOURCE",
            "document_approval_ref": "DEMO-APPROVAL", "document_sha256": SHA,
        }}

    def replay(self, read_point):
        def forbidden_write(_id, _payload):
            raise AssertionError("REPLAY_ATTEMPTED_TO_WRITE")
        return review.approve(
            self.proposal, OWNER, self.authorize,
            review.csrf_token(self.proposal, OWNER),
            forbidden_write, read_point)

    def test_replayed_approval_performs_fresh_qdrant_readback(self):
        reads = []
        def read(_cap, point):
            reads.append(point)
            return self.verified()
        result = self.replay(read)
        self.assertEqual(result["point_id"], self.point)
        self.assertTrue(result["replayed"])
        self.assertEqual(reads, [self.point])

    def test_missing_point_never_claims_saved(self):
        with self.assertRaisesRegex(RuntimeError, "APPROVED_POINT_READBACK_UNCONFIRMED"):
            self.replay(lambda *_: {"found": False})

    def test_unapproved_or_other_process_never_claims_saved(self):
        for field, value in (
            ("approved", False),
            ("process_id", "OTHER-PROCESS"),
            ("namespace", "OTHER-NS"),
            ("id", str(uuid.uuid4())),
            ("source_ref", "REPLACED"),
        ):
            item = self.verified()
            item["item"][field] = value
            with self.subTest(field=field):
                with self.assertRaisesRegex(RuntimeError, "APPROVED_POINT_READBACK_UNCONFIRMED"):
                    self.replay(lambda *_, item=item: item)

    def test_malformed_readback_never_claims_saved(self):
        with self.assertRaisesRegex(RuntimeError, "APPROVED_POINT_READBACK_UNCONFIRMED"):
            self.replay(lambda *_: None)

    def test_discrepant_document_provenance_never_claims_saved(self):
        for key, value in (
            ("document_sha256", "0"*64),
            ("document_approval_ref", "WRONG"),
            ("text", "WRONG"),
        ):
            bad = self.verified()
            bad["item"][key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(RuntimeError, "APPROVED_POINT_READBACK_UNCONFIRMED"):
                    self.replay(lambda *_, bad=bad: bad)

    def test_no_mutation_on_failed_replay(self):
        with self.assertRaises(RuntimeError):
            self.replay(lambda *_: {"found": False})
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT status FROM proposals").fetchone()[0],
                             "approved")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
