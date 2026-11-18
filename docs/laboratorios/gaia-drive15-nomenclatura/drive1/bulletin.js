'use strict';
const crypto=require('node:crypto');
const {DRIVE_ID,PATHS}=require('./config');
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const STATES=new Set([
 'INVENTORIED','IDENTITY_PENDING','CONTENT_PARTIAL','OCR_PENDING',
 'CLASSIFIED','NOMENCLATURE_PENDING','NAMING_PREVIEW','REVIEW_REQUIRED',
 'REGISTRATION_WAIT','BATCH_PLAN_READY','BLOCKED','THIRD_PARTY_REFERENCE'
]);
function digestBulletin(b){const {sha256,...rest}=b;return sha(rest);}
function validatePrior(b){
  if(!b||b.schema!=='gaia.drive1.topology-bulletin.v1'||b.driveId!==DRIVE_ID)
    throw Error('INVALID_PRIOR_BULLETIN');
  if(digestBulletin(b)!==b.sha256)throw Error('BULLETIN_TAMPERED');
}
function makeInitialBulletin(inventory,{observedAt,operatorScopeRef}={}){
  if(!inventory||inventory.complete!==true||inventory.driveId!==DRIVE_ID)
    throw Error('COMPLETE_DRIVE1_INVENTORY_REQUIRED');
  if(!operatorScopeRef||!observedAt)throw Error('SCOPE_AND_TIMESTAMP_REQUIRED');
  const ids=new Set(inventory.items.map(x=>x.id));
  const entries=inventory.items.map((x,index)=>{
    const pathIds=[x.id];let cur=x,seen=new Set([x.id]);
    while(cur.parentId!==PATHS.triage){
      if(!ids.has(cur.parentId))throw Error('ORPHAN_TOPOLOGY');
      if(seen.has(cur.parentId))throw Error('CYCLIC_TOPOLOGY');
      seen.add(cur.parentId);pathIds.unshift(cur.parentId);
      cur=inventory.items.find(z=>z.id===cur.parentId);
    }
    pathIds.unshift(PATHS.triage);
    return {
      ordinal:index+1,fileId:x.id,kind:x.folder?'FOLDER':'FILE',
      currentName:x.name,sourceParentId:x.parentId,pathIds,
      sourceVersion:x.version,sourceMimeType:x.mimeType,
      metadataParentVerified:x.parentVerified,
      stage:'INVENTORIED',proposedName:null,proposedParentId:null,
      ruleId:null,evidenceRefs:[],blockers:[],
      mutationStatus:'NOT_EXECUTED'
    };
  });
  const result={
    schema:'gaia.drive1.topology-bulletin.v1',batchId:inventory.batchId,driveId:DRIVE_ID,
    sourceFolderId:PATHS.triage,topologyFolderId:PATHS.topology,
    permanentTraceFolderId:PATHS.tracePermanent,
    sequence:1,previousSha256:null,observedAt,operatorScopeRef,
    inventoryDigest:sha(inventory.items),counts:inventory.counts,
    state:'INVENTORY_COMPLETE',entries,
    updates:[],persistedToDrive1:false,
    execution_attempted:false,verified_effect:false
  };
  return Object.freeze({...result,sha256:digestBulletin(result)});
}
/** Novo boletim, numerado e correlacionado, nunca sobrescrevendo o anterior. */
function nextBulletin(prior,inventory,observations,{observedAt}={}){
  validatePrior(prior);
  if(!observedAt||!Array.isArray(observations))throw Error('INVALID_UPDATE');
  if(inventory.batchId!==prior.batchId||inventory.driveId!==DRIVE_ID ||
     inventory.complete!==true||sha(inventory.items)!==prior.inventoryDigest)
    throw Error('SOURCE_INVENTORY_DRIFT');
  const patches=new Map();
  for(const o of observations){
    if(!o||!o.fileId||patches.has(o.fileId)||!STATES.has(o.stage))
      throw Error('INVALID_OR_DUPLICATE_OBSERVATION');
    if('execution_attempted' in o || 'verified_effect' in o || 'parents_after' in o)
      throw Error('PREVIEW_CANNOT_CLAIM_EXECUTION');
    patches.set(o.fileId,o);
  }
  const found=new Set();
  const entries=prior.entries.map(e=>{
    const o=patches.get(e.fileId);if(!o)return {...e};
    found.add(e.fileId);
    const m=inventory.items.find(x=>x.id===e.fileId);
    if(!m||m.version!==e.sourceVersion || m.parentId!==e.sourceParentId)
      throw Error('SOURCE_REVISION_CHANGED');
    const ev=Array.isArray(o.evidenceRefs)?o.evidenceRefs:[];
    if(ev.some(z=>typeof z!=='string'||!/^[A-Za-z0-9_-]{8,150}$/.test(z)))
      throw Error('EVIDENCE_IDS_INVALID');
    const p=o.preview||null;
    if(p && (p.fileId!==e.fileId || !['PREVIEW','BLOCKED'].includes(p.status)))
      throw Error('PREVIEW_MISMATCH');
    return {
      ...e,stage:o.stage,
      proposedName:p?.status==='PREVIEW'?p.proposedName:null,
      proposedParentId:p?.status==='PREVIEW'?p.proposedParentId:null,
      ruleId:p?.ruleId||null,
      evidenceRefs:[...new Set([...e.evidenceRefs,...ev])],
      blockers:Array.isArray(o.blockers)?o.blockers:[...e.blockers],
      mutationStatus:'NOT_EXECUTED'
    };
  });
  if(found.size!==patches.size)throw Error('OBSERVATION_OUT_OF_SCOPE');
  const result={
    ...prior,sequence:prior.sequence+1,previousSha256:prior.sha256,
    observedAt,state:'TOPOLOGY_IN_PROGRESS',entries,
    updates:[...patches].map(([fileId,o])=>({fileId,stage:o.stage})),
    persistedToDrive1:false,execution_attempted:false,verified_effect:false
  };
  delete result.sha256;
  return Object.freeze({...result,sha256:digestBulletin(result)});
}
function bulletinAsJson(b){
  validatePrior(b);
  return JSON.stringify(b,null,2)+'\n';
}
module.exports={makeInitialBulletin,nextBulletin,bulletinAsJson,validatePrior};
