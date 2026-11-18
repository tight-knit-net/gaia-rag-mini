"""GAIA Document MCP: isolated, side-effect-free contract kernel (phase 0)."""
from .contracts import ContractViolation, DocumentEvent, DocumentSource, Evidence
from .pipeline import KnowledgeCapture, ToolSpec, TOOL_CATALOG
__all__ = ["ContractViolation", "DocumentEvent", "DocumentSource", "Evidence", "KnowledgeCapture", "ToolSpec", "TOOL_CATALOG"]

