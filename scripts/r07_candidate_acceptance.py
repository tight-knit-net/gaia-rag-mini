"""R07 candidate acceptance: CI-only structural policy, never operational deployment.

Run only after validate, staging_image_smoke, r06_lifecycle_synthetic, and
r07_operational_isolated have succeeded. This read-only check cannot approve
migration, human memory writes, production deployment, or legacy shutdown.
"""
from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path


REQUIRED_TOOLS = {
    "memory_status",
    "memory_policy",
    "memory_list_process",
    "memory_search",
    "memory_search_all",
    "memory_get",
    "memory_find_by_source",
    "memory_similar_cases",
    "memory_assimilation_preview",
    "memory_index_preview",
    "memory_auto_prepare",
    "memory_prepare_after_approval",
    "memory_proposal_preview",
    "memory_pending_reviews",
    "memory_discard_proposal",
    "memory_approval_audit",
    "memory_export_process",
    "memory_process_timeline",
    "memory_stats",
    "gaia_skill_catalog",
    "gaia_skill_read",
    "gaia_skill_read_chunk",
    "gaia_skill_route",
    "gaia_skill_route_read",
}
REQUIRED_TESTS = (
    "tests/test_institutional_memory.py",
    "tests/test_lifecycle_read.py",
    "tests/test_migration_manifest.py",
    "tests/r06_live_review_e2e.py",
    "tests/r07_isolated_runtime_smoke.sh",
    "tests/test_r07_skill_router.py",
    "tests/test_r07_host_contract.py",
    "tests/test_r07_s6_security.py",
    "tests/test_r07_s7_recovery.py",
    "tests/test_r07_s8_supplychain.py",
    "tests/test_r07_s8_snapshot_contract.py",
    "tests/test_r07_s8_review_integrity.py",
)
REQUIRED_DOCS = (
    "docs/institucional/PLANO_VALIDACAO_R07.md",
    "docs/institucional/PLANO_FECHAMENTO_GAPS_E_CUTOVER_R07_2026-11-18.md",
    "skills/gaia-rag-processos-administrativos/references/10-assimilacao-institucional.md",
)


def tools_declared(source: str) -> set[str]:
    tree = ast.parse(source, filename="app/server.py")
    declared: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "mcp"
            and dec.func.attr == "tool"
            for dec in node.decorator_list
        ):
            declared.add(node.name)
    return declared


def owner_check_on_skill_handlers(source: str) -> bool:
    """Require explicit owner check inside every exposed skill reader/resource."""
    tree = ast.parse(source, filename="app/server.py")
    required = {
        "gaia_skill_catalog", "gaia_skill_read", "gaia_skill_read_chunk",
        "gaia_skill_resource_root", "gaia_skill_resource_retrieval",
        "gaia_skill_resource_proposal",
    }
    checks = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in required:
            continue
        checks[node.name] = any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == "_require"
            and len(item.args) >= 2
            and all(isinstance(arg, ast.Constant) for arg in item.args[:2])
            and [arg.value for arg in item.args[:2]] == ["chatgpt", "all-processes"]
            for item in ast.walk(node)
        )
    return set(checks) == required and all(checks.values())

def evaluate(root: Path) -> dict:
    checks: dict[str, bool] = {}
    app = (root / "app/server.py").read_text(encoding="utf-8")
    review = (root / "src/gaia_rag_r05/review.py").read_text(encoding="utf-8")
    router = (root / "src/gaia_rag_r05/skill_router.py").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/r05-skill-static.yml").read_text(encoding="utf-8")
    ghcr = (root / ".github/workflows/rag-ghcr-image.yml").read_text(encoding="utf-8")
    linode = (root / ".github/workflows/rag-linode-staging.yml").read_text(encoding="utf-8")

    checks["mcp_tools_present"] = REQUIRED_TOOLS <= tools_declared(app)
    checks["human_approval_route_present"] = (
        'Route("/review/{proposal_id}/approve"' in app
        and 'name="confirm" value="APROVAR"' in app
        and "def approve(" in review
        and "verify_csrf(" in review
        and "confirmed=read_point(" in review
    )
    checks["manual_discard_route_present"] = (
        'Route("/review/{proposal_id}/discard"' in app
        and 'name="confirm" value="DESCARTAR"' in app
        and "def discard(" in review
    )
    checks["runtime_candidate_identified"] = '"gaia-rag-mini-r07"' in app
    checks["review_off_without_explicit_flag"] = (
        'os.getenv("GAIA_RAG_ENABLE_REVIEW") == "1"' in app
        and '"ready_for_real_data": False' in app
    )
    checks["qdrant_write_behind_review"] = (
        "def _write_point(" in app
        and "def review_post(" in app
        and "review.approve(" in app
        and "GAIA_RAG_ENABLE_REVIEW" in app
    )
    checks["groq_api_not_activated"] = (
        "api.groq.com" not in app
        and "GROQ_API_KEY" not in app
        and "api.groq.com" not in review
        and "GROQ_API_KEY" not in review
    )
    checks["protected_ci_jobs_exist"] = all(
        marker in workflow for marker in (
            "  validate:", "  staging_image_smoke:",
            "  r06_lifecycle_synthetic:", "  r07_operational_isolated:",
            "  r07_candidate_acceptance:",
            "  r07_skill_router_synthetic:",
            "  r07_host_contract_synthetic:",
            "  r07_s6_security:",
            "  r07_s7_package:",
            "  r07_s7_sqlite_recovery:",
            "  r07_s8_supplychain:",
            "  r07_s8_review_and_snapshot:",
        )
    )
    checks["no_image_publication"] = (
        "if: " + "${{ false }}" in ghcr
        and "if: " + "${{ false }}" in linode
        and "actions/upload-artifact@" not in workflow
    )
    checks["skill_owner_only_on_all_read_endpoints"] = owner_check_on_skill_handlers(app)
    checks["skill_paths_are_checked_without_symlink_following"] = (
        "def _safe_installed_skill_bytes(" in app
        and "target.is_symlink()" in app
        and "_safe_installed_skill_bytes(path)" in app
        and "_safe_installed_skill_bytes(rel)" in app
    )
    checks["sqlite_connections_closed_and_legacy_discards_blocked"] = (
        "with closing(_connect()) as conn, conn:" in review
        and "DISCARD_SCHEMA_MIGRATION_REQUIRED" in review
        and "with closing(con):" in (root / "src/gaia_rag_r05/lifecycle_read.py").read_text(encoding="utf-8")
    )
    checks["skill_router_explicit_and_read_only"] = (
        "def gaia_skill_route(" in app
        and "def gaia_skill_route_read(" in app
        and "skill_router.route(" in app
        and "skill_router.read_selected(" in app
        and "host_must_explicitly_load" in router
        and "SKILL_VERSION_MISMATCH" in router
        and "SKILL_CONTENT_DRIFT" in router
        and "memory_write_permitted" in router
        and "_require(namespace, process_id)" in app
    )
    from r07_s7_package_preflight import inspect as package_inspect
    package_result = package_inspect(root)
    checks["s7_pinned_package_preflight_passed"] = package_result["pass"]
    checks["s7_recovery_test_and_preflight_present"] = (
        (root / "tests/test_r07_s7_recovery.py").is_file()
        and (root / "scripts/r07_s7_package_preflight.py").is_file()
    )
    from r07_s8_supplychain import create_sbom, validate_sbom
    locked_bytes = (root / "requirements.lock").read_bytes()
    checks["s8_deterministic_sbom_from_lock"] = (
        validate_sbom(create_sbom(locked_bytes), locked_bytes)["python_components"] == 29
    )
    checks["s8_review_replay_readback_preserved"] = (
        "def _verify_approved_point(" in review
        and "read_point(cap, row[\"point_id\"])" in review
        and "APPROVED_POINT_READBACK_UNCONFIRMED" in review
    )
    checks["s8_public_advisory_and_snapshot_gate_present"] = all(
        (root / path).is_file() for path in (
            "src/gaia_rag_r05/native_snapshot_plan.py",
            "scripts/r07_s8_supplychain.py",
            "tests/test_r07_s8_snapshot_contract.py",
        )
    )
    checks["test_files_present"] = all((root / path).is_file() for path in REQUIRED_TESTS)
    checks["governance_docs_present"] = all((root / path).is_file() for path in REQUIRED_DOCS)

    return {
        "checks": checks,
        "code_gate_passed": all(checks.values()),
        "scope": "R07_CI_CANDIDATE_ONLY",
        "production_homologated": False,
        "cloudflare_real_identity_tested": False,
        "customer_data_used": False,
        "external_llm_called": False,
        "qdrant_production_modified": False,
        "migration_performed": False,
        "legacy_shutdown_authorized": False,
        "next_gate": "AUTHORIZED_OPERATIONAL_DEPLOYMENT_ON_FUTURE_TARGET",
    }


def markdown(result: dict, sha: str, run_id: str) -> str:
    items = [
        "## R07 — CI candidate acceptance (not a production approval)",
        "",
        f"- Commit: `{sha or 'unknown'}`",
        f"- CI run: `{run_id or 'unknown'}`",
        f"- Code gate: **{'PASS' if result['code_gate_passed'] else 'FAIL'}**",
        "- External runtime / Cloudflare real / Qdrant production: **NOT TESTED**",
        "- No deployment, credentials, customer data or real-memory modification.",
        "",
        "| CI policy check | Result |",
        "| --- | --- |",
    ]
    items.extend(f"| {k} | {'PASS' if v else 'FAIL'} |"
                 for k, v in result["checks"].items())
    items.extend((
        "",
        "**Limitation:** passing this CI permits an engineering review of the R07 "
        "candidate, never a merge, production rollout, migration, or legacy cutoff.",
        "",
    ))
    return "\n".join(items)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-path", default="")
    args = parser.parse_args()
    result = evaluate(Path(args.root))
    md = markdown(result, os.getenv("GITHUB_SHA", ""),
                  os.getenv("GITHUB_RUN_ID", ""))
    print(md)
    if args.summary_path:
        with open(args.summary_path, "a", encoding="utf-8") as fd:
            fd.write(md)
    return 0 if result["code_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
