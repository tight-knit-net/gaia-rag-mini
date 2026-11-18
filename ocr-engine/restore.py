"""Restore an exported GAIA OCR ZIP into another PostgreSQL database.

Defaults to validation-only. Requires explicit --apply to insert.
DATABASE_URL must point at the intended destination database.
"""
import argparse
import hashlib
import json
import uuid
import zipfile

import engine

def restore(archive, apply=False):
    with zipfile.ZipFile(archive) as z:
        data=json.loads(z.read("manifest.json"))
        if data.get("schema")!="gaia-ocr-export-v1":
            raise ValueError("unsupported export schema")
        rows=[]
        for doc in data["documents"]:
            ident=str(uuid.UUID(str(doc["id"])))
            tenant=engine.check_tenant(doc["tenant"])
            original=z.read(f"files/{ident}/original")
            actual=hashlib.sha256(original).hexdigest()
            if actual != doc["sha256"] or actual != doc["sha256_original"]:
                raise ValueError(f"checksum mismatch: {ident}")
            pdf,_,media=engine.normalize(original,doc["filename"])
            processed_name=f"files/{ident}/ocr.pdf"
            output=z.read(processed_name) if processed_name in z.namelist() else None
            if output is not None:
                engine.pdf_text(output)
            rows.append((ident,tenant,doc["filename"],doc["media_type"],
                doc["sha256"],original,pdf,output,doc["text"],doc["status"],
                doc["provider"],doc.get("error"),doc["created_at"],doc.get("processed_at")))
    if apply:
        engine.setup()
        with engine.connection() as conn:
            for row in rows:
                conn.execute("""INSERT INTO ocr_documents
                    (id,tenant,filename,media_type,sha256,original_bytes,
                    normalized_pdf,ocr_pdf,ocr_text,status,provider,error,
                    created_at,processed_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING""",row)
    return {"validated":len(rows),"import_attempted":len(rows) if apply else 0,
            "applied":apply,"schema":"gaia-ocr-export-v1"}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("archive",help="gaia-ocr-tenant.zip")
    parser.add_argument("--apply",action="store_true",help="insert into DATABASE_URL")
    args=parser.parse_args()
    print(json.dumps(restore(args.archive,args.apply)))

