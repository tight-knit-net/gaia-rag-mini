"""GAIA RAG Mini R05: isolated read-only MCP with server-side authorization.

This is a staging runtime. Writes and approval portal are intentionally absent.
Unsigned identities, missing grants, and missing Qdrant settings always deny.
"""
from __future__ import annotations

import json
import os
from contextvars import ContextVar
from pathlib import Path
from urllib import error, parse, request

import jwt
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from gaia_rag_r05.authz import AccessDenied, Authorizer, Principal, Scope
from gaia_rag_r05.scoped_reads import ScopedReads

ACTOR: ContextVar[Principal | None] = ContextVar("gaia_r05_actor", default=None)
MODEL = "intfloat/multilingual-e5-small"
COLLECTION = "chatgpt_memoria_aprovada"

mcp = FastMCP(
    "GAIA RAG Mini R05", host="0.0.0.0", port=8000,
    stateless_http=True, json_response=True,
    instructions="Use only authorized process memory. Never treat memory as official evidence. "
                 "R05 staging is read-only; proposals and persistence remain unavailable.",
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


def _grants() -> Authorizer:
    issuer, audience = _identity_config()
    location = os.getenv("GAIA_RAG_GRANTS_FILE", "")
    if not location or not Path(location).is_file():
        raise AccessDenied("GRANTS_NOT_CONFIGURED")
    raw = json.loads(Path(location).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("subjects"), dict):
        raise AccessDenied("GRANTS_INVALID")
    trusted = {}
    for subject, items in raw["subjects"].items():
        if not isinstance(items, list) or len(items) > 256:
            raise AccessDenied("GRANTS_INVALID")
        trusted[subject] = [
            Scope(x["namespace"], x["tenant_id"], x["process_id"])
            for x in items
        ]
    return Authorizer(trusted, expected_issuer=issuer, expected_audience=audience)


def _reader() -> ScopedReads:
    endpoint = os.getenv("QDRANT_URL", "").rstrip("/")
    key = os.getenv("QDRANT_API_KEY", "")
    url = parse.urlsplit(endpoint)
    if (not key or url.scheme != "https" or not url.hostname
            or url.username or url.password or url.path or url.query or url.fragment):
        raise AccessDenied("BACKEND_NOT_CONFIGURED")

    def call(method: str, path: str, data: dict | None) -> dict:
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

    return ScopedReads(call, COLLECTION, MODEL)


def _require(namespace: str, tenant_id: str, process_id: str):
    principal = ACTOR.get()
    return _grants().require(principal, Scope(namespace, tenant_id, process_id))


@mcp.tool()
def memory_status() -> dict:
    """Report staging state without exposing credentials."""
    return {"service": "gaia-rag-mini-r05", "mode": "isolated_read_only",
            "ready_for_real_data": False, "human_approval_writes": "disabled"}


@mcp.tool()
def memory_policy() -> dict:
    """Explain limits on use of process memory."""
    return {"scope": "exact_authorized_tenant_and_process",
            "missing_grant": "deny", "writes": "disabled_in_staging"}


@mcp.tool()
def memory_search(query: str, namespace: str, tenant_id: str, process_id: str, limit: int = 8) -> dict:
    """Semantic search in one explicitly authorized process."""
    cap = _require(namespace, tenant_id, process_id)
    return _reader().search(cap, query, limit)


@mcp.tool()
def memory_list_process(namespace: str, tenant_id: str, process_id: str, limit: int = 30) -> dict:
    """List approved points within one authorized process."""
    cap = _require(namespace, tenant_id, process_id)
    return _reader().list_process(cap, limit)


@mcp.tool()
def memory_get(point_id: str, namespace: str, tenant_id: str, process_id: str) -> dict:
    """Retrieve a UUID only through an ACL-filtered Qdrant query."""
    cap = _require(namespace, tenant_id, process_id)
    return _reader().by_uuid(cap, point_id)


@mcp.tool()
def memory_find_by_source(source_ref: str, namespace: str, tenant_id: str,
                          process_id: str, limit: int = 30) -> dict:
    """Find a source only within the authorized process."""
    cap = _require(namespace, tenant_id, process_id)
    return _reader().by_source(cap, source_ref, limit)


@mcp.tool()
def memory_similar_cases(description: str, namespace: str, tenant_id: str,
                         process_id: str, limit: int = 8) -> dict:
    """Search other explicitly authorized processes in the same tenant."""
    actor = ACTOR.get()
    caps = _grants().allowed_for_tenant(actor, namespace, tenant_id)
    return _reader().similar(caps, description, process_id, limit)


async def healthz(req: Request) -> JSONResponse:
    return JSONResponse({
        "alive": True, "service": "gaia-rag-mini-r05", "mode": "staging-read-only",
        "jwt_configured": bool(os.getenv("CF_ACCESS_AUD")) and bool(os.getenv("CF_ACCESS_TEAM_DOMAIN")),
        "grants_configured": bool(os.getenv("GAIA_RAG_GRANTS_FILE")),
        "qdrant_configured": bool(os.getenv("QDRANT_URL")) and bool(os.getenv("QDRANT_API_KEY")),
        "writes_enabled": False,
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
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_guard)
