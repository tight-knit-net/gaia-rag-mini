'use strict';
// Bridge: Google Drive native connector READ ONLY -> local staged copies -> GAIA preview.
// Never makes network requests, never mutates Google Drive or source files.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {DRIVE_ID,PATHS}=require('../drive1/config');
const {inventoryFromReadOnlyPages}=require('../drive1/inventory');
const {makeInitialBulletin,nextBulletin}=require('../drive1/bulletin');
const {proposeItem,markCollisions,prepareBatch}=require('../drive1/workflow');
const ROOT='application/vnd.google-apps.folder';
const RULE={DANFSE:'NOM-001',CNPJ:'NOM-002',IPTU:'NOM-018',JUCESC:'NOM-016',CBMSC_AUTO:'NOM-003',DARE:'NOM-026',REQUERIMENTO_ASSINADO:'NOM-041',REQUERIMENTO_EDITAVEL:'NOM-042',CNH:'NOM-033'};
const MIME={'application/pdf':'.pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document':'.docx'};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function blocked(f,reason){return {status:'BLOCKED',reason,fileId:f.id,sourceParentId:f.parentId,sourceVersion:f.version,sourceName:f.name,execution_attempted:false,execution_allowed:false}}
function safe(s){return String(s??'-').replace(/[|\r\n]/g,' ').slice(0,230)}
function stage(f,record,dir){
 if(!record)return {error:'COPY_MISSING'};
 if(record.fileId!==f.id||record.sourceVersion!==f.version)return {error:'COPY_SOURCE_CHANGED'};
 const suffix=MIME[f.mimeType];
 if(!suffix)return {error:'MIME_NOT_SUPPORTED'};
 const filename=f.id+suffix,filepath=path.join(dir,filename);
 try{
  if(record.storedAs!==filename||!record.sha256||!(/^[a-f0-9]{64}$/).test(record.sha256))return {error:'STAGING_CONTRACT_INVALID'};
  const st=fs.lstatSync(filepath);
  if(!st.isFile()||st.isSymbolicLink()||st.nlink!==1||st.size!==record.bytes||st.size>25*1024*1024)return {error:'STAGING_SIZE_OR_LINK_INVALID'};
  const content=fs.readFileSync(filepath);
  if(hash(content)!==record.sha256)return {error:'SHA256_MISMATCH'};
  if(suffix==='.pdf'&&content.subarray(0,5).toString()!=='%PDF-')return {error:'MIME_SIGNATURE_MISMATCH'};
  if(suffix==='.docx'&&content.subarray(0,2).toString()!=='PK')return {error:'MIME_SIGNATURE_MISMATCH'};
  return {ok:true,sha256:record.sha256};
 }catch(e){return {error:e.code==='ENOENT'?'COPY_MISSING':'STAGING_READ_ERROR'}}
}
function suggest(f,metadata,clientId,clientProof){
 if(!metadata||metadata.provenance!=='DOCUMENT_VERIFIED_FIELDS'||metadata.fileId!==f.id||
    metadata.sourceVersion!==f.version)return blocked(f,'DOCUMENT_FIELDS_NOT_VERIFIED');
 if(metadata.clientId!==clientId)return blocked(f,'CLIENT_ID_MISMATCH');
 if(metadata.mimeType!==f.mimeType)return blocked(f,'MIME_CONFLICT');
 if(!Array.isArray(metadata.evidence)||!metadata.evidence.some(e=>e.sourceId===f.id&&e.verified===true&&e.locator))
   return blocked(f,'EVIDENCE_NOT_VERIFIED');
 const ruleId=RULE[metadata.documentType];
 if(!ruleId)return blocked(f,'DOCUMENT_TYPE_UNRECOGNIZED');
 const dest=metadata.destination;
 if(!dest||dest.driveId!==DRIVE_ID||dest.verified!==true)
   return blocked(f,'DESTINATION_NOT_VERIFIED');
 return proposeItem({
  item:f,clientId,clientProof,
  classification:{domain:metadata.domain,thirdParty:metadata.thirdParty===true,
   belongingVerified:true,evidence:metadata.evidence},
  nom:{ruleId,sourceRechecked:metadata.sourceRechecked===true,
   provided:metadata.provided||{},rawFields:metadata.rawFields||{},
   evidence:metadata.evidence},
  topology:{destinationParentId:dest.folderId,destinationDriveId:DRIVE_ID,
   destinationVerified:true,destinationAncestors:dest.ancestors,
   processVerified:dest.processVerified===true}
 });
}
function execute({manifest,sourceDir,outDir}){
 if(manifest?.schema!=='gaia.drive1.pilot.v1'||manifest.mode!=='READ_ONLY'||
    manifest.driveId!==DRIVE_ID||!/^\d{3}$/.test(manifest.clientId||'')||
    !Array.isArray(manifest.pages)||!Array.isArray(manifest.scopeIds)||
    !Array.isArray(manifest.copies))throw Error('INVALID_PILOT_MANIFEST');
 const inventory=inventoryFromReadOnlyPages({batchId:manifest.batchId,scopeIds:manifest.scopeIds,pages:manifest.pages});
 const files=inventory.items.filter(f=>!f.folder);
 const copies=new Map(manifest.copies.map(x=>[x.fileId,x]));
 if(copies.size!==manifest.copies.length||[...copies.keys()].some(id=>!files.some(f=>f.id===id)))
   throw Error('COPIES_OUT_OF_SCOPE_OR_DUPLICATE');
 const source=files.map(f=>{
  const byteResult=stage(f,copies.get(f.id),sourceDir);
  const proposal=byteResult.ok?suggest(f,(manifest.metadataById||{})[f.id],
   manifest.clientId,manifest.clientProof):blocked(f,byteResult.error);
  return {fileId:f.id,name:f.name,mimeType:f.mimeType,
   byteVerified:!!byteResult.ok,sha256:byteResult.sha256||null,proposal};
 });
 const checked=markCollisions(source.map(x=>x.proposal),manifest.destinationSnapshot?.files||[]);
 const rows=source.map((r,i)=>({...r,proposal:checked[i]}));
 const b1=makeInitialBulletin(inventory,{observedAt:manifest.observedAt||new Date().toISOString(),operatorScopeRef:'PILOT_'+manifest.batchId});
 const b2=nextBulletin(b1,inventory,rows.map(r=>({fileId:r.fileId,
  stage:r.proposal.status==='PREVIEW'?'NAMING_PREVIEW':r.byteVerified?'REVIEW_REQUIRED':'CONTENT_PARTIAL',
  preview:r.proposal,evidenceRefs:r.proposal.evidenceIds||[]})),{observedAt:new Date().toISOString()});
 const plan=prepareBatch({inventory,proposals:rows.map(r=>r.proposal),selectedFileIds:rows.map(r=>r.fileId),
  registrationGate:'WAIT',topologyBulletinPersisted:false,destinationSnapshot:manifest.destinationSnapshot||null});
 const summary={schema:'gaia.drive1.pilot-result.v1',batchId:manifest.batchId,
  clientId:manifest.clientId,files:files.length,staged:rows.filter(r=>r.byteVerified).length,
  preview:rows.filter(r=>r.proposal.status==='PREVIEW').length,
  blocked:rows.filter(r=>r.proposal.status==='BLOCKED').length,ocr:false,driveWrites:0,
  batchState:plan.state,blockers:plan.blockers};
 if(fs.existsSync(outDir))throw Error('OUTPUT_DIR_ALREADY_EXISTS');
 fs.mkdirSync(outDir,{recursive:true,mode:0o700});
 for(const [name,data] of [['catalogo.json',rows],['inventario.json',inventory],
   ['boletim_001.json',b1],['boletim_002.json',b2],['plano_BLOQUEADO.json',plan],['resumo.json',summary]])
   fs.writeFileSync(path.join(outDir,name),JSON.stringify(data,null,2)+'\n',{mode:0o600});
 const md=['# GAIA — Boletim do piloto real (leitura e prévia)','',
  '- Lote: '+safe(summary.batchId),
  '- Cliente: '+summary.clientId,
  '- Inventariados: '+summary.files,
  '- Cópias validadas: '+summary.staged,
  '- Nomes propostos: '+summary.preview,
  '- Pendentes: '+summary.blocked,
  '- OCR: não executado; datas e vínculos dependem de metadados documentais comprovados.',
  '- Google Drive: 0 alterações. Nenhum documento original foi renomeado.',
  '- Estado do lote: '+summary.batchState,'',
  '| File ID | Nome original | Novo nome (prévia) | Decisão |',
  '|---|---|---|---|'];
 for(const r of rows)md.push('| '+safe(r.fileId)+' | '+safe(r.name)+' | '+
   safe(r.proposal.proposedName)+' | '+safe(r.proposal.status==='PREVIEW'?'PREVIEW':r.proposal.reason)+' |');
 md.push('','Apenas cópias temporárias foram lidas; executar qualquer alteração no Drive exige novo processo de autorização.','');
 fs.writeFileSync(path.join(outDir,'BOLETIM.md'),md.join('\n'),{mode:0o600});
 return summary;
}
if(require.main===module){
 try{
  const [mf,src,out]=process.argv.slice(2);
  if(!mf||!src||!out)throw Error('USAGE: node pilot/run.js manifest.json raw_dir output_dir');
  console.log(JSON.stringify(execute({manifest:JSON.parse(fs.readFileSync(mf,'utf8')),sourceDir:src,outDir:out}),null,2));
 }catch(e){console.error('PILOT_BLOCKED:',e.message);process.exitCode=1}
}
module.exports={execute,stage,suggest,RULE};
