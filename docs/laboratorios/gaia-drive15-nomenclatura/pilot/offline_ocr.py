#!/usr/bin/env python3
"""OCR nativo/offline em arquivos verificados; SEM API, MCP ou escrita no Drive.

Entradas: pilot/<run>/manifest.json + raw/<fileId>.pdf|.docx
Saídas:  pilot/<run>/reports/ocr_local_<label>/*.txt e resultado.json
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, zipfile
from xml.etree import ElementTree as ET

MAX_FILE = 15 * 1024 * 1024
MAX_PAGES_HARD = 30
ID = re.compile(r'^[A-Za-z0-9_-]{8,150}$')
HEX = re.compile(r'^[0-9a-f]{64}$')

def fail(reason):
    raise ValueError(reason)

def run(args: list[str], timeout: int = 90) -> str:
    try:
        r = subprocess.run(args, check=True, capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8', errors='replace')
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise ValueError('LOCAL_READER_UNAVAILABLE_OR_FAILED: ' + type(e).__name__) from None

def safe_file(path: pathlib.Path, expected: dict) -> bytes:
    st = path.lstat()
    if path.is_symlink() or not path.is_file() or st.st_nlink != 1 or not 0 < st.st_size <= MAX_FILE:
        fail('UNSAFE_OR_OVERSIZED_FILE')
    b = path.read_bytes()
    if len(b) != expected['bytes'] or hashlib.sha256(b).hexdigest() != expected['sha256']:
        fail('SHA256_OR_SIZE_MISMATCH')
    if path.suffix == '.pdf' and not b.startswith(b'%PDF-'):
        fail('PDF_MAGIC_INVALID')
    if path.suffix == '.docx' and not b.startswith(b'PK'):
        fail('DOCX_MAGIC_INVALID')
    return b

def docx_text(p: pathlib.Path) -> list[dict]:
    with zipfile.ZipFile(p) as z:
        if sum(x.file_size for x in z.infolist()) > 20*1024*1024:
            fail('DOCX_TOO_LARGE_UNCOMPRESSED')
        if 'word/document.xml' not in z.namelist():
            fail('DOCX_DOCUMENT_XML_MISSING')
        root = ET.fromstring(z.read('word/document.xml'))
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text = '\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in root.findall('.//w:p',ns))
    return [{'page':1,'method':'DOCX_NATIVE','text':text,'chars':len(text),'quality':'REVIEW_REQUIRED'}]

def pdf_text(p: pathlib.Path, limit: int) -> list[dict]:
    info=run(['pdfinfo',str(p)],timeout=30)
    m=re.search(r'(?m)^Pages:\s+(\d+)\s*$',info)
    if not m:fail('PAGE_COUNT_UNKNOWN')
    pages=int(m.group(1))
    if pages<1 or pages>limit:fail('PAGE_LIMIT_REQUIRES_SEPARATE_AUTHORIZATION')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='gaia-offline-ocr-') as d:
        for page in range(1,pages+1):
            text=run(['pdftotext','-f',str(page),'-l',str(page),'-layout',str(p),'-'],timeout=35).strip()
            method='TEXT_NATIVE'
            if len(text)<60:
                stem=pathlib.Path(d)/f'page_{page}'
                run(['pdftoppm','-f',str(page),'-l',str(page),'-singlefile','-r','180','-png',str(p),str(stem)],timeout=90)
                img=stem.with_suffix('.png')
                if not img.is_file() or img.stat().st_size>35*1024*1024:fail('RASTERIZATION_FAILED')
                text=run(['tesseract',str(img),'stdout','-l','por+eng'],timeout=90).strip()
                method='OCR_TESSERACT'
            rows.append({'page':page,'method':method,'text':text,'chars':len(text),
                        'quality':'LOW_TEXT_REVIEW' if len(text)<60 else 'UNVERIFIED_TEXT'})
    return rows

def process(run_dir: pathlib.Path, label: str, limit: int = 10) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,50}',label):fail('INVALID_OUTPUT_LABEL')
    if not 1<=limit<=MAX_PAGES_HARD:fail('MAX_PAGES_OUT_OF_RANGE')
    if run_dir.is_symlink() or not run_dir.is_dir():fail('PILOT_RUN_DIR_INVALID')
    mf=json.loads((run_dir/'manifest.json').read_text('utf-8'))
    if mf.get('mode')!='READ_ONLY' or mf.get('driveId')!='0ALBFaLnE8ZPHUk9PVA' or mf.get('schema')!='gaia.drive1.pilot.v1':fail('PILOT_MANIFEST_INVALID')
    copies=mf.get('copies')
    if not isinstance(copies,list) or not copies:fail('COPIES_MISSING')
    outdir=run_dir/'reports'/('ocr_local_'+label)
    if outdir.exists():fail('REPORT_ALREADY_EXISTS')
    # Do not make report directories until *all* copy hashes and types are confirmed.
    prepared=[];ids=set()
    for c in copies:
        fid=c.get('fileId','');ext=pathlib.Path(c.get('storedAs','')).suffix
        if not ID.fullmatch(fid) or fid in ids or c.get('storedAs')!=fid+ext or ext not in ('.pdf','.docx') or not HEX.fullmatch(c.get('sha256','')):fail('COPY_DESCRIPTOR_INVALID')
        ids.add(fid)
        p=run_dir/'raw'/c['storedAs']
        safe_file(p,c)
        prepared.append((fid,p,c))
    outdir.mkdir(parents=True,mode=0o700)
    rows=[]
    try:
        for fid,p,c in prepared:
            try:
                pages=pdf_text(p,limit) if p.suffix=='.pdf' else docx_text(p)
                total='\n\n'.join(f'--- PAGE {x["page"]} / {x["method"]} ---\n{x["text"]}' for x in pages)+'\n'
                txtname=fid+'.txt'
                txtpath=outdir/txtname
                with txtpath.open('x',encoding='utf-8') as stream:stream.write(total)
                os.chmod(txtpath,0o600)
                rows.append({'fileId':fid,'status':'TEXT_EXTRACTED_REVIEW_REQUIRED','sourceSha256':c['sha256'],
                             'textSha256':hashlib.sha256(total.encode()).hexdigest(),'txtName':txtname,
                             'pages':len(pages),'ocrPages':sum(x['method']=='OCR_TESSERACT' for x in pages),
                             'lowTextPages':[x['page'] for x in pages if x['quality']=='LOW_TEXT_REVIEW'],
                             'textChars':sum(x['chars'] for x in pages),'humanVerified':False,'nomApproved':False})
            except ValueError as exc:
                rows.append({'fileId':fid,'status':'BLOCKED_REVIEW','reason':str(exc),
                             'sourceSha256':c['sha256'],'humanVerified':False,'nomApproved':False})
        report={'schema':'gaia.drive1.offline-ocr.v1','clientId':mf.get('clientId'),'batchId':mf.get('batchId'),
                'mode':'LOCAL_OFFLINE_NO_GOOGLE_API','results':rows,'driveWrites':0,'mcpPublishes':0,
                'automatedNOMOrMove':False,'validation':'OCR_COVERAGE_NOT_TEXT_ACCURACY',
                'note':'Resultados locais não comprovam a revisão humana nem a norma NOM.'}
        dest=outdir/'resultado.json'
        with dest.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        os.chmod(dest,0o600)
        return report
    except Exception:
        shutil.rmtree(outdir)
        raise

if __name__=='__main__':
    try:
        p=argparse.ArgumentParser();p.add_argument('run_dir');p.add_argument('--label',default='rodada01');p.add_argument('--max-pages',type=int,default=10)
        args=p.parse_args();r=process(pathlib.Path(args.run_dir),args.label,args.max_pages)
        print(json.dumps({'batchId':r['batchId'],'files':len(r['results']),'success':sum(x['status'].startswith('TEXT_') for x in r['results']),'blocked':sum(x['status'].startswith('BLOCKED') for x in r['results']),'driveWrites':0},ensure_ascii=False))
    except Exception as ex:
        print('OCR_OFFLINE_BLOCKED',str(ex),file=sys.stderr);sys.exit(2)
