"""R06: server-owned document approval + two-person-step memory review.

No MCP tool may approve or write a Qdrant point.  The only write entry point
is a browser POST protected by a verified Access JWT and a CSRF form token.
The approval ledger is SQLite on a dedicated persistent volume; the approved
document registry is separately provisioned by operations, never from MCP.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path

from .authz import AccessDenied, AuthorizedScope, require_issued_scope
from . import lifecycle_read

_REF = re.compile(r"^[a-zA-Z0-9_.:/-]{1,200}$")
_MAX_SUMMARY = 4000
_TTL = 14 * 24 * 3600

def _now() -> int:
    return int(time.time())

def _digest(*values: str) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def _required_ref(value: str) -> str:
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise ValueError("INVALID_REFERENCE")
    return value

def _registry_approved(capability: AuthorizedScope, source_ref: str,
                       document_approval_ref: str, document_sha256: str) -> str:
    """Verify documentary approval; return client tag as metadata, not permission.

    Approved-document registry must uniquely identify this document version;
    an owner can propose memory for any client's process.
    """
    scope = require_issued_scope(capability)
    path = os.getenv("GAIA_RAG_APPROVED_DOCS_FILE", "")
    if not path:
        raise AccessDenied("DOCUMENT_APPROVAL_REGISTRY_MISSING")
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("approved_documents"), list):
        raise AccessDenied("DOCUMENT_APPROVAL_REGISTRY_INVALID")
    matched = []
    for item in registry["approved_documents"]:
        if not isinstance(item, dict):
            raise AccessDenied("DOCUMENT_APPROVAL_REGISTRY_INVALID")
        if (item.get("namespace") == scope.namespace
                and item.get("process_id") == scope.process_id
                and item.get("source_ref") == source_ref
                and item.get("approval_ref") == document_approval_ref
                and item.get("document_sha256") == document_sha256
                and item.get("status") == "approved"):
            matched.append(item)
    if len(matched) != 1:
        raise AccessDenied("DOCUMENT_APPROVAL_NOT_VERIFIED")
    # A tenant/client tag is optional provenance, NEVER an access restriction.
    tenant = matched[0].get("tenant_id", "unassigned")
    if not isinstance(tenant, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,150}", tenant):
        raise AccessDenied("DOCUMENT_APPROVAL_REGISTRY_INVALID")
    return tenant


def _connect():
    path = Path(os.getenv("GAIA_RAG_REVIEW_DB", "/state/reviews.sqlite3"))
    if not path.is_absolute():
        raise AccessDenied("INVALID_REVIEW_DB")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=8, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=8000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            identity_key TEXT NOT NULL UNIQUE,
            namespace TEXT NOT NULL, tenant_id TEXT NOT NULL, process_id TEXT NOT NULL,
            created_by TEXT NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL,
            source_ref TEXT NOT NULL, document_approval_ref TEXT NOT NULL,
            document_sha256 TEXT NOT NULL, point_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL CHECK(status IN ('pending','approving','approved','discarded')),
            created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
            approved_by TEXT, approved_at INTEGER);
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER NOT NULL,
            proposal_id TEXT NOT NULL, event TEXT NOT NULL, actor TEXT NOT NULL);
    """)
    return conn

def _review_base() -> str:
    url = os.getenv("GAIA_RAG_REVIEW_BASE_URL", "").rstrip("/")
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path:
        raise AccessDenied("REVIEW_BASE_NOT_CONFIGURED")
    return url

def prepare(capability: AuthorizedScope, *, created_by: str, title: str, summary: str,
            source_ref: str, document_approval_ref: str, document_sha256: str) -> dict:
    s = require_issued_scope(capability)
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
        raise ValueError("INVALID_TITLE")
    if not isinstance(summary, str) or not 1 <= len(summary.strip()) <= _MAX_SUMMARY:
        raise ValueError("INVALID_SUMMARY")
    for v in (source_ref, document_approval_ref):
        _required_ref(v)
    if not isinstance(document_sha256, str) or not re.fullmatch("[0-9a-f]{64}", document_sha256):
        raise ValueError("INVALID_DOCUMENT_HASH")
    url = _review_base()
    if os.getenv("GAIA_RAG_ENABLE_REVIEW") != "1":
        raise AccessDenied("REVIEW_DISABLED")
    tenant_id = _registry_approved(capability, source_ref, document_approval_ref, document_sha256)
    # Tenant remains optional provenance, not a grant.
    identity_key = _digest(s.namespace, tenant_id, s.process_id, source_ref,
                           document_sha256, title.strip(), summary.strip())
    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "gaia-r06:" + identity_key))
    with closing(_connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM proposals WHERE identity_key=?", (identity_key,)).fetchone()
        if row is None:
            ident = str(uuid.uuid4())
            now = _now()
            conn.execute("""INSERT INTO proposals
                (id,identity_key,namespace,tenant_id,process_id,created_by,title,summary,
                 source_ref,document_approval_ref,document_sha256,point_id,status,created_at,expires_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (ident,identity_key,s.namespace,tenant_id,s.process_id,created_by,
                  title.strip(),summary.strip(),source_ref,document_approval_ref,
                  document_sha256,point_id,"pending",now,now+_TTL))
            conn.execute("INSERT INTO audit(at,proposal_id,event,actor) VALUES (?,?,?,?)",
                         (now,ident,"proposal_prepared",created_by))
            row = conn.execute("SELECT * FROM proposals WHERE id=?", (ident,)).fetchone()
        conn.commit()
        return {"proposal_id":row["id"],"status":row["status"],
                "review_url":url+"/review/"+row["id"],"expires_at":row["expires_at"],
                "stored":row["status"]=="approved"}

def get_proposal(identifier: str, capability: AuthorizedScope) -> dict:
    s = require_issued_scope(capability)
    with closing(_connect()) as conn, conn:
        row = conn.execute("SELECT * FROM proposals WHERE id=?", (str(uuid.UUID(identifier)),)).fetchone()
        if row is None or row["namespace"] != s.namespace or row["process_id"] != s.process_id:
            raise AccessDenied("PROPOSAL_NOT_FOUND")
        if capability.access_mode != "owner" and row["tenant_id"] != s.tenant_id:
            raise AccessDenied("PROPOSAL_NOT_FOUND")
        return {"proposal_id":row["id"],"title":row["title"],"summary":row["summary"],
                "source_ref":row["source_ref"],"status":row["status"],
                "expires_at":row["expires_at"],"point_id":row["point_id"] if row["status"]=="approved" else None}

def _checked_row(conn, identifier, actor, authorize):
    try:
        identifier = str(uuid.UUID(identifier))
    except (ValueError, TypeError):
        raise AccessDenied("PROPOSAL_NOT_FOUND") from None
    row = conn.execute("SELECT * FROM proposals WHERE id=?", (identifier,)).fetchone()
    if row is None:
        raise AccessDenied("PROPOSAL_NOT_FOUND")
    scope = authorize(row["namespace"],row["tenant_id"],row["process_id"])
    require_issued_scope(scope)
    if actor != scope.principal.subject:
        raise AccessDenied("ACCESS_DENIED")
    return row

def csrf_token(identifier: str, actor: str) -> str:
    secret = os.getenv("GAIA_RAG_CSRF_SECRET", "")
    if len(secret) < 32:
        raise AccessDenied("CSRF_NOT_CONFIGURED")
    exp = str(_now() + 600)
    stamp = exp+"."+secrets.token_urlsafe(18)
    mac = hmac.new(secret.encode(),f"{identifier}|{actor}|{stamp}".encode(),hashlib.sha256).hexdigest()
    return stamp+"."+mac

def verify_csrf(identifier: str, actor: str, token: str):
    try:
        exp, nonce, signature = token.split(".",2)
        secret = os.getenv("GAIA_RAG_CSRF_SECRET", "")
        if len(secret) < 32 or not nonce or int(exp) < _now() or int(exp)>_now()+600:
            raise ValueError()
        mac=hmac.new(secret.encode(),f"{identifier}|{actor}|{exp}.{nonce}".encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,mac):
            raise ValueError()
    except (ValueError,TypeError,AttributeError):
        raise AccessDenied("CSRF_DENIED") from None

def review_view(identifier: str, actor: str, authorize) -> dict:
    with closing(_connect()) as conn, conn:
        row = _checked_row(conn,identifier,actor,authorize)
        return {"id":row["id"],"title":row["title"],"summary":row["summary"],
                "source_ref":row["source_ref"],"status":row["status"],
                "expires_at":row["expires_at"],"process_id":row["process_id"],
                "csrf":csrf_token(row["id"],actor) if row["status"]=="pending" and row["expires_at"]>=_now() else None}

def _verify_approved_point(row, confirmed: dict) -> dict:
    """Require fresh positive readback of the same approved point and provenance."""
    if not isinstance(confirmed, dict) or confirmed.get("found") is not True:
        raise RuntimeError("APPROVED_POINT_READBACK_UNCONFIRMED")
    item = confirmed.get("item")
    if not isinstance(item, dict) or any((
        item.get("approved") is not True,
        item.get("namespace") != row["namespace"],
        item.get("process_id") != row["process_id"],
        item.get("source_ref") != row["source_ref"],
        item.get("document_approval_ref") != row["document_approval_ref"],
        item.get("document_sha256") != row["document_sha256"],
        item.get("text") != row["summary"],
        item.get("id") != row["point_id"],
    )):
        raise RuntimeError("APPROVED_POINT_READBACK_UNCONFIRMED")
    return item


def approve(identifier: str, actor: str, authorize, csrf: str, write_point, read_point) -> dict:
    # Browser-mediated: only caller that verified Access JWT and explicit CSRF POST can call.
    with closing(_connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _checked_row(conn,identifier,actor,authorize)
        verify_csrf(row["id"],actor,csrf)
        if row["status"]=="approved":
            # An old SQLite approval is not proof that its point still exists.
            # Release the transaction before the potentially slow Qdrant read.
            cap = authorize(row["namespace"], row["tenant_id"], row["process_id"])
            conn.commit()
            _verify_approved_point(row, read_point(cap, row["point_id"]))
            return {"stored":True,"point_id":row["point_id"],"replayed":True}
        if row["status"]!="pending" or row["expires_at"]<_now():
            raise AccessDenied("REVIEW_NOT_PENDING")
        # Validate the documentary approval registry again: it is revocable.
        cap=authorize(row["namespace"],row["tenant_id"],row["process_id"])
        tenant_tag = _registry_approved(cap,row["source_ref"],row["document_approval_ref"],row["document_sha256"])
        if tenant_tag != row["tenant_id"]:
            raise AccessDenied("DOCUMENT_APPROVAL_CHANGED")
        conn.execute("UPDATE proposals SET status='approving' WHERE id=?", (row["id"],))
        conn.execute("INSERT INTO audit(at,proposal_id,event,actor) VALUES (?,?,?,?)",
                     (_now(),row["id"],"human_click_authorized",actor))
        conn.commit()

    # Fail closed on ambiguous write/readback: do not automatically retry; operator
    # must reconcile using deterministic point ID.
    # Index metadata is generated only AFTER the human approval step.
    # It is advisory, not a legal conclusion or a new Qdrant payload index.
    indexing = lifecycle_read.index_candidate_preview(
        process_id=row["process_id"], title=row["title"],
        summary=row["summary"], source_ref=row["source_ref"])
    payload={
        "namespace":row["namespace"],"tenant_id":row["tenant_id"],"process_id":row["process_id"],
        "approved":True,"title":row["title"],"text":row["summary"],
        "source_ref":row["source_ref"],"document_sha256":row["document_sha256"],
        "document_approval_ref":row["document_approval_ref"],"approved_by":actor,"approved_at":_now(),
        "index_kind_suggested":indexing["suggested_kind"],
        "index_keywords_suggested":indexing["suggested_tags"],
        "index_method":"r07_deterministic_v1",
    }
    write_point(row["point_id"],payload)
    confirmed=read_point(cap,row["point_id"])
    item=_verify_approved_point(row,confirmed)
    if (item.get("index_method")!="r07_deterministic_v1"
            or item.get("index_keywords_suggested")!=indexing["suggested_tags"]):
        raise RuntimeError("READBACK_UNCONFIRMED")
    with closing(_connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("UPDATE proposals SET status='approved',approved_by=?,approved_at=? WHERE id=? AND status='approving'",
                     (actor,_now(),row["id"]))
        conn.execute("INSERT INTO audit(at,proposal_id,event,actor) VALUES (?,?,?,?)",
                     (_now(),row["id"],"readback_confirmed",actor))
        conn.commit()
    return {"stored":True,"point_id":row["point_id"],"replayed":False}

def _ledger_supports_discard(conn: sqlite3.Connection) -> bool:
    """Old R06 SQLite CHECK constraints cannot be expanded by CREATE IF NOT EXISTS.

    Fail closed and require a separately approved, backed-up schema migration.
    Never attempt an automatic migration during a browser click.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='proposals'"
    ).fetchone()
    return (row is not None and isinstance(row["sql"], str)
            and "'discarded'" in row["sql"].lower())


def discard(identifier: str, actor: str, authorize, csrf: str) -> dict:
    """Explicit human browser action, never an MCP direct mutation."""
    with closing(_connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _checked_row(conn, identifier, actor, authorize)
        verify_csrf(row["id"], actor, csrf)
        if row["status"] == "discarded":
            conn.commit()
            return {"discarded": True, "proposal_id": row["id"], "replayed": True}
        if row["status"] != "pending" or row["expires_at"] < _now():
            raise AccessDenied("DISCARD_NOT_PENDING")
        if not _ledger_supports_discard(conn):
            raise AccessDenied("DISCARD_SCHEMA_MIGRATION_REQUIRED")
        conn.execute("UPDATE proposals SET status='discarded' WHERE id=? AND status='pending'",
                     (row["id"],))
        conn.execute("INSERT INTO audit(at,proposal_id,event,actor) VALUES (?,?,?,?)",
                     (_now(), row["id"], "human_discarded", actor))
        conn.commit()
    return {"discarded": True, "proposal_id": row["id"], "replayed": False}


def pending(capability: AuthorizedScope, limit: int = 20) -> dict:
    s=require_issued_scope(capability)
    if type(limit)!=int or not 1<=limit<=50:
        raise ValueError("INVALID_LIMIT")
    with closing(_connect()) as conn, conn:
        rows=conn.execute("""SELECT id,title,status,expires_at FROM proposals
           WHERE namespace=? AND process_id=?
           ORDER BY created_at DESC LIMIT ?""",
           (s.namespace,s.process_id,limit)).fetchall()
        return {"proposals":[dict(row) for row in rows]}
