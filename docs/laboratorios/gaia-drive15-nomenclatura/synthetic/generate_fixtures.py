#!/usr/bin/env python3
"""Fixtures PDF e DOCX sintéticos: metadados sem OCR e sem conteúdo real."""
import hashlib,json,sys,zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xe
BASE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path("synthetic/generated").resolve()
DRIVE="0ALBFaLnE8ZPHUk9PVA"; ROOT="synthetic_batch_root_027"; SUB="synthetic_batch_sub_027"
# O campo expect serve APENAS aos asserts do laboratório.
CASES=[
 ("S01","nfse.pdf","DANFSE","EMPRESA","EMPRESA_A","03-08-2026","PREVIEW",{}),
 ("S02","cnpj.pdf","CNPJ","EMPRESA","EMPRESA_A","09-01-2026","FILENAME_COLLISION",{"data_abertura":"22-04-2021","data_situacao":"05-08-2024"}),
 ("S03","iptu.pdf","IPTU","IMOVEL","IMOVEL_A",None,"PREVIEW",{"inscricao":"24.58.018.0570.006.549"}),
 ("S04","alteracao.pdf","JUCESC","EMPRESA","EMPRESA_A","01-05-2026","PREVIEW",{"ordinal":"2","consolidado":True}),
 ("S05","fiscalizacao.pdf","CBMSC_AUTO","PROCESSO","PROCESSO_PMF","14-07-2026","PREVIEW",{}),
 ("S06","dare.pdf","DARE","PROCESSO","PROCESSO_PMF","10-09-2026","PREVIEW",{"teor":"MULTA_BOMBEIRO"}),
 ("S07","requerimento.docx","PMF_REQUERIMENTO","PROCESSO","PROCESSO_PMF","12-09-2026","PREVIEW",{"assinado":False}),
 ("S08","requerimento_assinado.pdf","PMF_REQUERIMENTO","PROCESSO","PROCESSO_PMF","12-09-2026","PREVIEW",{"assinado":True}),
 ("S09","cnh.pdf","CNH","PESSOA","PESSOA",None,"NOM_SOURCE_REVIEW_REQUIRED",{}),
 ("S10","cnpj_sem_emissao.pdf","CNPJ","EMPRESA","EMPRESA_A",None,"VARIAVEIS_FALTANTES",{}),
 ("S11","cnpj_copia.pdf","CNPJ","EMPRESA","EMPRESA_A","09-01-2026","FILENAME_COLLISION",{}),
 ("S12","terceiro.pdf","DANFSE","EMPRESA","EMPRESA_A","15-03-2026","THIRD_PARTY_CONFLICT",{"terceiro":True}),
 ("S13","data_invalida.pdf","DANFSE","EMPRESA","EMPRESA_A","31-02-2026","DATA_CALENDARIO_INVALIDA",{}),
 ("S14","desconhecido.pdf","DESCONHECIDO","OUTROS","PESSOA","06-05-2026","METADATA_TYPE_UNRECOGNIZED",{}),
 ("S15","extensao_errada.docx","DANFSE","EMPRESA","EMPRESA_A","08-06-2026","MIME_TYPE_CONFLICT",{}),
 ("S16","sem_metadados.pdf",None,None,None,None,"METADATA_MISSING",{}),
 ("S17","cliente_divergente.pdf","DANFSE","EMPRESA","EMPRESA_A","18-05-2026","CLIENT_MISMATCH",{"cliente":"888"})
]
def pdf(title,subject,lines):
    def enc(s):
        return str(s).replace("\\","\\\\").replace("(","\\(").replace(")","\\)").encode("cp1252","replace")
    instr=b"BT /F1 12 Tf 46 780 Td\n"
    for n,line in enumerate([title,"DOCUMENTO SINTETICO - SEM VALOR LEGAL"]+lines):
        if n:instr+=b"0 -23 Td\n"
        instr+=b"("+enc(line)+b") Tj\n"
    instr+=b"ET\n"
    objects=[b"<< /Type /Catalog /Pages 2 0 R >>",
      b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
      b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
      b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
      b"<< /Length "+str(len(instr)).encode()+b" >>\nstream\n"+instr+b"endstream",
      b"<< /Title ("+enc(title)+b") /Subject ("+enc(subject)+b") /Creator (GAIA SYNTHETIC LAB) >>"]
    raw=bytearray(b"%PDF-1.4\n");positions=[0]
    for i,obj in enumerate(objects,1):
        positions.append(len(raw));raw+=f"{i} 0 obj\n".encode()+obj+b"\nendobj\n"
    xref=len(raw);raw+=f"xref\n0 {len(objects)+1}\n".encode()+b"0000000000 65535 f \n"
    for pos in positions[1:]:raw+=f"{pos:010d} 00000 n \n".encode()
    raw+=f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R /Info 6 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(raw)
def docx(title,subject,lines,path):
    para=lambda s:"<w:p><w:r><w:t>"+xe(str(s))+"</w:t></w:r></w:p>"
    word='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+''.join(map(para,[title,"DOCUMENTO SINTETICO - SEM VALOR LEGAL"]+lines))+'</w:body></w:document>'
    core='<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>'+xe(title)+'</dc:title><dc:subject>'+xe(subject)+'</dc:subject></cp:coreProperties>'
    ct='<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'
    rel='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for a,b in [('[Content_Types].xml',ct),('_rels/.rels',rel),('word/document.xml',word),('docProps/core.xml',core)]:z.writestr(a,b)
    return path.read_bytes()
def generate():
    BASE.mkdir(parents=True,exist_ok=True);out=[]
    for cid,fname,kind,domain,destination,date,expect,extra in CASES:
        parent=SUB if cid in ("S05","S06","S07","S08") else ROOT
        target=BASE/"documentos"/("processos" if parent==SUB else "triagem")
        target.mkdir(parents=True,exist_ok=True)
        path=target/fname
        title="GAIA LAB - DOCUMENTO "+cid
        fields={"data_documento":date} if date else {}
        fields.update(extra)
        lines=["TIPO: "+str(kind),"CLIENTE: 027 (FICTICIO)"]+[str(k)+": "+str(v) for k,v in fields.items()]
        body=pdf(title,kind or "SEM_METADADOS",lines) if path.suffix==".pdf" else docx(title,kind,lines,path)
        if path.suffix==".pdf":path.write_bytes(body)
        digest=hashlib.sha256(body).hexdigest()
        record={"id":"synthetic_file_id_"+cid.lower(),"name":fname,"mimeType":"application/pdf" if path.suffix==".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "parents":[parent],"driveId":DRIVE,"version":"1","modifiedTime":"2026-11-18T00:00:00Z",
          "sha256":digest,"relativePath":str(path.relative_to(BASE)),"size":len(body),"caseId":cid}
        if kind:
            meta={"fixtureId":cid,"documentKind":kind,"domain":domain,"destinationKey":destination,
              "claimedClientId":extra.get("cliente","027"),"thirdParty":extra.get("terceiro",False),
              "fields":fields,"metadataSource":"SYNTHETIC_STRUCTURED_FIELDS_NO_OCR",
              "verifiedFixtureMetadata":True,"documentSha256":digest}
            path.with_suffix(path.suffix+".meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        out.append({"driveRecord":record,"expected":expect,"hasMetadata":bool(kind)})
    manifest={"schema":"gaia.synthetic-metadata-batch.v1","synthetic":True,"ocrUsed":False,
      "driveId":DRIVE,"sourceRoot":ROOT,"subfolder":SUB,"clientId":"027","cases":out}
    (BASE/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (BASE/"SHA256SUMS").write_text("\n".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+str(p.relative_to(BASE)) for p in sorted(BASE.rglob("*")) if p.is_file())+"\n",encoding="utf8")
    print(json.dumps({"total":len(out),"pdf":sum(x["driveRecord"]["mimeType"]=="application/pdf" for x in out),"docx":sum("wordprocessingml" in x["driveRecord"]["mimeType"] for x in out),"withMetadata":sum(x["hasMetadata"] for x in out),"path":str(BASE)}))
if __name__=="__main__":generate()
