'use strict';
const {DRIVE_ID,PATHS}=require('./config');
const {suggestDocumentName,rules}=require('../nomenclature');
const VALID_DOMAINS=new Set(['IMOVEL','EMPRESA','PESSOA','PROCESSO','CONTRATO','OUTROS']);
const AMBIGUOUS_NOM=new Set(['NOM-012','NOM-033','NOM-058','NOM-060']);
const NOM_RULES=new Set(rules.map(x=>x.rule_id));
const blocked=(reason,extra={})=>({status:'BLOCKED',reason,...extra,execution_attempted:false});

function validateClientProof(proof,clientId){
  return !!proof && proof.clientId===clientId && /^\d{3}$/.test(clientId) &&
    proof.driveId===DRIVE_ID && typeof proof.clientFolderId==='string' &&
    proof.indexVerified===true && proof.manifestVerified===true &&
    proof.indexFileId===PATHS.clientIndex &&
    typeof proof.manifestFileId==='string' && proof.manifestVersion!=null;
}
function validEvidence(evidence){
  return Array.isArray(evidence)&&evidence.length>0&&evidence.every(e=>
    e && typeof e.sourceId==='string' && e.sourceId.length>=8 &&
    typeof e.locator==='string' && e.locator.trim().length>0 &&
    e.verified===true);
}
/** Retorna DECISÃO DE PRÉVIA; não altera arquivos no Google. */
function proposeItem({item,clientId,clientProof,classification,nom,topology}={}){
  if(!item||item.folder)return blocked('DOCUMENT_FILE_REQUIRED');
  const base={
    fileId:item.id,sourceParentId:item.parentId,sourceName:item.name,
    sourceVersion:item.version,sourceMimeType:item.mimeType,clientId:clientId??null,
    sourceDriveId:DRIVE_ID,proposedParentId:null,proposedName:null,
    execution_attempted:false,verified_effect:false
  };
  function no(reason,extra={}){return {...base,...blocked(reason,extra)};}
  if(item.driveId!==DRIVE_ID)return no('CROSS_DRIVE');
  if(!item.parentVerified||item.version==null)return no('SOURCE_REVISION_OR_PARENT_UNVERIFIED');
  if(!validateClientProof(clientProof,clientId))return no('CLIENT_INDEX_MANIFEST_WAIT');
  if(!classification||!VALID_DOMAINS.has(classification.domain) ||
     !validEvidence(classification.evidence) || classification.belongingVerified!==true)
    return no('IDENTITY_OR_ENTITY_EVIDENCE_MISSING');
  if(classification.thirdParty===true)return no('THIRD_PARTY_CONFLICT');
  if(!topology || topology.destinationVerified!==true ||
     topology.destinationDriveId!==DRIVE_ID ||
     !Array.isArray(topology.destinationAncestors) ||
     !topology.destinationAncestors.includes(clientProof.clientFolderId) ||
     typeof topology.destinationParentId!=='string' ||
     topology.destinationParentId===PATHS.triage)
    return no('DESTINATION_TOPOLOGY_UNVERIFIED');
  // O domínio e o caminho de destino são distintos da regra NOM.
  if(classification.domain==='PROCESSO' && topology.processVerified!==true)
    return no('PROCESS_ASSOCIATION_PENDING');
  if(!nom || typeof nom.ruleId!=='string')return no('NOM_RULE_PENDING');
  if(AMBIGUOUS_NOM.has(nom.ruleId))return no('NOM_SOURCE_REVIEW_REQUIRED',{ruleId:nom.ruleId});
  if(!NOM_RULES.has(nom.ruleId))
    return no('CATALOG_60_NOT_RUNTIME_HOMOLOGATED',{ruleId:nom.ruleId});
  if(!validEvidence(nom.evidence) || nom.sourceRechecked!==true)
    return no('NOM_SOURCE_OR_FIELDS_UNVERIFIED',{ruleId:nom.ruleId});
  // Nunca inferir DATA a partir de modifiedTime.
  const suggestion=suggestDocumentName({
    rule_id:nom.ruleId,
    clientNNN:clientId,
    provided:nom.provided||{},
    rawFields:nom.rawFields||{},
    signals:nom.signals||[]
  });
  if(suggestion.status!=='OK')return no(suggestion.reason||'NOMENCLATURE_PENDING',{
    ruleId:nom.ruleId,missing:suggestion.missing||null
  });
  const proposedName=suggestion.finalFilename;
  if(proposedName===item.name && topology.destinationParentId===item.parentId)
    return no('NO_EFFECT_PROPOSED');
  return Object.freeze({
    ...base,status:'PREVIEW',reason:null,
    ruleId:nom.ruleId,proposedName,proposedParentId:topology.destinationParentId,
    domain:classification.domain,
    evidenceIds:[...new Set([...classification.evidence,...nom.evidence].map(e=>e.sourceId))],
    registrationGate:'WAIT_FOR_CLIENT_REGISTRATION_RELEASE',
    readBackRequired:true,approvalRef:null,
    execution_allowed:false
  });
}
const normalKey=(parent,name)=>parent+'\0'+String(name).normalize('NFKC').trim().toLocaleLowerCase('pt-BR');
function markCollisions(previews,existingDestinationFiles=[]){
  const existing=new Set(existingDestinationFiles.map(x=>normalKey(x.parentId,x.name)));
  const freq=new Map();
  for(const p of previews)if(p.status==='PREVIEW'){
    const key=normalKey(p.proposedParentId,p.proposedName);
    freq.set(key,(freq.get(key)||0)+1);
  }
  return previews.map(p=>{
    if(p.status!=='PREVIEW')return p;
    const k=normalKey(p.proposedParentId,p.proposedName);
    if(freq.get(k)>1 || existing.has(k)){
      return {...p,status:'BLOCKED',reason:'FILENAME_COLLISION',execution_allowed:false};
    }
    return p;
  });
}
/** Monta lista de ações pretendidas; permanece bloqueado para execução real. */
function prepareBatch({inventory,proposals,selectedFileIds,registrationGate='WAIT',topologyBulletinPersisted=false,destinationSnapshot=null}={}){
  if(!inventory||inventory.driveId!==DRIVE_ID||inventory.complete!==true)
    return blocked('INVENTORY_INCOMPLETE');
  if(!Array.isArray(proposals)||!Array.isArray(selectedFileIds)||!selectedFileIds.length)
    return blocked('BATCH_SCOPE_MISSING');
  const files=new Map(inventory.items.filter(x=>!x.folder).map(x=>[x.id,x]));
  const byId=new Map(proposals.map(x=>[x.fileId,x]));
  if(files.size!==selectedFileIds.length) return blocked('FULL_LOT_REQUIRED');
  if(byId.size!==proposals.length)return blocked('DUPLICATE_FILE_PROPOSAL');
  if(byId.size!==files.size)return blocked('MISSING_OR_EXTRA_PROPOSALS');
  const chosen=[],seen=new Set();
  for(const id of selectedFileIds){
    if(seen.has(id)||!files.has(id)||!byId.has(id))return blocked('FILE_NOT_IN_INVENTORY_OR_DUPLICATE');
    seen.add(id);
    const item=files.get(id),p=byId.get(id);
    if(p.sourceVersion!==item.version||p.sourceParentId!==item.parentId)
      return blocked('SOURCE_CHANGED',{fileId:id});
    chosen.push(p);
  }
  const blockers=[];
  const parents=[...new Set(chosen.filter(x=>x.status==='PREVIEW').map(x=>x.proposedParentId))];
  const destOk=destinationSnapshot && destinationSnapshot.driveId===DRIVE_ID &&
    destinationSnapshot.complete===true && Array.isArray(destinationSnapshot.folderIds) &&
    parents.every(parent=>destinationSnapshot.folderIds.includes(parent)) &&
    Array.isArray(destinationSnapshot.files);
  if(!destOk)blockers.push('DESTINATION_INVENTORY_NOT_VERIFIED');
  const checked=markCollisions(chosen,destOk?destinationSnapshot.files:[]);
  const pending=checked.filter(x=>x.status!=='PREVIEW');
  if(checked.some(x=>x.reason==='FILENAME_COLLISION'))blockers.push('FILENAME_COLLISION');
  if(pending.length)blockers.push('PREVIEW_INCOMPLETE');
  if(registrationGate!=='RELEASE_CONFIRMED')blockers.push('CLIENT_REGISTRATION_WAIT');
  if(topologyBulletinPersisted!==true)blockers.push('TOPOLOGY_BULLETIN_NOT_PERSISTED');
  return Object.freeze({
    schema:'gaia.drive1.batch-plan.v1',batchId:inventory.batchId,driveId:DRIVE_ID,
    state:blockers.length?'BLOCKED':'READY_FOR_SPECIFIC_OPERATOR_APPROVAL',
    blockers,fileCount:chosen.length,
    items:checked.map(x=>({
      fileId:x.fileId,expectedVersion:x.sourceVersion,from:x.sourceParentId,
      to:x.proposedParentId,oldName:x.sourceName,newName:x.proposedName,
      ruleId:x.ruleId,status:x.status,reason:x.reason||null
    })),
    approvalRef:null,execution_allowed:false,execution_attempted:false,
    effect_status:'NOT_EXECUTED',readback_status:'NOT_APPLICABLE'
  });
}
module.exports={proposeItem,prepareBatch,markCollisions,validateClientProof,validEvidence};
