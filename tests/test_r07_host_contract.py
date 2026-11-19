"""S5: synthetic host-side consumer of R07 MCP skill routing.

Exercises host-initiated discovery -> explicit selection -> chunk retrieval ->
independent SHA-256 verification. This does NOT load a skill in ChatGPT Work,
which is a separate operational gate. No external network, client data, secret
or memory persistence.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaia_rag_r05 import skill_router as router

NS = "chatgpt"
PROC = "DEMO-PROCESS-009"
OTHER = "DEMO-PROCESS-010"


class SyntheticHost:
    """Demonstration contract, not a server-side capability nor a host plugin."""
    def __init__(self, root: Path, *, authenticated: bool = True):
        self.root, self.authenticated = root, authenticated
        self.calls = []
        self.loaded = {}

    def select(self, mission: str, process_id: str = PROC):
        if not self.authenticated:
            raise PermissionError("HOST_UNAUTHENTICATED")
        self.calls.append(("select", mission, process_id))
        return router.route(self.root, mission=mission,
                            namespace=NS, process_id=process_id)

    def explicit_load(self, plan: dict, *, include_optional: bool = False):
        if not self.authenticated:
            raise PermissionError("HOST_UNAUTHENTICATED")
        if plan.get("status") != "READY_FOR_HOST_LOAD":
            raise RuntimeError("HOST_NO_ROUTE")
        if plan.get("host_must_explicitly_load") is not True:
            raise RuntimeError("HOST_AUTO_ACTIVATION_NOT_SUPPORTED")
        if plan.get("memory_write_permitted") is not False:
            raise RuntimeError("HOST_WRITE_PERMISSION_NOT_SUPPORTED")
        entries = plan["modules"] if include_optional else [
            x for x in plan["modules"] if x["required"]
        ]
        loaded = {}
        for item in entries:
            offset = 0
            chunks = []
            while True:
                result = router.read_selected(
                    self.root, mission=plan["mission"],
                    namespace=plan["namespace"],
                    process_id=plan["process_id"],
                    route_sha256=plan["route_sha256"],
                    expected_sha256=item["sha256"], path=item["path"],
                    offset=offset, max_chars=127,
                )
                self.calls.append(("read", item["path"], offset))
                assert result["host_activation_confirmed"] is False
                assert result["effects"] == "none"
                chunks.append(result["content"])
                next_offset = result["next_offset"]
                if next_offset is None:
                    break
                assert next_offset > offset
                offset = next_offset
            content = "".join(chunks)
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != item["sha256"]:
                raise RuntimeError("HOST_SHA_MISMATCH")
            loaded[item["path"]] = content
        self.loaded.update(loaded)
        return loaded


class HostContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "skill"
        self.root.mkdir()
        paths = {"SKILL.md"} | {x for paths in router._ROUTES.values() for x in paths}
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            # Unicode and long content exercise code-point offsets.
            path.write_text(
                "---\nname: gaia-rag-processos-administrativos\n---\n"
                + "Prévia sintética — não autoriza gravação. " * 18
                + relative, encoding="utf-8")

    def test_host_must_explicitly_load_modules(self):
        host = SyntheticHost(self.root)
        plan = host.select("memory_search")
        self.assertEqual(host.loaded, {})
        self.assertEqual([x[0] for x in host.calls], ["select"])
        loaded = host.explicit_load(plan)
        self.assertEqual(set(loaded), {"SKILL.md", "references/02-recuperacao.md"})
        self.assertGreater(len(host.calls), 3)
        self.assertTrue(all("não autoriza gravação" in s for s in loaded.values()))

    def test_optional_module_is_loaded_only_when_requested(self):
        host = SyntheticHost(self.root)
        plan = host.select("memory_proposal")
        required = host.explicit_load(plan)
        self.assertNotIn("references/05-esquema-logico.md", required)
        all_modules = host.explicit_load(plan, include_optional=True)
        self.assertEqual(set(all_modules),
                         {m["path"] for m in plan["modules"]})

    def test_explicit_host_load_of_seven_registered_missions(self):
        host = SyntheticHost(self.root)
        for mission in router._ROUTES:
            plan = host.select(mission)
            loaded = host.explicit_load(plan)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(len(plan["modules"]), 3)

    def test_unknown_mission_never_loads_content(self):
        host = SyntheticHost(self.root)
        plan = host.select("delete_memory_without_approval")
        self.assertEqual(plan["status"], "NO_ROUTE")
        with self.assertRaisesRegex(RuntimeError, "HOST_NO_ROUTE"):
            host.explicit_load(plan)
        self.assertEqual(host.loaded, {})

    def test_no_bypass_of_identity_in_host_emulator(self):
        host = SyntheticHost(self.root, authenticated=False)
        with self.assertRaisesRegex(PermissionError, "HOST_UNAUTHENTICATED"):
            host.select("memory_search")
        good_plan = router.route(self.root, mission="memory_search",
                                 namespace=NS, process_id=PROC)
        with self.assertRaisesRegex(PermissionError, "HOST_UNAUTHENTICATED"):
            host.explicit_load(good_plan)

    def test_stale_manifest_cannot_be_loaded(self):
        host = SyntheticHost(self.root)
        plan = host.select("memory_search")
        path = self.root / plan["modules"][1]["path"]
        path.write_text(path.read_text(encoding="utf-8") + "TROCA", encoding="utf-8")
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            host.explicit_load(plan)

    def test_concurrent_file_drift_between_selection_and_read_is_rejected(self):
        plan = router.route(self.root, mission="memory_search",
                            namespace=NS, process_id=PROC)
        real_reader = router._read_installed
        count = 0
        target = plan["modules"][1]["path"]

        def altered(root, rel):
            nonlocal count
            original = real_reader(root, rel)
            if rel == target:
                count += 1
                if count >= 2:
                    return original + b"CHANGED_AFTER_ROUTE"
            return original

        with patch.object(router, "_read_installed", side_effect=altered):
            with self.assertRaisesRegex(router.SkillRoutingError, "SKILL_CONTENT_DRIFT"):
                router.read_selected(
                    self.root, mission=plan["mission"],
                    process_id=PROC, namespace=NS,
                    route_sha256=plan["route_sha256"],
                    path=target, expected_sha256=plan["modules"][1]["sha256"],
                )

    def test_context_binding_rejects_wrong_process(self):
        plan = SyntheticHost(self.root).select("memory_search", process_id=PROC)
        with self.assertRaisesRegex(router.SkillRoutingError, "ROUTE_VERSION_MISMATCH"):
            router.read_selected(
                self.root, mission="memory_search", process_id=OTHER,
                namespace=NS, route_sha256=plan["route_sha256"],
                path=plan["modules"][1]["path"],
                expected_sha256=plan["modules"][1]["sha256"],
            )

    def test_host_loader_does_not_activate_or_save_memory(self):
        host = SyntheticHost(self.root)
        plan = host.select("memory_assimilation")
        host.explicit_load(plan)
        self.assertFalse(plan["authorization_granted"])
        self.assertFalse(plan["memory_write_permitted"])
        self.assertTrue(plan["host_must_explicitly_load"])
        self.assertTrue(all(action[0] in ("select", "read") for action in host.calls))


if __name__ == "__main__":
    unittest.main()
