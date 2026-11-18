'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const http=require('node:http'),crypto=require('node:crypto');
const {GaiaOcrClient,candidateRules,assessOcrResult,endpoint}=require('../ocr_bridge');
const pdf=Buffer.from('%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n');
const hash=crypto.createHash('sha256').update(pdf).digest('hex');
const id='a6224561-8af0-4143-9c2b-ad7c39f53c6e';
const token='synthetic-test-token-1234567';
const sampleText='COMPROVANTE DE INSCRIÇÃO E DE SITUAÇÃO CADASTRAL. CADASTRO NACIONAL DA PESSOA JURÍDICA. Emitido no dia 09/01/2026.';
async function serverFor({provider='mock',hashOverride=null,recordOverride=null}={}){
 const calls=[];
 const server=http.createServer((req,res)=>{
  const parts=[];
  req.on('data',c=>parts.push(c));
  req.on('end',()=>{
   calls.push({method:req.method,url:req.url,authorization:req.headers.authorization,
     contentType:req.headers['content-type'],bytes:Buffer.concat(parts).length});
   res.setHeader('Content-Type','application/json');
   if(req.url==='/healthz')return res.end(JSON.stringify({status:'ok',service:'gaia-ocr-lab',provider}));
   if(req.headers.authorization!=='Bearer '+token){res.statusCode=401;return res.end('{}')}
   if(req.method==='POST'&&req.url==='/v1/documents')
     return res.end(JSON.stringify({id,tenant:'synthetic_027',sha256:hashOverride||hash,pages:1,status:'uploaded'}));
   if(req.method==='POST'&&req.url.startsWith('/v1/documents/'))
     return res.end(JSON.stringify({id,tenant:'synthetic_027',sha256:hashOverride||hash,
       provider,status:'processed',text:sampleText,...recordOverride}));
   res.statusCode=404;res.end('{}');
  });
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 return {url:'http://127.0.0.1:'+server.address().port+'/',calls,
  close:()=>new Promise(r=>server.close(r))};
}
test('URL do serviço OCR limita host a loopback e contêiner privado',()=>{
 assert.throws(()=>endpoint('https://example.com/'),/OCR_ENDPOINT_MUST_BE_INTERNAL/);
 assert.throws(()=>endpoint('http://evil.example:8080/'),/OCR_ENDPOINT_MUST_BE_INTERNAL/);
 assert.throws(()=>endpoint('http://127.0.0.1:8080/other'),/OCR_ENDPOINT_MUST_BE_INTERNAL/);
 assert.equal(endpoint('http://api:8080/').hostname,'api');
});
test('reconhecimento OCR produz candidatos, sem converter em prova',()=>{
 const c=candidateRules(sampleText);
 assert.ok(c.some(x=>x.ruleId==='NOM-002'));
 const r=assessOcrResult({fileId:'synthetic_file_id_s02',sourceSha256:hash,
  tenant:'synthetic_027',record:{id,tenant:'synthetic_027',sha256:hash,provider:'mock',
   status:'processed',text:sampleText},synthetic:true});
 assert.equal(r.status,'MOCK_NOT_REAL_OCR');
 assert.equal(r.fieldsVerified,false);assert.equal(r.nameApproved,false);
 assert.equal(r.writeAllowed,false);assert.equal(r.textSha256.length,64);
 assert.ok(!Object.keys(r).includes('text'));
});
test('integração real HTTP do piloto com OCR mock recebe texto e mantém pendente',async()=>{
 const local=await serverFor();
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  const result=await api.analyze({fileId:'synthetic_file_id_s01',filename:'nfse.pdf',bytes:pdf,
   sha256:hash,tenant:'synthetic_027',synthetic:true});
  assert.equal(result.provider,'mock');
  assert.equal(result.status,'MOCK_NOT_REAL_OCR');
  assert.equal(result.sourceVerified,true);
  assert.equal(result.fieldsVerified,false);
  assert.equal(local.calls.length,3);
  assert.deepEqual(local.calls.map(x=>x.method),['GET','POST','POST']);
  assert.equal(local.calls[1].authorization,'Bearer '+token);
  assert.match(local.calls[1].contentType,/multipart\/form-data/);
 }finally{await local.close()}
});
test('cliente real não pode entrar sem autorização de ID',async()=>{
 const local=await serverFor();
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  await assert.rejects(api.analyze({fileId:'real_google_drive_file',filename:'nfse.pdf',bytes:pdf,
   sha256:hash,tenant:'client_009'}),/REAL_FILE_NOT_IN_APPROVED_BATCH/);
  assert.equal(local.calls.length,0);
 }finally{await local.close()}
});
test('OCR mock não é apresentado como OCR real para cliente',async()=>{
 const local=await serverFor();
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  await assert.rejects(api.analyze({fileId:'real_google_drive_file',filename:'nfse.pdf',bytes:pdf,
   sha256:hash,tenant:'client_009',authorizedFileIds:['real_google_drive_file']}),
  /REAL_OCR_ENGINE_NOT_ACTIVE/);
  assert.equal(local.calls.length,1);
 }finally{await local.close()}
});
test('serviço externo iLoveAPI exige autorização específica e não recebe bytes sem ela',async()=>{
 const local=await serverFor({provider:'iloveapi'});
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  await assert.rejects(api.analyze({fileId:'synthetic_file_id_s01',filename:'nfse.pdf',bytes:pdf,
   sha256:hash,tenant:'synthetic_027',synthetic:true}),/EXTERNAL_OCR_APPROVAL_REQUIRED/);
  assert.equal(local.calls.length,1);
 }finally{await local.close()}
});
test('hash de entrada incorreto bloqueia antes de qualquer chamada HTTP',async()=>{
 const local=await serverFor();
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  await assert.rejects(api.analyze({fileId:'synthetic_file_id_s01',filename:'nfse.pdf',
   bytes:pdf,sha256:'0'.repeat(64),tenant:'synthetic_027',synthetic:true}),
   /OCR_SOURCE_SHA_MISMATCH/);
  assert.equal(local.calls.length,0);
 }finally{await local.close()}
});
test('hash do serviço divergente aborta antes de solicitar OCR',async()=>{
 const local=await serverFor({hashOverride:'f'.repeat(64)});
 try{
  const api=new GaiaOcrClient({baseUrl:local.url,token});
  await assert.rejects(api.analyze({fileId:'synthetic_file_id_s01',filename:'nfse.pdf',
   bytes:pdf,sha256:hash,tenant:'synthetic_027',synthetic:true}),
   /OCR_UPLOAD_READBACK_MISMATCH/);
  assert.equal(local.calls.length,2);
 }finally{await local.close()}
});
test('contrato reprova texto vazio ou registro de outro tenant',()=>{
 assert.throws(()=>assessOcrResult({fileId:'synthetic_file_id_s01',sourceSha256:hash,
  tenant:'tenant_a',record:{sha256:hash,tenant:'tenant_b',status:'processed',provider:'mock',
   text:sampleText}}),/OCR_PROVENANCE_MISMATCH/);
});
