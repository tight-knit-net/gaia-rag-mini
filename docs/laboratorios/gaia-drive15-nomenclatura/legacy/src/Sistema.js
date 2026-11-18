/**
 * Sistema — pastas técnicas em 4– BANCO DE DADOS/_SISTEMA (cache de OCR, logs,
 * índice de clientes) e a pasta de registro append-only do aprendizado.
 * IDs ficam guardados em ScriptProperties para não procurar toda vez.
 */

var SYS_PROP = 'GAIA_SISTEMA_IDS';
var _sysIdsExec = null; // conferido uma vez por execução (evita uma consulta ao Drive a cada OCR/log)

function sysFolders() {
  if (_sysIdsExec) return _sysIdsExec;
  var props = PropertiesService.getScriptProperties();
  var cached = null;
  try { cached = JSON.parse(props.getProperty(SYS_PROP) || 'null'); } catch (e) { cached = null; }
  if (cached && cached.root && dsIsLiveFolder(cached.root) && cached.ocr && cached.tmp && cached.logs && cached.chatgpt) return (_sysIdsExec = cached);
  var root = ensureFolder(ROOTS.BANCO_DE_DADOS, SISTEMA_CFG.FOLDER).id;
  var ids = {
    root: root,
    ocr: ensureFolder(root, SISTEMA_CFG.OCR).id,
    tmp: ensureFolder(root, SISTEMA_CFG.TMP_OCR).id,
    logs: ensureFolder(root, SISTEMA_CFG.LOGS).id,
    chatgpt: ensureFolder(root, SISTEMA_CFG.REVISAO_CHATGPT).id
  };
  props.setProperty(SYS_PROP, JSON.stringify(ids));
  return (_sysIdsExec = ids);
}

/* ---------------- Índice de clientes ---------------- */

function sysLoadClientesIndex() {
  var f = dsFindByName(sysFolders().root, SISTEMA_CFG.CLIENTES_INDEX)[0];
  if (!f) return crEmptyIndex();
  try { var j = readJson(f.id); j.clientes = j.clientes || {}; j.vinculos = j.vinculos || {}; return j; }
  catch (e) { throw new Error('CLIENTES_INDEX.json ilegível: ' + e.message); }
}

function sysSaveClientesIndex(idx) {
  var root = sysFolders().root;
  var f = dsFindByName(root, SISTEMA_CFG.CLIENTES_INDEX)[0];
  if (f) writeJson(f.id, idx); else createJson(SISTEMA_CFG.CLIENTES_INDEX, root, idx);
}

/* ---------------- Cache de OCR ---------------- */

function sysOcrSave(existingRef, payload) {
  var content = JSON.stringify(payload);
  if (existingRef) {
    try { DriveApp.getFileById(existingRef).setContent(content); return existingRef; } catch (e) { /* recria abaixo */ }
  }
  return DriveApp.getFolderById(sysFolders().ocr).createFile(payload.file_id + '.json', content, 'application/json').getId();
}

function sysOcrLoad(ref) {
  if (!ref) return null;
  try { return readJson(ref); } catch (e) { return null; }
}

/* ---------------- Log persistido ---------------- */

function sysAppendRunLog(jobId, lines) {
  if (!lines || !lines.length) return;
  var name = 'RUN_' + jobId + '.log';
  var folder = sysFolders().logs;
  var text = lines.map(function (l) { return l.t + ' [' + l.n + '] ' + l.m; }).join('\n') + '\n';
  var f = dsFindByName(folder, name)[0];
  if (f) {
    var file = DriveApp.getFileById(f.id);
    var old = file.getBlob().getDataAsString();
    if (old.length > 400000) old = old.slice(old.length - 300000);
    file.setContent(old + text);
  } else {
    DriveApp.getFolderById(folder).createFile(name, text, 'text/plain');
  }
}

/* ---------------- Registro append-only do aprendizado ---------------- */

function sysKnowledgeDeltaFolder() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('GAIA_KNOWLEDGE_DELTA');
  if (id && dsIsLiveFolder(id)) return id;
  var cur = ROOTS.OFFICE_KNOWLEDGE;
  KNOWLEDGE_DELTA_PATH.forEach(function (n) { cur = ensureFolder(cur, n).id; });
  props.setProperty('GAIA_KNOWLEDGE_DELTA', cur);
  return cur;
}

function sysWriteKnowledgeDelta(entry) {
  var stamp = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyyMMdd-HHmmss');
  var name = 'DELTA_NOMENCLATURA__' + stamp + '__' + (entry.rule_id || 'SEM_REGRA') + '.json';
  return createJson(name, sysKnowledgeDeltaFolder(), entry).id;
}
