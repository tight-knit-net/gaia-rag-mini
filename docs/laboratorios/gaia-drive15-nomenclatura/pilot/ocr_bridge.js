'use strict';
/**
 * Bridge to the separate GAIA OCR REST engine in ocr-engine/api.py.
 * This module cannot mutate Google Drive or auto-homologate extracted fields.
 * The only supported pilot transport is a private/local HTTP endpoint.
 */
const http=require('node:http');
const crypto=require('node:crypto');
const {URL}=require('node:url');

const MAX_PDF=15*1024*1024;
const MAX_RESPONSE=3*1024*1024;
const ALLOWED_HOSTS=new Set(['127.0.0.1','localhost','api','gaia-ocr-api']);
const PDF_HEADER=Buffer.from('%PDF-');
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const failure=(code)=>Object.assign(new Error(code),{code});
function endpoint(raw){
 const url=new URL(raw||'');
 if(url.protocol!=='http:'||!ALLOWED_HOSTS.has(url.hostname)||
    !url.port||url.username||url.password||url.pathname!=='/'||
    url.search||url.hash)throw failure('OCR_ENDPOINT_MUST_BE_INTERNAL');
 return url;
}
function sanitizeFilename(name){
 if(typeof name!=='string'||!name.endsWith('.pdf')||name.length>150||
    name.includes('/')||name.includes('\\')||/[\u0000-\u001f]/.test(name))
    throw failure('OCR_PDF_FILENAME_INVALID');
 return name;
}
function requestJSON(url,method,path,token,body=null,contentType=null){
 return new Promise((resolve,reject)=>{
  const data=body||undefined;
  const req=http.request({
   hostname:url.hostname,port:Number(url.port),path,method,
   headers:{
    'Authorization':'Bearer '+token,'Accept':'application/json',
    'Content-Type':contentType||'application/json',
    ...(data?{'Content-Length':data.length}:{}),
   },
   timeout:25000,agent:false
  },res=>{
   if(res.statusCode<200||res.statusCode>=300){
    res.resume();return reject(failure('OCR_API_HTTP_'+res.statusCode));
   }
   let size=0;const chunks=[];
   res.on('data',part=>{
    size+=part.length;
    if(size>MAX_RESPONSE){req.destroy(failure('OCR_RESPONSE_TOO_LARGE'));return}
    chunks.push(part)
   });
   res.on('end',()=>{
    try{
     const data=JSON.parse(Buffer.concat(chunks).toString('utf8'));
     if(!data||typeof data!=='object'||Array.isArray(data))throw Error();
     resolve(data);
    }catch{reject(failure('OCR_INVALID_JSON_RESPONSE'))}
   });
  });
  req.on('timeout',()=>req.destroy(failure('OCR_API_TIMEOUT')));
  req.on('error',err=>reject(err.code?.startsWith('OCR_')?err:failure('OCR_API_UNREACHABLE')));
  req.end(data);
 });
}
function multipart(buffer,tenant,filename){
 const boundary='GAIAOCR_'+crypto.randomBytes(16).toString('hex');
 const start=Buffer.from(
  '--'+boundary+'\r\nContent-Disposition: form-data; name="tenant"\r\n\r\n'+tenant+'\r\n'+
  '--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="'+filename+'"\r\n'+
  'Content-Type: application/pdf\r\n\r\n','utf8');
 const end=Buffer.from('\r\n--'+boundary+'--\r\n');
 return {body:Buffer.concat([start,buffer,end]),contentType:'multipart/form-data; boundary='+boundary};
}
function candidateRules(text){
 const normalized=String(text||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/\s+/g,' ');
 const clues=[
  ['NOM-001',[/\bDANFSE\b/,/\bNFS[\s-]?E\b/]],
  ['NOM-002',[/COMPROVANTE DE INSCRICAO/,/SITUACAO CADASTRAL/,/CADASTRO NACIONAL DA PESSOA JURIDICA/]],
  ['NOM-003',[/AUTO DE FISCALIZACAO/,/\bCBMSC\b/,/E-SCI/]],
  ['NOM-018',[/CERTIDAO CADASTRAL/,/INSCRICAO IMOBILIARIA/,/CODIGO DO IMOVEL/]],
  ['NOM-016',[/ALTERACAO CONTRATUAL/,/\bJUCESC\b/,/JUNTA COMERCIAL/]],
  ['NOM-026',[/DOCUMENTO DE ARRECADACAO ESTADUAL/,/\bDARE\b/]]
 ];
 return clues
 .map(([id,regexps])=>({ruleId:id,signalCount:regexps.filter(p=>p.test(normalized)).length}))
 .filter(x=>x.signalCount>=2).sort((a,b)=>b.signalCount-a.signalCount);
}
function assessOcrResult({fileId,sourceSha256,tenant,record,synthetic=false}){
 if(!record||record.sha256!==sourceSha256||record.tenant!==tenant)
  throw failure('OCR_PROVENANCE_MISMATCH');
 if(record.status!=='processed'||!['mock','iloveapi'].includes(record.provider)||
    typeof record.text!=='string'||Buffer.byteLength(record.text,'utf8')>MAX_RESPONSE)
  throw failure('OCR_OUTPUT_UNVERIFIED');
 const candidates=candidateRules(record.text);
 const mock=record.provider==='mock';
 const hasText=record.text.trim().length>=25 &&
   !record.text.includes('[MODO MOCK: nenhum texto extraivel');
 return {
  schema:'gaia.pilot.ocr-candidate.v1',fileId,sha256:sourceSha256,
  ocrDocumentId:String(record.id),tenant,provider:record.provider,
  status:mock?'MOCK_NOT_REAL_OCR':hasText?'OCR_TEXT_REQUIRES_REVIEW':'OCR_NO_USABLE_TEXT',
  textSha256:sha(Buffer.from(record.text,'utf8')),
  textChars:record.text.length,hasText,ruleCandidates:candidates,
  sourceVerified:true,fieldsVerified:false,clientVerified:false,
  nameApproved:false,writeAllowed:false,synthetic
 };
}
class GaiaOcrClient{
 constructor({baseUrl='http://127.0.0.1:18788/',token}={}){
  this.url=endpoint(baseUrl);
  if(typeof token!=='string'||token.length<12)throw failure('OCR_TOKEN_REQUIRED');
  this.token=token;
 }
 async health(){
  const r=await requestJSON(this.url,'GET','/healthz',this.token);
  if(r.status!=='ok'||!['mock','iloveapi'].includes(r.provider))
   throw failure('OCR_ENGINE_NOT_READY');
  return {provider:r.provider,ready:true};
 }
 async analyze({
  fileId,filename,bytes,sha256:expectedSha,tenant,synthetic=false,
  authorizedFileIds=[],externalProviderApproved=false
 }={}){
  if(!/^[A-Za-z0-9_-]{8,150}$/.test(fileId||''))throw failure('OCR_FILE_ID_INVALID');
  if(!/^[A-Za-z0-9_-]{1,40}$/.test(tenant||''))throw failure('OCR_TENANT_INVALID');
  sanitizeFilename(filename);
  if(!Buffer.isBuffer(bytes)||bytes.length<10||bytes.length>MAX_PDF||
     !bytes.subarray(0,5).equals(PDF_HEADER))throw failure('OCR_PDF_INVALID');
  if(sha(bytes)!==expectedSha)throw failure('OCR_SOURCE_SHA_MISMATCH');
  if(!synthetic&&(!Array.isArray(authorizedFileIds)||!authorizedFileIds.includes(fileId)))
   throw failure('REAL_FILE_NOT_IN_APPROVED_BATCH');
  const service=await this.health();
  if(service.provider==='iloveapi'&&!externalProviderApproved)
   throw failure('EXTERNAL_OCR_APPROVAL_REQUIRED');
  if(!synthetic&&service.provider==='mock')
   throw failure('REAL_OCR_ENGINE_NOT_ACTIVE');
  const pack=multipart(bytes,tenant,filename);
  const uploaded=await requestJSON(this.url,'POST','/v1/documents',this.token,pack.body,pack.contentType);
  if(!uuid.test(uploaded.id)||uploaded.sha256!==expectedSha||uploaded.tenant!==tenant)
   throw failure('OCR_UPLOAD_READBACK_MISMATCH');
  const rec=await requestJSON(this.url,'POST','/v1/documents/'+uploaded.id+'/ocr?tenant='+encodeURIComponent(tenant),this.token);
  if(rec.id!==uploaded.id||rec.provider!==service.provider)
   throw failure('OCR_PROVIDER_OR_ID_DRIFT');
  return assessOcrResult({fileId,sourceSha256:expectedSha,tenant,record:rec,synthetic});
 }
}
module.exports={GaiaOcrClient,assessOcrResult,candidateRules,endpoint,MAX_PDF};
