'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {run,readBytesAndMetadata,classify,pagesFromManifest}=require('../metadata_engine');
const {inventoryFromReadOnlyPages}=require('../../drive1/inventory');
const {DRIVE_ID}=require('../../drive1/config');
const base=process.env.GAIA_SYNTHETIC_FIXTURES||path.resolve(__dirname,'../generated');
const manifest=()=>JSON.parse(fs.readFileSync(path.join(base,'manifest.json'),'utf8'));
const lookup=(c,r)=>r.rows.find(x=>x.fixtureId===c);
test('17 documentos físicos, 15 PDF e 2 DOCX com bytes e hashes verificados',()=>{
 const m=manifest();
 assert.equal(m.cases.length,17);
 assert.equal(m.cases.filter(x=>x.driveRecord.mimeType==='application/pdf').length,15);
 assert.equal(m.cases.filter(x=>x.hasMetadata).length,16);
 for(const c of m.cases){
   const f=path.join(base,c.driveRecord.relativePath);
   assert.ok(fs.statSync(f).size>200);
   const got=readBytesAndMetadata(base,c.driveRecord);
   if(c.hasMetadata)assert.equal(got.error,undefined,c.driveRecord.caseId);
   else assert.equal(got.error,'METADATA_MISSING');
 }
});
test('pipeline gera 7 previews e bloqueia 10 casos adversariais sem OCR',()=>{
 const r=run(base);
 assert.equal(r.summary.documents,17);
 assert.equal(r.summary.proposals,7);
 assert.equal(r.summary.blocked,10);
 assert.deepEqual(r.summary.expectationMismatches,[]);
 assert.equal(r.summary.ocrUsed,false);
 assert.equal(r.summary.drive1Mutations,0);
 assert.equal(r.plan.execution_attempted,false);
});
test('identificação de DANFSe pela classe de metadados e data da evidência',()=>{
 const r=run(base);
 assert.equal(lookup('S01',r).kind,'DANFSE');
 assert.equal(lookup('S01',r).decision.ruleId,'NOM-001');
 assert.equal(lookup('S01',r).decision.proposedName,'027_DANFSe-03-08-2026.pdf');
});
test('IPTU extrai unidade 006 da inscrição, sem perder zeros',()=>{
 const r=run(base);
 assert.equal(lookup('S03',r).decision.proposedName,'027_CERTIDÃO_DE_IPTU_006.pdf');
});
test('reconhecimento distingue requerimento DOCX não assinado e PDF assinado',()=>{
 const r=run(base),a=lookup('S07',r),b=lookup('S08',r);
 assert.equal(a.decision.ruleId,'NOM-042');
 assert.equal(b.decision.ruleId,'NOM-041');
 assert.match(a.decision.proposedName,/\.docx$/);
 assert.match(b.decision.proposedName,/_assinado\.pdf$/);
});
test('data da Receita vem da emissão do comprovante, nunca de abertura ou modifiedTime',()=>{
 const r=run(base);
 const x=lookup('S02',r);
 assert.equal(x.decision.proposedName,'027_CNPJ_09-01-2026.pdf');
 assert.doesNotMatch(x.decision.proposedName,/22-04-2021|05-08-2024|18-11-2026/);
});
test('colisão preserva IDs independentes e bloqueia ambos',()=>{
 const r=run(base);
 assert.equal(lookup('S02',r).decision.reason,'FILENAME_COLLISION');
 assert.equal(lookup('S11',r).decision.reason,'FILENAME_COLLISION');
 assert.notEqual(lookup('S02',r).fileId,lookup('S11',r).fileId);
});
test('documento de terceiro, data inválida, CNH não homologada e cliente errado são bloqueados',()=>{
 const r=run(base);
 for(const [caseId,reason] of [
 ['S09','NOM_SOURCE_REVIEW_REQUIRED'],
 ['S12','THIRD_PARTY_CONFLICT'],
 ['S13','DATA_CALENDARIO_INVALIDA'],
 ['S17','CLIENT_MISMATCH']
 ])assert.equal(lookup(caseId,r).decision.reason,reason);
});
test('documento sem metadata e formato DOCX disfarçado de DANFSE não são nomeados',()=>{
 const r=run(base);
 assert.equal(lookup('S16',r).decision.reason,'METADATA_MISSING');
 assert.equal(lookup('S15',r).decision.reason,'MIME_TYPE_CONFLICT');
});
test('alterar sha no manifesto é detectado antes do reconhecimento',()=>{
 const m=manifest();
 m.cases[0].driveRecord.sha256='0'.repeat(64);
 const r=run(base,{overrideManifest:m});
 assert.equal(lookup('S01',r).decision.reason,'DOCUMENT_HASH_MISMATCH');
});
test('tipo/dominio divergentes são identificados como inconsistência de metadados',()=>{
 const m=manifest(),record=m.cases[0].driveRecord;
 const meta=readBytesAndMetadata(base,record).meta;
 assert.equal(classify({...meta,domain:'PESSOA'},record).error,'ENTITY_DOMAIN_MISMATCH');
});
test('escopo de outro Drive bloqueado em inventário recursivo',()=>{
 const m=manifest(),pg=pagesFromManifest(m);
 pg[1].items[1].driveId='OTHER_DRIVE';
 assert.throws(()=>inventoryFromReadOnlyPages({
  batchId:'synthetic-lote-027',scopeIds:[m.sourceRoot],pages:pg
 }),/CROSS_DRIVE_REFERENCE/);
});
test('boletim 001/002 registra 17 arquivos e 2 pastas, com continuidade por SHA',()=>{
 const r=run(base),b1=r.bulletins[0],b2=r.bulletins[1];
 assert.equal(r.inventory.counts.files,17);
 assert.equal(r.inventory.counts.folders,2);
 assert.equal(b1.entries.length,19);
 assert.equal(b2.previousSha256,b1.sha256);
 assert.equal(b2.sequence,2);
 assert.equal(b2.persistedToDrive1,false);
 assert.ok(b2.entries.some(x=>x.stage==='NAMING_PREVIEW'));
 assert.ok(b2.entries.some(x=>x.stage==='REVIEW_REQUIRED'));
});
test('lote de casos bons pode ser todo identificado, mas aguarda cadastro/boletim',()=>{
 const m=manifest();m.cases=m.cases.filter(x=>['S01','S03','S04','S05','S06','S07','S08'].includes(x.driveRecord.caseId));
 const r=run(base,{overrideManifest:m});
 assert.equal(r.summary.proposals,7);
 assert.equal(r.summary.blocked,0);
 assert.equal(r.plan.state,'BLOCKED');
 assert.deepEqual(r.plan.blockers,['CLIENT_REGISTRATION_WAIT','TOPOLOGY_BULLETIN_NOT_PERSISTED']);
});
test('nenhum módulo de testes tenta renomear ou escrever no Drive',()=>{
 const r=run(base);
 assert.equal(r.plan.execution_allowed,false);
 assert.equal(r.plan.effect_status,'NOT_EXECUTED');
 assert.equal(r.plan.readback_status,'NOT_APPLICABLE');
 assert.equal(r.summary.drive1Mutations,0);
 assert.equal(r.inventory.driveId,DRIVE_ID);
});
