"""G14-H OCR R02 contract crosswalk: metadata-only synthetic validation.

Does not perform OCR, call a provider, trust source identity, read clients,
write documents, run an external parser or create approved memories.
Input data is DEMO, page-level metadata; no extracted text is accepted.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import re

from .contracts import ContractViolation
from .process_learning import AdministrativeProcess, SyntheticOwnerOnly

_SHA = re.compile(r"^[a-f0-9]{64}$")
_REF = re.compile(r"^[A-Za-z0-9_.:/-]{3,200}$")
_KINDS = frozenset({
    "NATIVE", "OCR_READABLE", "LOW_CONFIDENCE", "EMPTY",
    "GRAPHIC", "TECHNICAL", "INVALID",
})
_KNOWN_FORMATS = frozenset({"PDF", "DWG", "KML", "SHP", "GEOJSON"})
_NON_OCR_ROUTES = {
    "DWG": "CAD_ANALYZER_REQUIRED",
    "KML": "KML_SAFE_PARSER_REQUIRED",
    "SHP": "SHAPESET_VALIDATOR_REQUIRED",
    "GEOJSON": "GEOJSON_STRUCTURAL_VALIDATION_REQUIRED",
}
_EXCEPTION_CODES = frozenset({
    "PAGE_UNREADABLE", "ROTATION_RETRY_EXHAUSTED", "LOW_CONFIDENCE",
    "SERVICE_EXCEPTION_REPORT", "KML_ENCODING_CONVERSION_REQUIRED",
    "SHAPESET_MISSING_DBF", "PROVIDER_FAILURE_SYNTHETIC",
    "SIZE_LIMIT", "PAGE_LIMIT",
})
_MAX_PAGES = 64
_MAX_ATTEMPTS = 3


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_ref(value: str):
    if not isinstance(value, str) or not _REF.fullmatch(value):
        raise ContractViolation("OCR_METADATA_IDENTIFIER_INVALID")


def _require_digest(value: str):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise ContractViolation("OCR_METADATA_DIGEST_INVALID")


def _check_chunks(chunks, total: int, completed: bool) -> set[int]:
    if not isinstance(chunks, (tuple, list)):
        raise ContractViolation("OCR_CHUNK_CONTRACT_INVALID")
    seen: set[int] = set()
    next_page = 1
    for chunk in chunks:
        if (not isinstance(chunk, (tuple, list)) or len(chunk) != 2
                or not all(_is_int(n) for n in chunk)):
            raise ContractViolation("OCR_CHUNK_CONTRACT_INVALID")
        start, end = chunk
        if start != next_page or not start <= end <= total or (end-start+1) > 8:
            raise ContractViolation("OCR_CHUNK_CONTRACT_INVALID")
        seen.update(range(start, end+1))
        next_page = end+1
    if completed and (not seen or len(seen) != total):
        raise ContractViolation("OCR_PAGE_COVERAGE_INCOMPLETE")
    return seen


def preview_ocr_r02_contract(
    *, owner: SyntheticOwnerOnly, claimed_owner: str,
    process: AdministrativeProcess, document_id: str, source_ref: str,
    source_version: str, source_sha256: str, format_kind: str,
    execution_state: str, total_pages: int, chunks: tuple,
    pages: tuple[dict, ...], exceptions: tuple[str, ...] = (),
) -> dict:
    """Validate synthetic OCR R02 event semantics, not operational evidence.

    Every completed PDF must have ordered, nonoverlapping <=8-page chunks
    covering every page and page-level quality. A completed *job* does not
    imply a legible *document*. Non-OCR formats are routed only by metadata.
    """
    if not isinstance(owner, SyntheticOwnerOnly):
        raise ContractViolation("OWNER_FIXTURE_REQUIRED")
    owner.require(claimed_owner)
    if not isinstance(process, AdministrativeProcess):
        raise ContractViolation("INVALID_PROCESS")
    for value in (document_id, source_ref, source_version):
        _require_ref(value)
    if not document_id.startswith("DOC_DEMO_") or "FILE_DEMO_" not in source_ref:
        raise ContractViolation("SYNTHETIC_DOCUMENT_ONLY")
    _require_digest(source_sha256)
    if format_kind not in _KNOWN_FORMATS:
        raise ContractViolation("OCR_FORMAT_UNSUPPORTED")
    if execution_state not in {"completed", "partial", "failed", "routed"}:
        raise ContractViolation("OCR_EXECUTION_STATE_INVALID")
    if not isinstance(pages, tuple) or not isinstance(exceptions, tuple):
        raise ContractViolation("OCR_METADATA_SHAPE_INVALID")
    if any(not isinstance(exc, str) or exc not in _EXCEPTION_CODES
           for exc in exceptions):
        raise ContractViolation("OCR_EXCEPTION_CODE_INVALID")
    if format_kind != "PDF":
        if (total_pages != 0 or pages or chunks or execution_state not in {"routed", "failed"}):
            raise ContractViolation("NON_OCR_ROUTING_REQUIRED")
        route = _NON_OCR_ROUTES[format_kind]
        if "SERVICE_EXCEPTION_REPORT" in exceptions:
            route = "INVALID_EXPORT_NO_OCR"
        elif format_kind == "KML" and "KML_ENCODING_CONVERSION_REQUIRED" in exceptions:
            route = "DERIVED_UTF8_COPY_REQUIRED"
        elif format_kind == "SHP" and "SHAPESET_MISSING_DBF" in exceptions:
            route = "INCOMPLETE_SHAPESET"
        quality = "NOT_APPLICABLE"
        page_counts = {}
        coverage = True
    else:
        if execution_state == "routed":
            raise ContractViolation("OCR_EXECUTION_STATE_INVALID")
        if not _is_int(total_pages) or not 1 <= total_pages <= _MAX_PAGES:
            raise ContractViolation("OCR_PAGE_LIMIT_INVALID")
        observed = _check_chunks(chunks, total_pages, execution_state == "completed")
        page_numbers: set[int] = set()
        kinds = []
        for page in pages:
            if not isinstance(page, dict) or set(page) != {
                "page", "quality", "confidence", "attempts", "text_sha256"
            }:
                raise ContractViolation("OCR_PAGE_METADATA_INVALID")
            number, kind = page["page"], page["quality"]
            if (not _is_int(number) or not 1 <= number <= total_pages
                    or number in page_numbers or number not in observed):
                raise ContractViolation("OCR_PAGE_NUMBER_INVALID")
            if kind not in _KINDS:
                raise ContractViolation("OCR_PAGE_QUALITY_INVALID")
            confidence, attempts = page["confidence"], page["attempts"]
            if (confidence is not None and (
                    isinstance(confidence, bool)
                    or not isinstance(confidence, (int, float))
                    or not 0 <= confidence <= 1)):
                raise ContractViolation("OCR_CONFIDENCE_INVALID")
            if not _is_int(attempts) or not 0 <= attempts <= _MAX_ATTEMPTS:
                raise ContractViolation("OCR_ATTEMPTS_INVALID")
            if kind == "OCR_READABLE" and (attempts < 1 or confidence is None
                                            or confidence < 0.75):
                raise ContractViolation("OCR_QUALITY_CONTRADICTION")
            if kind == "LOW_CONFIDENCE" and (
                    attempts < 1 or confidence is None or confidence >= 0.75):
                raise ContractViolation("OCR_QUALITY_CONTRADICTION")
            if kind == "NATIVE" and attempts != 0:
                raise ContractViolation("OCR_QUALITY_CONTRADICTION")
            digest = page["text_sha256"]
            if digest is not None:
                _require_digest(digest)
            if kind in ("OCR_READABLE", "NATIVE") and digest is None:
                raise ContractViolation("OCR_TEXT_DIGEST_REQUIRED")
            page_numbers.add(number)
            kinds.append(kind)
        coverage = len(page_numbers) == total_pages and page_numbers == observed
        if execution_state == "completed" and not coverage:
            raise ContractViolation("OCR_PAGE_COVERAGE_INCOMPLETE")
        page_counts = dict(sorted(Counter(kinds).items()))
        if execution_state != "completed" or not coverage:
            quality = "INCOMPLETE"
        elif all(kind in {"NATIVE", "OCR_READABLE"} for kind in kinds):
            quality = "LEGIBLE_ALL_PAGES"
        else:
            quality = "NEEDS_DOCUMENT_REVIEW"
        route = "PDF_PAGE_REVIEW" if quality == "NEEDS_DOCUMENT_REVIEW" else "PDF_TEXT_OR_OCR"
    digest = sha256(json.dumps({
        "process_key": process.process_key, "process_id": process.process_id,
        "document_id": document_id, "source_ref": source_ref,
        "source_version": source_version, "source_sha256": source_sha256,
        "format_kind": format_kind, "execution_state": execution_state,
        "total_pages": total_pages, "chunks": chunks,
        "pages": pages, "exceptions": exceptions,
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": "gaia.g14h-ocr-r02-metadata-preview.v1",
        "process_id": process.process_id,
        "process_key": process.process_key,
        "document_id": document_id,
        "source_ref": source_ref,
        "source_version": source_version,
        "source_sha256": source_sha256,
        "job_state": execution_state.upper(),
        "document_quality": quality,
        "format_kind": format_kind,
        "route": route,
        "total_pages": total_pages,
        "pages_accounted": len(pages),
        "all_pages_accounted": coverage,
        "quality_counts": page_counts,
        "safe_preview_fingerprint": digest,
        "eligible_for_verified_document_evidence": False,
        "requires_source_authentication": True,
        "requires_document_review": True,
        "memory_approved": False,
        "qdrant_written": False,
        "provider_connected": False,
        "actual_ocr_performed": False,
    }
