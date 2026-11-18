/**
 * DriveService — camada única que fala com o Google Drive (Advanced Drive v3).
 *
 * Regras honradas:
 *  - MOVE ONLY: mover NUNCA faz COPY como fallback (falha preserva origem e vira bloqueio).
 *  - file_id/folder_id são a identidade; nome/caminho são snapshots.
 *  - Usa appProperties para amarrar metadados próprios (file_id/vínculos) quando útil.
 *
 * Requer o Advanced Drive Service habilitado (appsscript.json: Drive v3).
 * A maior parte só roda no Apps Script (não no node). Helpers puros ficam ao fim e são testáveis.
 */

var DRIVE_OPTS_ALL = { supportsAllDrives: true, includeItemsFromAllDrives: true };

function nowIso() { return new Date().toISOString(); }

/** Baixa o conteúdo textual de um arquivo do Drive (funciona em Drive Compartilhado). */
function driveGetText(fileId) {
  return DriveApp.getFileById(fileId).getBlob().getDataAsString();
}

/** Lê e faz parse de um JSON do Drive. */
function readJson(fileId) {
  return JSON.parse(driveGetText(fileId));
}

/** Sobrescreve o conteúdo de um arquivo JSON existente (mantém o file_id). Via DriveApp (confiável em Shared Drive). */
function writeJson(fileId, obj) {
  DriveApp.getFileById(fileId).setContent(JSON.stringify(obj, null, 2));
  return { id: fileId };
}

function _ppIso(d) { try { return d ? d.toISOString() : null; } catch (e) { return null; } }
function _ppSize(f) { try { return String(f.getSize()); } catch (e) { return null; } }

/** Cria um novo arquivo JSON dentro de parentId. Retorna metadados (id, name). */
function createJson(name, parentId, obj) {
  var f = DriveApp.getFolderById(parentId).createFile(name, JSON.stringify(obj, null, 2), 'application/json');
  return { id: f.getId(), name: f.getName() };
}

/** Metadados de um arquivo/pasta. */
function getMeta(fileId, fields) {
  var opts = { fields: fields || 'id,name,parents,mimeType,modifiedTime,size,appProperties' };
  for (var k in DRIVE_OPTS_ALL) opts[k] = DRIVE_OPTS_ALL[k];
  return Drive.Files.get(fileId, opts);
}

/** Lista filhos de uma pasta (com paginação). Retorna array de {id,name,mimeType,modifiedTime,size}. */
function listChildren(folderId, mimeType) {
  var folder = DriveApp.getFolderById(folderId);
  var out = [];
  var itF = folder.getFolders();
  while (itF.hasNext()) { var d = itF.next(); out.push({ id: d.getId(), name: d.getName(), mimeType: 'application/vnd.google-apps.folder', modifiedTime: _ppIso(d.getLastUpdated()), size: null }); }
  var itFi = folder.getFiles();
  while (itFi.hasNext()) { var f = itFi.next(); out.push({ id: f.getId(), name: f.getName(), mimeType: f.getMimeType(), modifiedTime: _ppIso(f.getLastUpdated()), size: _ppSize(f) }); }
  if (mimeType) out = out.filter(function (o) { return o.mimeType === mimeType; });
  return out;
}

/**
 * MOVE ONLY: move o arquivo para newParentId removendo oldParentId.
 * Se oldParentId não for informado, descobre pelos parents atuais.
 * NUNCA copia. Falha lança erro (o chamador registra bloqueio e preserva origem).
 */
function moveFileOnly(fileId, newParentId, oldParentId) {
  if (!oldParentId) {
    var meta = getMeta(fileId, 'id,parents');
    oldParentId = (meta.parents && meta.parents[0]) || null;
  }
  var opts = { addParents: newParentId, removeParents: oldParentId || undefined, fields: 'id,parents,name' };
  for (var k in DRIVE_OPTS_ALL) opts[k] = DRIVE_OPTS_ALL[k];
  var res = Drive.Files.update({}, fileId, null, opts);
  // verificação: destino presente e origem removida
  var parents = res.parents || [];
  if (parents.indexOf(newParentId) === -1) throw new Error('MOVE_FALHOU: destino não confirmado para ' + fileId);
  return res;
}

/** Renomeia (não move). */
function renameFile(fileId, newName) {
  var opts = { fields: 'id,name' };
  for (var k in DRIVE_OPTS_ALL) opts[k] = DRIVE_OPTS_ALL[k];
  return Drive.Files.update({ name: newName }, fileId, null, opts);
}

/** Lê/grava appProperties (metadados próprios do script no arquivo). */
function getAppProperties(fileId) { var m = getMeta(fileId, 'id,appProperties'); return m.appProperties || {}; }
function setAppProperties(fileId, props) {
  var opts = { fields: 'id,appProperties' };
  for (var k in DRIVE_OPTS_ALL) opts[k] = DRIVE_OPTS_ALL[k];
  return Drive.Files.update({ appProperties: props }, fileId, null, opts);
}

/** Acha uma subpasta por nome dentro de parentId (ou null). */
function findFolder(parentId, name) {
  var it = DriveApp.getFolderById(parentId).getFoldersByName(name);
  if (it.hasNext()) { var d = it.next(); return { id: d.getId(), name: d.getName() }; }
  return null;
}

/** Acha ou cria uma subpasta (idempotente por nome). */
function ensureFolder(parentId, name) {
  var f = findFolder(parentId, name);
  if (f) return f;
  var d = DriveApp.getFolderById(parentId).createFolder(name);
  return { id: d.getId(), name: d.getName() };
}

/* ---------------- Listagem sem itens na lixeira ---------------- */

function _dsIter(folder, kind) {
  try { return kind === 'folders' ? folder.searchFolders('trashed = false') : folder.searchFiles('trashed = false'); }
  catch (e) { return kind === 'folders' ? folder.getFolders() : folder.getFiles(); }
}

/** Subpastas (não excluídas) de folderId: [{id, name}]. */
function dsListFolders(folderId) {
  var it = _dsIter(DriveApp.getFolderById(folderId), 'folders'), out = [];
  while (it.hasNext()) { var d = it.next(); if (!d.isTrashed()) out.push({ id: d.getId(), name: d.getName() }); }
  return out;
}

/** Arquivos (não excluídos) de folderId: [{id, name, mimeType, size, modifiedTime}]. */
function dsListFiles(folderId) {
  var it = _dsIter(DriveApp.getFolderById(folderId), 'files'), out = [];
  while (it.hasNext()) {
    var f = it.next();
    out.push({ id: f.getId(), name: f.getName(), mimeType: f.getMimeType(), size: _ppSize(f), modifiedTime: _ppIso(f.getLastUpdated()) });
  }
  return out;
}

function dsIsLiveFolder(id) {
  try { return !DriveApp.getFolderById(id).isTrashed(); } catch (e) { return false; }
}

/** Metadados completos (inclui md5Checksum, parents, trashed). */
function dsMeta(fileId) {
  return getMeta(fileId, 'id,name,mimeType,parents,trashed,size,md5Checksum,modifiedTime');
}

/** MOVE ONLY + renomeia numa única chamada; confere o destino. Nunca copia. */
function dsMoveRename(fileId, newName, newParentId, oldParentId) {
  var opts = { addParents: newParentId, removeParents: oldParentId, fields: 'id,name,parents' };
  for (var k in DRIVE_OPTS_ALL) opts[k] = DRIVE_OPTS_ALL[k];
  var res = Drive.Files.update(newName ? { name: newName } : {}, fileId, null, opts);
  var parents = res.parents || [];
  if (parents.indexOf(newParentId) === -1 || parents.indexOf(oldParentId) !== -1) throw new Error('MOVE_NAO_CONFIRMADO: ' + fileId);
  return res;
}

/** Arquivo com esse nome exato já existe na pasta? Devolve [{id}] (sem itens na lixeira). */
function dsFindByName(folderId, name) {
  var it = DriveApp.getFolderById(folderId).getFilesByName(name), out = [];
  while (it.hasNext()) { var f = it.next(); if (!f.isTrashed()) out.push({ id: f.getId(), name: f.getName() }); }
  return out;
}

/* ---------------- Helpers puros (testáveis em node) ---------------- */

/** Escapa valor para a query do Drive (aspas simples). */
function quoteQ(v) { return "'" + String(v).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'"; }

/** Monta a query de filhos de uma pasta (opcionalmente por mimeType). */
function buildChildrenQuery(folderId, mimeType) {
  var q = quoteQ(folderId) + ' in parents and trashed=false';
  if (mimeType) q += ' and mimeType=' + quoteQ(mimeType);
  return q;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { quoteQ: quoteQ, buildChildrenQuery: buildChildrenQuery, nowIso: nowIso };
}
