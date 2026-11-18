'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {validateCatalog,getCatalog,gateRule}=require('../catalog60');
test('índice federado tem 60 IDs distintos, 56 bases + 4 novos',()=>{
 const c=getCatalog();
 assert.equal(validateCatalog(c),true);
 assert.equal(c.rules.length,60);
 assert.equal(c.counts.base,56);
 assert.equal(c.counts.new,4);
 assert.equal(c.status,'DERIVED_NONCANONICAL_NOT_RELEASED');
});
test('quatro regras novas ficam somente em referência até homologação de runtime',()=>{
 const c=getCatalog();
 for(const id of ['NOM-057','NOM-058','NOM-059','NOM-060']){
  const g=gateRule(id,c);
  assert.equal(g.status,'REFERENCE_ONLY');
  assert.equal(g.runtimeSupported,false);
  assert.equal(g.executed,false);
 }
});
test('ressalvas de overlays e fonte são preservadas',()=>{
 const c=getCatalog();
 for(const id of ['NOM-012','NOM-033','NOM-058','NOM-060']){
  assert.equal(gateRule(id,c).reviewRequired,true);
 }
});
test('catálogo com ID e status de fonte errados é rejeitado',()=>{
 const c=getCatalog();
 assert.throws(()=>validateCatalog({...c,target_drive_id:'OUTRO_DRIVE'}),/CATALOG_SOURCE_OR_STATUS_MISMATCH/);
 assert.throws(()=>validateCatalog({...c,status:'RELEASED'}),/CATALOG_SOURCE_OR_STATUS_MISMATCH/);
});
test('catálogo adulterado por regra duplicada é rejeitado',()=>{
 const c=getCatalog(),copy={...c,rules:c.rules.map(x=>({...x}))};
 copy.rules[59].rule_id=copy.rules[58].rule_id;
 assert.throws(()=>validateCatalog(copy),/DUPLICATE_RULE_ID/);
});
