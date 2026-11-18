'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {fingerprint,asPage,asInventoryItem}=require('../snapshot');
const {DRIVE_ID,PATHS}=require('../../drive1/config');
const ref={
 id:'synthetic_connector_file_01',title:'PROTOCOLO.pdf',mime_type:'application/pdf',
 drive_id:DRIVE_ID,parent_ids:[PATHS.triage],
 size:'1016',modified_time:'2026-11-18T09:00:00Z'
};
test('Google connector metadata yields stable OBS fingerprint not native version',()=>{
 const a=asInventoryItem(ref,PATHS.triage);
 const b=asInventoryItem({...ref},PATHS.triage);
 assert.equal(a.version,b.version);
 assert.ok(a.version.startsWith('OBS_'));
 assert.equal(a.versionBasis,'OBSERVED_METADATA_FINGERPRINT_NOT_GOOGLE_VERSION');
 assert.equal(a.parents[0],PATHS.triage);
});
test('readback detects source metadata drift',()=>{
 const a=fingerprint(ref,PATHS.triage);
 const b=fingerprint({...ref,modified_time:'2026-11-18T09:30:00Z'},PATHS.triage);
 assert.notEqual(a,b);
});
test('cross-drive and wrong parent are blocked',()=>{
 assert.throws(()=>asInventoryItem({...ref,drive_id:'some_other_drive'},PATHS.triage),/CROSS_DRIVE/);
 assert.throws(()=>asInventoryItem({...ref,parent_ids:['other_parent']},PATHS.triage),/GOOGLE_PARENT_NOT_CONFIRMED/);
});
test('a full page exactly at limit cannot be certified complete',()=>{
 const entries=Array.from({length:100},(_,i)=>({...ref,id:'synthetic_connector_file_'+String(i+1)}));
 assert.throws(()=>asPage(PATHS.triage,entries,{maxRequested:100}),/PAGINATION_UNVERIFIED/);
});
test('valid observed page is consumable as Drive1 inventory page',()=>{
 const page=asPage(PATHS.triage,[ref]);
 assert.equal(page.complete,true);
 assert.equal(page.items.length,1);
});
