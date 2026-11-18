"""R06 end-to-end against a disposable REAL Qdrant (no customer data)."""
import json
import os
import re
import sys
import time
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib import request

sys.path.insert(0, str(Path("/app/src")))
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient
import app.server as server

Q_URL=os.environ.get("GAIA_R06_QDRANT_TEST_URL","http://gaia-rag-r06-demo-qdrant:6333")
ISS="https://gaia-demo.cloudflareaccess.com"
AUD="GAIA-R06-TEST-AUDIENCE"
A="gaia.a@example.invalid"
B="gaia.b@example.invalid"
NS="gaia-demo"
TA="DEMO-TENANT-A"
TB="DEMO-TENANT-B"
PA="DEMO-PROCESS-A1"
PB="DEMO-PROCESS-B1"
DOC="DOCUMENTO DEMO FICTICIO — minuta de conveniencia aprovada internamente; nao houve protocolo."
SHA=hashlib.sha256(DOC.encode()).hexdigest()
SOURCE="DEMO-DOC-001"
APPROVAL="DEMO-APPROVAL-001"
POINTS=f"/collections/{server.COLLECTION}/points"
checks=0

def q(method,path,data=None):
    body=None if data is None else json.dumps(data).encode()
    req=request.Request(Q_URL+path,method=method,data=body,headers={"Content-Type":"application/json"})
    with request.urlopen(req,timeout=10) as response:
        return json.load(response)
def transport(method,path,data=None):
    if method=="PUT" and path.endswith("/points?wait=true") and data:
        data={**data,"points":[{**p,"vector":[1.,0,0,0]} for p in data["points"]]}
    if method=="POST" and path.endswith("/query") and data and isinstance(data.get("query"),dict):
        data={**data,"query":[1.,0,0,0]}
    return q(method,path,data)
def check(name,expected,actual=""):
    global checks
    if not expected:raise AssertionError(f"FAIL {name}: {actual}")
    checks+=1
    print(f"PASS {name}: {actual}",flush=True)
def count():
    return q("POST",POINTS+"/count",{"exact":True})["result"]["count"]
def main():
    for _ in range(50):
        try:
            q("GET","/collections")
            break
        except Exception:time.sleep(.2)
    else:raise RuntimeError("test Qdrant unavailable")
    assert q("PUT",f"/collections/{server.COLLECTION}",{"vectors":{"size":4,"distance":"Cosine"}})["status"]=="ok"
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    jwks=jwt.PyJWKClient
    class DemoJwks:
        def __init__(self,url):pass
        def get_signing_key_from_jwt(self,raw):
            return SimpleNamespace(key=key.public_key())
    jwt.PyJWKClient=DemoJwks
    def token(who):
        return jwt.encode({"iss":ISS,"aud":AUD,"email":who,"exp":int(time.time())+3600},
                          key,algorithm="RS256",headers={"kid":"R06-TEST"})
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        grants=root/"grants.json"
        docs=root/"documents.json"
        grants.write_text(json.dumps({"subjects":{
            A:[{"namespace":NS,"tenant_id":TA,"process_id":PA}],
            B:[{"namespace":NS,"tenant_id":TB,"process_id":PB}]}}))
        docs.write_text(json.dumps({"approved_documents":[{
           "namespace":NS,"tenant_id":TA,"process_id":PA,
           "source_ref":SOURCE,"approval_ref":APPROVAL,
           "document_sha256":SHA,"status":"approved"}]}))
        os.environ.update({
            "CF_ACCESS_TEAM_DOMAIN":ISS,
            "CF_ACCESS_AUD":AUD,
            "GAIA_RAG_GRANTS_FILE":str(grants),
            "GAIA_RAG_APPROVED_DOCS_FILE":str(docs),
            "GAIA_RAG_REVIEW_DB":str(root/"review.sqlite3"),
            "GAIA_RAG_REVIEW_BASE_URL":"https://gaia-demo.example.invalid",
            "GAIA_RAG_CSRF_SECRET":"R06-VERY-LONG-TEST-SECRET-ONLY-NO-PRODUCTION-012345",
            "GAIA_RAG_ENABLE_REVIEW":"1",
        })
        old=server._qrequest
        server._qrequest=transport
        try:
            with TestClient(server.app) as client:
                def call(method,params=None,identity=A,n=1):
                    return client.post("/mcp",headers={
                      "cf-access-jwt-assertion":token(identity),
                      "MCP-Protocol-Version":"2025-06-18",
                      "Accept":"application/json, text/event-stream",
                      "Content-Type":"application/json"},
                      json={"jsonrpc":"2.0","id":n,"method":method,"params":params or {}})
                def tool(name,args,identity=A):
                    r=call("tools/call",{"name":name,"arguments":args},identity)
                    j=r.json(); output=j.get("result",{})
                    data=output.get("structuredContent")
                    if data is None and output.get("content"):
                        data=json.loads(output["content"][0]["text"])
                    return data,output.get("isError"),r
                scope={"namespace":NS,"tenant_id":TA,"process_id":PA}
                bscope={"namespace":NS,"tenant_id":TB,"process_id":PB}
                tool_list=call("tools/list")
                tools={t["name"] for t in tool_list.json()["result"]["tools"]}
                required={"memory_process_start","memory_prepare_after_approval",
                          "memory_proposal_preview","memory_pending_reviews",
                          "gaia_skill_catalog","gaia_skill_read"}
                check("R06-01_TOOLS_PRESENT",required<=tools,",".join(sorted(required)))
                catalog,err,_=tool("gaia_skill_catalog",{})
                check("R06-02_SKILL_MANIFEST",not err and len(catalog["files"])>=10,str(len(catalog.get("files",[]))))
                skill,err,_=tool("gaia_skill_read",{"path":"SKILL.md"})
                check("R06-03_SKILL_READ",not err and "gaia-rag-processos-administrativos" in skill["content"])
                denied,err,_=tool("gaia_skill_read",{"path":"../../etc/passwd"})
                check("R06-04_PATH_TRAVERSAL_DENIED",err is True,"file read rejected")
                prepare={"title":"DEMO memoria de processo","summary":"DEMO: minuta interna aprovada; protocolo nao comprovado.",
                         "source_ref":SOURCE,"document_approval_ref":APPROVAL,
                         "document_sha256":SHA,**scope}
                other,err,_=tool("memory_prepare_after_approval",{**prepare,"tenant_id":TB,"process_id":PB})
                check("R06-05_OTHER_CLIENT_CANNOT_PROPOSE",err is True)
                docs.write_text('{"approved_documents":[]}')
                notapproved,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-06_NO_DOCUMENT_APPROVAL_DENIED",err is True)
                docs.write_text(json.dumps({"approved_documents":[{
                   "namespace":NS,"tenant_id":TA,"process_id":PA,
                   "source_ref":SOURCE,"approval_ref":APPROVAL,
                   "document_sha256":SHA,"status":"approved"}]}))
                proposal,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-07_CREATE_PROPOSAL",not err and proposal["status"]=="pending",str(proposal))
                ident=proposal["proposal_id"]
                check("R06-08_ZERO_WRITES_BEFORE_CLICK",count()==0,str(count()))
                again,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-09_DEDUPLICATE_PROPOSAL",not err and again["proposal_id"]==ident)
                listing,err,_=tool("memory_pending_reviews",scope)
                check("R06-10_LIST_PENDING",not err and len(listing["proposals"])==1)
                url=f"/review/{ident}"
                authhdr={"cf-access-jwt-assertion":token(A)}
                page=client.get(url,headers=authhdr)
                check("R06-11_REVIEW_HTML_AUTH",page.status_code==200 and "Aprovar e gravar" in page.text)
                csrf=re.search(r'name="csrf" value="([^"]+)"',page.text).group(1)
                bad=client.post(url+"/approve",data={"confirm":"APROVAR","csrf":"forged"},headers={**authhdr,"origin":"https://gaia-demo.example.invalid"})
                check("R06-12_BAD_CSRF_BLOCKED",bad.status_code==403 and count()==0)
                bad_origin=client.post(url+"/approve",data={"confirm":"APROVAR","csrf":csrf},headers={**authhdr,"origin":"https://evil.example.invalid"})
                check("R06-13_BAD_ORIGIN_BLOCKED",bad_origin.status_code==403 and count()==0)
                bpage=client.get(url,headers={"cf-access-jwt-assertion":token(B)})
                check("R06-14_CROSS_TENANT_BROWSER_DENIED",bpage.status_code==403)
                ok=client.post(url+"/approve",data={"confirm":"APROVAR","csrf":csrf},headers={**authhdr,"origin":"https://gaia-demo.example.invalid"})
                check("R06-15_HUMAN_CLICK_APPROVES",ok.status_code==200 and "confirmada" in ok.text,ok.status_code)
                check("R06-16_EXACTLY_ONE_QDRANT_POINT",count()==1,str(count()))
                replay=client.post(url+"/approve",data={"confirm":"APROVAR","csrf":csrf},headers={**authhdr,"origin":"https://gaia-demo.example.invalid"})
                check("R06-17_REPLAY_IDEMPOTENT",replay.status_code==200 and count()==1)
                obtained,err,_=tool("memory_list_process",scope)
                check("R06-18_READBACK_IN_NEW_TOOL_SESSION",not err and len(obtained["items"])==1 and obtained["items"][0]["tenant_id"]==TA)
                other,err,_=tool("memory_list_process",bscope,identity=B)
                check("R06-19_SECOND_TENANT_IS_EMPTY",not err and other["items"]==[])
                illicit,err,_=tool("memory_list_process",scope,identity=B)
                check("R06-20_OTHER_TENANT_CANNOT_READ_A",err is True)
                preview,err,_=tool("memory_proposal_preview",{**scope,"proposal_id":ident})
                check("R06-21_APPROVAL_STATUS_AUDIT",not err and preview["status"]=="approved")
                newproposal,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-22_PREPARE_AFTER_APPROVED_RETURNS_SAME",not err and newproposal["status"]=="approved" and count()==1)
                print("GAIA_R06_TESTS="+str(checks),flush=True)
        finally:
            server._qrequest=old
            jwt.PyJWKClient=jwks
if __name__=="__main__":main()
