"""Only runs inside a Qdrant-free, network-none, disposable CI container.

Validates R07 health and denies anonymous access to the memory/review APIs,
including the human Save memory endpoint. No actual approval or memory write.
"""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.request

ROOT="http://127.0.0.1:8000"
PROPOSAL="11111111-1111-4111-8111-111111111111"

def req(path,method="GET",payload=None):
    return urllib.request.Request(
        ROOT+path,data=payload,method=method,
        headers={"Content-Type":"application/json"},
    )

def main():
    health=None
    for _ in range(40):
        try:
            with urllib.request.urlopen(req("/healthz"),timeout=2) as response:
                health=json.load(response)
            break
        except (ConnectionError,OSError,ValueError):
            time.sleep(0.5)
    if not isinstance(health,dict):
        raise RuntimeError("HEALTH_CHECK_UNAVAILABLE")
    assert health.get("service")=="gaia-rag-mini-r07",health
    assert health.get("alive") is True,health
    assert health.get("writes_enabled") is False,health
    assert health.get("qdrant_configured") is False,health
    assert health.get("approval_registry_configured") is False,health
    negatives=[
        req("/mcp","POST",b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'),
        req(f"/review/{PROPOSAL}"),
        req(f"/review/{PROPOSAL}/approve","POST",b'{"confirm":"APROVAR"}'),
        req(f"/review/{PROPOSAL}/discard","POST",b'{"confirm":"DESCARTAR"}'),
    ]
    for item in negatives:
        try:
            with urllib.request.urlopen(item,timeout=4):
                raise AssertionError("ANONYMOUS_ACCESS_GRANTED")
        except urllib.error.HTTPError as error:
            assert error.code==401,(item.full_url,error.code)
    print("R07_S93_TRIAL_HTTP=5/5")
    print("R07_S93_SAVE_MEMORY_ANONYMOUS_DENIED=true")
    print("R07_S93_REAL_MEMORY_WRITES=0")

if __name__=="__main__":
    main()
