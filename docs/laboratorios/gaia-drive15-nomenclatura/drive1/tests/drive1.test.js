'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {inventoryFromReadOnlyPages}=require('../inventory');
const {proposeItem,markCollisions,prepareBatch}=require('../workflow');
const {makeInitialBulletin,nextBulletin,validatePrior,bulletinAsJson}=require('../bulletin');
const h=require('./helpers');
const inventory=()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:h.pages()});
const file=(inv=inventory())=>inv.items.find(x=>x.id===h.first);
const proposal=(item=file(),opts={})=>proposeItem({
 item,clientId:'027',clientProof:h.proof(),classification:h.classify(),
 nom:h.nom(),topology:h.topology(),...opts
});
test('inventário completo lê apenas o lote da Triagem e exclui 3 pastas técnicas',()=>{
 const inv=inventory();
 assert.deepEqual(inv.counts,{total:4,files:2,folders:2});
 assert.deepEqual(inv.items.map(x=>x.id),[h.root,h.first,h.sub,h.second]);
 assert.equal(inv.execution_attempted,false);
});
test('nenhuma raiz externa à Triagem é aceita como escopo',()=>{
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:['outsider01'],pages:h.pages()}),/OUTSIDE_TRIAGE_SCOPE/);
});
test('página truncada bloqueia, sem concluir inventário por 100 primeiros itens',()=>{
 const pg=h.pages();pg[1].complete=false;pg[1].nextPageToken='NEXT';
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:pg}),/INVENTORY_INCOMPLETE/);
});
test('subpasta não inspecionada bloqueia lote',()=>{
 const pg=h.pages().slice(0,2);
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:pg}),/INVENTORY_INCOMPLETE/);
});
test('item de outro Drive jamais entra no inventário',()=>{
 const pg=h.pages();pg[1].items[0].driveId='OTHER_DRIVE';
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:pg}),/CROSS_DRIVE_REFERENCE/);
});
test('pai informado divergente bloqueia',()=>{
 const pg=h.pages();pg[1].items[0].parents=['outsideParent'];
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:pg}),/PARENT_MISMATCH/);
});
test('página não autorizada de outra pasta bloqueia vazamento de escopo',()=>{
 const pg=h.pages();pg.push(h.page('other_folder_a',[]));
 assert.throws(()=>inventoryFromReadOnlyPages({batchId:'synthetic-lot-001',scopeIds:[h.root],pages:pg}),/PAGE_OUT_OF_SCOPE/);
});
test('proposta só nomeia com evidência, cliente, versão e destino confirmados',()=>{
 const p=proposal();
 assert.equal(p.status,'PREVIEW');
 assert.equal(p.proposedName,'027_DANFSe-03-08-2026.pdf');
 assert.equal(p.proposedParentId,h.dest);
 assert.equal(p.execution_attempted,false);
 assert.equal(p.execution_allowed,false);
});
test('cadastro ou manifesto não conciliado impede nomeação de lote',()=>{
 const p=h.proof();p.manifestVerified=false;
 assert.equal(proposal(file(),{clientProof:p}).reason,'CLIENT_INDEX_MANIFEST_WAIT');
});
test('metadados sem revisão/pai confirmado bloqueiam',()=>{
 const item={...file(),version:null};
 assert.equal(proposal(item).reason,'SOURCE_REVISION_OR_PARENT_UNVERIFIED');
});
test('documento de terceiro não é atribuído ao cliente',()=>{
 assert.equal(proposal(file(),{classification:{...h.classify(),thirdParty:true}}).reason,'THIRD_PARTY_CONFLICT');
});
test('classificação sem evidência verificada bloqueia',()=>{
 assert.equal(proposal(file(),{classification:{...h.classify(),evidence:[]}}).reason,'IDENTITY_OR_ENTITY_EVIDENCE_MISSING');
});
test('destino fora do cliente validado bloqueia',()=>{
 assert.equal(proposal(file(),{topology:{...h.topology(),destinationAncestors:['other_client_folder']}}).reason,'DESTINATION_TOPOLOGY_UNVERIFIED');
});
test('processo administrativo exige associação a processo identificado',()=>{
 assert.equal(proposal(file(),{classification:h.classify('PROCESSO'),topology:{...h.topology(),processVerified:false}}).reason,'PROCESS_ASSOCIATION_PENDING');
});
test('regra NOM 057 da biblioteca derivada ainda não está homologada no runtime',()=>{
 assert.equal(proposal(file(),{nom:{...h.nom(),ruleId:'NOM-057'}}).reason,'CATALOG_60_NOT_RUNTIME_HOMOLOGATED');
});
test('ressalvas NOM-033, NOM-058, NOM-060 não podem ser ignoradas',()=>{
 for(const ruleId of ['NOM-033','NOM-058','NOM-060'])
  assert.equal(proposal(file(),{nom:{...h.nom(),ruleId}}).reason,'NOM_SOURCE_REVIEW_REQUIRED');
});
test('faltam evidências para os campos NOM',()=>{
 assert.equal(proposal(file(),{nom:{...h.nom(),sourceRechecked:false}}).reason,'NOM_SOURCE_OR_FIELDS_UNVERIFIED');
});
test('colisão no mesmo destino bloqueia os itens, sem sufixo automático',()=>{
 const a=proposal(file());
 const b={...a,fileId:h.second,sourceParentId:h.sub};
 const res=markCollisions([a,b]);
 assert.equal(res[0].reason,'FILENAME_COLLISION');
 assert.equal(res[1].reason,'FILENAME_COLLISION');
});
test('colisão com nome já existente no destino bloqueia',()=>{
 const p=proposal();
 assert.equal(markCollisions([p],[{parentId:h.dest,name:p.proposedName,id:'another_id'}])[0].reason,'FILENAME_COLLISION');
});
function completeTwoProposals(inv=inventory()){
 const first=proposal(inv.items.find(x=>x.id===h.first));
 const second=proposal(inv.items.find(x=>x.id===h.second),{
   nom:{...h.nom(),ruleId:'NOM-002',provided:{DATA:'09-01-2026'}}
 });
 return [first,second];
}
const destinationSnapshot=()=>({
 driveId:h.DRIVE_ID,complete:true,folderIds:[h.dest],files:[]
});
test('lote bloqueado enquanto cadastro e boletim aguardam',()=>{
 const inv=inventory(),proposals=completeTwoProposals(inv);
 const b=prepareBatch({inventory:inv,proposals,selectedFileIds:[h.first,h.second],
  destinationSnapshot:destinationSnapshot()});
 assert.equal(b.state,'BLOCKED');
 assert.deepEqual(b.blockers,['CLIENT_REGISTRATION_WAIT','TOPOLOGY_BULLETIN_NOT_PERSISTED']);
 assert.equal(b.execution_attempted,false);
});
test('mesmo com liberações declaradas, motor apenas propõe pacote para aprovação',()=>{
 const inv=inventory(),proposals=completeTwoProposals(inv);
 const b=prepareBatch({inventory:inv,proposals,selectedFileIds:[h.first,h.second],
  registrationGate:'RELEASE_CONFIRMED',topologyBulletinPersisted:true,
  destinationSnapshot:destinationSnapshot()});
 assert.equal(b.state,'READY_FOR_SPECIFIC_OPERATOR_APPROVAL');
 assert.equal(b.execution_allowed,false);
 assert.equal(b.effect_status,'NOT_EXECUTED');
});
test('versão de arquivo divergente antes do lote bloqueia',()=>{
 const inv=inventory(),proposals=completeTwoProposals(inv);
 proposals[0]={...proposals[0],sourceVersion:'anterior'};
 assert.equal(prepareBatch({inventory:inv,proposals,selectedFileIds:[h.first,h.second]}).reason,'SOURCE_CHANGED');
});
test('destino não inventariado impede liberar pacote',()=>{
 const inv=inventory(),proposals=completeTwoProposals(inv);
 const b=prepareBatch({inventory:inv,proposals,selectedFileIds:[h.first,h.second],
  registrationGate:'RELEASE_CONFIRMED',topologyBulletinPersisted:true});
 assert.ok(b.blockers.includes('DESTINATION_INVENTORY_NOT_VERIFIED'));
});
test('lote parcial não pode seguir para movimentação',()=>{
 const inv=inventory(),proposals=completeTwoProposals(inv);
 assert.equal(prepareBatch({inventory:inv,proposals,selectedFileIds:[h.first]}).reason,'FULL_LOT_REQUIRED');
});
test('boletim inicial indexa arquivo, pastas e cadeia de pais pelo ID',()=>{
 const inv=inventory();
 const b=makeInitialBulletin(inv,{observedAt:'2026-11-18T09:00:00Z',operatorScopeRef:'synthetic-scope'});
 validatePrior(b);
 assert.equal(b.entries.length,4);
 assert.deepEqual(b.entries.find(x=>x.fileId===h.second).pathIds,[h.PATHS.triage,h.root,h.sub,h.second]);
 assert.equal(b.persistedToDrive1,false);
});
test('boletim subsequente é encadeado por SHA-256, sequencial e sem reescrita de anterior',()=>{
 const inv=inventory();
 const first=makeInitialBulletin(inv,{observedAt:'2026-11-18T09:00:00Z',operatorScopeRef:'synthetic-scope'});
 const second=nextBulletin(first,inv,[{fileId:h.first,stage:'NAMING_PREVIEW',preview:proposal(),evidenceRefs:['synthetic_evidence_ref']}],{observedAt:'2026-11-18T09:05:00Z'});
 validatePrior(second);
 assert.equal(first.sequence,1);assert.equal(second.sequence,2);
 assert.equal(second.previousSha256,first.sha256);
 assert.equal(second.entries.find(x=>x.fileId===h.first).proposedName,'027_DANFSe-03-08-2026.pdf');
 assert.equal(second.entries.find(x=>x.fileId===h.second).stage,'INVENTORIED');
 assert.equal(JSON.parse(bulletinAsJson(second)).persistedToDrive1,false);
});
test('boletim adulterado é rejeitado',()=>{
 const inv=inventory(),b=makeInitialBulletin(inv,{observedAt:'2026-11-18T09:00:00Z',operatorScopeRef:'synthetic-scope'});
 assert.throws(()=>validatePrior({...b,sequence:999}),/BULLETIN_TAMPERED/);
});
test('boletim não aceita alegação de movimento em modo somente leitura',()=>{
 const inv=inventory(),b=makeInitialBulletin(inv,{observedAt:'2026-11-18T09:00:00Z',operatorScopeRef:'synthetic-scope'});
 assert.throws(()=>nextBulletin(b,inv,[{fileId:h.first,stage:'NAMING_PREVIEW',execution_attempted:true}],{observedAt:'2026-11-18T09:05:00Z'}),/PREVIEW_CANNOT_CLAIM_EXECUTION/);
});
test('boletim rejeita versão divergente ou escopo mudado no inventário',()=>{
 const inv=inventory(),b=makeInitialBulletin(inv,{observedAt:'2026-11-18T09:00:00Z',operatorScopeRef:'synthetic-scope'});
 assert.throws(()=>nextBulletin(b,{...inv,items:[...inv.items].reverse()},[],{observedAt:'2026-11-18T09:05:00Z'}),/SOURCE_INVENTORY_DRIFT/);
});

test('colisão de mesmo nome ignora diferença de caixa Unicode',()=>{
 const p=proposal();
 const otherName=p.proposedName.toLocaleLowerCase('pt-BR');
 assert.equal(markCollisions([p],[{parentId:h.dest,name:otherName,id:'other_copy'}])[0].reason,'FILENAME_COLLISION');
});
test('não há funções de escrita Google nos módulos Drive 1',()=>{
 const fs=require('node:fs'),path=require('node:path');
 for(const f of ['config.js','inventory.js','workflow.js','bulletin.js','catalog60.js']){
  const s=fs.readFileSync(path.join(__dirname,'..',f),'utf8');
  assert.doesNotMatch(s,/\b(?:DriveApp|UrlFetchApp|googleapis|axios)\b/);
  assert.doesNotMatch(s,/\.files\.update\s*\(/);
 }
});
