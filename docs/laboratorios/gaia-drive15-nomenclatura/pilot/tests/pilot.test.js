'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {execute,stage}=require('../run');
const {setup,purge}=require('../purge');
const {pagesFromManifest}=require('../../synthetic/metadata_engine');
const {DRIVE_ID,PATHS}=require('../../drive1/config');
const FIX=process.env.GAIA_SYNTHETIC_FIXTURES||path.resolve(__dirname,'../../synthetic/generated');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function make(){
 const m=JSON.parse(fs.readFileSync(path.join(FIX,'manifest.json'),'utf8'));
 m.cases=m.cases.filter(x=>['S01','S16'].includes(x.driveRecord.caseId));
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gaia-pilot-tests-'));
 const raw=path.join(temp,'raw');fs.mkdirSync(raw);
 const first=m.cases[0].driveRecord;
 const original=path.join(FIX,first.relativePath);
 const content=fs.readFileSync(original);
 fs.writeFileSync(path.join(raw,first.id+'.pdf'),content);
 const clientFolderId='synthetic_client_folder_027';
 const manifest={
  schema:'gaia.drive1.pilot.v1',mode:'READ_ONLY',batchId:'synthetic-pilot-027',
  driveId:DRIVE_ID,scopeIds:[m.sourceRoot],pages:pagesFromManifest(m),
  clientId:'027',observedAt:'2026-11-18T09:35:00Z',
  copies:[{fileId:first.id,sourceVersion:first.version,
   storedAs:first.id+'.pdf',sha256:sha(content),bytes:content.length}],
  clientProof:{clientId:'027',driveId:DRIVE_ID,clientFolderId,
   indexVerified:true,manifestVerified:true,indexFileId:PATHS.clientIndex,
   manifestFileId:'synthetic_manifest_027',manifestVersion:'1'},
  destinationSnapshot:{driveId:DRIVE_ID,complete:true,
   folderIds:['synthetic_destination_empresa_027'],files:[]},
  metadataById:{
   [first.id]:{
    provenance:'DOCUMENT_VERIFIED_FIELDS',fileId:first.id,sourceVersion:first.version,
    clientId:'027',mimeType:first.mimeType,documentType:'DANFSE',domain:'EMPRESA',
    sourceRechecked:true,provided:{DATA:'03-08-2026'},
    evidence:[{sourceId:first.id,locator:'synthetic-sidecar:/data_documento',verified:true}],
    destination:{folderId:'synthetic_destination_empresa_027',driveId:DRIVE_ID,
     verified:true,ancestors:[clientFolderId,'synthetic_destination_empresa_027']}
   }
  }
 };
 return {temp,raw,manifest,first};
}
test('piloto lê 2 arquivos sintéticos e propõe nome só com evidência validada',()=>{
 const t=make(),out=path.join(t.temp,'output');
 try{
  const s=execute({manifest:t.manifest,sourceDir:t.raw,outDir:out});
  assert.equal(s.files,2);assert.equal(s.staged,1);
  assert.equal(s.preview,1);assert.equal(s.blocked,1);
  assert.equal(s.driveWrites,0);assert.equal(s.ocr,false);
  assert.equal(s.batchState,'BLOCKED');
  const c=JSON.parse(fs.readFileSync(path.join(out,'catalogo.json')));
  assert.equal(c[0].proposal.proposedName,'027_DANFSe-03-08-2026.pdf');
  assert.equal(c[1].proposal.reason,'COPY_MISSING');
  const b2=JSON.parse(fs.readFileSync(path.join(out,'boletim_002.json')));
  const b1=JSON.parse(fs.readFileSync(path.join(out,'boletim_001.json')));
  assert.equal(b2.previousSha256,b1.sha256);
  assert.match(fs.readFileSync(path.join(out,'BOLETIM.md'),'utf8'),/Nomes propostos: 1/);
 }finally{fs.rmSync(t.temp,{recursive:true,force:true})}
});
test('SHA incorreto bloqueia arquivo sem produzir prévia',()=>{
 const t=make();try{
  const f=t.manifest.pages[1].items.find(x=>x.id===t.first.id);
  const record={...t.manifest.copies[0],sha256:'0'.repeat(64)};
  assert.equal(stage(f,record,t.raw).error,'SHA256_MISMATCH');
 }finally{fs.rmSync(t.temp,{recursive:true,force:true})}
});
test('campo não comprovado pelo documento não promove nome',()=>{
 const t=make(),out=path.join(t.temp,'result');
 try{
  t.manifest.metadataById[t.first.id].provenance='FILENAME_GUESS_ONLY';
  const s=execute({manifest:t.manifest,sourceDir:t.raw,outDir:out});
  assert.equal(s.preview,0);
  const c=JSON.parse(fs.readFileSync(path.join(out,'catalogo.json')));
  assert.equal(c[0].proposal.reason,'DOCUMENT_FIELDS_NOT_VERIFIED');
 }finally{fs.rmSync(t.temp,{recursive:true,force:true})}
});
test('cópia fora do inventário não entra no lote',()=>{
 const t=make(),out=path.join(t.temp,'out');
 try{t.manifest.copies.push({...t.manifest.copies[0],fileId:'outsider_document_id'});
  assert.throws(()=>execute({manifest:t.manifest,sourceDir:t.raw,outDir:out}),/COPIES_OUT_OF_SCOPE_OR_DUPLICATE/);
 }finally{fs.rmSync(t.temp,{recursive:true,force:true})}
});
test('limpeza de sandbox é dry-run por padrão e conserva relatórios',()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gaia-clean-'));
 const old=process.env.GAIA_PILOT_BASE;
 // Teste unitário da limpeza num subprocesso para isolar o caminho base por execução
 const {spawnSync}=require('node:child_process');
 try{
  const app=path.resolve(__dirname,'../purge.js');
  const env={...process.env,GAIA_PILOT_BASE:temp};
  let r=spawnSync(process.execPath,[app,'setup','pilot_027_test001','027'],{env,encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  const p=path.join(temp,'pilot_027_test001');
  fs.writeFileSync(path.join(p,'raw','testfile.pdf'),Buffer.from('%PDF-1.4\nsynthetic'));
  fs.writeFileSync(path.join(p,'reports','BOLETIM.md'),'# relatório preservado');
  r=spawnSync(process.execPath,[app,'purge','pilot_027_test001'],{env,encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  assert.equal(JSON.parse(r.stdout).status,'DRY_RUN');
  assert.ok(fs.existsSync(path.join(p,'raw','testfile.pdf')));
  r=spawnSync(process.execPath,[app,'purge','pilot_027_test001','--commit'],{env,encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  assert.equal(JSON.parse(r.stdout).status,'LOCAL_COPIES_DISCARDED');
  assert.ok(!fs.existsSync(path.join(p,'raw')));
  assert.ok(fs.existsSync(path.join(p,'reports','BOLETIM.md')));
  assert.ok(fs.existsSync(path.join(p,'reports','LOCAL_COPIES_PURGED.json')));
 }finally{fs.rmSync(temp,{recursive:true,force:true});if(old===undefined)delete process.env.GAIA_PILOT_BASE}
});
