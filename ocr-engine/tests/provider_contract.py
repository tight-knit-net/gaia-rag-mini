import io, json, os
from unittest.mock import patch
import engine
from pypdf import PdfWriter
class FakeResponse:
    def __init__(self,data): self.data=data
    def json(self): return self.data if isinstance(self.data,dict) else {}
    @property
    def content(self):return self.data if isinstance(self.data,bytes) else b''
    def raise_for_status(self):pass
class FakeClient:
    def __init__(self,server="api11.ilovepdf.com"):self.server=server; self.calls=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def get(self,url,**kw):
        self.calls.append(("GET",url))
        assert kw["headers"]["X-Api-Key"]=="fake-key"
        if "/start/pdfocr" in url:return FakeResponse({"server":self.server,"task":"synthetic-task"})
        if "/download/" in url:return FakeResponse(pdf_bytes)
        raise AssertionError(url)
    def post(self,url,**kw):
        self.calls.append(("POST",url))
        assert kw["headers"]["X-Api-Key"]=="fake-key"
        if url.endswith("/upload"):
            assert kw["data"]["task"]=="synthetic-task"
            return FakeResponse({"server_filename":"fake.pdf"})
        if url.endswith("/process"):
            payload=kw["json"]
            assert payload["tool"]=="pdfocr"
            assert payload["ocr_mode"]=="standard"
            assert payload["ocr_languages"]==["por","eng"]
            assert payload["files"][0]["server_filename"]=="fake.pdf"
            return FakeResponse({"status":"ok"})
        raise AssertionError(url)
w=PdfWriter();w.add_blank_page(width=595,height=842);o=io.BytesIO();w.write(o);pdf_bytes=o.getvalue()
before=os.environ.get("ILOVEAPI_SECRET")
os.environ["ILOVEAPI_SECRET"]="fake-key"
fake=FakeClient()
with patch.object(engine.httpx,"Client",return_value=fake):
    out=engine._iloveapi(pdf_bytes)
assert out.startswith(b"%PDF-")
assert [m for m,u in fake.calls]==["GET","POST","POST","GET"]
fakebad=FakeClient("attacker.invalid")
with patch.object(engine.httpx,"Client",return_value=fakebad):
    try:engine._iloveapi(pdf_bytes)
    except RuntimeError as e:assert "servidor invalida" in str(e)
    else:raise AssertionError("SSRF validation failed")
os.environ.pop("ILOVEAPI_SECRET")
try:engine._iloveapi(pdf_bytes)
except RuntimeError as e:assert "ausente" in str(e)
else:raise AssertionError("missing key allowed")
if before is not None:os.environ["ILOVEAPI_SECRET"]=before
print(json.dumps({"mocked_vendor_contract":"PASS","steps":["start","upload","process","download"],"header":"X-Api-Key","server_allowlist":"PASS","missing_secret":"PASS","actual_provider_network_call":False},ensure_ascii=False))
