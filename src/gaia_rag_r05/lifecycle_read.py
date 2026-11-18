"""R07 read-only lifecycle utilities for exact-process Qdrant and review ledger.

No filesystem creation, SQL mutation, Qdrant write, external LLM call, or
automatic proposal approval. Only approved points are supplied by ScopedReads.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from pathlib import Path


def collect_process(reader, capability, *, max_items: int = 300, page_size: int = 100,
                    start_offset: str | int | None = None):
    """Bounded pagination with explicit incomplete-coverage warning."""
    if type(max_items) is not int or not 1 <= max_items <= 300:
        raise ValueError("INVALID_MAX_ITEMS")
    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise ValueError("INVALID_PAGE_SIZE")
    items, cursor, seen_ids, seen_cursors = [], start_offset, set(), set()
    if start_offset is not None:
        seen_cursors.add(str(start_offset))
    while len(items) < max_items:
        requested = min(page_size, max_items - len(items))
        page = reader.list_process(capability, limit=requested, offset=cursor)
        if not isinstance(page, dict) or not isinstance(page.get("items"), list):
            raise RuntimeError("INVALID_PAGE")
        for item in page["items"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), (str, int)):
                raise RuntimeError("INVALID_PAGE_ITEM")
            ident = str(item["id"])
            if ident in seen_ids:
                raise RuntimeError("REPEATED_POINT")
            seen_ids.add(ident)
            items.append(item)
        new_cursor = page.get("next_offset")
        if new_cursor is None:
            return {"items": items, "next_offset": None, "complete": True}
        if not page["items"] or str(new_cursor) in seen_cursors:
            raise RuntimeError("PAGINATION_STALLED")
        seen_cursors.add(str(new_cursor))
        cursor = new_cursor
    return {"items": items, "next_offset": cursor, "complete": False}


def process_timeline(reader, capability, *, max_items: int = 300):
    """Chronology of approved memories; timestamps reflect memory approval."""
    page = collect_process(reader, capability, max_items=max_items)
    rows = []
    for item in page["items"]:
        at = item.get("approved_at")
        if not isinstance(at, (int, float)) or isinstance(at, bool):
            at = None
        rows.append({
            "point_id": item["id"], "process_id": item.get("process_id"),
            "title": item.get("title"), "kind": item.get("kind"),
            "source_ref": item.get("source_ref"),
            "approved_at": at, "approved_by": item.get("approved_by"),
        })
    rows.sort(key=lambda x: (x["approved_at"] is None,
                             -(x["approved_at"] or 0), str(x["point_id"])))
    return {
        "items": rows,
        "truncated": not page["complete"],
        "next_offset": page["next_offset"],
        "sort": "approved_at_desc_nulls_last",
        "warning": None if page["complete"] else "TIMELINE_PARTIAL",
    }


def process_export(reader, capability, *, max_items: int = 100,
                   offset: str | int | None = None):
    """Owned, bounded export of approved summaries, never source documents."""
    page = collect_process(reader, capability, max_items=max_items,
                           start_offset=offset)
    payload = json.dumps(page["items"], ensure_ascii=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "entries": page["items"], "count": len(page["items"]),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "truncated": not page["complete"],
        "next_offset": page["next_offset"],
        "format": "gaia-approved-memory-json-v1",
        "warning": None if page["complete"] else "EXPORT_PARTIAL",
    }


def _ledger_path() -> Path:
    path = Path(os.getenv("GAIA_RAG_REVIEW_DB", "/state/reviews.sqlite3"))
    if not path.is_absolute():
        raise ValueError("INVALID_REVIEW_DB")
    return path


def _read_ledger():
    """Never create a file or table during a read operation."""
    path = _ledger_path()
    if not path.is_file():
        return None
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=4)
    con.row_factory = sqlite3.Row
    return con


def pending_reviews(namespace: str, process_id: str, *, limit: int = 20,
                    offset: int = 0):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("INVALID_LIMIT")
    if type(offset) is not int or not 0 <= offset <= 100000:
        raise ValueError("INVALID_OFFSET")
    con = _read_ledger()
    if con is None:
        return {"proposals": [], "storage_available": False,
                "next_offset": None, "coverage": "unavailable"}
    with con:
        rows = con.execute(
            "SELECT id,title,status,expires_at,process_id,created_at "
            "FROM proposals WHERE namespace=? AND process_id=? AND status='pending' "
            "ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?",
            (namespace, process_id, limit + 1, offset)).fetchall()
    result = [dict(row) for row in rows[:limit]]
    return {
        "proposals": result, "storage_available": True,
        "next_offset": offset + limit if len(rows) > limit else None,
        "coverage": "current_r07_ledger_only",
    }


def approval_events(namespace: str, *, process_id: str = "",
                    limit: int = 50, offset: int = 0):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("INVALID_LIMIT")
    if type(offset) is not int or not 0 <= offset <= 100000:
        raise ValueError("INVALID_OFFSET")
    con = _read_ledger()
    if con is None:
        return {"events": [], "storage_available": False,
                "next_offset": None, "coverage": "unavailable"}
    sql = ("SELECT a.id,a.at,a.proposal_id,a.event,a.actor,p.process_id "
           "FROM audit a JOIN proposals p ON p.id=a.proposal_id "
           "WHERE p.namespace=?")
    params = [namespace]
    if process_id:
        sql += " AND p.process_id=?"
        params.append(process_id)
    sql += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
    params.extend([limit + 1, offset])
    with con:
        rows = con.execute(sql, params).fetchall()
    return {
        "events": [dict(row) for row in rows[:limit]],
        "storage_available": True,
        "next_offset": offset + limit if len(rows) > limit else None,
        "coverage": "current_r07_ledger_only",
    }


def proposal_statistics(namespace: str, *, process_id: str = ""):
    """Counts of the local proposal ledger, not Qdrant point counts."""
    con = _read_ledger()
    if con is None:
        return {"storage_available": False, "proposal_counts": None,
                "coverage": "unavailable"}
    sql = "SELECT status,COUNT(*) AS n FROM proposals WHERE namespace=?"
    params = [namespace]
    if process_id:
        sql += " AND process_id=?"
        params.append(process_id)
    sql += " GROUP BY status"
    with con:
        rows = con.execute(sql, params).fetchall()
    counts = {"pending": 0, "approving": 0, "approved": 0, "discarded": 0}
    for row in rows:
        counts[row["status"]] = row["n"]
    return {"storage_available": True, "proposal_counts": counts,
            "coverage": "current_r07_ledger_only"}


_STOP = frozenset({"para", "como", "com", "esta", "esse", "isso", "pela", "pelo",
                   "sobre", "entre", "quando", "ainda", "documento", "processo",
                   "cliente", "depois", "antes", "serao", "foram", "neste", "deste"})
_CATEGORIES = {
    "procedimento": ("triagem", "fluxo", "procedimento", "protocolo", "conferencia"),
    "modelo": ("modelo", "minuta", "contrato", "procuracao", "requerimento"),
    "pendencia": ("pendencia", "pendente", "incompleto", "bloqueio", "revisar"),
    "norma": ("legislacao", "norma", "decreto", "resolucao", "portaria"),
}


def index_candidate_preview(*, process_id: str, title: str, summary: str,
                            source_ref: str, evidence_status: str = "documentada"):
    """Local metadata preview; no external provider receives customer content."""
    for name, value, maximum in (
        ("PROCESS_ID", process_id, 200), ("TITLE", title, 160),
        ("SUMMARY", summary, 4000), ("SOURCE_REF", source_ref, 300),
    ):
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError("INVALID_" + name)
    if evidence_status not in {"alegada", "documentada", "confirmada", "simulada"}:
        raise ValueError("INVALID_EVIDENCE_STATUS")
    from .institutional_memory import _normalized
    normalized = "".join(ch for ch in unicodedata.normalize(
        "NFKD", _normalized(title + " " + summary))
        if not unicodedata.combining(ch))
    words = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", normalized)
    tags = sorted({w[:48] for w in words if w not in _STOP})[:12]
    matches = [category for category, terms in _CATEGORIES.items()
               if any(term in normalized for term in terms)]
    category = matches[0] if matches else "registro_caso"
    return {
        "process_id": process_id.strip(), "title": title.strip(),
        "source_ref": source_ref.strip(),
        "summary_sha256": hashlib.sha256(summary.strip().encode("utf-8")).hexdigest(),
        "suggested_kind": category, "suggested_tags": tags,
        "evidence_status": evidence_status,
        "recommend_review": evidence_status in {"documentada", "confirmada"},
        "document_approval_required": True,
        "human_memory_approval_required": True,
        "automatic_save": False, "persisted": False, "external_llm_used": False,
        "next_step": "REVISAR_FONTE_E_PREPARAR_PROPOSTA_COM_APROVACAO_HUMANA",
    }
