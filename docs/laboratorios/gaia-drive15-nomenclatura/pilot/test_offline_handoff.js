'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {receive,verify,checksum,validatePackage}=require('./offline_handoff');
const id='1AbCdEfGh0123',clientId='009',triage='1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-',driveId='0ALBFaLnE8ZPHUk9PVA';
const content=Buffer.from('%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n');
function fixture(){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gaia-handoff-')),inbox=path.join(dir,'inbox'),base=path.join(dir,'pilots');fs.mkdirSync(inbox);fs.mkdirSync(base);
 const f=id+'.pdf';fs.writeFileSync(path.join(inbox,f),content);
 const m={schema:'gaia.drive1.pilot.v1',mode:'READ_ONLY',batchId:'pilot_009_20261118_01',driveId,clientId,scopeIds:[id],pages:[{parentId:triage,driveId,complete:true,nextPageToken:null,items:[{id,name:'doc teste.pdf',mimeType:'application/pdf',parents:[triage],driveId,version:'OBS_aa'}]}],clientProof:{clientId,driveId,clientFolderId:'11VO63mnCFuZF_POIWwf5rTBcS9UYQlr5',indexVerified:true,manifestVerified:true,indexFileId:'1E3j-K4GxNfYLEjrDl_OE1jNuQPV9EU_M',manifestFileId:'1EH7qc_nX7MXjLgPhCC-0O7GgtshJLvvD',manifestVersion:'OBS_22'},metadataById:{},destinationSnapshot:null};
 const pkg={schema:'gaia.drive1.offline-handoff.v1',driveId,clientId,triageFolderId:triage,runId:m.batchId,pilotManifest:m,approval:{operation:'READ_ONLY_OCR_NOM_PREVIEW',ref:'OPERATOR_TEST_ONLY',runId:m.batchId,clientId,fileIds:[id]},files:[{fileId:id,sourceParentId:triage,sourceName:'doc teste.pdf',mimeType:'application/pdf',localName:f,sha256:checksum(content),bytes:content.length}]};
 return{pkg,dir,inbox,base,cleanup:()=>fs.rmSync(dir,{force:true,recursive:true})};
}
function rejects(mod,code){const f=fixture();try{mod(f);assert.throws(()=>validatePackage(f.pkg),{code});}finally{f.cleanup()}}
test('synthetic handoff validates and verifies bytes',()=>{const f=fixture();try{assert.equal(receive(f.pkg,f.inbox,f.base).status,'RECEIVED_VERIFIED_NOT_OCR_PROCESSED');assert.equal(verify(f.pkg.runId,f.base).files,1);assert.equal(fs.readFileSync(path.join(f.base,f.pkg.runId,'raw',id+'.pdf')).toString(),content.toString())}finally{f.cleanup()}});
test('never publishes documents to git and no network implementation',()=>{const body=fs.readFileSync(path.join(__dirname,'offline_handoff.js'),'utf8');assert.ok(!body.includes('require(\'node:http\')'));assert.ok(!body.includes('https.request'));assert.ok(!body.includes('fetch('))});
test('blocks wrong shared drive',()=>rejects(f=>f.pkg.driveId='bad','WRONG_DRIVE_TRIAGE_OR_CLIENT'));
test('blocks wrong triage folder',()=>rejects(f=>f.pkg.triageFolderId='bad','WRONG_DRIVE_TRIAGE_OR_CLIENT'));
test('blocks wrong client ID',()=>rejects(f=>f.pkg.clientId='008','WRONG_DRIVE_TRIAGE_OR_CLIENT'));
test('blocks missing operator approval',()=>rejects(f=>f.pkg.approval=null,'SCOPED_APPROVAL_MISSING'));
test('blocks mismatched approval client',()=>rejects(f=>f.pkg.approval.clientId='008','SCOPED_APPROVAL_MISSING'));
test('blocks no actual index proof',()=>rejects(f=>f.pkg.pilotManifest.clientProof.indexVerified=false,'CLIENT_PROOF_MISSING'));
test('blocks no manifest proof',()=>rejects(f=>f.pkg.pilotManifest.clientProof.manifestVerified=false,'CLIENT_PROOF_MISSING'));
test('blocks different file id',()=>rejects(f=>f.pkg.files[0].fileId='anotherFake','FILE_ID_NOT_IN_APPROVED_SCOPE'));
test('blocks altered document name',()=>rejects(f=>f.pkg.files[0].sourceName='other.pdf','PROVIDER_SNAPSHOT_MISMATCH'));
test('blocks altered source parent',()=>rejects(f=>f.pkg.files[0].sourceParentId='bad','PROVIDER_SNAPSHOT_MISMATCH'));
test('blocks unsupported format',()=>rejects(f=>f.pkg.files[0].mimeType='application/zip','PROVIDER_SNAPSHOT_MISMATCH'));
test('blocks wrong file hash',()=>{const f=fixture();try{f.pkg.files[0].sha256='0'.repeat(64);assert.throws(()=>receive(f.pkg,f.inbox,f.base),{code:'FILE_SHA_OR_SIZE_MISMATCH'});assert.equal(fs.readdirSync(f.base).length,0)}finally{f.cleanup()}});
test('blocks spoofed PDF header',()=>{const f=fixture();try{const b=Buffer.from('this is not a PDF but bytes');fs.writeFileSync(path.join(f.inbox,id+'.pdf'),b);f.pkg.files[0].sha256=checksum(b);f.pkg.files[0].bytes=b.length;assert.throws(()=>receive(f.pkg,f.inbox,f.base),{code:'PDF_SIGNATURE_INVALID'})}finally{f.cleanup()}});
test('blocks symlink files',()=>{const f=fixture();try{fs.renameSync(path.join(f.inbox,id+'.pdf'),path.join(f.inbox,'payload.pdf'));fs.symlinkSync('payload.pdf',path.join(f.inbox,id+'.pdf'));assert.throws(()=>receive(f.pkg,f.inbox,f.base),{code:'SOURCE_FILE_UNSAFE'})}finally{f.cleanup()}});
test('blocks duplicate rerun',()=>{const f=fixture();try{receive(f.pkg,f.inbox,f.base);assert.throws(()=>receive(f.pkg,f.inbox,f.base),{code:'RUN_ALREADY_EXISTS'})}finally{f.cleanup()}});
test('detects post-handoff tampering',()=>{const f=fixture();try{receive(f.pkg,f.inbox,f.base);fs.chmodSync(path.join(f.base,f.pkg.runId,'raw',id+'.pdf'),0o600);fs.appendFileSync(path.join(f.base,f.pkg.runId,'raw',id+'.pdf'),'evil');assert.throws(()=>verify(f.pkg.runId,f.base),{code:'COPY_READBACK_FAILED'})}finally{f.cleanup()}});
test('blocks partial listing',()=>rejects(f=>f.pkg.pilotManifest.pages[0].complete=false,'INVENTORY_INCOMPLETE'));
test('blocks wrong scope',()=>rejects(f=>f.pkg.pilotManifest.scopeIds=['file_missing'],'OUTSIDE_TRIAGE_SCOPE'));
