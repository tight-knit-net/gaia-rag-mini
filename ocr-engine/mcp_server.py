import os
import engine
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GAIA OCR Engine - Internal Test Lab",
              host="127.0.0.1",port=18789,
              stateless_http=True,json_response=True)

@mcp.tool()
def ocr_process(document_id:str, tenant:str="test") -> dict:
    """Perform mock OCR (or gated iLoveAPI OCR) on a preuploaded document."""
    result=engine.process(tenant,document_id)
    return result or {"error":"not_found"}

@mcp.tool()
def ocr_document(document_id:str, tenant:str="test") -> dict:
    """Read extracted OCR text and SHA256 for a tenant-owned document."""
    return engine.get_record(tenant,document_id) or {"error":"not_found"}

@mcp.tool()
def ocr_search(query:str, tenant:str="test") -> list[dict]:
    """Find OCR documents in the temporary SQL full-text index."""
    return engine.search(tenant,query)

if __name__ == "__main__":
    engine.setup()
    mcp.run(transport="streamable-http")

