#!/usr/bin/env node
'use strict';
/* Executa o fluxo de metadados contra um lote fictício e renomeia SOMENTE cópias locais. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {run,DEST}=require('./metadata_engine');
function sha(b){return crypto.createHash('sha256').update(b).digest('hex')}
function save(dest,value){fs.writeFileSync(dest,JSON.stringify(value,null,2)+'\n','utf8')}
function main(){
 const base=path.resolve(process.argv[2]||'synthetic/generated');
 const target=path.resolve(process.argv[3]||'synthetic/resultado-local');
 if(target===base||target.startsWith(base+path.sep))
   throw Error('OUTPUT_MUST_BE_OUTSIDE_SOURCE_FIXTURES');
 if(fs.existsSync(target))throw Error('OUTPUT_ALREADY_EXISTS_TO_PROTECT_PREVIOUS_EVIDENCE');
 const {inventory,rows,bulletins,plan,summary}=run(base);
 if(summary.expectationMismatches.length)throw Error('UNEXPECTED_CASE_CLASSIFICATION');
 if(summary.documents!==17||summary.proposals!==7||summary.blocked!==10)
   throw Error('UNEXPECTED_FIXTURE_COUNTS');
 fs.mkdirSync(target,{recursive:true});
 save(path.join(target,'catalogo_documentos.json'),rows);
 save(path.join(target,'inventario_topologico.json'),inventory);
 save(path.join(target,'boletim_001.json'),bulletins[0]);
 save(path.join(target,'boletim_002.json'),bulletins[1]);
 save(path.join(target,'plano_lote_BLOQUEADO.json'),plan);
 const m=JSON.parse(fs.readFileSync(path.join(base,'manifest.json'),'utf8'));
 const byId=new Map(m.cases.map(x=>[x.driveRecord.id,x.driveRecord]));
 const receipts=[];
 for(const x of rows){
  if(x.decision.status!=='PREVIEW')continue;
  const rec=byId.get(x.fileId),original=path.join(base,rec.relativePath);
  const folder=Object.entries(DEST).find(([,id])=>id===x.decision.proposedParentId)?.[0];
  if(!folder)throw Error('DESTINATION_NOT_IN_SYNTHETIC_SCOPE');
  const proposed=x.decision.proposedName;
  if(!proposed||path.basename(proposed)!==proposed||/[\\/]/.test(proposed)||proposed.includes('..'))
   throw Error('UNSAFE_PROPOSED_NAME');
  const destDir=path.join(target,'arquivos_renomeados_LOCAL',folder);
  const staging=path.join(target,'staging');
  fs.mkdirSync(destDir,{recursive:true});fs.mkdirSync(staging,{recursive:true});
  const temp=path.join(staging,x.fileId+path.extname(rec.name));
  const dest=path.join(destDir,proposed);
  if(fs.existsSync(dest))throw Error('DESTINATION_COLLISION_AT_COPY_TIME');
  // O arquivo de origem na fixture permanece intacto; o rename é na cópia de staging.
  fs.copyFileSync(original,temp,fs.constants.COPYFILE_EXCL);
  if(sha(fs.readFileSync(temp))!==rec.sha256)throw Error('STAGING_SHA_MISMATCH');
  fs.renameSync(temp,dest);
  const outputDigest=sha(fs.readFileSync(dest));
  if(outputDigest!==rec.sha256||sha(fs.readFileSync(original))!==rec.sha256)
   throw Error('RENAMED_COPY_INTEGRITY_FAILURE');
  receipts.push({
   fixtureId:x.fixtureId,fileId:x.fileId,original:rec.name,proposedName:proposed,
   localDestination:path.relative(target,dest),sha256:outputDigest,
   result:'LOCAL_SANDBOX_COPY_RENAMED_AND_HASH_VERIFIED',
   drive1Mutation:false,originalPreserved:true
  });
 }
 if(receipts.length!==7)throw Error('RENAMED_COPIES_COUNT_MISMATCH');
 const evidence={...summary,renameCopiesVerified:receipts.length,
  rawSourceUntouched:true,drive1FilesChanged:0,
  batchEffect:'NOT_EXECUTED', localRenameOnly:true,
  originalPdfAndDocxRemainInSource:true,
  topologyBulletinsProduced:bulletins.length,
  bulletinHashChainVerified:bulletins[1].previousSha256===bulletins[0].sha256};
 save(path.join(target,'recibos_renomeacao_LOCAL.json'),receipts);
 save(path.join(target,'resumo_validado.json'),evidence);
 const lines=[
 '# Homologação sintética – GAIA Drive 1',
 '',
 'Execução apenas em cópias de documentos fictícios PDF/DOCX com metadados estruturados.',
 'OCR: NÃO USADO. DRIVE 1: SOMENTE LEITURA, 0 alterações.',
 '',
 'Documentos: '+summary.documents+'. Propostas corretas: '+summary.proposals+'. Bloqueios esperados: '+summary.blocked+'.',
 'Arquivos realmente renomeados no sandbox local: '+receipts.length+'. Originais preservados (SHA-256).',
 'Boletins 001 e 002: encadeados por SHA-256. Plano para Drive 1: '+plan.state+'.',
 'Motivos de bloqueio do lote: '+plan.blockers.join(', ')+'.',
 '',
 '| ID | Tipo por metadados | Regra NOM | Nome proposto | Resultado |',
 '|---|---|---|---|---|'
 ];
 for(const x of rows)lines.push('| '+x.fixtureId+' | '+(x.kind||'indeterminado')+
  ' | '+(x.decision.ruleId||'-')+' | '+(x.decision.proposedName||'-')+
  ' | '+(x.decision.status==='PREVIEW'?'LOCAL_SIMULADO':x.decision.reason)+' |');
 lines.push('','Observação: as evidências de identidade, tipo e datas são artificiais no sidecar de metadados. Nenhuma propriedade jurídica, assinatura ou conteúdo de PDF foi certificado neste teste.','');
 fs.writeFileSync(path.join(target,'RELATORIO_FINAL.md'),lines.join('\n'),'utf8');
 console.log(JSON.stringify(evidence,null,2));
}
try{main()}catch(e){console.error('SYNTHETIC_E2E_FAILED:',e.message);process.exitCode=1}
