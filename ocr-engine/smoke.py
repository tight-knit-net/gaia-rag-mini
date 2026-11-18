"""Pure-Python smoke E2E, no external document or API credits."""
import io
import json
import os
import urllib.request
import uuid
from zipfile import ZipFile

BASE=os.getenv("GAIA_OCR_URL","http://127.0.0.1:18788")
TOKEN=os.environ["GAIA_OCR_TOKEN"]

def synthetic_pdf(text):
    stream=f"BT /F1 14 Tf 72 730 Td ({text}) Tj ET".encode("ascii")
    objs=[
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "+str(len(stream)).encode()+b" >>\nstream\n"+stream+b"\nendstream",
    ]
    raw=b"%PDF-1.4\n"
    pos=[0]
    for n,obj in enumerate(objs,1):
        pos.append(len(raw))
        raw+=f"{n} 0 obj\n".encode()+obj+b"\nendobj\n"
    xref=len(raw)
    raw+=b"xref\n0 6\n0000000000 65535 f \n"
    for off in pos[1:]:
        raw+=f"{off:010d} 00000 n \n".encode()
    raw+=f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return raw

def request(method,path,data=None,ctype=None):
    headers={"Authorization":"Bearer "+TOKEN}
    if ctype:
        headers["Content-Type"]=ctype
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=30) as response:
        data=response.read()
        return data if "application/zip" in response.headers.get("Content-Type","") else json.loads(data)

def upload(filename,raw,tenant):
    boundary="gaia"+uuid.uuid4().hex
    payload=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"tenant\"\r\n\r\n{tenant}\r\n"
             f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
             "Content-Type: application/pdf\r\n\r\n").encode()+raw+f"\r\n--{boundary}--\r\n".encode()
    return request("POST","/v1/documents",payload,f"multipart/form-data; boundary={boundary}")

def main():
    assert request("GET","/healthz")["status"]=="ok"
    ids=[]
    for n in range(10):
        item=upload(f"synthetic-{n}.pdf",synthetic_pdf(f"GAIA SINTETICO CASO {n}"),"test")
        ids.append(item["id"])
        outcome=request("POST",f"/v1/documents/{item['id']}/ocr?tenant=test",b"")
        assert outcome["status"]=="processed" and "SINTETICO" in outcome["text"]
        assert outcome["provider"]=="mock"
    found=request("GET","/v1/search?tenant=test&q=SINTETICO")
    assert len(found)>=10
    backup=request("GET","/v1/export?tenant=test")
    z=ZipFile(io.BytesIO(backup))
    manifest=json.loads(z.read("manifest.json"))
    assert len(manifest["documents"])>=10
    assert all(f"files/{ident}/original" in z.namelist() for ident in ids)
    print(json.dumps({"status":"PASS","batch":10,"retrieved":len(found),
                      "backup_documents":len(manifest["documents"]),
                      "ocr_provider":"mock","real_ocr":False},ensure_ascii=False))

if __name__=="__main__":
    main()

