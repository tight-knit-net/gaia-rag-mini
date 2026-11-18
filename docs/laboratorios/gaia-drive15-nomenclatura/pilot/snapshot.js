'use strict';
/** Native Google Drive connector metadata -> synthetic revision fence for PREVIEW.
 * Google native connector does not currently expose Drive API version.
 * This hash is NOT a provider version or transactional ETag.
 */
const crypto=require('crypto');
const {DRIVE_ID,PATHS}=require('../drive1/config');
function fingerprint(m,parentId){
 const id=m.id,name=m.title||m.name,mime=m.mime_type||m.mimeType,
  modified=m.modified_time||m.modifiedTime,size=String(m.size??'');
 if(!id||!name||!mime||!modified||!parentId||m.drive_id!==DRIVE_ID)
  throw Error('SOURCE_METADATA_INCOMPLETE');
 const digest=crypto.createHash('sha256').update([id,parentId,name,mime,size,modified].join('\n')).digest('hex');
 return 'OBS_'+digest.slice(0,32);
}
function asInventoryItem(meta,parentId){
 if(!Array.isArray(meta.parent_ids)||!meta.parent_ids.includes(parentId))
  throw Error('GOOGLE_PARENT_NOT_CONFIRMED');
 if(meta.drive_id!==DRIVE_ID)throw Error('CROSS_DRIVE');
 return {
  id:meta.id,name:meta.title,mimeType:meta.mime_type,
  parents:[parentId],driveId:DRIVE_ID,
  version:fingerprint(meta,parentId),
  versionBasis:'OBSERVED_METADATA_FINGERPRINT_NOT_GOOGLE_VERSION',
  modifiedTime:meta.modified_time,size:meta.size
 };
}
function asPage(parentId,metaItems,{maxRequested=100}={}){
 if(!Array.isArray(metaItems)||metaItems.length>=maxRequested)
  throw Error('PAGINATION_UNVERIFIED');
 return {
  parentId,driveId:DRIVE_ID,complete:true,nextPageToken:null,
  items:metaItems.map(x=>asInventoryItem(x,parentId)),
  revisionBasis:'OBSERVED_METADATA_FINGERPRINT_NOT_GOOGLE_VERSION'
 };
}
module.exports={fingerprint,asInventoryItem,asPage};
