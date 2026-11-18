"""Synthetic unit tests of R07 preflight; no SSH, Docker or filesystem changes."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import r07_testlab_preflight as preflight

HEAD = "a" * 40
NAME = "gaia-rag-r07-testlab-synthetic"


class TestR07TestLabPreflight(unittest.TestCase):
    def test_parent_and_prefix_required(self):
        base = Path("/tmp/demo-parent")
        good = "/tmp/demo-parent/gaia-rag-r07-sandbox"
        self.assertEqual(preflight.safe_workspace(good, parent=base), Path(good))
        with self.assertRaisesRegex(ValueError, "NOT_R07_WORKSPACE"):
            preflight.safe_workspace("/tmp/demo-parent/gaia-rag-r06-sandbox", parent=base)
        with self.assertRaisesRegex(ValueError, "OUTSIDE_APPROVED"):
            preflight.safe_workspace("/tmp/other/gaia-rag-r07-sandbox", parent=base)

    def test_container_selection_is_restricted(self):
        self.assertEqual(preflight.safe_container_name(NAME), NAME)
        with self.assertRaisesRegex(ValueError, "NOT_R07_CONTAINER"):
            preflight.safe_container_name("gaia-rag-r06-preview")
        with self.assertRaisesRegex(ValueError, "INVALID_CONTAINER"):
            preflight.safe_container_name("gaia-rag-r07-;docker rm")

    def test_absent_workspace_fails_without_creating_anything(self):
        # Synthetic workspace: never access retired TestLab or /home/ubuntu.
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "gaia-rag-r07-nonexistent-synth")
            with patch.object(preflight, "safe_workspace", return_value=Path(path)):
                result = preflight.inspect(path, HEAD)
            self.assertFalse(result["workspace_present"])
            self.assertEqual(result["blockers"], ["R07_WORKSPACE_NOT_INSTALLED"])
            self.assertFalse(result["mutation_performed"])
            self.assertFalse(result["testlab_homologated"])

    def test_sha_must_be_exact(self):
        # Invalid SHA is tested without probing any real host directory.
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "gaia-rag-r07-unit")
            with patch.object(preflight, "safe_workspace", return_value=Path(path)):
                with self.assertRaisesRegex(ValueError, "INVALID_SHA"):
                    preflight.inspect(path, "not-a-sha")

    def test_matching_checkout_and_isolated_container(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "gaia-rag-r07-demo"
            folder.mkdir()
            responses = [
                (True, "true"), (True, HEAD),
                (True, "feat/r07-office-knowledge-assimilation"),
                (True, ""), (True, "true|none|true|{\"8000/tcp\":null}")
            ]
            with patch.object(preflight, "safe_workspace", return_value=folder), \
                 patch.object(preflight, "command", side_effect=responses):
                out = preflight.inspect(str(folder), HEAD, NAME)
            self.assertFalse(out["blockers"])
            self.assertTrue(out["container_running"])
            self.assertTrue(out["published_ports_absent"])
            self.assertTrue(out["working_tree_clean"])
            self.assertFalse(out["testlab_homologated"])

    def test_nonisolated_container_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "gaia-rag-r07-demo"
            folder.mkdir()
            responses = [
                (True, "true"), (True, HEAD),
                (True, "feat/r07-office-knowledge-assimilation"),
                (True, ""), (True, "true|bridge|false|{\"8000/tcp\":[{\"HostPort\":\"8000\"}]}")
            ]
            with patch.object(preflight, "safe_workspace", return_value=folder), \
                 patch.object(preflight, "command", side_effect=responses):
                out = preflight.inspect(str(folder), HEAD, NAME)
            self.assertIn("R07_NETWORK_NOT_ISOLATED", out["blockers"])
            self.assertIn("R07_ROOTFS_NOT_READONLY", out["blockers"])
            self.assertIn("R07_PUBLIC_PORTS_PRESENT", out["blockers"])


if __name__ == "__main__":
    unittest.main()
