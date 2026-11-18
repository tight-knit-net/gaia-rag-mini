# GAIA Document MCP — isolated development scaffold

State: **phase 0, contract kernel and synthetic tests, no MCP server or external integration active**.

## Goal
A single document-processing MCP for the GAIA ecosystem, with adapters for Stirling-PDF, DocuSeal, GroqCloud, Google Drive/Docs/Sheets and the existing nomenclature pipeline, sending **reviewed institutional candidates** to GAIA RAG R07/R06. The GAIA RAG core remains the sole controller of approved Qdrant memories.

## Implemented now
- Pure Python versioned document-source/evidence/event contract.
- Local in-memory synthetic operation receipts and idempotent fingerprints.
- Fail-closed memory preview with explicit blocks and provenance.
- High-level intended tool capability catalog and conservative feature flags.
- Offline unittest suite and branch-only GitHub Actions workflow.

## Not implemented / not authorized
No network server, live MCP registration, OAuth/token exchange, Drive read/write, PDF OCR, Groq invocation, DocuSeal API, persistent operational store, R07 call, Qdrant write, deployment or handling of real documents. No change to app/server.py or any parent branch.

## Offline validation
```bash
python -m unittest discover -s tests -p test_document_mcp.py -v
```

See `docs/document-mcp/` for source audit, architecture, requirements, integration matrix, security and acceptance gates.

