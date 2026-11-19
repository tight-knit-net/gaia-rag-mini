"""R07 S7 SQLite backup/restore simulation with disposable synthetic ledger.

ONLY TemporaryDirectory paths. Never connect to external Qdrant, TestLab,
Cloudflare, production services or real customer documents.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
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


def fingerprint(conn: sqlite3.Connection) -> str:
    rows = [tuple(x) for x in conn.execute(
        "SELECT id,namespace,process_id,source_ref,status,point_id "
        "FROM proposals ORDER BY id"
    )]
    events = [tuple(x) for x in conn.execute(
        "SELECT proposal_id,event,actor FROM audit ORDER BY id"
    )]
    raw = json.dumps([rows, events], ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gaia-r07-s7-demo-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "synthetic-ledger.sqlite3"
        self.patcher = patch.dict(os.environ, {"GAIA_RAG_REVIEW_DB": str(self.db)})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        with closing(review._connect()) as db:
            now = review._now()
            for n, status in enumerate(("pending", "approved", "discarded"), start=1):
                proposal = str(uuid.uuid4())
                db.execute(
                    """INSERT INTO proposals(
                        id,identity_key,namespace,tenant_id,process_id,created_by,
                        title,summary,source_ref,document_approval_ref,
                        document_sha256,point_id,status,created_at,expires_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (proposal, f"S7-DEMO-{n}", "gaia-demo", "S7-DEMO-CLIENT",
                     "S7-DEMO-ADMIN-PROCESS", "owner@example.invalid",
                     "Synthetic demo", f"Fake value {n}", "DEMO-DOCUMENT",
                     "S7-DEMO-APPROVAL", "a"*64, str(uuid.uuid4()), status,
                     now - 10, now + 3600),
                )
                db.execute("INSERT INTO audit(at,proposal_id,event,actor) "
                           "VALUES(?,?,?,?)",
                           (now, proposal, "synthetic_" + status,
                            "owner@example.invalid"))

    def backup(self) -> tuple[Path, str]:
        snapshot = self.root / "snapshot.sqlite3"
        with closing(sqlite3.connect(self.db)) as source, closing(
            sqlite3.connect(snapshot)
        ) as target:
            expected = fingerprint(source)
            # SQLite online backup includes already-committed WAL transactions.
            source.backup(target)
            self.assertEqual(target.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(fingerprint(target), expected)
        return snapshot, expected

    def test_online_backup_wal_integrity_and_no_state_promotion(self):
        snap, expected = self.backup()
        self.assertTrue(snap.is_file())
        with closing(sqlite3.connect(snap)) as db:
            self.assertEqual(fingerprint(db), expected)
            status_counts = dict(db.execute(
                "SELECT status,COUNT(*) FROM proposals GROUP BY status"
            ).fetchall())
        self.assertEqual(status_counts,
                         {"pending": 1, "approved": 1, "discarded": 1})

    def test_isolated_restore_reverts_synthetic_mutation(self):
        snap, expected = self.backup()
        with closing(sqlite3.connect(self.db)) as active:
            active.execute("UPDATE proposals SET status='discarded' WHERE status='pending'")
            active.commit()
            self.assertNotEqual(fingerprint(active), expected)
        restored = self.root / "restored.sqlite3"
        with closing(sqlite3.connect(snap)) as source, closing(
            sqlite3.connect(restored)
        ) as dest:
            source.backup(dest)
            self.assertEqual(fingerprint(dest), expected)
            self.assertEqual(dest.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        with closing(sqlite3.connect(self.db)) as active:
            self.assertNotEqual(fingerprint(active), expected)
        # No overwrite of active state occurred. Operator-controlled cutover is separate.

    def test_missing_snapshot_refused(self):
        missing = self.root / "missing.sqlite3"
        self.assertFalse(missing.exists())
        with self.assertRaises(sqlite3.OperationalError):
            sqlite3.connect(f"file:{missing}?mode=ro", uri=True)
        self.assertFalse(missing.exists())

    def test_corrupt_snapshot_refused_without_touching_original(self):
        _, expected = self.backup()
        invalid = self.root / "invalid.sqlite3"
        invalid.write_bytes(b"S7-DEMO-NOT-A-SQLITE-BACKUP")
        with closing(sqlite3.connect(invalid)) as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("PRAGMA integrity_check").fetchone()
        with closing(sqlite3.connect(self.db)) as active:
            self.assertEqual(fingerprint(active), expected)

    def test_no_real_paths_or_credentials(self):
        self.assertTrue(self.db.is_relative_to(self.root))
        self.assertFalse(any(p.name.startswith("QDRANT") for p in self.root.iterdir()))
        self.assertTrue(str(self.db).startswith(str(self.root)))


if __name__ == "__main__":
    unittest.main()
