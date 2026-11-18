'use strict';
/** End-to-end OCR staging -> candidate reading -> naming report. No Drive writes. */
const fs=require('node:fs'),path=require('node:path');
const {execute,stage}=require('./run');
const {GaiaOcrClient}=require('./ocr_bridge');
const {DRIVE_ID}=require('../drive1/config');
const PDF='application/pdf';
const safe=s=>String(s??'-').replace(/[|\r\n\u0000-\u001f]/g,' ').slice(0,180);

async function processOcrBatch({
 manifest,sourceDir,outDir,client,synthetic=false,
 authorizedFileIds=[],externalProviderApproved=false
}={}){
 if(manifest?.schema!=='gaia.drive1.pilot.v1'||manifest.driveId!==DRIVE_ID)
  throw Error('PILOT_MANIFEST_NOT_VERIFIED');
 if(!client||typeof client.analyze!=='function')throw Error('OCR_CLIENT_REQUIRED');
 if(!synthetic&&(!manifest.clientProof?.indexVerified||!manifest.clientProof?.manifestVerified||
    !authorizedFileIds.length))throw Error('REAL_BATCH_APPROVAL_REQUIRED');
 const copies=new Map(manifest.copies.map(x=>[x.fileId,x]));
 if(copies.size!==manifest.copies.length)throw Error('DUPLICATED_COPIES');
 if(fs.existsSync(outDir))throw Error('REPORT_DIR_ALREADY_EXISTS');
 const baseline=execute({manifest,sourceDir,outDir});
 const catalog=JSON.parse(fs.readFileSync(path.join(outDir,'catalogo.json'),'utf8'));
 const inventory=JSON.parse(fs.readFileSync(path.join(outDir,'inventario.json'),'utf8'));
 const items=new Map(inventory.items.filter(x=>!x.folder).map(x=>[x.id,x]));
 const tenant='pilot_'+manifest.clientId+'_'+manifest.batchId.replace(/[^a-zA-Z0-9_-]/g,'').slice(0,25);
 const review=[];
 for(const row of catalog){
  const item=items.get(row.fileId);
  if(!item)throw Error('INVENTORY_CATALOG_MISMATCH');
  const itemResult={fileId:item.id,status:'NOT_PROCESSED',provider:null,
   ruleCandidates:[],needsHumanReview:true,fieldsVerified:false};
  if(item.mimeType!==PDF){itemResult.status='DOCX_NATIVE_READING_PENDING';review.push(itemResult);continue;}
  const copy=copies.get(item.id),verified=stage(item,copy,sourceDir);
  if(verified.error){itemResult.status=verified.error;review.push(itemResult);continue;}
  if(!synthetic&&!authorizedFileIds.includes(item.id)){
   itemResult.status='NOT_IN_APPROVED_OCR_SCOPE';review.push(itemResult);continue;
  }
  try{
   const reading=await client.analyze({
    fileId:item.id,filename:item.name,
    bytes:fs.readFileSync(path.join(sourceDir,copy.storedAs)),
    sha256:copy.sha256,tenant,synthetic,
    authorizedFileIds,externalProviderApproved
   });
   Object.assign(itemResult,{
    status:reading.status,provider:reading.provider,ocrDocumentId:reading.ocrDocumentId,
    textSha256:reading.textSha256,textChars:reading.textChars,
    hasText:reading.hasText,sourceVerified:reading.sourceVerified,
    ruleCandidates:reading.ruleCandidates
   });
  }catch(e){itemResult.status=e.code?.startsWith('OCR_')?e.code:'OCR_SERVICE_FAILURE'}
  review.push(itemResult);
 }
 const stats={
  schema:'gaia.drive1.ocr-pilot-result.v1',batchId:manifest.batchId,
  clientId:manifest.clientId,sourceDriveId:DRIVE_ID,synthetic,
  files:catalog.length,ocrReal:review.filter(x=>x.provider==='iloveapi'&&x.hasText).length,
  ocrMock:review.filter(x=>x.provider==='mock').length,
  nativePending:review.filter(x=>x.status==='DOCX_NATIVE_READING_PENDING').length,
  failures:review.filter(x=>x.status==='OCR_SERVICE_FAILURE'||x.status.startsWith('OCR_')&&!x.provider).length,
  reviewedAndApproved:0,driveWrites:0,waitingForHumanReview:true,
  sourceOfTruth:'GOOGLE_DRIVE1_READONLY',fullTextStoredInReport:false,
  sqlCleanupRequiredAfterProcessing:true,
  namingPreviewCount:baseline.preview,namingBlockedCount:baseline.blocked
 };
 fs.writeFileSync(path.join(outDir,'OCR_REVISAO.json'),JSON.stringify({summary:stats,items:review},null,2)+'\n',{mode:0o600});
 const original=fs.readFileSync(path.join(outDir,'BOLETIM.md'),'utf8');
 const md=[original.replace(
  '- OCR: não executado; datas e vínculos dependem de metadados documentais comprovados.',
  '- OCR: executado em etapa isolada; reconhecimento e variáveis ainda exigem revisão.'),
  '','## Resultados OCR em ambiente isolado','',
  '- OCR real: '+stats.ocrReal,
  '- Mock (não conta como OCR real): '+stats.ocrMock,
  '- DOCX aguardando extração nativa: '+stats.nativePending,
  '- Sem aprovação automática de nenhuma regra NOM ou vínculo de cliente.',
  '- Textos OCR integrais não estão neste MD; hashes e candidatos são rastreáveis.',
  '',
  '| File ID | Status OCR | Regras candidatas | Revisão humana |',
  '|---|---|---|---|'];
 for(const x of review)md.push('| '+safe(x.fileId)+' | '+safe(x.status)+' | '+
   safe(x.ruleCandidates.map(y=>y.ruleId).join(', '))+' | PENDENTE |');
 md.push('','## Retenção e descarte',
  'O OCR SQL guarda original, PDF processado e texto. Após comprovar que relatório autorizado foi preservado, encerrar o banco temporário e eliminar sua mídia. Excluir raw local NÃO elimina cópias SQL. O Drive 1 permanece intacto.','');
 fs.writeFileSync(path.join(outDir,'BOLETIM_OCR.md'),md.join('\n'),{mode:0o600});
 return {summary:stats,items:review};
}
if(require.main===module){
 (async()=>{
  const [mf,raw,out]=process.argv.slice(2);
  if(!mf||!raw||!out)throw Error('USAGE: node pilot/ocr_batch.js manifest.json raw_dir output_dir');
  if(process.env.GAIA_OCR_SYNTHETIC!=='1')throw Error('REAL_DOCS_REQUIRE_EXPLICIT_SCOPED_ORCHESTRATOR');
  const manifest=JSON.parse(fs.readFileSync(mf,'utf8'));
  const client=new GaiaOcrClient({baseUrl:process.env.GAIA_OCR_BASE_URL,token:process.env.GAIA_OCR_TOKEN});
  const result=await processOcrBatch({manifest,sourceDir:raw,outDir:out,client,synthetic:true});
  process.stdout.write(JSON.stringify(result.summary,null,2)+'\n');
 })().catch(e=>{console.error('OCR_PILOT_BLOCKED',e.code||e.message);process.exitCode=1});
}
module.exports={processOcrBatch};
