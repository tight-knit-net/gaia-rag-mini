'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const gate=require('./gaia_nom_gate.js');
const catalog=JSON.parse(fs.readFileSync(__dirname+'/002_INDICE_FEDERADO_60_REGRAS.json','utf8'));
const rule018=catalog.rules.find(x=>x.rule_id==='NOM-018');
const c=()=>({driveId:'0ALBFaLnE8ZPHUk9PVA',
 client:{id:'009',rootId:'CLIENT009',indexId:'009',manifestId:'009',indexRootId:'CLIENT009',manifestRootId:'CLIENT009',indexVerified:true,manifestVerified:true},
 file:{id:'F1',name:'auto de embargo.pdf',parentId:'TRIAGE',driveId:'0ALBFaLnE8ZPHUk9PVA',revision:'R1',triageProven:true},
 destination:{id:'P1',driveId:'0ALBFaLnE8ZPHUk9PVA',ancestorIds:['CLIENT009','PROC'],liveListingVerified:true,existingFiles:[]},
 sanitizationVerified:true,affiliationVerified:true,fileFormatReviewed:true,documentRiskCleared:true,
 nom:{mode:'PREFIX_ONLY_NO_NOM',sourceCurrentVerified:true,noPositiveNomVerified:true,basenameSanitizedVerified:true,sanitizedBasename:'auto de embargo.pdf'}});
const auth=(x)=>{let p=gate.candidate(x);x.authorization={approved:true,ref:'APPROVAL-EXACT-F1',fileId:x.file.id,sourceParentId:x.file.parentId,destinationId:x.destination.id,clientId:x.client.id,exactName:p.proposedName,originalRevision:x.file.revision,approvedPostRenameRevision:'R2'};x.readback={provider:'NATIVE_GOOGLE_DRIVE',verified:true,id:x.file.id,name:p.proposedName,parentId:x.file.parentId,driveId:x.driveId,revision:'R2'};return x;};
function why(x){return gate.candidate(x).reason}
test('01 preserve original basename + exact ID prefix only',()=>{let r=gate.candidate(c());assert.equal(r.proposedName,'009_auto de embargo.pdf');assert.equal(r.status,'PREVIEW_ONLY');assert.equal(r.allowMove,false)});
test('02 never allow a MOVE in preview',()=>{assert.equal(gate.candidate(c()).allowMove,false)});
test('03 idempotency: already-prefixed name',()=>{let x=c();x.file.name='009_auto de embargo.pdf';let p=gate.candidate(x);assert.equal(p.renameRequired,false);assert.equal(p.proposedName,x.file.name)});
test('04 wrong client prefix: hard block',()=>{let x=c();x.file.name='008_auto de embargo.pdf';assert.equal(why(x),'WRONG_CLIENT_PREFIX')});
test('05 repeated client prefix: hard block',()=>{let x=c();x.file.name='009_009_auto de embargo.pdf';assert.equal(why(x),'DUPLICATED_OR_EMPTY_PREFIX')});
test('06 unverified matching 009 folder name not enough for identity',()=>{let x=c();x.client.indexVerified=false;assert.equal(why(x),'CLIENT_IDENTITY_UNVERIFIED')});
test('07 wrong target Drive block',()=>{let x=c();x.destination.driveId='OTHER';assert.equal(why(x),'WRONG_DRIVE')});
test('08 target outside client tree block',()=>{let x=c();x.destination.ancestorIds=['OTHER'];assert.equal(why(x),'DESTINATION_NOT_VERIFIED_IN_CLIENT_TREE')});
test('09 absent destination listing blocks',()=>{let x=c();x.destination.existingFiles=null;assert.equal(why(x),'DESTINATION_NOT_VERIFIED_IN_CLIENT_TREE')});
test('10 collision distinct file ID blocks without autosuffix',()=>{let x=c();x.destination.existingFiles=[{id:'F2',name:'009_auto de embargo.pdf'}];assert.equal(why(x),'COLLISION_DISTINCT_DRIVE_FILE_ID')});
test('11 cannot treat missing OCR as no NOM match',()=>{let x=c();x.nom.noPositiveNomVerified=false;assert.equal(why(x),'NO_NOM_FALLBACK_NOT_PROVEN')});
test('12 unresolved NOM blocks',()=>{let x=c();x.nom.mode='UNKNOWN_OR_CONFLICT';assert.equal(why(x),'NOM_UNKNOWN_OR_CONFLICT')});
test('13 verified NOM positive can propose exact pattern',()=>{let x=c();x.nom={mode:'NOM_POSITIVE',ruleId:'NOM-018',sourceCurrentVerified:true,sourceConstraintsVerified:true,variablesProven:true,extensionProven:true,signatureGateCleared:true,patternReviewed:true,humanReviewApproved:true,catalogIsNonReleased:true,ruleRecord:rule018,selectedTemplate:rule018.approved_pattern,provenVariables:{UNIDADE_IPTU:'001'},resolvedApprovedPattern:'CERTIDÃO_DE_IPTU_001.pdf'};let p=gate.candidate(x);assert.equal(p.proposedName,'009_CERTIDÃO_DE_IPTU_001.pdf');assert.equal(p.status,'PREVIEW_ONLY')});
test('14 NOM placeholder blocks',()=>{let x=c();x.nom={mode:'NOM_POSITIVE',ruleId:'NOM-018',sourceCurrentVerified:true,sourceConstraintsVerified:true,variablesProven:true,extensionProven:true,signatureGateCleared:true,patternReviewed:true,humanReviewApproved:true,catalogIsNonReleased:true,ruleRecord:rule018,selectedTemplate:rule018.approved_pattern,provenVariables:{},resolvedApprovedPattern:'CERTIDÃO_DE_IPTU_<UNIDADE_IPTU>.pdf'};assert.equal(why(x),'NOM_PATTERN_OR_VARIABLE_MISMATCH')});
test('15 missing approval blocks even if correct readback',()=>{let x=auth(c());x.authorization.approved=false;assert.equal(gate.beforeMove(x).reason,'EXACT_MOVE_AUTHORIZATION_MISSING')});
test('16 fail rename readback - still unprefixed',()=>{let x=auth(c());x.readback.name=x.file.name;assert.equal(gate.beforeMove(x).reason,'RENAME_READBACK_REQUIRED_BEFORE_MOVE')});
test('17 fail stale revision',()=>{let x=auth(c());x.readback.revision='R1';assert.equal(gate.beforeMove(x).reason,'RENAME_READBACK_REQUIRED_BEFORE_MOVE')});
test('18 exact approval + provider readback READY_FOR_MOVE',()=>{let x=auth(c());let r=gate.beforeMove(x);assert.equal(r.status,'READY_FOR_MOVE');assert.equal(r.allowMove,true)});
test('19 postmove mismatched parent remains UNCERTAIN',()=>{let x=auth(c()),p=gate.beforeMove(x);assert.equal(gate.verifyAfterMove(p,{provider:'NATIVE_GOOGLE_DRIVE',verified:true,id:'F1',name:p.verifiedName,parentId:'WRONG',driveId:x.driveId}).status,'EXECUTION_UNCERTAIN')});
test('20 postmove exact readback verified',()=>{let x=auth(c()),p=gate.beforeMove(x);assert.equal(gate.verifyAfterMove(p,{provider:'NATIVE_GOOGLE_DRIVE',verified:true,id:'F1',name:p.verifiedName,parentId:'P1',driveId:x.driveId}).status,'MOVED_VERIFIED')});
test('21 no authorized source rewrite',()=>{let x=c();assert.equal(gate.candidate(x).originalName,'auto de embargo.pdf');assert.equal(x.file.name,'auto de embargo.pdf')});
test('22 catalog NOM 001-060 unchanged with unique patterns',()=>{let j=JSON.parse(fs.readFileSync(__dirname+'/002_INDICE_FEDERADO_60_REGRAS.json','utf8'));assert.equal(j.rules.length,60);assert.equal(new Set(j.rules.map(r=>r.rule_id)).size,60);assert.equal(j.status,'DERIVED_NONCANONICAL_NOT_RELEASED');assert.equal(j.folder_naming_rules.status,'NOT_HOMOLOGATED')});
test('23 source file cannot be folder',()=>{let x=c();x.file.isFolder=true;assert.equal(why(x),'SOURCE_OR_REVISION_UNVERIFIED')});
test('24 no approval after renaming from original version mismatch',()=>{let x=auth(c());x.authorization.originalRevision='stale';assert.equal(gate.beforeMove(x).reason,'EXACT_MOVE_AUTHORIZATION_MISSING')});

test('25 reject changed NOM name beyond official pattern',()=>{let x=c();x.nom={mode:'NOM_POSITIVE',ruleId:'NOM-018',sourceCurrentVerified:true,sourceConstraintsVerified:true,variablesProven:true,extensionProven:true,signatureGateCleared:true,patternReviewed:true,humanReviewApproved:true,catalogIsNonReleased:true,ruleRecord:rule018,selectedTemplate:rule018.approved_pattern,provenVariables:{UNIDADE_IPTU:'001'},resolvedApprovedPattern:'CERTIDÃO IPTU 001.pdf'};assert.equal(why(x),'NOM_PATTERN_OR_VARIABLE_MISMATCH')});
test('26 reject invalid calendar day in NOM',()=>{let x=c();let rule=catalog.rules.find(r=>r.rule_id==='NOM-001');x.nom={mode:'NOM_POSITIVE',ruleId:'NOM-001',sourceCurrentVerified:true,sourceConstraintsVerified:true,variablesProven:true,extensionProven:true,signatureGateCleared:true,patternReviewed:true,humanReviewApproved:true,catalogIsNonReleased:true,ruleRecord:rule,selectedTemplate:rule.approved_pattern,provenVariables:{'DD-MM-AAAA':'31-02-2026'},resolvedApprovedPattern:'DANFSe-31-02-2026.pdf'};assert.equal(why(x),'NOM_PATTERN_OR_VARIABLE_MISMATCH')});
test('27 original 60 NOM templates intact',()=>{assert.equal(catalog.rules.find(r=>r.rule_id==='NOM-013').approved_pattern,'RECIBO_DE_PAGAMENTO_GAIA_R$<valor>');assert.equal(catalog.rules.find(r=>r.rule_id==='NOM-033').approved_pattern,'CNH.pdf');assert.equal(catalog.rules.find(r=>r.rule_id==='NOM-034').approved_pattern,'PROCURACAO_PARTICULAR_assinado.pdf')});
test('28 preserve accented basename and compound extension literally',()=>{let x=c();x.file.name='Declaração Técnica revisada.PDF';x.nom.sanitizedBasename=x.file.name;assert.equal(gate.candidate(x).proposedName,'009_Declaração Técnica revisada.PDF')});
test('29 preserve filename without extension when no NOM',()=>{let x=c();x.file.name='ATESTADO OFICIAL';x.nom.sanitizedBasename=x.file.name;assert.equal(gate.candidate(x).proposedName,'009_ATESTADO OFICIAL')});
test('30 support 011 client only with verified 011 identity',()=>{let x=c();x.client={id:'011',rootId:'CLIENT011',indexId:'011',manifestId:'011',indexRootId:'CLIENT011',manifestRootId:'CLIENT011',indexVerified:true,manifestVerified:true};x.destination.ancestorIds=['CLIENT011','PROC'];assert.equal(gate.candidate(x).proposedName,'011_auto de embargo.pdf')});
test('31 missing documentary affiliation blocks',()=>{let x=c();x.affiliationVerified=false;assert.equal(why(x),'DOCUMENT_EVIDENCE_MISSING')});
