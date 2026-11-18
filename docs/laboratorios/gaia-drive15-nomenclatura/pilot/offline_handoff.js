'use strict';
/** File-only courier. NO Google API, HTTP, MCP, or GitHub data transport. */
const fs=require('node:fs'), path=require('node:path'),crypto=require('node:crypto');
const DRIVE_ID='0ALBFaLnE8ZPHUk9PVA';
const PATHS={triage:'1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-',clientIndex:'1E3j-K4GxNfYLEjrDl_OE1jNuQPV9EU_M'};
const TECHNICAL=new Set(['1obPrd8IpvOvlFSgx5tGa1lQtt7x6SwEb','14lBYiStqthQsEWtNzbCpZSeRXGZxR8K_','1l0VI0NW8CDRkPbTtmC0CczyzDpXGp6bo','1Uh0pm8zmGnbzChLXZFxaRn_IAWxIwITA','1rQOZ1uEIHl3XEOytSO2nqtqfBrpRQeDc']);
function validateClientProof(p,id){return p && p.clientId===id && /^\d{3}$/.test(id) && p.driveId===DRIVE_ID && typeof p.clientFolderId==='string' && p.indexVerified===true && p.manifestVerified===true && p.indexFileId===PATHS.clientIndex && typeof p.manifestFileId==='string' && p.manifestVersion!=null;}
/** Validate operator-supplied Drive snapshot. Does not authenticate that snapshot. */
function inventoryFromReadOnlyPages({batchId,pages,scopeIds}={}){
 if(!RUN.test(batchId||'')||!Array.isArray(pages)||!Array.isArray(scopeIds)||!scopeIds.length)throw BAD('INVENTORY_SCOPE_INVALID');
 const byParent=new Map();
 for(const p of pages){
  if(!p||p.driveId!==DRIVE_ID||byParent.has(p.parentId))throw BAD('INVENTORY_PARENT_INVALID');
  if(p.complete!==true||p.nextPageToken||!Array.isArray(p.items))throw BAD('INVENTORY_INCOMPLETE');
  byParent.set(p.parentId,p.items.map(x=>({id:x.id,name:x.name??x.title,mimeType:x.mimeType??x.mime_type,parentId:p.parentId,driveId:x.driveId??x.drive_id,version:x.version,parentVerified:(x.parents??x.parent_ids??[]).includes(p.parentId),folder:(x.mimeType??x.mime_type)==='application/vnd.google-apps.folder'})));
 }
 if(!byParent.has(PATHS.triage))throw BAD('TRIAGE_PAGE_MISSING');
 const top=byParent.get(PATHS.triage).filter(x=>!TECHNICAL.has(x.id));
 for(const id of scopeIds)if(!top.some(x=>x.id===id))throw BAD('OUTSIDE_TRIAGE_SCOPE');
 const accepted=[],visited=new Set(),stack=top.filter(x=>scopeIds.includes(x.id));
 while(stack.length){const x=stack.pop();
  if(!x||!ID.test(x.id||'')||visited.has(x.id)||!x.parentVerified||x.driveId!==DRIVE_ID||typeof x.name!=='string'||!x.mimeType||!x.version)throw BAD('INVALID_SOURCE_INVENTORY');
  if(TECHNICAL.has(x.id))throw BAD('TECHNICAL_CONTROL_IN_SCOPE');
  visited.add(x.id);accepted.push(x);
  if(x.folder){if(!byParent.has(x.id))throw BAD('INVENTORY_INCOMPLETE');stack.push(...byParent.get(x.id));}
 }
 const allowed=new Set([PATHS.triage,...accepted.filter(x=>x.folder).map(x=>x.id)]);
 for(const id of byParent.keys())if(!allowed.has(id))throw BAD('PAGE_OUT_OF_SCOPE');
 return{items:accepted};
}
const MAX_BYTES=15*1024*1024;
const BASE=process.env.GAIA_PILOT_BASE||'/home/ubuntu/gaia-test-lab-homologacao/pilots';
const BAD=(code)=>{const e=new Error(code);e.code=code;return e;};
const SHA=/^[a-f0-9]{64}$/i,ID=/^[A-Za-z0-9_-]{8,150}$/,RUN=/^[a-z0-9][a-z0-9_-]{7,70}$/;
const MIME={'application/pdf':'.pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document':'.docx'};
const checksum=(buf)=>crypto.createHash('sha256').update(buf).digest('hex');
function noSymlinkFile(p){let s=fs.lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||!s.size||s.size>MAX_BYTES)throw BAD('SOURCE_FILE_UNSAFE');return s;}
function noSymlinkDirectory(p){let s=fs.lstatSync(p);if(!s.isDirectory()||s.isSymbolicLink())throw BAD('DIRECTORY_UNSAFE');}
function magic(buf,ext){if(ext==='.pdf'&&!buf.subarray(0,5).equals(Buffer.from('%PDF-')))throw BAD('PDF_SIGNATURE_INVALID');if(ext==='.docx'&&!buf.subarray(0,2).equals(Buffer.from('PK')))throw BAD('DOCX_SIGNATURE_INVALID');}
function validatePackage(pkg){
 if(!pkg||pkg.schema!=='gaia.drive1.offline-handoff.v1'||pkg.runId!==pkg.pilotManifest?.batchId||!RUN.test(pkg.runId||''))throw BAD('HANDOFF_SCHEMA_OR_RUN_INVALID');
 const m=pkg.pilotManifest;
 if(m.schema!=='gaia.drive1.pilot.v1'||m.mode!=='READ_ONLY'||m.driveId!==DRIVE_ID||pkg.driveId!==DRIVE_ID||!/^\d{3}$/.test(m.clientId||'')||pkg.clientId!==m.clientId||pkg.triageFolderId!==PATHS.triage)throw BAD('WRONG_DRIVE_TRIAGE_OR_CLIENT');
 if(!validateClientProof(m.clientProof,m.clientId))throw BAD('CLIENT_PROOF_MISSING');
 const a=pkg.approval;
 if(!a||a.operation!=='READ_ONLY_OCR_NOM_PREVIEW'||a.runId!==pkg.runId||a.clientId!==m.clientId||typeof a.ref!=='string'||a.ref.length<6||!Array.isArray(a.fileIds)||a.fileIds.length===0)throw BAD('SCOPED_APPROVAL_MISSING');
 const inv=inventoryFromReadOnlyPages({batchId:m.batchId,pages:m.pages,scopeIds:m.scopeIds});
 const files=inv.items.filter(v=>!v.folder);
 if(!files.length||files.length!==pkg.files?.length||files.length!==a.fileIds.length)throw BAD('FILE_SCOPE_MISMATCH');
 const idset=new Set(files.map(v=>v.id)),authorized=new Set(a.fileIds),copied=new Set();
 if(idset.size!==files.length||authorized.size!==a.fileIds.length)throw BAD('DUPLICATE_FILE_ID');
 for(const x of pkg.files){
  if(!x||!ID.test(x.fileId||'')||!idset.has(x.fileId)||!authorized.has(x.fileId)||copied.has(x.fileId))throw BAD('FILE_ID_NOT_IN_APPROVED_SCOPE');
  copied.add(x.fileId);
  const item=files.find(v=>v.id===x.fileId);
  if(!item.parentVerified||!item.version||item.driveId!==DRIVE_ID||item.parentId!==x.sourceParentId||item.name!==x.sourceName||item.mimeType!==x.mimeType)throw BAD('PROVIDER_SNAPSHOT_MISMATCH');
  const ext=MIME[x.mimeType];if(!ext)throw BAD('FORMAT_NOT_SUPPORTED_IN_PILOT');
  if(x.localName!==x.fileId+ext||!SHA.test(x.sha256||'')||!Number.isSafeInteger(x.bytes)||x.bytes<=0||x.bytes>MAX_BYTES)throw BAD('FILE_DESCRIPTOR_INVALID');
 }
 if([...idset].some(id=>!copied.has(id)||!authorized.has(id)))throw BAD('APPROVAL_SCOPE_INCOMPLETE');
 return {m,files};
}
function receive(pkg,inbox,root=BASE){
 const {m}=validatePackage(pkg);const base=path.resolve(root),run=path.join(base,pkg.runId);
 if(!fs.existsSync(base))throw BAD('PILOT_BASE_NOT_CREATED');noSymlinkDirectory(base);noSymlinkDirectory(inbox);
 if(fs.existsSync(run))throw BAD('RUN_ALREADY_EXISTS');
 // All bytes verified before creating anything in the pilot root.
 const read=[];
 for(const entry of pkg.files){
  const p=path.join(path.resolve(inbox),entry.localName);noSymlinkFile(p);
  const b=fs.readFileSync(p);if(b.length!==entry.bytes||checksum(b)!==entry.sha256.toLowerCase())throw BAD('FILE_SHA_OR_SIZE_MISMATCH');
  magic(b,MIME[entry.mimeType]);read.push({entry,b});
 }
 fs.mkdirSync(run,{mode:0o700});
 try{
  const raw=path.join(run,'raw'),reports=path.join(run,'reports');fs.mkdirSync(raw,{mode:0o700});fs.mkdirSync(reports,{mode:0o700});
  const copies=[];
  for(const {entry,b} of read){
   const storedAs=entry.localName,target=path.join(raw,storedAs);
   fs.writeFileSync(target,b,{flag:'wx',mode:0o400});fs.chmodSync(target,0o400);
   if(checksum(fs.readFileSync(target))!==entry.sha256.toLowerCase())throw BAD('COPY_READBACK_FAILED');
   copies.push({fileId:entry.fileId,sourceVersion:m.pages.flatMap(x=>x.items).find(x=>x.id===entry.fileId)?.version,storedAs,sha256:entry.sha256.toLowerCase(),bytes:entry.bytes});
  }
  const actualManifest={...m,copies};
  fs.writeFileSync(path.join(run,'manifest.json'),JSON.stringify(actualManifest,null,2)+'\n',{mode:0o600,flag:'wx'});
  fs.writeFileSync(path.join(run,'pilot.marker.json'),JSON.stringify({schema:'gaia.drive1.pilot-marker.v1',runId:pkg.runId,clientId:pkg.clientId,driveId:DRIVE_ID,rawOnly:true},null,2)+'\n',{mode:0o600,flag:'wx'});
  const receipt={schema:'gaia.drive1.handoff-receipt.v1',runId:pkg.runId,clientId:pkg.clientId,files:copies.length,sourceDriveId:DRIVE_ID,sourceTriageFolderId:PATHS.triage,sourceMode:'OPERATOR_ATTESTED_DRIVE_SNAPSHOT',deliveryMode:'MANUAL_OFFLINE_FILE_COURIER',status:'RECEIVED_VERIFIED_NOT_OCR_PROCESSED',driveWrites:0,githubDocumentsUploaded:0,approvalRef:pkg.approval.ref};
  fs.writeFileSync(path.join(reports,'TRANSPORT_RECEIPT.json'),JSON.stringify(receipt,null,2)+'\n',{mode:0o600,flag:'wx'});
  return receipt;
 }catch(e){fs.rmSync(run,{recursive:true,force:true});throw e;}
}
function verify(runId,root=BASE){
 if(!RUN.test(runId||''))throw BAD('INVALID_RUN_ID');const dir=path.join(path.resolve(root),runId);noSymlinkDirectory(dir);noSymlinkDirectory(path.join(dir,'raw'));
 const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
 const entries=manifest.copies;
 if(!Array.isArray(entries)||!entries.length)throw BAD('COPIES_MISSING');
 for(const v of entries){if(!ID.test(v.fileId)||!/^[A-Za-z0-9_-]+\.(?:pdf|docx)$/.test(v.storedAs)||v.storedAs.split('.')[0]!==v.fileId||!SHA.test(v.sha256))throw BAD('UNSAFE_COPY_DESCRIPTOR');
  let p=path.join(dir,'raw',v.storedAs);let s=noSymlinkFile(p);if(s.size!==v.bytes||checksum(fs.readFileSync(p))!==v.sha256)throw BAD('COPY_READBACK_FAILED');}
 return {status:'VERIFIED_FOR_READ_ONLY_PILOT',runId,files:entries.length,driveWrites:0};
}
if(require.main===module){
 try{
  const [cmd,...args]=process.argv.slice(2);let r;
  if(cmd==='receive'&&args.length===3){const [packageFile,inbox,base]=args;r=receive(JSON.parse(fs.readFileSync(packageFile,'utf8')),inbox,base)}
  else if(cmd==='verify'&&args.length===2){r=verify(args[0],args[1])}
  else throw BAD('USAGE: node pilot/offline_handoff.js receive package.json inbox/ pilot_base/ | verify run_id pilot_base/');
  process.stdout.write(JSON.stringify(r,null,2)+'\n');
 }catch(e){process.stderr.write('HANDOFF_BLOCKED '+e.code+'\n');process.exitCode=2;}
}
module.exports={validatePackage,receive,verify,checksum};
