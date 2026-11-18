"""R07 isolated Skilldrum-inspired router tests; synthetic files, no network."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05 import skill_router as router


class SkillRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "skills"
        self.root.mkdir()
        paths = {"SKILL.md"} | {p for v in router._ROUTES.values() for p in v}
        for path in paths:
            f = self.root / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(("---\nname: demo\n---\n" if path == "SKILL.md" else "")
                         + f"SKILL DEMO MODULE {path}: "
                         + ("CONTEUDO SINTETICO. " * 40), encoding="utf-8")

    def route(self, mission="memory_search", namespace="chatgpt",
              process_id="DEMO-PROCESS-1"):
        return router.route(self.root, mission=mission, namespace=namespace,
                            process_id=process_id)

    def get_chunk(self, plan, file_index=1, **overrides):
        selected = plan["modules"][file_index]
        args = {
            "mission": plan["mission"], "namespace": plan["namespace"],
            "process_id": plan["process_id"], "route_sha256": plan["route_sha256"],
            "path": selected["path"], "expected_sha256": selected["sha256"],
            "max_chars": 100,
        }
        args.update(overrides)
        return router.read_selected(self.root, **args)

    def test_all_seven_missions_have_stable_file_order(self):
        self.assertEqual(len(router._ROUTES), 7)
        for name in router._ROUTES:
            plan = self.route(name)
            self.assertEqual(plan["status"], "READY_FOR_HOST_LOAD")
            self.assertEqual(plan["modules"][0]["path"], "SKILL.md")
            self.assertEqual(plan["modules"][0]["order"], 0)
            self.assertTrue(plan["modules"][1]["required"])
            self.assertFalse(plan["modules"][2]["required"])
            self.assertEqual(len(plan["route_sha256"]), 64)

    def test_selection_and_progressive_read_integrity(self):
        plan = self.route()
        selected = plan["modules"][1]
        chunks = []
        offset = 0
        while True:
            out = self.get_chunk(plan, offset=offset)
            chunks.append(out["content"])
            self.assertEqual(out["sha256"], selected["sha256"])
            self.assertFalse(out["host_activation_confirmed"])
            self.assertEqual(out["effects"], "none")
            if out["next_offset"] is None:
                break
            offset = out["next_offset"]
        self.assertEqual("".join(chunks),
                         (self.root / selected["path"]).read_text(encoding="utf-8"))

    def test_unknown_mission_fails_closed(self):
        plan = self.route("create_admin_user")
        self.assertEqual(plan["status"], "NO_ROUTE")
        self.assertEqual(plan["modules"], [])
        self.assertFalse(plan["authorization_granted"])
        self.assertFalse(plan["memory_write_permitted"])

    def test_unknown_mission_cannot_be_loaded(self):
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_NOT_FOUND"):
            router.read_selected(self.root, mission="create_admin_user",
                namespace="chatgpt", process_id="DEMO-PROCESS-1",
                route_sha256="0"*64, path="SKILL.md",
                expected_sha256="0"*64)

    def test_mismatched_scope_never_reuses_route_receipt(self):
        plan = self.route()
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            self.get_chunk(plan, process_id="DEMO-PROCESS-2")
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            self.get_chunk(plan, namespace="another")
        # Same authenticated GAIA owner may select another process explicitly;
        # process identifiers are locators and NOT per-client ACLs.
        second = self.route(process_id="DEMO-OTHER-CLIENT-PROCESS")
        self.assertNotEqual(second["route_sha256"], plan["route_sha256"])
        self.assertEqual(second["modules"][1]["sha256"],
                         plan["modules"][1]["sha256"])

    def test_other_module_cannot_be_loaded_under_selected_route(self):
        plan = self.route()
        other = self.route("memory_proposal")["modules"][1]
        with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_NOT_SELECTED"):
            self.get_chunk(plan, path=other["path"],
                           expected_sha256=other["sha256"])

    def test_digest_rejects_tampered_metadata(self):
        plan = self.route()
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            self.get_chunk(plan, route_sha256="f"*64)
        with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_VERSION_MISMATCH"):
            self.get_chunk(plan, expected_sha256="a"*64)

    def test_hash_drifts_when_file_modified(self):
        plan = self.route()
        f = self.root / plan["modules"][1]["path"]
        f.write_text(f.read_text() + "CHANGED", encoding="utf-8")
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            self.get_chunk(plan)
        new = self.route()
        self.assertNotEqual(plan["route_sha256"], new["route_sha256"])

    def test_symlinked_module_is_denied(self):
        plan = self.route()
        f = self.root / plan["modules"][1]["path"]
        fake = self.root / "other-file"
        fake.write_text("PUBLIC DEMO", encoding="utf-8")
        f.unlink()
        f.symlink_to(fake)
        with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_PATH_NOT_TRUSTED"):
            self.route()

    def test_symlinked_directory_is_denied(self):
        f = self.root / "references"
        real = self.root / "real-reference-folder"
        f.rename(real)
        f.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_PATH_NOT_TRUSTED"):
            self.route()

    def test_wrong_offset_and_chunk_size_rejected(self):
        plan = self.route()
        for change in ({"offset": -1}, {"offset": 1000001},
                       {"offset": True}, {"max_chars": 50},
                       {"max_chars": 3001}, {"max_chars": True}):
            with self.assertRaises(router.SkillRoutingError):
                self.get_chunk(plan, **change)

    def test_missing_module_has_explicit_error(self):
        f = self.root / self.route()["modules"][1]["path"]
        f.unlink()
        with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_MODULE_UNAVAILABLE"):
            self.route()

    def test_context_identifiers_reject_traversal_and_injection(self):
        for bad in ("../PRIVATE", "client/id", "", "x" * 151, "UPPER SPACE"):
            with self.assertRaisesRegex(router.SkillRoutingError, "INVALID_ROUTE_SCOPE"):
                self.route(process_id=bad)

    def test_no_automatic_saving_or_host_activation(self):
        plan = self.route("memory_proposal")
        self.assertTrue(plan["host_must_explicitly_load"])
        self.assertFalse(plan["memory_write_permitted"])
        self.assertFalse(plan["authorization_granted"])
        self.assertEqual(plan["effects"], "none")


if __name__ == "__main__":
    unittest.main()
