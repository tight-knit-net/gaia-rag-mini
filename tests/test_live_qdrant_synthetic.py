"""GAIA R05 host integration test: real disposable Qdrant, synthetic tenants only."""
from __future__ import annotations
import json
import time
import uuid
from urllib import request, error
from gaia_rag_r05.authz import AccessDenied, Authorizer, Principal, Scope
from gaia_rag_r05.scoped_reads import ScopedReads

URL = "http://gaia-rag-r05-qdrant-test:6333"
COLLECTION = "gaia_r05_demo"
NAMESPACE = "demo"
ISSUER = "https://demo.cloudflareaccess.com"
AUDIENCE = "DEMO-AUDIENCE-ONLY"
SA1 = Scope(NAMESPACE, "DEMO-TENANT-A", "DEMO-A1")
SA2 = Scope(NAMESPACE, "DEMO-TENANT-A", "DEMO-A2")
SB1 = Scope(NAMESPACE, "DEMO-TENANT-B", "DEMO-B1")
A = Principal("demo-a@example.invalid", ISSUER, AUDIENCE)
B = Principal("demo-b@example.invalid", ISSUER, AUDIENCE)
def ident(n):
    return str(uuid.UUID(int=n))
def req(method, path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    q = request.Request(URL+path, data=payload, method=method,
                        headers={"Content-Type": "application/json"})
    with request.urlopen(q, timeout=8) as result:
        return json.load(result)

def wait_for_qdrant():
    for _ in range(60):
        try:
            req("GET", "/collections")
            return
        except Exception:
            time.sleep(.25)
    raise RuntimeError("QDRANT_SYNTHETIC_STARTUP_FAILED")

def sample(n, scope, *, approved=True, tenant=True, source="DEMO-SOURCE"):
    payload = {"namespace":scope.namespace, "process_id":scope.process_id,
               "approved":approved, "source_ref":source, "text":"DEMOS ONLY"}
    if tenant:
        payload["tenant_id"]=scope.tenant_id
    return {"id":ident(n), "vector":[1.0,0.0,0.0,0.0], "payload":payload}

def run():
    wait_for_qdrant()
    assert req("PUT",f"/collections/{COLLECTION}",{"vectors":{"size":4,"distance":"Cosine"}})["status"]=="ok"
    rows = [
        sample(1,SA1),sample(2,SA2),sample(3,SB1),
        sample(4,SA1,approved=False),sample(5,SA1,tenant=False),
        sample(6,SA1,source="DEMO-OTHER"),
    ]
    assert req("PUT",f"/collections/{COLLECTION}/points?wait=true",{"points":rows})["status"]=="ok"
    request_log = []
    def real_transport(method,path,data=None):
        request_log.append((method,path,data))
        # Only the embeddings are mocked because local Qdrant lacks cloud text
        # inference. Qdrant executes every actual payload filter and point read.
        if method=="POST" and path.endswith("/query") and data and isinstance(data.get("query"),dict):
            data = {**data, "query":[1.0,0.0,0.0,0.0]}
        return req(method,path,data)
    auth = Authorizer({A.subject:[SA1,SA2],B.subject:[SB1]},
                      expected_issuer=ISSUER,expected_audience=AUDIENCE)
    reader = ScopedReads(real_transport,COLLECTION,"DEMO-embeddings")
    a1 = auth.require(A,SA1)
    a2 = auth.require(A,SA2)
    b1 = auth.require(B,SB1)

    result=reader.list_process(a1)
    ids={p["id"] for p in result["items"]}
    assert ids=={ident(1),ident(6)},("list_process",ids)
    print("PASS real Qdrant list_process: exact tenant, process and approved")

    assert reader.by_uuid(a1,ident(1))["found"] is True
    assert reader.by_uuid(a1,ident(3))=={"found":False}
    assert reader.by_uuid(a1,ident(5))=={"found":False}
    print("PASS real Qdrant UUID: owned, cross-tenant and missing-tenant")

    source=reader.by_source(a1,"DEMO-SOURCE")["items"]
    assert [p["id"] for p in source]==[ident(1)],source
    print("PASS real Qdrant by_source: no cross-tenant records")

    hits=reader.search(a1,"DEMO query",limit=15)["hits"]
    assert {p["id"] for p in hits}=={ident(1),ident(6)}
    print("PASS real Qdrant semantic query filters (synthetic vector only)")

    similar=reader.similar((a1,a2),"DEMO query","DEMO-A1",limit=12)["similar"]
    assert {p["id"] for p in similar}=={ident(2)}
    print("PASS real Qdrant similar: only separately authorized process")

    before=len(request_log)
    try:
        reader.list_process(auth.require(B,SA1))
        assert False,"cross-tenant request allowed"
    except AccessDenied:
        pass
    assert len(request_log)==before
    print("PASS cross-tenant authorization denied before backend read")

    try:
        reader.similar((a2,),"DEMO","DEMO-A1")
        assert False,"similarity allowed without grant for current process"
    except AccessDenied:
        pass
    print("PASS missing current-process grant denied")
    print("GAIA_REAL_SYNTHETIC_TESTS_PASS=7")

if __name__=="__main__":
    run()
