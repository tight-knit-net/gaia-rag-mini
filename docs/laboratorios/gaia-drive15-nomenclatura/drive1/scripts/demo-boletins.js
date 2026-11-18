'use strict';
/**
 * Demonstração OFFLINE sem Drive e sem credenciais.
 * Saída JSON exclusivamente sintética: boletins 001/002 + lote bloqueado.
 */
const {inventoryFromReadOnlyPages}=require('../inventory');
const {makeInitialBulletin,nextBulletin}=require('../bulletin');
const {proposeItem,prepareBatch,markCollisions}=require('../workflow');
const h=require('../tests/helpers');
const observedAt='2026-11-18T09:00:00Z';
const inv=inventoryFromReadOnlyPages({
 batchId:'demo-sintetico-001',scopeIds:[h.root],pages:h.pages()
});
const fileA=inv.items.find(i=>i.id===h.first);
const fileB=inv.items.find(i=>i.id===h.second);
const pA=proposeItem({
 item:fileA,clientId:'027',clientProof:h.proof(),
 classification:h.classify(),nom:h.nom(),topology:h.topology()
});
const pB=proposeItem({
 item:fileB,clientId:'027',clientProof:h.proof(),
 classification:h.classify(),nom:{...h.nom(),ruleId:'NOM-002',provided:{DATA:'09-01-2026'}},
 topology:h.topology()
});
const previews=markCollisions([pA,pB],[]);
const boletim1=makeInitialBulletin(inv,{observedAt,operatorScopeRef:'simulacao-local-sem-autorizacao'});
const boletim2=nextBulletin(boletim1,inv,[
 {fileId:fileA.id,stage:'NAMING_PREVIEW',preview:previews[0],evidenceRefs:['synthetic_proof_001']},
 {fileId:fileB.id,stage:'NAMING_PREVIEW',preview:previews[1],evidenceRefs:['synthetic_proof_002']}
],{observedAt:'2026-11-18T09:05:00Z'});
const plan=prepareBatch({
 inventory:inv,proposals:previews,selectedFileIds:[fileA.id,fileB.id],
 destinationSnapshot:{driveId:h.DRIVE_ID,folderIds:[h.dest],files:[],complete:true},
 registrationGate:'WAIT',topologyBulletinPersisted:false
});
process.stdout.write(JSON.stringify({
 synthetic:true,drive1_mutations:0,
 boletim1,boletim2,plan
},null,2)+'\n');
