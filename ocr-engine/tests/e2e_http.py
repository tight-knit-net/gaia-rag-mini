import io, os, json, hashlib, re, time, zipfile
import httpx
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

page=Image.new('RGB',(1500,2100),'white')
draw=ImageDraw.Draw(page)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',40)
bold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',46)
fields=[
 "DOCUMENTO SINTETICO - TESTE OCR REAL",
 "CLIENTE: MARIA TESTE EXEMPLO",
 "PROCESSO: GAIA-009-2026",
 "DATA: 18/11/2026",
 "PROTOCOLO: LAB-4829",
 "VALOR: R$ 1.275,40",
 "DOCUMENTO DE TESTE - SEM CLIENTE REAL"
]
for i,text in enumerate(fields):
    draw.text((85,110+i*185),text,fill='black',font=bold if i==0 else font)
file=io.BytesIO();page.save(file,'PDF',resolution=200);raw=file.getvalue()
before=''.join(pg.extract_text() or '' for pg in PdfReader(io.BytesIO(raw)).pages)
assert not before.strip(),"source not image only"
headers={"Authorization":"Bearer "+os.environ["GAIA_OCR_TOKEN"]}
url="http://127.0.0.1:18791"
tenant="ocr_e2e_synthetic"
start=time.monotonic()
with httpx.Client(timeout=150.0) as c:
    r=c.get(url+"/healthz");r.raise_for_status();health=r.json()
    assert health["provider"]=="tesseract"
    unauthorized=c.get(url+"/v1/search",params={"tenant":tenant,"q":"PROTOCOLO"})
    assert unauthorized.status_code==401,unauthorized.status_code
    created=c.post(url+"/v1/documents",headers=headers,data={"tenant":tenant},files={"file":("ficha_ficticia_escaneada.pdf",raw,"application/pdf")})
    created.raise_for_status(); staged=created.json()
    ident=staged["id"]
    processed=c.post(url+f"/v1/documents/{ident}/ocr",params={"tenant":tenant},headers=headers)
    processed.raise_for_status();result=processed.json()
    assert result["provider"]=="tesseract",result
    text=result["text"]
    normalized=re.sub(r'\s+',' ',text.upper())
    fields_test={x:x in normalized for x in ['MARIA TESTE EXEMPLO','GAIA-009-2026','18/11/2026','LAB-4829','1.275,40','SEM CLIENTE REAL']}
    record=c.get(url+f"/v1/documents/{ident}",params={"tenant":tenant},headers=headers)
    record.raise_for_status()
    getpdf=c.get(url+f"/v1/documents/{ident}/file",params={"tenant":tenant,"kind":"ocr"},headers=headers)
    getpdf.raise_for_status()
    ocr_text_from_pdf=''.join(pg.extract_text() or '' for pg in PdfReader(io.BytesIO(getpdf.content)).pages)
    search=c.get(url+"/v1/search",params={"tenant":tenant,"q":"PROTOCOLO"},headers=headers)
    search.raise_for_status()
    exp=c.get(url+"/v1/export",params={"tenant":tenant},headers=headers)
    exp.raise_for_status()
    z=zipfile.ZipFile(io.BytesIO(exp.content))
    manifest=json.loads(z.read("manifest.json"))
    other_tenant=c.get(url+"/v1/search",params={"tenant":"other_synthetic","q":"PROTOCOLO"},headers=headers)
    other_tenant.raise_for_status()
    check={
      "all_fields_recognized":all(fields_test.values()),
      "pdf_searchable":'GAIA-009-2026' in ocr_text_from_pdf,
      "stored_record":record.json()["id"]==ident,
      "original_sha256_valid":staged["sha256"]==hashlib.sha256(raw).hexdigest(),
      "fts_search_finds_document":any(x["id"]==ident for x in search.json()),
      "other_tenant_isolated":not other_tenant.json(),
      "export_manifest_contains_document":any(x["id"]==ident for x in manifest["documents"]),
      "bearer_required":unauthorized.status_code==401
    }
    print(json.dumps({
        "provider":health["provider"],
        "location":"Linode Test Lab",
        "document_id":ident,
        "tenant":tenant,
        "original_pages":staged["pages"],
        "source_text_characters":len(before),
        "ocr_text":text,
        "field_checks":fields_test,
        "system_checks":check,
        "result":"PASS" if all(check.values()) else "FAIL",
        "seconds":round(time.monotonic()-start,2),
        "export_files":len(z.namelist()),
        "sha256":staged["sha256"]
    },ensure_ascii=False,indent=2))
