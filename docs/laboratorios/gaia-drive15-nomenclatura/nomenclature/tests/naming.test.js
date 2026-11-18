'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {suggestDocumentName,rules}=require('../index.js');
const original=require('../core/NomenclatureEngine.js');
const suggest=x=>suggestDocumentName(x);
test('56 regras vigentes carregadas',()=>{assert.equal(rules.length,56);assert.equal(rules.filter(r=>r.status==='VIGENTE').length,56)});
test('NOM-001: NNN e data',()=>{const o=suggest({rule_id:'NOM-001',clientNNN:'27',provided:{DATA:'03-08-2026'}});assert.equal(o.finalFilename,'027_DANFSe-03-08-2026.pdf');assert.equal(o.write_performed,false)});
test('NOM-002: CNPJ',()=>{assert.equal(suggest({rule_id:'NOM-002',clientNNN:'009',provided:{DATA:'09-01-2026'}}).finalFilename,'009_CNPJ_09-01-2026.pdf')});
test('NOM-018: extração da unidade IPTU',()=>{assert.equal(suggest({rule_id:'NOM-018',clientNNN:'27',rawFields:{inscricao_imobiliaria_completa:'24.56.060.0600.006.157'}}).finalFilename,'027_CERTIDÃO_DE_IPTU_006.pdf')});
test('NOM-016: consolidação',()=>{assert.equal(suggest({rule_id:'NOM-016',clientNNN:'27',provided:{DATA:'01-05-2026',ORDINAL:'2',consolidado:true}}).finalFilename,'027_2ª_ALTERAÇÃO_JUCESC_CONSOLIDADO_01-05-2026.pdf')});
test('campos faltantes ficam pendentes',()=>{const o=suggest({rule_id:'NOM-001',clientNNN:'27',provided:{}});assert.equal(o.reason,'VARIAVEIS_FALTANTES');assert.equal(o.write_performed,false)});
test('data com formato incorreto fica pendente',()=>{assert.equal(suggest({rule_id:'NOM-001',clientNNN:'27',provided:{DATA:'2026-08-03'}}).status,'PENDENTE_NOMENCLATURA')});
test('regressão: data impossível é aceita pelo legado, bloqueada no isolado',()=>{
 const i={rule_id:'NOM-001',clientNNN:'27',provided:{DATA:'31-02-2026'}};
 assert.equal(original.composeFinalFilename(rules[0],i.provided,i.clientNNN).status,'OK');
 assert.equal(suggest(i).reason,'DATA_CALENDARIO_INVALIDA');
});
test('regressão: nome com separador de diretório é bloqueado',()=>{
 const i={rule_id:'NOM-026',clientNNN:'27',provided:{DATA:'03-08-2026',TEOR:'../arquivo'}};
 assert.equal(suggest(i).reason,'NOME_INSEGURO');
});
test('regra inexistente não gera nome',()=>{assert.equal(suggest({rule_id:'NOM-999',clientNNN:'27'}).reason,'REGRA_INEXISTENTE')});
test('sem evidências de reconhecimento suficientes não escolhe regra',()=>{
 const o=suggest({signals:['DANFSe','NFS-e'],clientNNN:'27',provided:{DATA:'03-08-2026'}});
 assert.equal(o.reason,'TIPO_NAO_RECONHECIDO');
 assert.ok(o.suggestions.some(x=>x.rule_id==='NOM-001'));
});
test('entrada inválida bloqueada',()=>{assert.equal(suggest(null).reason,'ENTRADA_INVALIDA')});
test('núcleo isolado não usa serviços de escrita/leitura do Google',()=>{
 for(const f of ['Text.js','NomenclatureEngine.js','NomenclatureRefinements.js','GaiaOffice.js']){
  const s=fs.readFileSync(path.join(__dirname,'../core',f),'utf8');
  assert.doesNotMatch(s,/\b(?:DriveApp|Drive\.Files|UrlFetchApp|PropertiesService|ScriptApp|SpreadsheetApp)\b/);
 }
});

