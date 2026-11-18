import hashlib
import tempfile
import subprocess
from pathlib import Path
import io
import os
import re
import uuid
import zipfile
import json
from datetime import datetime
from typing import Optional

import httpx
import psycopg
from psycopg.rows import dict_row
from pypdf import PdfWriter, PdfReader
from PIL import Image, UnidentifiedImageError

MAX_FILE = 15 * 1024 * 1024
MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "10"))
PROVIDER = os.getenv("OCR_PROVIDER", "mock")
DB_URL = os.environ["DATABASE_URL"]
TENANT_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,40}$")
SERVER_PATTERN = re.compile(r"^api[0-9]*\.ilovepdf\.com$")

def connection():
    return psycopg.connect(DB_URL, row_factory=dict_row, connect_timeout=5)

def setup():
    with connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_documents (
          id uuid PRIMARY KEY,
          tenant varchar(40) NOT NULL,
          filename text NOT NULL,
          media_type text NOT NULL,
          sha256 char(64) NOT NULL,
          original_bytes bytea NOT NULL,
          normalized_pdf bytea NOT NULL,
          ocr_pdf bytea,
          ocr_text text NOT NULL DEFAULT '',
          status varchar(16) NOT NULL DEFAULT 'uploaded',
          provider varchar(24) NOT NULL DEFAULT '',
          error text,
          created_at timestamptz NOT NULL DEFAULT now(),
          processed_at timestamptz
        )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ocr_documents_tenant ON ocr_documents (tenant, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS ocr_documents_search ON ocr_documents USING GIN (to_tsvector('simple', ocr_text))")

def check_tenant(tenant):
    if not TENANT_PATTERN.fullmatch(tenant or ""):
        raise ValueError("tenant invalido")
    return tenant

def pdf_text(raw):
    reader = PdfReader(io.BytesIO(raw), strict=False)
    if reader.is_encrypted:
        raise ValueError("PDF criptografado nao suportado")
    if len(reader.pages) == 0:
        raise ValueError("PDF sem paginas")
    return "\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)

def normalize(raw, filename):
    if not raw or len(raw) > MAX_FILE:
        raise ValueError("arquivo vazio ou maior que 15 MiB")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf" and raw.startswith(b"%PDF-"):
        _, pages = pdf_text(raw)
        return raw, pages, "application/pdf"
    if ext in ("jpg", "jpeg", "png") and (raw.startswith(b"\xff\xd8") or raw.startswith(b"\x89PNG")):
        try:
            image = Image.open(io.BytesIO(raw))
            image.verify()
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            pdf = io.BytesIO()
            image.save(pdf, "PDF", resolution=200.0)
            return pdf.getvalue(), 1, "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("imagem invalida") from exc
    raise ValueError("somente PDF, PNG ou JPEG com assinatura valida")

def stage(tenant, filename, raw):
    tenant = check_tenant(tenant)
    filename = re.sub(r"[\x00-\x1f/\\]", "_", filename or "document.pdf")[:160]
    pdf, pages, media = normalize(raw, filename)
    ident = str(uuid.uuid4())
    digest = hashlib.sha256(raw).hexdigest()
    with connection() as conn:
        conn.execute("""INSERT INTO ocr_documents
          (id,tenant,filename,media_type,sha256,original_bytes,normalized_pdf)
          VALUES (%s,%s,%s,%s,%s,%s,%s)""",
          (ident, tenant, filename, media, digest, raw, pdf))
    return {"id":ident, "tenant":tenant, "filename":filename,
            "sha256":digest, "status":"uploaded", "pages":pages,
            "bytes":len(raw), "provider_configured":PROVIDER}

def public_record(record, include_text=True):
    if record is None:
        return None
    out = {k:record[k] for k in (
        "id","tenant","filename","media_type","sha256","status","provider","error",
        "created_at","processed_at") if k in record}
    for k, v in list(out.items()):
        if isinstance(v, (uuid.UUID, datetime)):
            out[k] = str(v)
    if include_text:
        out["text"] = record.get("ocr_text") or ""
    return out

def get_record(tenant, ident):
    tenant = check_tenant(tenant)
    with connection() as conn:
        row=conn.execute("""SELECT id,tenant,filename,media_type,sha256,status,
             provider,error,created_at,processed_at,ocr_text FROM ocr_documents
             WHERE id=%s AND tenant=%s""",(ident,tenant)).fetchone()
    return public_record(row)

def get_bytes(tenant, ident, kind):
    if kind not in ("original","ocr"):
        raise ValueError("kind deve ser original ou ocr")
    with connection() as conn:
        row=conn.execute("""SELECT original_bytes,ocr_pdf,filename,media_type
          FROM ocr_documents WHERE id=%s AND tenant=%s""",
          (ident,check_tenant(tenant))).fetchone()
    if not row:
        return None
    raw = row["original_bytes" if kind == "original" else "ocr_pdf"]
    if raw is None:
        return None
    return bytes(raw), ("application/pdf" if kind == "ocr" else row["media_type"]), row["filename"]

def _iloveapi(pdf):
    key=os.getenv("ILOVEAPI_SECRET","")
    if not key:
        raise RuntimeError("ILOVEAPI_SECRET ausente")
    headers={"X-Api-Key":key}
    timeout=httpx.Timeout(120.0, connect=15.0)
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        start=client.get("https://api.ilovepdf.com/v1/start/pdfocr", headers=headers)
        start.raise_for_status()
        task_info=start.json()
        host=str(task_info.get("server",""))
        task=task_info.get("task")
        if not SERVER_PATTERN.fullmatch(host) or not isinstance(task,str) or not task:
            raise RuntimeError("resposta de servidor invalida da iLoveAPI")
        base=f"https://{host}/v1"
        upload=client.post(f"{base}/upload",headers=headers,data={"task":task},
              files={"file":("document.pdf",pdf,"application/pdf")})
        upload.raise_for_status()
        server_filename=upload.json()["server_filename"]
        options={"task":task,"tool":"pdfocr",
                 "files":[{"server_filename":server_filename,"filename":"document.pdf"}],
                 "ocr_mode":os.getenv("OCR_MODE","standard")}
        if options["ocr_mode"] == "standard":
            options["ocr_languages"]=["por","eng"]
        processed=client.post(f"{base}/process",headers=headers,json=options)
        processed.raise_for_status()
        download=client.get(f"{base}/download/{task}",headers=headers)
        download.raise_for_status()
        if len(download.content) > 30*1024*1024 or not download.content.startswith(b"%PDF-"):
            raise RuntimeError("saida OCR nao parece um PDF valido")
        return download.content


def _tesseract(pdf):
    """Genuine OCR of scanned pages in an isolated temporary directory."""
    _, pages = pdf_text(pdf)
    writer = PdfWriter()
    with tempfile.TemporaryDirectory(prefix="gaia-ocr-e2e-") as workdir:
        inp = Path(workdir) / "source.pdf"
        inp.write_bytes(pdf)
        for page_no in range(1, pages + 1):
            stem = Path(workdir) / f"page-{page_no}"
            subprocess.run(
                ["pdftoppm", "-f", str(page_no), "-l", str(page_no),
                 "-singlefile", "-r", "180", "-png", str(inp), str(stem)],
                check=True, timeout=90, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            image = stem.with_suffix(".png")
            if not image.exists() or image.stat().st_size > 35*1024*1024:
                raise RuntimeError("imagem rasterizada indisponivel ou grande")
            ocrstem = Path(workdir) / f"result-{page_no}"
            subprocess.run(["tesseract", str(image), str(ocrstem),
                            "-l", "por+eng", "pdf"], check=True, timeout=90,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            writer.append(str(ocrstem.with_suffix(".pdf")))
        result = io.BytesIO()
        writer.write(result)
        output = result.getvalue()
        if len(output) > 30*1024*1024:
            raise RuntimeError("PDF OCR excedeu limite")
        return output

def process(tenant, ident):
    tenant=check_tenant(tenant)
    with connection() as conn:
        row=conn.execute("""SELECT id,filename,normalized_pdf,status
            FROM ocr_documents WHERE id=%s AND tenant=%s FOR UPDATE""",
            (ident,tenant)).fetchone()
        if not row:
            return None
        if row["status"]=="processed":
            return get_record(tenant,ident)
        if row["status"]=="processing":
            raise ValueError("documento ja em processamento")
        if PROVIDER == "iloveapi" and os.getenv("OCR_ALLOW_REAL_DOCUMENTS","0") != "1":
            raise ValueError("envio real bloqueado por configuracao")
        if PROVIDER not in ("mock","iloveapi","tesseract"):
            raise ValueError("OCR_PROVIDER invalido")
        pdf=bytes(row["normalized_pdf"])
        _, pages=pdf_text(pdf)
        if pages > MAX_PAGES:
            raise ValueError("documento excede limite de paginas por tarefa")
        conn.execute("UPDATE ocr_documents SET status='processing',error=NULL WHERE id=%s",(ident,))
    try:
        output = (pdf if PROVIDER=="mock" else (_tesseract(pdf) if PROVIDER=="tesseract" else _iloveapi(pdf)))
        extracted,_ = pdf_text(output)
        if PROVIDER!="mock" and not extracted.strip():
            raise RuntimeError("ocr retornou texto vazio")
        if PROVIDER=="mock" and not extracted.strip():
            extracted="[MODO MOCK: nenhum texto extraivel, OCR real NAO realizado]"
        with connection() as conn:
            conn.execute("""UPDATE ocr_documents
                SET ocr_pdf=%s,ocr_text=%s,status='processed',
                provider=%s,processed_at=now(),error=NULL
                WHERE id=%s AND tenant=%s""",
                (output,extracted,PROVIDER,ident,tenant))
    except Exception as exc:
        # Never store credentials or API response bodies in error records.
        with connection() as conn:
            conn.execute("""UPDATE ocr_documents SET status='failed',error=%s
                WHERE id=%s AND tenant=%s""",(type(exc).__name__,ident,tenant))
        raise RuntimeError(f"falha no processamento: {type(exc).__name__}") from None
    return get_record(tenant,ident)

def search(tenant, term, limit=25):
    tenant=check_tenant(tenant)
    if len(term)>150:
        raise ValueError("termo muito longo")
    with connection() as conn:
        rows=conn.execute("""SELECT id,tenant,filename,media_type,sha256,status,
                 provider,error,created_at,processed_at,ocr_text
            FROM ocr_documents
            WHERE tenant=%s AND status='processed'
              AND to_tsvector('simple',ocr_text) @@ plainto_tsquery('simple',%s)
            ORDER BY processed_at DESC LIMIT %s""",(tenant,term, max(1,min(limit,100)))).fetchall()
    return [public_record(r) for r in rows]

def export_zip(tenant):
    tenant=check_tenant(tenant)
    with connection() as conn:
        rows=conn.execute("""SELECT id,tenant,filename,media_type,sha256,status,
             provider,error,created_at,processed_at,ocr_text,original_bytes,ocr_pdf
             FROM ocr_documents WHERE tenant=%s ORDER BY created_at""",(tenant,)).fetchall()
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        manifest=[]
        for row in rows:
            ident=str(row["id"])
            info=public_record(row)
            info["sha256_original"]=hashlib.sha256(bytes(row["original_bytes"])).hexdigest()
            z.writestr(f"files/{ident}/original", bytes(row["original_bytes"]))
            if row["ocr_pdf"] is not None:
                z.writestr(f"files/{ident}/ocr.pdf", bytes(row["ocr_pdf"]))
            manifest.append(info)
        z.writestr("manifest.json",json.dumps(
            {"schema":"gaia-ocr-export-v1","tenant":tenant,"documents":manifest},
            ensure_ascii=False,indent=2).encode("utf-8"))
    return out.getvalue()

