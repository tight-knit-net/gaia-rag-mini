"""S9 lock integrity negatives, without networking or real credentials."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from r07_s9_wheel_lock import read_hash_lock, parse_pinned

LOCK=(Path(__file__).resolve().parents[1]/"requirements.lock").read_text(encoding="utf-8")


class WheelLockTests(unittest.TestCase):
    def test_all_29_pinned_wheels_have_sha256(self):
        hashes=read_hash_lock(LOCK)
        self.assertEqual(len(hashes),29)
        self.assertTrue(all(len(v)==64 for v in hashes.values()))

    def test_exact_names_versions_remain_pinned(self):
        entries=parse_pinned(LOCK)
        self.assertEqual(len(entries),29)
        self.assertIn(("mcp==1.30.0","mcp"),entries)
        self.assertIn(("PyJWT[crypto]==2.15.1","pyjwt"),entries)

    def test_one_missing_hash_denied(self):
        lines=LOCK.splitlines()
        i=next(i for i,l in enumerate(lines) if l.startswith("anyio=="))
        lines[i]=lines[i].split(" --hash=")[0]
        with self.assertRaisesRegex(ValueError,"UNHASHED"):
            read_hash_lock("\n".join(lines))

    def test_hash_tamper_or_uppercase_denied(self):
        edited=LOCK.replace("--hash=sha256:","--hash=sha256:Z",1)
        with self.assertRaisesRegex(ValueError,"UNHASHED"):
            read_hash_lock(edited)

    def test_duplicate_package_denied(self):
        item=next(l for l in LOCK.splitlines() if l.startswith("mcp=="))
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            read_hash_lock(LOCK+"\n"+item+"\n")

    def test_incomplete_package_set_denied(self):
        original=LOCK.splitlines()
        modified=[x for x in original if not x.startswith("uvicorn==")]
        with self.assertRaisesRegex(ValueError,"WRONG_LOCK_COUNT"):
            read_hash_lock("\n".join(modified))


if __name__=="__main__":
    unittest.main()
