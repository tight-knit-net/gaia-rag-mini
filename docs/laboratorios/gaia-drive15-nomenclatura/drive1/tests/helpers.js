'use strict';
const {DRIVE_ID,PATHS}=require('../config');
const FOLDER='application/vnd.google-apps.folder';
const root='synthetic_batch_a01';
const sub='synthetic_subdir_a';
const first='synthetic_document_a01';
const second='synthetic_document_b02';
const dest='synthetic_destination_a';
const client='synthetic_clientfolder';
function item(id,parent,name,mime='application/pdf',version='1',extra={}){
  return {id,name,mimeType:mime,parents:[parent],driveId:DRIVE_ID,version,...extra};
}
function page(parentId,items,extra={}){
  return {parentId,driveId:DRIVE_ID,complete:true,nextPageToken:null,items,...extra};
}
function pages(){
  return [
    page(PATHS.triage,[
      item(PATHS.topology,PATHS.triage,'000_TOPOLOGIA_E_RASTREABILIDADE',FOLDER),
      item(PATHS.ocr,PATHS.triage,'000_LEITURA_OCR',FOLDER),
      item(PATHS.quarantine,PATHS.triage,'000_QUARENTENA',FOLDER),
      item(root,PATHS.triage,'LOTE FICTICIO',FOLDER)
    ]),
    page(root,[
      item(first,root,'arquivo antigo 1.pdf'),
      item(sub,root,'subpasta fictícia',FOLDER)
    ]),
    page(sub,[item(second,sub,'arquivo antigo 2.pdf')])
  ];
}
function proof(){
  return {clientId:'027',driveId:DRIVE_ID,clientFolderId:client,
    indexVerified:true,manifestVerified:true,indexFileId:PATHS.clientIndex,
    manifestFileId:'synthetic_manifest_id',manifestVersion:'9'};
}
function classify(domain='IMOVEL'){
  return {domain,belongingVerified:true,thirdParty:false,
    evidence:[{sourceId:'synthetic_proof_001',locator:'p. 2, campo identificador',verified:true}]};
}
function nom(){
  return {ruleId:'NOM-001',sourceRechecked:true,provided:{DATA:'03-08-2026'},
    evidence:[{sourceId:'synthetic_proof_002',locator:'p. 1, data de emissão',verified:true}]};
}
function topology(){
  return {destinationParentId:dest,destinationDriveId:DRIVE_ID,
    destinationAncestors:[client,dest],destinationVerified:true,processVerified:true};
}
module.exports={DRIVE_ID,PATHS,root,sub,first,second,dest,client,pages,page,item,proof,classify,nom,topology,FOLDER};
