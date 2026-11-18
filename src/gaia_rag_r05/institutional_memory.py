"""R07 institutional memory assessment. Read-only; NEVER persists or approves.

An approved memory is evidence of a reviewed summary, not an official act.
Supersession here means a *candidate for human review*, not mutation of the
previous Qdrant point. All decisions must preserve source/provenance.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Iterable

KINDS = frozenset({
    "registro_caso", "procedimento", "modelo", "norma", "precedente",
    "licao_aprendida", "decisao_interna", "pendencia", "simulacao",
})
EVIDENCE = frozenset({"alegada", "documentada", "confirmada", "simulada"})
_MAX_TEXT = 4000
_MAX_REF = 300


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _require_text(value: str, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("INVALID_" + name)
    return value.strip()


def _point_id(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        return str(uuid.UUID(value))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("INVALID_PRIOR_POINT_ID") from None


def _safe_previous(items: Iterable[dict], process_id: str) -> list[dict]:
    safe = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("INVALID_PREVIOUS_MEMORY")
        if item.get("process_id") != process_id or item.get("approved") is not True:
            raise ValueError("PREVIOUS_SCOPE_UNVERIFIED")
        # Only emit metadata and short controlled excerpts, not the full corpus.
        safe.append(item)
    return safe


def preview(
    *,
    process_id: str,
    title: str,
    summary: str,
    source_ref: str,
    kind: str,
    evidence_status: str,
    previous: Iterable[dict],
    prior_point_id: str | None = None,
    coverage_complete: bool = False,
) -> dict:
    """Compare an institutional candidate with VERIFIED same-process memories.

    No update/revoke, automatic learning, approval or cross-client copying.
    The LLM/human must verify documentary quality and legal applicability.
    """
    process_id = _require_text(process_id, "PROCESS_ID", 200)
    title = _require_text(title, "TITLE", 160)
    summary = _require_text(summary, "SUMMARY", _MAX_TEXT)
    source_ref = _require_text(source_ref, "SOURCE_REF", _MAX_REF)
    if kind not in KINDS:
        raise ValueError("INVALID_MEMORY_KIND")
    if evidence_status not in EVIDENCE:
        raise ValueError("INVALID_EVIDENCE_STATUS")
    prior_point_id = _point_id(prior_point_id)
    memories = _safe_previous(previous, process_id)
    exact = []
    same_source_revision = []
    related = []
    prior_found = False
    for item in memories:
        ident = item.get("id")
        if ident is not None:
            ident = str(ident)
        old_text = item.get("text", "")
        old_title = item.get("title", "")
        old_source = item.get("source_ref", "")
        if prior_point_id and ident == prior_point_id:
            prior_found = True
        if _normalized(old_text) == _normalized(summary):
            exact.append({"point_id": ident, "source_ref": old_source})
        elif old_source == source_ref:
            same_source_revision.append({
                "point_id": ident, "source_ref": old_source,
                "reason": "same_source_changed_summary",
            })
        elif _normalized(old_title) == _normalized(title):
            related.append({"point_id": ident, "source_ref": old_source})
    if prior_point_id and not prior_found:
        if coverage_complete:
            raise ValueError("PRIOR_NOT_FOUND_IN_PROCESS")
        # Prevent false assertion when list pagination is incomplete.
        previous_unverified = True
    else:
        previous_unverified = False

    if evidence_status == "simulada" or kind == "simulacao":
        disposition = "EXEMPLO_NAO_PROMOVER"
    elif exact:
        disposition = "DUPLICATA_NAO_PROPOR"
    elif prior_point_id or same_source_revision:
        disposition = "REVISAO_CANDIDATA"
    elif related:
        disposition = "RELACAO_A_VERIFICAR"
    else:
        disposition = "NOVA_CANDIDATA"

    blockers = []
    if evidence_status in {"alegada", "simulada"}:
        blockers.append("EVIDENCIA_INSUFICIENTE_PARA_FATO")
    if kind == "simulacao":
        blockers.append("SIMULACAO_NAO_E_PRECEDENTE_REAL")
    if exact:
        blockers.append("DUPLICIDADE_IDENTIFICADA")
    if previous_unverified:
        blockers.append("MEMORIA_ANTERIOR_NAO_VERIFICADA")
    if not coverage_complete:
        blockers.append("COBERTURA_PARCIAL_DO_HISTORICO")

    return {
        "process_id": process_id,
        "kind": kind,
        "evidence_status": evidence_status,
        "title": title,
        "source_ref": source_ref,
        "disposition": disposition,
        "exact_duplicates": exact[:20],
        "same_source_revisions": same_source_revision[:20],
        "related_titles": related[:20],
        "prior_point_id": prior_point_id,
        "prior_verified": bool(prior_point_id and prior_found),
        "prior_history_complete": coverage_complete,
        "blockers": blockers,
        "next_step": (
            "CANDIDATO_EDITORIAL_SEM_GRAVACAO"
            if blockers or disposition != "NOVA_CANDIDATA"
            else "CONFERIR_DOCUMENTO_E_APROVACAO_ANTES_DE_PREPARAR_PROPOSTA"
        ),
        "document_approval_required": True,
        "human_memory_approval_required": True,
        "old_points_unchanged": True,
        "persisted": False,
        "note": (
            "Uma revisão mais precisa não revoga automaticamente a memória anterior. "
            "Registrar antes/depois, origem, data, jurisdição, limite e link de linhagem; "
            "obter aprovação documental e clique humano no portal existente."
        ),
    }
