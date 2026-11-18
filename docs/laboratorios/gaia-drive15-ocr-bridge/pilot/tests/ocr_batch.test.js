'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('fs'),os=require('os'),path=require('path'),crypto=require('crypto');
const {processOcrBatch}=require('../ocr_batch');
const {pagesFromManifest}=require('../../synthetic/metadata_engine');
const {DRIVE_ID}=require('../../drive1/config');
const FIX=process.env.GAIA_SYNTHETIC_FIXTURES||path.resolve(__dirname,'../../synthetic/generated');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function arrange(){
 const source=JSON.parse(fs.readFileSync(path.join(FIX,'manifest.json'),'utf8'));
 source.cases=source.cases.filter(x=>['S01','S07'].includes(x.driveRecord.caseId));
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'gaia-ocr-batch-'));
 const raw=path.join(folder,'raw');fs.mkdirSync(raw);
 const copies=[];
 for(const row of source.cases){
  const rec=row.driveRecord;
  const b=fs.readFileSync(path.join(FIX,rec.relativePath));
  const suffix=path.extname(rec.name),storedAs=rec.id+suffix;
  fs.writeFileSync(path.join(raw,storedAs),b);
  copies.push({fileId:rec.id,sourceVersion:'1',storedAs,bytes:b.length,sha256:hash(b)});
 }
 const manifest={
  schema:'gaia.drive1.pilot.v1',mode:'READ_ONLY',
  driveId:DRIVE_ID,batchId:'batch_synth_ocr_027',
  clientId:'027',scopeIds:[source.sourceRoot],pages:pagesFromManifest(source),
  copies,metadataById:{},
  destinationSnapshot:{driveId:DRIVE_ID,complete:true,folderIds:[],files:[]}
 };
 return {folder,raw,manifest};
}
test('OCR E2E sintético gera BOLETIM_OCR.md e mantém NOM bloqueada',async()=>{
 const t=arrange();
 const calls=[];
 const client={analyze:async opts=>{
  calls.push({fileId:opts.fileId,synthetic:opts.synthetic});
  return {status:'MOCK_NOT_REAL_OCR',provider:'mock',
   ocrDocumentId:'synthetic-ocr-job-001',textSha256:'a'.repeat(64),
   textChars:100,hasText:true,sourceVerified:true,
   ruleCandidates:[{ruleId:'NOM-001',signalCount:2}]};
 }};
 try{
  const dir=path.join(t.folder,'reports');
  const r=await processOcrBatch({manifest:t.manifest,sourceDir:t.raw,outDir:dir,client,synthetic:true});
  assert.equal(r.summary.files,2);
  assert.equal(r.summary.ocrMock,1);
  assert.equal(r.summary.ocrReal,0);
  assert.equal(r.summary.nativePending,1);
  assert.equal(r.summary.namingPreviewCount,0);
  assert.equal(r.summary.namingBlockedCount,2);
  assert.equal(r.summary.reviewedAndApproved,0);
  assert.equal(r.summary.driveWrites,0);
  assert.equal(calls.length,1);
  assert.equal(calls[0].synthetic,true);
  assert.ok(fs.existsSync(path.join(dir,'boletim_001.json')));
  assert.ok(fs.existsSync(path.join(dir,'boletim_002.json')));
  assert.ok(fs.readFileSync(path.join(dir,'BOLETIM_OCR.md'),'utf8').includes('NOM-001'));
  const review=JSON.parse(fs.readFileSync(path.join(dir,'OCR_REVISAO.json'),'utf8'));
  assert.equal(review.items[0].fieldsVerified,false);
  assert.equal(review.items.find(x=>x.status==='DOCX_NATIVE_READING_PENDING')?.status,'DOCX_NATIVE_READING_PENDING');
 }finally{fs.rmSync(t.folder,{recursive:true,force:true})}
});
test('cliente real sem cliente validado não envia PDF a OCR',async()=>{
 const t=arrange();let called=false;
 try{
  await assert.rejects(processOcrBatch({
   manifest:t.manifest,sourceDir:t.raw,outDir:path.join(t.folder,'output'),
   client:{analyze:async()=>{called=true;}},synthetic:false,authorizedFileIds:[t.manifest.copies[0].fileId]
  }),/REAL_BATCH_APPROVAL_REQUIRED/);
  assert.equal(called,false);
 }finally{fs.rmSync(t.folder,{recursive:true,force:true})}
});
test('erro do serviço OCR mantém relatório e fila de revisão',async()=>{
 const t=arrange();
 try{
  const r=await processOcrBatch({manifest:t.manifest,sourceDir:t.raw,
   outDir:path.join(t.folder,'output'),
   client:{analyze:async()=>{const e=new Error('unreachable');e.code='OCR_API_UNREACHABLE';throw e}},
   synthetic:true});
  assert.equal(r.items.find(x=>x.status==='OCR_API_UNREACHABLE')?.status,'OCR_API_UNREACHABLE');
  assert.equal(r.items[0].needsHumanReview,true);
  assert.equal(r.summary.namingPreviewCount,0);
 }finally{fs.rmSync(t.folder,{recursive:true,force:true})}
});
