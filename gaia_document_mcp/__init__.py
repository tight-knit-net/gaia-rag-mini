"""GAIA Document MCP — contract kernel only; no MCP server or effectful adapters."""
from .contracts import ContractViolation, DocumentEvent, DocumentSource, Evidence
from .pipeline import KnowledgeCapture, ToolSpec, TOOL_CATALOG
from .trust import ReviewAttestation, ReviewProofVerifier

__all__ = [
    "ContractViolation", "DocumentEvent", "DocumentSource", "Evidence",
    "KnowledgeCapture", "ToolSpec", "TOOL_CATALOG",
    "ReviewAttestation", "ReviewProofVerifier",
]

