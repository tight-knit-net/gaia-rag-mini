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
        owners=root/"owners.json"
        docs=root/"documents.json"
        owners.write_text(json.dumps({"subjects":[A]}))
        docs.write_text(json.dumps({"approved_documents":[{
           "namespace":NS,"tenant_id":TA,"process_id":PA,
           "source_ref":SOURCE,"approval_ref":APPROVAL,
           "document_sha256":SHA,"status":"approved"}]}))
        os.environ.update({
            "CF_ACCESS_TEAM_DOMAIN":ISS,
            "CF_ACCESS_AUD":AUD,
            "GAIA_RAG_OWNER_SUBJECTS_FILE":str(owners),
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
                        raw=output["content"][0]["text"]
                        try:data=json.loads(raw)
                        except (ValueError,TypeError):data={"error":raw}
                    return data,output.get("isError"),r
                scope={"namespace":NS,"process_id":PA}
                bscope={"namespace":NS,"process_id":PB}
                tool_list=call("tools/list")
                tools={t["name"] for t in tool_list.json()["result"]["tools"]}
                required={"memory_process_start","memory_prepare_after_approval",
                          "memory_proposal_preview","memory_pending_reviews",
                          "gaia_skill_catalog","gaia_skill_read","memory_search_all"}
                check("R06-01_TOOLS_PRESENT",required<=tools,",".join(sorted(required)))
                catalog,err,_=tool("gaia_skill_catalog",{})
                check("R06-02_SKILL_MANIFEST",not err and len(catalog["files"])>=10,str(len(catalog.get("files",[]))))
                skill,err,_=tool("gaia_skill_read",{"path":"SKILL.md"})
                check("R06-03_SKILL_READ",not err and "gaia-rag-processos-administrativos" in skill["content"])
                resources=call("resources/list")
                listed={x.get("uri") for x in resources.json().get("result",{}).get("resources",[])}
                uri="skill://gaia-rag-processos-administrativos/SKILL.md"
                check("R06-03A_MCP_RESOURCES_LIST",resources.status_code==200 and uri in listed)
                contents=call("resources/read",{"uri":uri})
                resource_items=contents.json().get("result",{}).get("contents",[])
                check("R06-03B_MCP_RESOURCES_READ",contents.status_code==200 and bool(resource_items) and "gaia-rag-processos-administrativos" in resource_items[0].get("text",""))
                # S6: a valid Cloudflare JWT belonging to a NON-owner must not
                # expose skill instructions, resources or catalog metadata.
                for skill_tool, args in (
                    ("gaia_skill_catalog", {}),
                    ("gaia_skill_read", {"path": "SKILL.md"}),
                    ("gaia_skill_read_chunk", {"path": "SKILL.md"}),
                ):
                    denied_content, skill_err, _ = tool(skill_tool, args, identity=B)
                    check("S6_OWNER_ONLY_" + skill_tool, skill_err is True
                          and not (isinstance(denied_content, dict)
                                   and denied_content.get("content")))
                denied_resource = call("resources/read", {"uri": uri}, identity=B)
                response_json = denied_resource.json()
                check("S6_OWNER_ONLY_MCP_RESOURCE",
                      "error" in response_json or
                      (response_json.get("result", {}).get("isError") is True))
                # A symlinked parent directory must not be used to read a
                # plausible allowlisted filename outside the installed skill.
                fake_root = root / "symlinked-skills"
                fake_root.mkdir()
                outside = root / "outside-skill-package"
                outside.mkdir()
                (outside / "02-recuperacao.md").write_text(
                    "S6-SYNTHETIC-UNTRUSTED-CONTENT", encoding="utf-8")
                (fake_root / "references").symlink_to(outside, target_is_directory=True)
                original_skill_root = server._skill_root
                server._skill_root = lambda: fake_root
                try:
                    escaped, escape_err, _ = tool(
                        "gaia_skill_read",
                        {"path": "references/02-recuperacao.md"})
                    check("S6_SYMLINK_PARENT_DENIED",
                          escape_err is True
                          and "S6-SYNTHETIC-UNTRUSTED-CONTENT" not in str(escaped))
                finally:
                    server._skill_root = original_skill_root
                denied,err,_=tool("gaia_skill_read",{"path":"../../etc/passwd"})
                check("R06-04_PATH_TRAVERSAL_DENIED",err is True,"file read rejected")
                prepare={"title":"DEMO memoria de processo","summary":"DEMO: minuta interna aprovada; protocolo nao comprovado.",
                         "source_ref":SOURCE,"document_approval_ref":APPROVAL,
                         "document_sha256":SHA,**scope}
                # R07 Skilldrum-style route tests use DEMO identity and installed modules.
                skill_route_tools={"gaia_skill_route","gaia_skill_route_read"}
                check("R07-SR01_TOOLS_EXPOSED",skill_route_tools<=tools)
                route,err,_=tool("gaia_skill_route",{**scope,"mission":"memory_search"})
                check("R07-SR02_EXACT_ROUTE",not err and route["status"]=="READY_FOR_HOST_LOAD"
                      and route["modules"][1]["path"]=="references/02-recuperacao.md"
                      and route["host_must_explicitly_load"] is True)
                selected=route["modules"][1]
                load_args={**scope,"mission":"memory_search","path":selected["path"],
                           "route_sha256":route["route_sha256"],
                           "expected_sha256":selected["sha256"],"max_chars":200}
                loaded,err,_=tool("gaia_skill_route_read",load_args)
                check("R07-SR03_PROGRESSIVE_MODULE_READ",
                      not err and loaded["path"]==selected["path"]
                      and len(loaded["content"])<=200
                      and loaded["host_activation_confirmed"] is False)
                # S5: simulate an MCP host explicitly loading the *entire*
                # selected route (not just a single preview chunk).
                host_loaded={}
                catalog_by_path={x["path"]:x["sha256"] for x in catalog["files"]}
                for module in route["modules"]:
                    fragments=[]
                    cursor=0
                    for step in range(200):
                        item,read_err,_=tool("gaia_skill_route_read",{
                            **scope, "mission":route["mission"],
                            "path":module["path"],
                            "route_sha256":route["route_sha256"],
                            "expected_sha256":module["sha256"],
                            "offset":cursor,"max_chars":119})
                        if read_err or not item or item.get("host_activation_confirmed") is not False:
                            raise AssertionError("S5_HOST_READ_FAILED")
                        fragments.append(item["content"])
                        next_cursor=item["next_offset"]
                        if next_cursor is None:
                            break
                        if not isinstance(next_cursor,int) or next_cursor<=cursor:
                            raise AssertionError("S5_HOST_PAGE_STALLED")
                        cursor=next_cursor
                    else:
                        raise AssertionError("S5_HOST_PAGE_LIMIT")
                    full="".join(fragments)
                    if (hashlib.sha256(full.encode("utf-8")).hexdigest()!=module["sha256"]
                            or catalog_by_path.get(module["path"])!=module["sha256"]):
                        raise AssertionError("S5_HOST_MANIFEST_SHA_MISMATCH")
                    host_loaded[module["path"]]=full
                check("R07-S5-01_HOST_FULL_ROUTE_LOAD",
                      len(host_loaded)==3 and "SKILL.md" in host_loaded
                      and "references/02-recuperacao.md" in host_loaded)
                check("R07-S5-02_FULL_BYTE_HASHES_AND_CATALOG",
                      all(hashlib.sha256(v.encode("utf-8")).hexdigest()
                          ==catalog_by_path[k] for k,v in host_loaded.items()))
                check("R07-S5-03_HOST_READ_DOES_NOT_SAVE",count()==0)
                wrong_scope,err,_=tool("gaia_skill_route_read",
                                      {**load_args,"process_id":PB})
                check("R07-SR04_CROSS_PROCESS_ROUTE_MISMATCH",err is True)
                wrong_hash,err,_=tool("gaia_skill_route_read",
                                     {**load_args,"expected_sha256":"0"*64})
                check("R07-SR05_STALE_FILE_HASH_DENIED",err is True)
                other_module,err,_=tool("gaia_skill_route_read",
                       {**load_args,"path":"references/03-producao-e-proposta.md"})
                check("R07-SR06_UNSELECTED_MODULE_DENIED",err is True)
                unknown_route,err,_=tool("gaia_skill_route",
                                          {**scope,"mission":"delete_memories"})
                check("R07-SR07_UNKNOWN_MISSION_FAIL_CLOSED",
                      not err and unknown_route["status"]=="NO_ROUTE"
                      and unknown_route["modules"]==[])
                illicit_route,err,_=tool("gaia_skill_route",
                                          {**scope,"mission":"memory_search"},
                                          identity=B)
                check("R07-SR08_NONOWNER_DENIED",err is True)
                owner_other_process,err,_=tool("gaia_skill_route",
                                      {**bscope,"mission":"memory_search"},identity=A)
                check("R07-SR09_OWNER_CROSS_CLIENT_NOT_BLOCKED",
                      not err and owner_other_process["status"]=="READY_FOR_HOST_LOAD"
                      and owner_other_process["route_sha256"]!=route["route_sha256"])
                check("R07-SR10_ROUTER_NEVER_PERSISTS",count()==0)
                other,err,_=tool("memory_prepare_after_approval",{**prepare,"process_id":PB},identity=B)
                check("R06-05_NONOWNER_CANNOT_PROPOSE",err is True)
                docs.write_text('{"approved_documents":[]}')
                notapproved,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-06_NO_DOCUMENT_APPROVAL_DENIED",err is True)
                docs.write_text(json.dumps({"approved_documents":[{
                   "namespace":NS,"tenant_id":TA,"process_id":PA,
                   "source_ref":SOURCE,"approval_ref":APPROVAL,
                   "document_sha256":SHA,"status":"approved"}]}))
                opened,err,_=tool("memory_process_start",scope)
                check("R06-06A_EXACT_PROCESS_START",not err and opened["process_id"]==PA and opened["approved_memories"]["items"]==[])
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
                other,err,_=tool("memory_list_process",bscope,identity=A)
                check("R06-19_OTHER_CLIENT_PROCESS_EMPTY_INITIAL",not err and other["items"]==[])
                illicit,err,_=tool("memory_list_process",scope,identity=B)
                check("R06-20_NONOWNER_CANNOT_READ_A",err is True)
                preview,err,_=tool("memory_proposal_preview",{**scope,"proposal_id":ident})
                check("R06-21_APPROVAL_STATUS_AUDIT",not err and preview["status"]=="approved")
                newproposal,err,_=tool("memory_prepare_after_approval",prepare)
                check("R06-22_PREPARE_AFTER_APPROVED_RETURNS_SAME",not err and newproposal["status"]=="approved" and count()==1)
                # R07 candidate-only contract checks on disposable Qdrant and DEMO ledger.
                new_tools={"memory_discard_proposal","memory_auto_prepare","memory_process_timeline","memory_export_process",
                           "memory_approval_audit","memory_stats",
                           "memory_index_preview","gaia_skill_read_chunk"}
                check("R07-01_NEW_TOOLS",new_tools<=tools)
                chunk,err,_=tool("gaia_skill_read_chunk",{"path":"SKILL.md","max_chars":300})
                check("R07-02_SKILL_CHUNK",not err and chunk["content"].startswith("---")
                      and len(chunk["content"])<=300 and chunk["sha256"])
                index,err,_=tool("memory_index_preview",{
                    **scope,"title":"DEMO memorando","summary":"Triagem de documento e contrato DEMO",
                    "source_ref":SOURCE})
                check("R07-03_INDEX_PREVIEW",not err and index["automatic_save"] is False
                      and index["external_llm_used"] is False)
                timeline,err,_=tool("memory_process_timeline",scope)
                check("R07-04_TIMELINE",not err and len(timeline["items"])==1
                      and timeline["truncated"] is False)
                exported,err,_=tool("memory_export_process",{**scope,"max_items":1})
                check("R07-05_EXPORT_HASH",not err and exported["count"]==1
                      and len(exported["sha256"])==64)
                stats,err,_=tool("memory_stats",scope)
                check("R07-06_STATS",not err and stats["qdrant_approved_points"]==1
                      and stats["proposal_counts"]["approved"]==1)
                audits,err,_=tool("memory_approval_audit",scope)
                check("R07-07_AUDIT",not err and audits["storage_available"]
                      and any(e["event"]=="readback_confirmed" for e in audits["events"]))
                pending_after,err,_=tool("memory_pending_reviews",scope)
                check("R07-08_APPROVED_NOT_PENDING",not err
                      and pending_after["proposals"]==[]
                      and pending_after["storage_available"])
                check("R07-09_INDEX_PERSISTED_POST_CLICK",
                      obtained["items"][0].get("index_method")=="r07_deterministic_v1")
                second_source = "DEMO-DOC-002"
                second_approval = "DEMO-APPROVAL-002"
                docs.write_text(json.dumps({"approved_documents":[{
                   "namespace":NS,"tenant_id":TA,"process_id":PA,
                   "source_ref":SOURCE,"approval_ref":APPROVAL,
                   "document_sha256":SHA,"status":"approved"},{
                   "namespace":NS,"tenant_id":TA,"process_id":PA,
                   "source_ref":second_source,"approval_ref":second_approval,
                   "document_sha256":SHA,"status":"approved"}]}))
                assist={**scope,"title":"DEMO nova instrução",
                        "summary":"Procedimento fictício novo a conferir antes de protocolo.",
                        "source_ref":second_source,
                        "document_approval_ref":second_approval,
                        "document_sha256":SHA}
                draft,err,_=tool("memory_auto_prepare",assist)
                check("R07-10_AUTO_PREVIEW_NO_WRITE",
                      not err and draft["status"]=="PREVIEW_ONLY_CONFIRM_TO_PREPARE"
                      and draft["proposal_prepared"] is False and count()==1)
                assisted,err,_=tool("memory_auto_prepare",
                                    {**assist,"user_confirmed_proposal":True})
                check("R07-11_PREPARE_NO_QDRANT_WRITE",
                      not err and assisted["proposal_prepared"]
                      and assisted["status"]=="pending"
                      and assisted["human_save_required"] and count()==1)
                discard_link,err,_=tool("memory_discard_proposal",{
                    **scope,"proposal_id":assisted["proposal_id"]})
                check("R07-12_DISCARD_TOOL_READ_ONLY",
                      not err and discard_link["human_confirmation_required"]
                      and discard_link["tool_side_effects"]=="none" and count()==1)
                discard_page=client.get("/review/"+assisted["proposal_id"],headers=authhdr)
                dcsrf=re.search(r'name="csrf" value="([^"]+)"',discard_page.text).group(1)
                bad_discard=client.post("/review/"+assisted["proposal_id"]+"/discard",
                                        data={"confirm":"DESCARTAR","csrf":"forged"},
                                        headers={**authhdr,"origin":"https://gaia-demo.example.invalid"})
                check("R07-13_DISCARD_BAD_CSRF",bad_discard.status_code==403 and count()==1)
                done_discard=client.post("/review/"+assisted["proposal_id"]+"/discard",
                                         data={"confirm":"DESCARTAR","csrf":dcsrf},
                                         headers={**authhdr,"origin":"https://gaia-demo.example.invalid"})
                check("R07-14_HUMAN_DISCARD_NO_QDRANT_CHANGE",
                      done_discard.status_code==200 and count()==1)
                after_discard,err,_=tool("memory_pending_reviews",scope)
                check("R07-15_DISCARDED_NOT_PENDING",
                      not err and after_discard["proposals"]==[])
                after_stats,err,_=tool("memory_stats",scope)
                check("R07-16_DISCARDED_IN_STATS",
                      not err and after_stats["proposal_counts"]["discarded"]==1)
                # Same GAIA owner must see approved memory from a different client.
                id_b="22222222-2222-4222-8222-222222222222"
                payload_b={"namespace":NS,"tenant_id":TB,"process_id":PB,
                           "approved":True,"title":"DEMO B","text":"Cliente B: decisao ficticia",
                           "source_ref":"DEMO-B-SOURCE"}
                q("PUT",POINTS+"?wait=true",{"points":[{"id":id_b,"payload":payload_b,"vector":[0.9,0.1,0,0]}]})
                result_b,err,_=tool("memory_list_process",bscope,identity=A)
                check("R06-23_OWNER_CAN_ACCESS_OTHER_CLIENT",not err and len(result_b["items"])==1
                      and result_b["items"][0]["tenant_id"]==TB)
                lookup_b,err,_=tool("memory_get",{"point_id":id_b,**bscope},identity=A)
                check("R06-24_OWNER_GET_CROSS_CLIENT_UUID",not err and lookup_b["found"] is True)
                source_b,err,_=tool("memory_find_by_source",{"source_ref":"DEMO-B-SOURCE",**bscope},identity=A)
                check("R06-25_OWNER_GET_CROSS_CLIENT_SOURCE",not err and len(source_b["items"])==1)
                analogy,err,_=tool("memory_similar_cases",{"description":"DEMO","namespace":NS,"process_id":PA},identity=A)
                check("R06-26_OWNER_SIMILAR_ACROSS_CLIENTS",not err and any(x["process_id"]==PB for x in analogy["similar"]))
                global_hits,err,_=tool("memory_search_all",{"query":"DEMO","namespace":NS,"limit":10},identity=A)
                check("R06-27_OWNER_GLOBAL_SEARCH",not err and
                      any(x["process_id"]==PB for x in global_hits["hits"]))
                # Legacy records with no tenant_id must be readable by owner.
                legacy_id="33333333-3333-4333-8333-333333333333"
                q("PUT",POINTS+"?wait=true",{"points":[{"id":legacy_id,"vector":[0.7,0.3,0,0],
                     "payload":{"namespace":NS,"process_id":"DEMO-LEGACY",
                                "approved":True,"text":"Memoria antiga sem cliente",
                                "source_ref":"DEMO-LEGACY"}}]})
                legacy,err,_=tool("memory_list_process",{"namespace":NS,"process_id":"DEMO-LEGACY"},identity=A)
                check("R06-28_OWNER_READS_LEGACY_NO_TENANT",not err and len(legacy["items"])==1)
                outsider,err,_=tool("memory_search_all",{"query":"DEMO","namespace":NS},identity=B)
                check("R06-29_OUTSIDER_CANNOT_GLOBAL_SEARCH",err is True)
                check("R06-30_RECORDS_STORED_BY_LAB_ONLY",count()==3,str(count()))
                print("GAIA_R06_TESTS="+str(checks),flush=True)
        finally:
            server._qrequest=old
            jwt.PyJWKClient=jwks
if __name__=="__main__":main()
