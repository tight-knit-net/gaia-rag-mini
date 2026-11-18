import hmac
import os
from fastapi import FastAPI, UploadFile, File, Form, Query, Header, HTTPException, Depends
from fastapi.responses import Response
import engine

app=FastAPI(title="GAIA OCR Engine (Test Lab)",version="0.1.0",
            docs_url=None,redoc_url=None)

@app.on_event("startup")
def start():
    engine.setup()

def guard(authorization: str|None=Header(default=None)):
    secret=os.getenv("GAIA_OCR_TOKEN","")
    expected="Bearer "+secret
    if not secret or not authorization or not hmac.compare_digest(authorization,expected):
        raise HTTPException(status_code=401,detail="unauthorized")

def execute(fn,*a,**kw):
    try:
        return fn(*a,**kw)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc)) from exc
    except Exception:
        raise HTTPException(status_code=502,detail="processing failed; check server logs") from None

@app.get("/healthz")
def health():
    try:
        with engine.connection() as conn:
            conn.execute("SELECT 1")
        return {"status":"ok","service":"gaia-ocr-lab","provider":engine.PROVIDER}
    except Exception:
        raise HTTPException(status_code=503,detail="database unavailable") from None

@app.post("/v1/documents",dependencies=[Depends(guard)])
async def upload(file:UploadFile=File(...), tenant:str=Form("test")):
    raw=await file.read(engine.MAX_FILE+1)
    return execute(engine.stage,tenant,file.filename or "document.pdf",raw)

@app.post("/v1/documents/{document_id}/ocr",dependencies=[Depends(guard)])
def process(document_id:str,tenant:str=Query("test")):
    result=execute(engine.process,tenant,document_id)
    if result is None:
        raise HTTPException(status_code=404,detail="not found")
    return result

@app.get("/v1/documents/{document_id}",dependencies=[Depends(guard)])
def document(document_id:str,tenant:str=Query("test")):
    result=execute(engine.get_record,tenant,document_id)
    if result is None:
        raise HTTPException(status_code=404,detail="not found")
    return result

@app.get("/v1/documents/{document_id}/file",dependencies=[Depends(guard)])
def download(document_id:str,tenant:str=Query("test"),kind:str=Query("original")):
    result=execute(engine.get_bytes,tenant,document_id,kind)
    if result is None:
        raise HTTPException(status_code=404,detail="not found")
    data,media,name=result
    return Response(data,media_type=media,headers={
        "Content-Disposition":f'attachment; filename="{document_id}-'+kind+'"',
        "X-Original-Filename": name.encode("ascii","ignore").decode("ascii")[:100]
    })

@app.get("/v1/search",dependencies=[Depends(guard)])
def search(q:str=Query(...,min_length=1),tenant:str=Query("test"),limit:int=Query(25,ge=1,le=100)):
    return execute(engine.search,tenant,q,limit)

@app.get("/v1/export",dependencies=[Depends(guard)])
def export(tenant:str=Query("test")):
    out=execute(engine.export_zip,tenant)
    return Response(out,media_type="application/zip",headers={
        "Content-Disposition":f'attachment; filename="gaia-ocr-{tenant}.zip"'
    })

