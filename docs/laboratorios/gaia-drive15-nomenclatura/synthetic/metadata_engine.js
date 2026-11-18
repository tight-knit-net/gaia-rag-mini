'use strict';
/* Ensaio E2E: ler bytes/sha/metadata sintetica; jamais conectar ao Google Drive. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {DRIVE_ID,PATHS}=require('../drive1/config');
const {inventoryFromReadOnlyPages}=require('../drive1/inventory');
const {proposeItem,markCollisions,prepareBatch}=require('../drive1/workflow');
const {makeInitialBulletin,nextBulletin}=require('../drive1/bulletin');
const FOLDER='application/vnd.google-apps.folder';
const PDF='application/pdf';
const DOCX='application/vnd.openxmlformats-officedocument.wordprocessingml.document';
const SYN_CLIENT='synthetic_client_folder_027';
const DEST={
 EMPRESA_A:'synthetic_destination_empresa_027',
 IMOVEL_A:'synthetic_destination_imovel_A_027',
 PROCESSO_PMF:'synthetic_destination_processo_027',
 PESSOA:'synthetic_destination_pessoa_027'
};
const MAP={
 DANFSE:{rule:'NOM-001',domain:'EMPRESA',mime:PDF},
 CNPJ:{rule:'NOM-002',domain:'EMPRESA',mime:PDF},
 IPTU:{rule:'NOM-018',domain:'IMOVEL',mime:PDF},
 JUCESC:{rule:'NOM-016',domain:'EMPRESA',mime:PDF},
 CBMSC_AUTO:{rule:'NOM-003',domain:'PROCESSO',mime:PDF},
 DARE:{rule:'NOM-026',domain:'PROCESSO',mime:PDF},
 PMF_REQUERIMENTO:{domain:'PROCESSO',mime:null},
 CNH:{rule:'NOM-033',domain:'PESSOA',mime:PDF}
};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function fail(file,reason,detail=null){
 return {fileId:file.id,sourceParentId:file.parentId,sourceVersion:file.version,
  sourceName:file.name,sourceMimeType:file.mimeType,status:'BLOCKED',reason,
  detail,proposedName:null,proposedParentId:null,ruleId:null,
  execution_attempted:false,execution_allowed:false};
}
function readBytesAndMetadata(base,record){
 const relative=record.relativePath;
 if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split(/[\\/]/).includes('..'))
   return {error:'FIXTURE_PATH_INVALID'};
 const absolute=path.resolve(base,relative);
 if(!absolute.startsWith(path.resolve(base)+path.sep))return {error:'FIXTURE_PATH_INVALID'};
 let bytes;
 try{bytes=fs.readFileSync(absolute)}catch{return {error:'DOCUMENT_NOT_FOUND'}}
 if(bytes.length!==record.size||hash(bytes)!==record.sha256)
   return {error:'DOCUMENT_HASH_MISMATCH'};
 if(record.mimeType===PDF){
   if(bytes.subarray(0,5).toString()!=='%PDF-')return {error:'MIME_SIGNATURE_MISMATCH'};
 }else if(record.mimeType===DOCX){
   if(bytes.subarray(0,2).toString()!=='PK')return {error:'MIME_SIGNATURE_MISMATCH'};
 }else return {error:'MIME_UNSUPPORTED'};
 let meta;
 try{meta=JSON.parse(fs.readFileSync(absolute+'.meta.json','utf8'))}
 catch(e){return {error:e.code==='ENOENT'?'METADATA_MISSING':'METADATA_INVALID_JSON'}}
 if(!meta||meta.documentSha256!==record.sha256||meta.verifiedFixtureMetadata!==true||
    meta.metadataSource!=='SYNTHETIC_STRUCTURED_FIELDS_NO_OCR')
   return {error:'METADATA_INTEGRITY_INVALID'};
 if(record.mimeType===PDF){
   // SOMENTE dicionário de propriedades PDF /Subject, não extrai texto de página.
   const subject=bytes.toString('latin1').match(/\/Subject \(([^)]*)\)/);
   if(!subject||subject[1]!==meta.documentKind)return {error:'EMBEDDED_SUBJECT_MISMATCH'};
 }
 return {meta};
}
function pagesFromManifest(m){
 const root=m.sourceRoot,sub=m.subfolder;
 const folder=(id,name,parent)=>({id,name,parents:[parent],driveId:DRIVE_ID,mimeType:FOLDER,version:'1'});
 const control=[PATHS.topology,PATHS.ocr,PATHS.quarantine].map(id=>folder(id,'CONTROLE_PERMANENTE',PATHS.triage));
 const items=m.cases.map(x=>x.driveRecord);
 const rootItems=items.filter(x=>x.parents.includes(root));
 const subItems=items.filter(x=>x.parents.includes(sub));
 const page=(parentId,list)=>({parentId,items:list,driveId:DRIVE_ID,complete:true,nextPageToken:null});
 return [
  page(PATHS.triage,[...control,folder(root,'LOTE DE TESTE 027',PATHS.triage)]),
  page(root,[folder(sub,'PROCESSOS FICTICIOS',root),...rootItems]),
  page(sub,subItems)
 ];
}
function classify(meta,rec){
 const kind=meta.documentKind,spec=MAP[kind];
 if(!spec)return {error:'METADATA_TYPE_UNRECOGNIZED'};
 if(meta.claimedClientId!=='027')return {error:'CLIENT_MISMATCH'};
 if(spec.domain!==meta.domain)return {error:'ENTITY_DOMAIN_MISMATCH'};
 if(kind==='PMF_REQUERIMENTO'){
   const signed=meta.fields?.assinado;
   if(typeof signed!=='boolean')return {error:'SIGNATURE_STATUS_UNVERIFIED'};
   if((signed?PDF:DOCX)!==rec.mimeType)return {error:'MIME_TYPE_CONFLICT'};
   return {kind,ruleId:signed?'NOM-041':'NOM-042',domain:spec.domain};
 }
 if(spec.mime!==rec.mimeType)return {error:'MIME_TYPE_CONFLICT'};
 return {kind,ruleId:spec.rule,domain:spec.domain};
}
function proveNom(meta,ruleId,sourceId){
 const f=meta.fields||{},provided={},rawFields={};
 if(['NOM-001','NOM-002','NOM-003','NOM-016','NOM-041','NOM-042'].includes(ruleId))
   if(f.data_documento)provided.DATA=f.data_documento;
 if(ruleId==='NOM-016'){
   if(f.ordinal)provided.ORDINAL=f.ordinal;
   if(typeof f.consolidado==='boolean')provided.consolidado=f.consolidado;
 }
 if(ruleId==='NOM-018'&&f.inscricao)rawFields.inscricao_imobiliaria_completa=f.inscricao;
 if(ruleId==='NOM-026'){
   if(f.data_documento)provided.DATA=f.data_documento;
   if(f.teor)provided.TEOR=f.teor;
 }
 return {ruleId,provided,rawFields,sourceRechecked:true,
   evidence:[{sourceId,locator:'synthetic-metadata:/fields',verified:true}]};
}
function assess(base,record,item){
 const got=readBytesAndMetadata(base,record);
 if(got.error)return {decision:fail(item,got.error),kind:null,domain:null};
 const meta=got.meta,classified=classify(meta,record);
 if(classified.error)return {decision:fail(item,classified.error),kind:meta.documentKind,domain:meta.domain};
 const dest=DEST[meta.destinationKey];
 if(!dest)return {decision:fail(item,'DESTINATION_KEY_UNRECOGNIZED'),kind:meta.documentKind,domain:meta.domain};
 const verified=[{sourceId:item.id,locator:'synthetic-metadata:/documentKind',verified:true}];
 const input={
   item,clientId:'027',
   clientProof:{clientId:'027',driveId:DRIVE_ID,clientFolderId:SYN_CLIENT,
     indexVerified:true,manifestVerified:true,indexFileId:PATHS.clientIndex,
     manifestFileId:'synthetic_manifest_027',manifestVersion:'1'},
   classification:{domain:classified.domain,belongingVerified:true,
     thirdParty:meta.thirdParty===true,evidence:verified},
   topology:{destinationParentId:dest,destinationDriveId:DRIVE_ID,
     destinationAncestors:[SYN_CLIENT,dest],destinationVerified:true,
     processVerified:true},
   nom:proveNom(meta,classified.ruleId,item.id)
 };
 return {decision:proposeItem(input),kind:meta.documentKind,domain:classified.domain};
}
function run(base,{overrideManifest=null}={}){
 const manifest=overrideManifest||JSON.parse(fs.readFileSync(path.join(base,'manifest.json'),'utf8'));
 if(!manifest.synthetic||manifest.ocrUsed!==false||manifest.driveId!==DRIVE_ID)
   throw Error('ONLY_SYNTHETIC_METADATA_MANIFEST_ALLOWED');
 const inventory=inventoryFromReadOnlyPages({
   batchId:'synthetic-lote-027-20261118',scopeIds:[manifest.sourceRoot],pages:pagesFromManifest(manifest)
 });
 const norm=new Map(inventory.items.map(x=>[x.id,x]));
 const raw=manifest.cases.map(c=>{
   const {decision,kind,domain}=assess(base,c.driveRecord,norm.get(c.driveRecord.id));
   return {fixtureId:c.driveRecord.caseId,kind,domain,expected:c.expected,decision,
     fileId:c.driveRecord.id,sourceMime:c.driveRecord.mimeType,
     sha256:c.driveRecord.sha256,metadataOnly:true};
 });
 const collisions=markCollisions(raw.map(x=>x.decision),[]);
 const rows=raw.map((x,i)=>({...x,decision:collisions[i]}));
 const b1=makeInitialBulletin(inventory,{observedAt:'2026-11-18T09:15:00Z',operatorScopeRef:'LOTE_SINTETICO_APENAS_TESTE'});
 const b2=nextBulletin(b1,inventory,rows.map(x=>({
   fileId:x.fileId,stage:x.decision.status==='PREVIEW'?'NAMING_PREVIEW':'REVIEW_REQUIRED',
   preview:x.decision,evidenceRefs: x.decision.evidenceIds||[]
 })),{observedAt:'2026-11-18T09:16:00Z'});
 const plan=prepareBatch({inventory,proposals:rows.map(x=>x.decision),
   selectedFileIds:rows.map(x=>x.fileId),
   registrationGate:'WAIT',topologyBulletinPersisted:false,
   destinationSnapshot:{driveId:DRIVE_ID,complete:true,folderIds:Object.values(DEST),files:[]}
 });
 const summary={
   synthetic:true,ocrUsed:false,drive1Mutations:0,
   documents:rows.length,documentFormats:{
    pdf:rows.filter(x=>x.sourceMime===PDF).length,
    docx:rows.filter(x=>x.sourceMime===DOCX).length
   },
   proposals:rows.filter(x=>x.decision.status==='PREVIEW').length,
   blocked:rows.filter(x=>x.decision.status!=='PREVIEW').length,
   reasons:rows.filter(x=>x.decision.reason).reduce((o,x)=>(o[x.decision.reason]=(o[x.decision.reason]||0)+1,o),{}),
   expectationMismatches:rows.filter(x=>x.expected!==
     (x.decision.status==='PREVIEW'?'PREVIEW':x.decision.reason))
     .map(x=>({caseId:x.fixtureId,expected:x.expected,got:x.decision.reason})),
   batchState:plan.state,batchBlockers:plan.blockers
 };
 return {inventory,rows,bulletins:[b1,b2],plan,summary};
}
module.exports={run,assess,readBytesAndMetadata,pagesFromManifest,classify,MAP,DEST};
