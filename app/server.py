"""GAIA RAG Mini R07 candidate: owner-wide process memory with verified identity.

All clients and processes are visible to the authorized GAIA owner. Client
projects organize work, but do not grant or restrict access. Memory writes
still require separately verified document approval and human browser review.
"""
from __future__ import annotations

import json
import os
from contextvars import ContextVar
from html import escape as html_escape
from pathlib import Path
from urllib import error, parse, request

import jwt
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route

from gaia_rag_r05.authz import AccessDenied, OwnerAuthorizer, Principal, Scope
from gaia_rag_r05.scoped_reads import ScopedReads
from gaia_rag_r05 import review, institutional_memory, lifecycle_read

ACTOR: ContextVar[Principal | None] = ContextVar("gaia_r05_actor", default=None)
MODEL = "intfloat/multilingual-e5-small"
COLLECTION = "chatgpt_memoria_aprovada"

mcp = FastMCP(
    "GAIA RAG Mini R07 (isolated candidate)", host="0.0.0.0", port=8000,
    stateless_http=True, json_response=True,
    instructions="Use only authorized process memory. Never treat memory as official evidence. "
                 "R07 isolated candidate: documentary approval and protected human review required.",
)


def _identity_config() -> tuple[str, str]:
    issuer = os.getenv("CF_ACCESS_TEAM_DOMAIN", "").rstrip("/")
    audience = os.getenv("CF_ACCESS_AUD", "")
    url = parse.urlsplit(issuer)
    if (url.scheme != "https" or not url.hostname
            or not url.hostname.endswith(".cloudflareaccess.com")
            or url.path or url.query or url.fragment or len(audience) < 12):
        raise AccessDenied("ACCESS_NOT_CONFIGURED")
    return issuer, audience


def _authenticated_actor(req: Request) -> Principal:
    issuer, audience = _identity_config()
    bearer = req.headers.get("cf-access-jwt-assertion", "")
    if not bearer:
        bearer = req.cookies.get("CF_Authorization", "")
    if not bearer:
        raise AccessDenied("ACCESS_DENIED")
    key = jwt.PyJWKClient(issuer + "/cdn-cgi/access/certs").get_signing_key_from_jwt(bearer).key
    claims = jwt.decode(
        bearer, key, algorithms=["RS256"], audience=audience, issuer=issuer, leeway=20,
        options={"require": ["exp", "iss", "aud"]},
    )
    subject = claims.get("email")
    if not isinstance(subject, str) or not subject.strip():
        raise AccessDenied("ACCESS_DENIED")
    return Principal(subject.strip().lower(), issuer, audience)


def _owners() -> OwnerAuthorizer:
    """Owner identities from an operator-managed registry, never from MCP data."""
    issuer, audience = _identity_config()
    location = os.getenv("GAIA_RAG_OWNER_SUBJECTS_FILE", "")
    if not location or not Path(location).is_file():
        raise AccessDenied("OWNERS_NOT_CONFIGURED")
    raw = json.loads(Path(location).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("subjects"), list):
        raise AccessDenied("OWNERS_INVALID")
    return OwnerAuthorizer(raw["subjects"], expected_issuer=issuer,
                           expected_audience=audience)


def _qrequest(method: str, path: str, data: dict | None) -> dict:
    endpoint = os.getenv("QDRANT_URL", "").rstrip("/")
    key = os.getenv("QDRANT_API_KEY", "")
    key_file = os.getenv("QDRANT_API_KEY_FILE", "")
    if not key and key_file:
        key_path = Path(key_file)
        if not key_path.is_absolute() or not key_path.is_file():
            raise AccessDenied("BACKEND_NOT_CONFIGURED")
        key = key_path.read_text(encoding="utf-8").strip()
    url = parse.urlsplit(endpoint)
    if (not key or url.scheme != "https" or not url.hostname
            or url.username or url.password or url.path or url.query or url.fragment):
        raise AccessDenied("BACKEND_NOT_CONFIGURED")

    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = request.Request(
        endpoint + path, method=method, data=payload,
        headers={"api-key": key, "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            result = json.load(response)
    except error.HTTPError as exc:
        raise RuntimeError("BACKEND_FAILED") from exc
    if not isinstance(result, dict):
        raise RuntimeError("BACKEND_FAILED")
    return result


def _reader() -> ScopedReads:
    return ScopedReads(_qrequest, COLLECTION, MODEL)


def _require(namespace: str, process_id: str):
    """Verify the GAIA owner, then issue a capability for the exact process."""
    return _owners().require(ACTOR.get(), Scope(namespace, "owner-all", process_id))


@mcp.tool()
def memory_status() -> dict:
    """Report staging state without exposing credentials."""
    return {"service": "gaia-rag-mini-r07", "mode": "controlled_staging",
            "identity_ready": bool(os.getenv("CF_ACCESS_AUD") and os.getenv("CF_ACCESS_TEAM_DOMAIN")),
            "owners_ready": bool(os.getenv("GAIA_RAG_OWNER_SUBJECTS_FILE")),
            "qdrant_ready": bool(os.getenv("QDRANT_URL") and
                                 (os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_API_KEY_FILE"))),
            "human_approval_writes": "browser_only" if os.getenv("GAIA_RAG_ENABLE_REVIEW") == "1" else "disabled",
            "ready_for_real_data": False}


@mcp.tool()
def memory_policy() -> dict:
    """Explain limits on use of process memory."""
    return {"scope": "verified_owner_across_all_clients",
            "client_permission_blocks": "disabled", "process_id": "exact_locator",
            "unverified_identity": "deny", "document_approval_registry": "server_owned",
            "proposals": "prepare_only", "writes": "authenticated_browser_csrf_only",
            "human_review_enabled": os.getenv("GAIA_RAG_ENABLE_REVIEW") == "1"}


@mcp.tool()
def memory_search(query: str, process_id: str, namespace: str = "chatgpt",
                  limit: int = 8) -> dict:
    """Search approved memory for an exact process; owner may access any client."""
    return _reader().search(_require(namespace, process_id), query, limit)


@mcp.tool()
def memory_search_all(query: str, namespace: str = "chatgpt", limit: int = 8) -> dict:
    """Owner searches all approved GAIA memories; locate processes across clients."""
    return _reader().search_all_owner(_require(namespace, "all-processes"), query, limit)


@mcp.tool()
def memory_list_process(process_id: str, namespace: str = "chatgpt",
                        limit: int = 30, offset: str | int | None = None) -> dict:
    """List approved records with a Qdrant cursor; never truncate silently."""
    return _reader().list_process(_require(namespace, process_id), limit, offset)


@mcp.tool()
def memory_get(point_id: str, process_id: str, namespace: str = "chatgpt") -> dict:
    """Retrieve a UUID within the specified process; no per-client authorization."""
    return _reader().by_uuid(_require(namespace, process_id), point_id)


@mcp.tool()
def memory_find_by_source(source_ref: str, process_id: str, namespace: str = "chatgpt",
                          limit: int = 30) -> dict:
    """Find a source in the exact process, across any client's records."""
    return _reader().by_source(_require(namespace, process_id), source_ref, limit)


@mcp.tool()
def memory_similar_cases(description: str, process_id: str,
                         namespace: str = "chatgpt", limit: int = 8) -> dict:
    """Find other approved processes, including cases from different clients."""
    return _reader().similar_owner(_require(namespace, process_id), description, limit)


@mcp.tool()
def memory_process_start(process_id: str, namespace: str = "chatgpt",
                         description: str = "") -> dict:
    """Open any process with exact identity, independent of its client project."""
    cap = _require(namespace, process_id)
    if not isinstance(description, str) or len(description) > 4000:
        raise ValueError("INVALID_DESCRIPTION")
    return {"process_id": process_id, "namespace": namespace,
            "approved_memories": _reader().list_process(cap, 20)}


@mcp.tool()
def memory_assimilation_preview(
    process_id: str, title: str, summary: str, source_ref: str,
    kind: str = "registro_caso", evidence_status: str = "documentada",
    prior_point_id: str = "", namespace: str = "chatgpt",
) -> dict:
    """Compare approved history to an institutional candidate: NO write/revoke.

    A later or more precise source is only a PROPOSED revision until
    documentary approval and the existing human review portal confirm it.
    """
    cap = _require(namespace, process_id)
    reader = _reader()
    items = []
    offset = None
    complete = False
    for _ in range(3):  # max 300 records; report partial coverage explicitly.
        page = reader.list_process(cap, limit=100, offset=offset)
        items.extend(page["items"])
        offset = page["next_offset"]
        if offset is None:
            complete = True
            break
    if prior_point_id and not any(str(x.get("id")) == prior_point_id for x in items):
        prior = reader.by_uuid(cap, prior_point_id)
        if prior.get("found"):
            items.append(prior["item"])
        elif complete:
            raise ValueError("PRIOR_NOT_FOUND_IN_PROCESS")
    assessment = institutional_memory.preview(
        process_id=process_id, title=title, summary=summary,
        source_ref=source_ref, kind=kind, evidence_status=evidence_status,
        previous=items, prior_point_id=prior_point_id,
        coverage_complete=complete,
    )
    assessment["observed_history_count"] = len(items)
    assessment["tool_side_effects"] = "none"
    return assessment



@mcp.tool()
def memory_process_timeline(process_id: str, namespace: str = "chatgpt",
                            max_items: int = 300) -> dict:
    """Read chronological approved-memory metadata; mark incomplete coverage."""
    cap = _require(namespace, process_id)
    return {"process_id": process_id, **lifecycle_read.process_timeline(
        _reader(), cap, max_items=max_items)}


@mcp.tool()
def memory_export_process(process_id: str, namespace: str = "chatgpt",
                          max_items: int = 100,
                          offset: str | int | None = None) -> dict:
    """Bounded export of approved summaries with hash and continuation marker."""
    cap = _require(namespace, process_id)
    return {"process_id": process_id, **lifecycle_read.process_export(
        _reader(), cap, max_items=max_items, offset=offset)}


@mcp.tool()
def memory_approval_audit(namespace: str = "chatgpt", process_id: str = "",
                          limit: int = 50, offset: int = 0) -> dict:
    """Read R07 review-ledger events. Does not include legacy DB until reconciliation."""
    _require(namespace, process_id or "all-processes")
    return lifecycle_read.approval_events(
        namespace, process_id=process_id, limit=limit, offset=offset)


@mcp.tool()
def memory_stats(namespace: str = "chatgpt", process_id: str = "") -> dict:
    """Separate real Qdrant approved-point count from R07 proposal counts."""
    _require(namespace, process_id or "all-processes")
    must = [{"key": "namespace", "match": {"value": namespace}},
            {"key": "approved", "match": {"value": True}}]
    if process_id:
        must.append({"key": "process_id", "match": {"value": process_id}})
    response = _qrequest(
        "POST", f"/collections/{COLLECTION}/points/count",
        {"filter": {"must": must}, "exact": True})
    result = response.get("result", {})
    if response.get("status") != "ok" or type(result.get("count")) is not int:
        raise RuntimeError("COUNT_UNCONFIRMED")
    local = lifecycle_read.proposal_statistics(namespace, process_id=process_id)
    return {"namespace": namespace, "process_id": process_id or None,
            "qdrant_approved_points": result["count"],
            "qdrant_count_exact": True, **local}


@mcp.tool()
def memory_index_preview(process_id: str, title: str, summary: str,
                         source_ref: str, evidence_status: str = "documentada",
                         namespace: str = "chatgpt") -> dict:
    """Generate index keywords/classification locally; NEVER save or send externally."""
    _require(namespace, process_id)
    return lifecycle_read.index_candidate_preview(
        process_id=process_id, title=title, summary=summary,
        source_ref=source_ref, evidence_status=evidence_status)



@mcp.tool()
def memory_auto_prepare(
    process_id: str, title: str, summary: str, source_ref: str,
    document_approval_ref: str, document_sha256: str,
    kind: str = "auto", evidence_status: str = "documentada",
    prior_point_id: str = "", user_confirmed_proposal: bool = False,
    namespace: str = "chatgpt",
) -> dict:
    """LLM-assisted editorial preparation, NEVER automatic Qdrant persistence.

    In preview mode no changes occur. Explicitly confirmed preparation still
    requires documentary registry approval and human browser click/readback.
    """
    _require(namespace, process_id)
    indexed = lifecycle_read.index_candidate_preview(
        process_id=process_id, title=title, summary=summary,
        source_ref=source_ref, evidence_status=evidence_status)
    chosen_kind = indexed["suggested_kind"] if kind == "auto" else kind
    assessment = memory_assimilation_preview(
        process_id=process_id, title=title, summary=summary,
        source_ref=source_ref, kind=chosen_kind,
        evidence_status=evidence_status, prior_point_id=prior_point_id,
        namespace=namespace)
    result = {
        "candidate": indexed, "assessment": assessment,
        "proposal_prepared": False, "persisted": False,
        "human_save_required": True,
        "external_llm_used": False,
    }
    if (assessment["blockers"] or assessment["disposition"] != "NOVA_CANDIDATA"
            or not indexed["recommend_review"]):
        result["status"] = "BLOCKED_FOR_EDITORIAL_REVIEW"
        return result
    if user_confirmed_proposal is not True:
        result["status"] = "PREVIEW_ONLY_CONFIRM_TO_PREPARE"
        return result
    cap = _require(namespace, process_id)
    proposed = review.prepare(
        cap, created_by=ACTOR.get().subject, title=title,
        summary=summary, source_ref=source_ref,
        document_approval_ref=document_approval_ref,
        document_sha256=document_sha256)
    result["proposal_prepared"] = True
    result["status"] = proposed["status"]
    result["proposal_id"] = proposed["proposal_id"]
    result["review_url"] = proposed["review_url"]
    result["persisted"] = proposed.get("stored") is True
    result["human_save_required"] = proposed.get("stored") is not True
    return result


@mcp.tool()
def memory_prepare_after_approval(process_id: str, title: str, summary: str,
                                  source_ref: str, document_approval_ref: str,
                                  document_sha256: str, namespace: str = "chatgpt") -> dict:
    """Prepare a document-approved proposal for any client; still no direct write."""
    cap = _require(namespace, process_id)
    return review.prepare(cap, created_by=ACTOR.get().subject, title=title,
                          summary=summary, source_ref=source_ref,
                          document_approval_ref=document_approval_ref,
                          document_sha256=document_sha256)


@mcp.tool()
def memory_proposal_preview(proposal_id: str, process_id: str,
                            namespace: str = "chatgpt") -> dict:
    """Read an exact process proposal; owner can view any client's proposal."""
    return review.get_proposal(proposal_id, _require(namespace, process_id))


@mcp.tool()
def memory_discard_proposal(proposal_id: str, process_id: str,
                            namespace: str = "chatgpt") -> dict:
    """Return the human-review link; NEVER discard via an LLM-triggered MCP call."""
    cap = _require(namespace, process_id)
    proposal = review.get_proposal(proposal_id, cap)
    return {"proposal_id": proposal_id, "status": proposal["status"],
            "human_confirmation_required": True,
            "review_url": review._review_base() + "/review/" + proposal_id,
            "discarded": proposal["status"] == "discarded",
            "tool_side_effects": "none"}


@mcp.tool()
def memory_pending_reviews(process_id: str, namespace: str = "chatgpt",
                           limit: int = 20, offset: int = 0) -> dict:
    """Read only PENDING proposals from the current R07 ledger, not the legacy queue."""
    _require(namespace, process_id)
    return lifecycle_read.pending_reviews(namespace, process_id, limit=limit, offset=offset)


def _review_authorize(namespace: str, tenant_id: str, process_id: str):
    """Tenant is documentary metadata, not a permission boundary for GAIA owner."""
    return _require(namespace, process_id)


def _write_point(point_id: str, payload: dict) -> None:
    if os.getenv("GAIA_RAG_ENABLE_REVIEW") != "1":
        raise AccessDenied("REVIEW_DISABLED")
    result = _qrequest("PUT", f"/collections/{COLLECTION}/points?wait=true", {
        "points": [{"id": point_id, "payload": payload,
                    "vector": {"text": payload["text"], "model": MODEL}}]})
    if result.get("status") != "ok":
        raise RuntimeError("QDRANT_WRITE_UNCONFIRMED")


def _read_point(cap, point_id):
    return _reader().by_uuid(cap, point_id)


def _safe_review_response(html: str, status: int = 200) -> HTMLResponse:
    return HTMLResponse(html, status_code=status, headers={
        "Cache-Control": "no-store, max-age=0",
        "Content-Security-Policy": "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'; style-src 'unsafe-inline'",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
    })


async def review_get(req: Request):
    try:
        principal = ACTOR.get()
        page = review.review_view(req.path_params["proposal_id"], principal.subject, _review_authorize)
        disabled = page["status"] != "pending" or page["csrf"] is None
        body = ("<h1>GAIA — revisão humana de memória</h1><p>Proposta: "
                + html_escape(page["id"]) + "</p><h2>" + html_escape(page["title"])
                + "</h2><pre>" + html_escape(page["summary"]) + "</pre><p>Fonte: "
                + html_escape(page["source_ref"]) + "</p><p>Processo: "
                + html_escape(page["process_id"]) + "</p><p>Estado: "
                + html_escape(page["status"]) + "</p>")
        indexed = lifecycle_read.index_candidate_preview(
            process_id=page["process_id"], title=page["title"],
            summary=page["summary"], source_ref=page["source_ref"])
        body += ("<p>Indexação sugerida (não oficial): "
                 + html_escape(indexed["suggested_kind"]) + " / "
                 + html_escape(", ".join(indexed["suggested_tags"]))
                 + "</p><p>Somente o botão humano abaixo autoriza salvar.</p>")
        if not disabled:
            body += ('<form method="POST" action="/review/' + html_escape(page["id"]) + '/approve">'
                     '<input type="hidden" name="csrf" value="' + html_escape(page["csrf"]) + '">'
                     '<p>Confira a fonte documental e o conteúdo. A aprovação grava UMA memória.</p>'
                     '<button type="submit" name="confirm" value="APROVAR">Salvar memória — Aprovar e gravar</button></form>'
                     '<form method="POST" action="/review/' + html_escape(page["id"]) + '/discard">'
                     '<input type="hidden" name="csrf" value="' + html_escape(page["csrf"]) + '">'
                     '<button type="submit" name="confirm" value="DESCARTAR">Descartar proposta</button></form>')
        return _safe_review_response("<!doctype html><html lang='pt-BR'><meta charset='utf-8'><title>Revisão GAIA</title><body>"+body+"</body></html>")
    except Exception:
        return JSONResponse({"error": "REVIEW_UNAVAILABLE"}, status_code=403)


async def review_post(req: Request):
    try:
        origin = req.headers.get("origin", "")
        if origin != review._review_base():
            raise AccessDenied("ORIGIN_DENIED")
        if req.headers.get("content-type", "").split(";")[0].strip().lower() != "application/x-www-form-urlencoded":
            raise AccessDenied("CONTENT_TYPE_DENIED")
        if int(req.headers.get("content-length", "0")) > 4096:
            raise AccessDenied("BODY_TOO_LARGE")
        form = await req.form()
        if form.get("confirm") != "APROVAR" or not isinstance(form.get("csrf"), str):
            raise AccessDenied("HUMAN_CLICK_REQUIRED")
        result = review.approve(req.path_params["proposal_id"], ACTOR.get().subject,
                                _review_authorize, form["csrf"], _write_point, _read_point)
        return _safe_review_response("<h1>Memória confirmada após readback</h1><p>ID: "
                                     + html_escape(result["point_id"]) + "</p>")
    except Exception:
        return JSONResponse({"error": "REVIEW_NOT_COMPLETED"}, status_code=403)


async def review_discard_post(req: Request):
    """Human CSRF-protected discard; no Qdrant deletion or content mutation."""
    try:
        origin = req.headers.get("origin", "")
        if origin != review._review_base():
            raise AccessDenied("ORIGIN_DENIED")
        if req.headers.get("content-type", "").split(";")[0].strip().lower() != "application/x-www-form-urlencoded":
            raise AccessDenied("CONTENT_TYPE_DENIED")
        if int(req.headers.get("content-length", "0")) > 4096:
            raise AccessDenied("BODY_TOO_LARGE")
        form = await req.form()
        if form.get("confirm") != "DESCARTAR" or not isinstance(form.get("csrf"), str):
            raise AccessDenied("HUMAN_CLICK_REQUIRED")
        result = review.discard(req.path_params["proposal_id"], ACTOR.get().subject,
                                _review_authorize, form["csrf"])
        return _safe_review_response(
            "<h1>Proposta descartada após revisão humana</h1><p>ID: "
            + html_escape(result["proposal_id"]) + "</p>")
    except Exception:
        return JSONResponse({"error": "DISCARD_NOT_COMPLETED"}, status_code=403)


def _skill_root() -> Path:
    return Path("/app/skills/gaia-rag-processos-administrativos")


_SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/01-contexto-e-isolamento.md",
    "references/02-recuperacao.md",
    "references/03-producao-e-proposta.md",
    "references/04-governanca-e-evidencia.md",
    "references/05-esquema-logico.md",
    "references/06-continuidade-processual.md",
    "references/07-contratos-mcp-atual.md",
    "references/08-arquitetura-tecnica-nao-mutativa.md",
    "references/09-instalacao-e-portabilidade.md",
    "references/10-assimilacao-institucional.md",
    "governanca/POLITICA_MEMORIA.md",
    "assets/templates/memoria.md",
)


@mcp.tool()
def gaia_skill_catalog() -> dict:
    """Discover installed, versioned skill files; loading is still host-driven."""
    import hashlib
    root = _skill_root()
    result = []
    for rel in _SKILL_FILES:
        f = root / rel
        if not f.is_file():
            raise AccessDenied("SKILL_NOT_INSTALLED")
        result.append({"path": rel, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    return {"name": "gaia-rag-processos-administrativos",
            "activation": "host_must_explicitly_load",
            "files": result}


@mcp.tool()
def gaia_skill_read(path: str) -> dict:
    """Read an allowlisted skill file progressively; no filesystem traversal."""
    if path not in _SKILL_FILES:
        raise AccessDenied("SKILL_PATH_DENIED")
    target = _skill_root() / path
    if not target.is_file() or target.is_symlink():
        raise AccessDenied("SKILL_NOT_INSTALLED")
    return {"path": path, "content": target.read_text(encoding="utf-8")}




@mcp.tool()
def gaia_skill_read_chunk(path: str, offset: int = 0, max_chars: int = 2400) -> dict:
    """Small immutable skill chunk for MCP hosts with response-size limitations."""
    import hashlib
    if path not in _SKILL_FILES:
        raise AccessDenied("SKILL_PATH_DENIED")
    if type(offset) is not int or offset < 0 or offset > 1000000:
        raise ValueError("INVALID_OFFSET")
    if type(max_chars) is not int or not 100 <= max_chars <= 3000:
        raise ValueError("INVALID_MAX_CHARS")
    f = _skill_root() / path
    if not f.is_file() or f.is_symlink():
        raise AccessDenied("SKILL_NOT_INSTALLED")
    raw = f.read_text(encoding="utf-8")
    if offset > len(raw):
        raise ValueError("OFFSET_OUT_OF_RANGE")
    chunk = raw[offset:offset + max_chars]
    return {"path": path, "offset": offset, "content": chunk,
            "total_chars": len(raw), "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "next_offset": offset + len(chunk) if offset + len(chunk) < len(raw) else None}


@mcp.resource("skill://gaia-rag-processos-administrativos/SKILL.md")
def gaia_skill_resource_root() -> str:
    """Fetch canonical skill entry when MCP resources are supported by the host."""
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


@mcp.resource("skill://gaia-rag-processos-administrativos/references/02-recuperacao.md")
def gaia_skill_resource_retrieval() -> str:
    return (_skill_root() / "references/02-recuperacao.md").read_text(encoding="utf-8")


@mcp.resource("skill://gaia-rag-processos-administrativos/references/03-producao-e-proposta.md")
def gaia_skill_resource_proposal() -> str:
    return (_skill_root() / "references/03-producao-e-proposta.md").read_text(encoding="utf-8")


async def healthz(req: Request) -> JSONResponse:
    return JSONResponse({
        "alive": True, "service": "gaia-rag-mini-r07", "mode": "staging-controlled",
        "jwt_configured": bool(os.getenv("CF_ACCESS_AUD")) and bool(os.getenv("CF_ACCESS_TEAM_DOMAIN")),
        "owners_configured": bool(os.getenv("GAIA_RAG_OWNER_SUBJECTS_FILE")),
        "qdrant_configured": bool(os.getenv("QDRANT_URL")) and
                             bool(os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_API_KEY_FILE")),
        "writes_enabled": os.getenv("GAIA_RAG_ENABLE_REVIEW") == "1" and bool(os.getenv("GAIA_RAG_CSRF_SECRET")),
        "approval_registry_configured": bool(os.getenv("GAIA_RAG_APPROVED_DOCS_FILE")),
    })


async def auth_guard(req: Request, call_next):
    if req.url.path == "/healthz":
        return await call_next(req)
    try:
        principal = _authenticated_actor(req)
    except Exception:
        return JSONResponse({"error": "ACCESS_DENIED"}, status_code=401)
    token = ACTOR.set(principal)
    try:
        return await call_next(req)
    finally:
        ACTOR.reset(token)


app = mcp.streamable_http_app()
app.routes.insert(0, Route("/healthz", endpoint=healthz, methods=["GET"]))
app.routes.insert(1, Route("/review/{proposal_id}", endpoint=review_get, methods=["GET"]))
app.routes.insert(2, Route("/review/{proposal_id}/approve", endpoint=review_post, methods=["POST"]))
app.routes.insert(3, Route("/review/{proposal_id}/discard", endpoint=review_discard_post, methods=["POST"]))
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_guard)
