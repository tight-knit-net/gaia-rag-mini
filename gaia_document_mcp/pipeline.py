"""Metadata-only operational capture; institutional memory remains PREVIEW ONLY."""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import DocumentEvent, ContractViolation
from .trust import ReviewAttestation, ReviewProofVerifier

@dataclass(frozen=True)
class ToolSpec:
    name: str
    effect: str
    adapter: str
    requires_approval: bool

# Planned capabilities, not registered MCP tools.
TOOL_CATALOG: tuple[ToolSpec, ...] = (
    ToolSpec("document.inspect", "read", "drive", False),
    ToolSpec("document.ocr", "derived_file", "stirling", False),
    ToolSpec("document.pdf_transform", "derived_file", "stirling", False),
    ToolSpec("document.catalog_preview", "preview", "gaia_nom", False),
    ToolSpec("document.name_preview", "preview", "gaia_nom", False),
    ToolSpec("document.workspace_read", "read", "google", False),
    ToolSpec("document.workspace_write", "external_write", "google", True),
    ToolSpec("document.prepare_signature", "external_write", "docuseal", True),
    ToolSpec("document.send_signature", "external_write", "docuseal", True),
    ToolSpec("document.external_ai", "external_disclosure", "groq", True),
    ToolSpec("document.memory_preview", "preview", "rag_r07", False),
    ToolSpec("document.memory_prepare", "approval_workflow", "rag_r06", True),
)

class KnowledgeCapture:
    """Receipts in RAM are ONLY synthetic fixtures; never claim persistence."""

    def __init__(self) -> None:
        self._receipts: dict[str, dict] = {}

    def capture(self, event: DocumentEvent) -> dict:
        if not isinstance(event, DocumentEvent):
            raise ContractViolation("INVALID_EVENT")
        e = event.envelope()
        key = e["event_key"]
        if key not in self._receipts:
            self._receipts[key] = {
                "schema": "gaia.document-receipt.v2",
                **{k: v for k, v in e.items() if k != "schema"},
                "persisted": False, "drive_write_performed": False,
                "memory_write_performed": False,
            }
        return dict(self._receipts[key])

    def memory_preview(self, event: DocumentEvent, *,
                       proof: ReviewAttestation | None = None,
                       verifier: ReviewProofVerifier | None = None) -> dict:
        self.capture(event)
        blockers = []
        if event.status != "completed":
            blockers.append("OPERATION_NOT_COMPLETED")
        if event.source.client_id is None or event.source.process_id is None:
            blockers.append("CASE_BINDING_PENDING")
        if event.source.sha256_original is None:
            blockers.append("SOURCE_HASH_UNKNOWN")
        if not event.source_verified:
            blockers.append("SOURCE_NOT_VERIFIED")
        if not event.client_verified:
            blockers.append("CLIENT_NOT_VERIFIED")
        if not event.fields_verified:
            blockers.append("FIELDS_NOT_VERIFIED")
        if not event.evidence or not all(x.reviewer_verified for x in event.evidence):
            blockers.append("EVIDENCE_NOT_REVIEWED")
        if event.operation == "ocr":
            if event.provider.lower() == "mock":
                blockers.append("OCR_MOCK_NOT_EVIDENCE")
            if not event.ocr_reviewed:
                blockers.append("OCR_NOT_REVIEWED")
        if not event.summary.strip():
            blockers.append("NO_DURABLE_KNOWLEDGE_SUMMARY")
        if event.external_llm_used:
            blockers.append("EXTERNAL_LLM_DATA_POLICY_REVIEW_REQUIRED")
        if not (isinstance(verifier, ReviewProofVerifier) and verifier.verify(event, proof)):
            blockers.append("TRUSTED_REVIEW_ATTESTATION_MISSING_OR_INVALID")
        # This is editorial eligibility only. Document approval and memory click
        # are two different, independent steps owned by the R06 backend.
        return {
            "schema": "gaia.memory-candidate.v2",
            "candidate": not blockers,
            "blockers": blockers,
            "event_key": event.fingerprint(),
            "process_id": event.source.process_id,
            "source_ref": event.source.source_ref,
            "document_sha256": event.source.sha256_original,
            "summary_sha256": event.envelope()["summary_sha256"],
            "title": "Conhecimento documental proposto",
            "summary": event.summary.strip() if not blockers else None,
            "document_approval_ref": None,
            "requires_document_registry_approval": True,
            "requires_r06_human_approval": True,
            "r07_comparison_pending": True,
            "persisted": False,
            "old_points_unchanged": True,
        }

