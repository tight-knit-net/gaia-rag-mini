'use strict';
const {DRIVE_ID,PATHS,TECHNICAL_IDS}=require('./config');
const folderMime='application/vnd.google-apps.folder';
const fail=(code,detail)=>Object.assign(new Error(code+(detail?': '+detail:'')),{code});

function normalizeItem(raw,parentId){
  if(!raw || typeof raw!=='object' || !raw.id || typeof (raw.name??raw.title)!=='string')
    throw fail('METADATA_INCOMPLETE','missing file id or name');
  const actualParents=raw.parents??raw.parent_ids??null;
  if(actualParents!==null && (!Array.isArray(actualParents)||!actualParents.includes(parentId)))
    throw fail('PARENT_MISMATCH',raw.id);
  const driveId=raw.driveId??raw.drive_id;
  if(driveId!==DRIVE_ID)throw fail('CROSS_DRIVE_REFERENCE',raw.id);
  const mimeType=raw.mimeType??raw.mime_type;
  if(!mimeType)throw fail('MIME_MISSING',raw.id);
  const id=String(raw.id);
  if(!/^[A-Za-z0-9_-]{8,150}$/.test(id))throw fail('INVALID_GOOGLE_ID');
  return Object.freeze({
    id, name:raw.name??raw.title, mimeType, parentId, driveId,
    parentVerified:actualParents!==null,
    version:raw.version==null?null:String(raw.version),
    md5Checksum:raw.md5Checksum??raw.md5_checksum??null,
    modifiedTime:raw.modifiedTime??raw.modified_time??null,
    folder:mimeType===folderMime
  });
}
function isTechnical(item){
  return TECHNICAL_IDS.has(item.id) ||
    (item.parentId===PATHS.triage &&
      /^(?:000_AI_RULES\.json|000_LEIA_PRIMEIRO_TRIAGEM\.md)$/.test(item.name));
}

/**
 * Recebe PÁGINAS JÁ LIDAS no Drive por conector somente-leitura.
 * Uma página = {parentId, driveId, complete, nextPageToken:null, items:[]}.
 * Para cada pasta de lote é obrigatório listar seus filhos; lacuna bloqueia o lote.
 * Nunca consulta uma API, inventa caminho ou altera um arquivo.
 */
function inventoryFromReadOnlyPages({batchId,pages,scopeIds}={}){
  if(!batchId || !/^[A-Za-z0-9_-]{3,100}$/.test(batchId))throw fail('INVALID_BATCH_ID');
  if(!Array.isArray(scopeIds)||!scopeIds.length||!Array.isArray(pages))throw fail('SCOPE_MISSING');
  const pagesByParent=new Map();
  for(const p of pages){
    if(!p||p.driveId!==DRIVE_ID)throw fail('CROSS_DRIVE_PAGE');
    if(pagesByParent.has(p.parentId))throw fail('DUPLICATE_PAGE',p.parentId);
    // Não confundir truncamento do conector com ausência de itens.
    if(p.complete!==true||p.nextPageToken)throw fail('INVENTORY_INCOMPLETE',p.parentId);
    if(!Array.isArray(p.items))throw fail('PAGE_ITEMS_MISSING');
    pagesByParent.set(p.parentId,p.items.map(x=>normalizeItem(x,p.parentId)));
  }
  if(!pagesByParent.has(PATHS.triage))throw fail('TRIAGE_PAGE_MISSING');
  const entrants=pagesByParent.get(PATHS.triage).filter(x=>!isTechnical(x));
  const scopes=[...new Set(scopeIds)];
  for(const s of scopes)if(!entrants.some(x=>x.id===s))throw fail('OUTSIDE_TRIAGE_SCOPE',s);
  const accepted=[],visited=new Set(),stack=entrants.filter(x=>scopes.includes(x.id)).reverse();
  while(stack.length){
    const item=stack.pop();
    if(visited.has(item.id))throw fail('DUPLICATE_OR_CYCLE',item.id);
    visited.add(item.id);
    accepted.push(item);
    if(item.folder){
      if(!pagesByParent.has(item.id))throw fail('INVENTORY_INCOMPLETE',item.id);
      for(const child of [...pagesByParent.get(item.id)].reverse()){
        if(isTechnical(child))throw fail('TECHNICAL_CONTROL_IN_BATCH',child.id);
        stack.push(child);
      }
    }
  }
  // Proibido anexar ao inventário conteúdo de pastas fora do escopo.
  const allowedParents=new Set([PATHS.triage,...accepted.filter(x=>x.folder).map(x=>x.id)]);
  for(const id of pagesByParent.keys())if(!allowedParents.has(id))throw fail('PAGE_OUT_OF_SCOPE',id);
  return Object.freeze({
    schema:'gaia.drive1.inventory.v1',
    batchId,driveId:DRIVE_ID,
    scopeIds:scopes,
    complete:true,
    items:accepted,
    counts:{total:accepted.length,files:accepted.filter(x=>!x.folder).length,folders:accepted.filter(x=>x.folder).length},
    state:'INVENTORY_COMPLETE',
    source:'GOOGLE_DRIVE_READ_ONLY_SNAPSHOT',
    execution_attempted:false
  });
}
module.exports={inventoryFromReadOnlyPages,normalizeItem,isTechnical,fail};
