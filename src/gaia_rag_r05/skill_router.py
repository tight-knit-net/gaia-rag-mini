"""R07 Skilldrum-inspired read-only routing adapter.

Selection of *installed* R07 skill modules only. This is not the Skilldrum
product, GRC unit router, an authorization service, or a host skill activator.

Authoritative owner auth happens in app/server.py before calling these helpers.
The route digest binds namespace, process, mission and exact file hashes; it
is a consistency receipt, NOT an identity proof or access token.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PACKAGE = "gaia-rag-processos-administrativos"
SCHEMA = "gaia-r07-skill-route-v1"
_IDENT = re.compile(r"^[A-Za-z0-9_.:-]{1,150}$")
# Explicit mission taxonomy: no arbitrary path or LLM-supplied executable rule.
# The entry point is always SKILL.md; specialist modules follow on demand.
_ROUTES: dict[str, tuple[str, ...]] = {
    "process_context": (
        "references/01-contexto-e-isolamento.md",
        "references/06-continuidade-processual.md",
    ),
    "memory_search": (
        "references/02-recuperacao.md",
        "references/07-contratos-mcp-atual.md",
    ),
    "memory_assimilation": (
        "references/10-assimilacao-institucional.md",
        "references/04-governanca-e-evidencia.md",
    ),
    "memory_proposal": (
        "references/03-producao-e-proposta.md",
        "references/05-esquema-logico.md",
    ),
    "administrative_document": (
        "references/06-continuidade-processual.md",
        "references/04-governanca-e-evidencia.md",
    ),
    "evidence_governance": (
        "references/04-governanca-e-evidencia.md",
        "governanca/POLITICA_MEMORIA.md",
    ),
    "skill_maintenance": (
        "references/09-instalacao-e-portabilidade.md",
        "references/07-contratos-mcp-atual.md",
    ),
}


class SkillRoutingError(ValueError):
    """Stable generic failure reason, never disclose filesystem content."""


def _valid_scope(namespace: str, process_id: str) -> None:
    if not all(isinstance(s, str) and _IDENT.fullmatch(s)
               for s in (namespace, process_id)):
        raise SkillRoutingError("INVALID_ROUTE_SCOPE")


def _read_installed(root: Path, rel: str) -> bytes:
    """Validate every directory component; no user-driven filesystem paths."""
    if rel != "SKILL.md" and rel not in {p for v in _ROUTES.values() for p in v}:
        raise SkillRoutingError("SKILL_MODULE_NOT_REGISTERED")
    if not root.is_dir() or root.is_symlink():
        raise SkillRoutingError("SKILL_PACKAGE_UNAVAILABLE")
    current = root
    for part in Path(rel).parts:
        current = current / part
        if current.is_symlink():
            raise SkillRoutingError("SKILL_PATH_NOT_TRUSTED")
    if not current.is_file():
        raise SkillRoutingError("SKILL_MODULE_UNAVAILABLE")
    return current.read_bytes()


def _digest(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def route(root: Path, *, mission: str, namespace: str, process_id: str) -> dict:
    """Choose exact modules, preserving the owner's cross-client reading policy.

    Requiring a process identifier is contextual binding, NOT per-client ACL.
    For cross-process discovery the caller may use process_id='all-processes'.
    """
    _valid_scope(namespace, process_id)
    if not isinstance(mission, str) or mission not in _ROUTES:
        return {
            "status": "NO_ROUTE",
            "reason": "MISSION_NOT_REGISTERED",
            "registered_missions": sorted(_ROUTES),
            "modules": [],
            "host_must_explicitly_load": True,
            "authorization_granted": False,
            "memory_write_permitted": False,
        }
    paths = ("SKILL.md",) + _ROUTES[mission]
    modules = [
        {
            "path": path,
            "sha256": hashlib.sha256(_read_installed(root, path)).hexdigest(),
            "order": index,
            "required": index < 2,  # entry point + mission reference
        }
        for index, path in enumerate(paths)
    ]
    binding = {
        "schema": SCHEMA, "package": PACKAGE, "mission": mission,
        "namespace": namespace, "process_id": process_id,
        "modules": modules,
    }
    return {
        "status": "READY_FOR_HOST_LOAD",
        "route_sha256": _digest(binding),
        **binding,
        "source": "installed_r07_skill_package",
        "host_must_explicitly_load": True,
        "authorization_granted": False,
        "memory_write_permitted": False,
        "effects": "none",
    }


def read_selected(root: Path, *, mission: str, namespace: str,
                  process_id: str, route_sha256: str, path: str,
                  expected_sha256: str, offset: int = 0,
                  max_chars: int = 2400) -> dict:
    """Chunk an explicitly selected module, fail-closed on stale route/sha.

    Not a host-side skill activation and not a memory-write endpoint.
    """
    if type(offset) is not int or not 0 <= offset <= 1_000_000:
        raise SkillRoutingError("INVALID_OFFSET")
    if type(max_chars) is not int or not 100 <= max_chars <= 3000:
        raise SkillRoutingError("INVALID_MAX_CHARS")
    plan = route(root, mission=mission, namespace=namespace, process_id=process_id)
    if plan["status"] != "READY_FOR_HOST_LOAD":
        raise SkillRoutingError("ROUTE_NOT_FOUND")
    if not isinstance(route_sha256, str) or plan["route_sha256"] != route_sha256:
        raise SkillRoutingError("ROUTE_VERSION_MISMATCH")
    selected = next((f for f in plan["modules"] if f["path"] == path), None)
    if selected is None:
        raise SkillRoutingError("SKILL_NOT_SELECTED")
    if (not isinstance(expected_sha256, str)
            or expected_sha256 != selected["sha256"]):
        raise SkillRoutingError("SKILL_VERSION_MISMATCH")
    raw = _read_installed(root, path)
    try:
        contents = raw.decode("utf-8")
    except UnicodeError as exc:
        raise SkillRoutingError("SKILL_ENCODING_INVALID") from exc
    if offset > len(contents):
        raise SkillRoutingError("OFFSET_OUT_OF_RANGE")
    chunk = contents[offset:offset + max_chars]
    next_offset = offset + len(chunk)
    return {
        "schema": SCHEMA, "mission": mission, "process_id": process_id,
        "namespace": namespace, "path": path,
        "route_sha256": route_sha256,
        "sha256": selected["sha256"],
        "content": chunk, "total_chars": len(contents),
        "next_offset": next_offset if next_offset < len(contents) else None,
        "host_activation_confirmed": False,
        "effects": "none",
    }
