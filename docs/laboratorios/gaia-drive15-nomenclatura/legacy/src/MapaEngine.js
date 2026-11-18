/**
 * MapaEngine — MAPA_BANCO_DE_DADOS (4 áreas: arquivos, entidades, pastas, movimentos).
 * Núcleo puro e idempotente. Identidade: file_id (arquivos/movimentos), folder_id (pastas).
 * Persistência (JSON no Drive) fica em MapaStore (funções Drive no fim; não testadas por node).
 */

var MAPA_VOCAB = {
  status_leitura: ['MAPEADO', 'PARCIAL', 'OCR_NECESSARIO', 'ERRO', 'NAO_CLASSIFICADO'],
  estado_no_acervo: ['ATIVO', 'STAGED', 'MOVIDO'],
  pasta_status: ['NAO_INICIADA', 'PARCIAL', 'COMPLETA', 'DESATUALIZADA'],
  entidade_tipo: ['pessoa', 'empresa', 'imovel', 'processo']
};

function _cloneM(o) { return JSON.parse(JSON.stringify(o)); }
function _failM(errors) { return { ok: false, errors: errors }; }

function createMapa(nowIso) {
  return {
    schema: 'gaia-mapa-banco/1.0',
    generated_at: nowIso || null,
    updated_at: nowIso || null,
    arquivos: [],
    entidades: [],
    pastas: [],
    movimentos: []
  };
}

function newArquivo() {
  return {
    file_id: null, parent_folder_id: null, caminho_snapshot: null, nome_arquivo: null,
    mime: null, tamanho: null, modified_time_origem: null, status_leitura: 'NAO_CLASSIFICADO',
    metodo_leitura: null, tipo_documental: null, resumo_curto: null, entidades_chave: [],
    paginas_regioes_lidas: [], uso_ocr_visao: false, data_leitura: null,
    confianca_pertencimento: null, confianca_conteudo: null, observacoes: null,
    estado_no_acervo: 'ATIVO', dados_staging: null
  };
}
function newPasta() {
  return {
    folder_id: null, parent: null, caminho_snapshot: null, nome: null, ultimo_inventario: null,
    quantidade_observada: null, arquivos_mapeados: null, pendentes: null, status: 'NAO_INICIADA', observacoes: null
  };
}
function newEntidade() {
  return { file_id: null, tipo: null, papel_no_documento: null, identificadores: [], contexto: null, confianca: null, validacao_humana: false, observacoes: null };
}
function newMovimento() {
  return {
    movimento_id: null, file_id: null, nome_original: null, origem_anterior_ao_staging: null,
    origem_parent_path: null, staging_folder_key: null, entrada_em_staging: null, cliente: null,
    destino_final: null, nome_final: null, autorizacao_operador: null, data_movimento: null,
    status: null, manifesto_relacionado: null, workflow_checkpoint_relacionado: null, observacoes: null
  };
}

function _idx(arr, key, val) { for (var i = 0; i < arr.length; i++) if (arr[i][key] === val) return i; return -1; }

/** Upsert de arquivo por file_id (idempotente: cria ou mescla). */
function upsertArquivo(mapa, rec, nowIso) {
  if (!rec || !rec.file_id) return _failM(['arquivo sem file_id']);
  if (rec.status_leitura && MAPA_VOCAB.status_leitura.indexOf(rec.status_leitura) === -1) return _failM(['status_leitura inválido: ' + rec.status_leitura]);
  if (rec.estado_no_acervo && MAPA_VOCAB.estado_no_acervo.indexOf(rec.estado_no_acervo) === -1) return _failM(['estado_no_acervo inválido: ' + rec.estado_no_acervo]);
  var m = _cloneM(mapa);
  var i = _idx(m.arquivos, 'file_id', rec.file_id);
  if (i === -1) { var base = newArquivo(); for (var k in rec) base[k] = rec[k]; m.arquivos.push(base); }
  else { for (var k2 in rec) m.arquivos[i][k2] = rec[k2]; }
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, mapa: m };
}

/** Upsert de pasta por folder_id. */
function upsertPasta(mapa, rec, nowIso) {
  if (!rec || !rec.folder_id) return _failM(['pasta sem folder_id']);
  if (rec.status && MAPA_VOCAB.pasta_status.indexOf(rec.status) === -1) return _failM(['status de pasta inválido: ' + rec.status]);
  var m = _cloneM(mapa);
  var i = _idx(m.pastas, 'folder_id', rec.folder_id);
  if (i === -1) { var base = newPasta(); for (var k in rec) base[k] = rec[k]; m.pastas.push(base); }
  else { for (var k2 in rec) m.pastas[i][k2] = rec[k2]; }
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, mapa: m };
}

/** Adiciona entidade (evita duplicar file_id+tipo+1º identificador). */
function addEntidade(mapa, rec, nowIso) {
  if (!rec || !rec.file_id) return _failM(['entidade sem file_id']);
  if (!rec.tipo || MAPA_VOCAB.entidade_tipo.indexOf(rec.tipo) === -1) return _failM(['tipo de entidade inválido: ' + rec.tipo]);
  var m = _cloneM(mapa);
  var id0 = (rec.identificadores && rec.identificadores[0]) || null;
  var dup = m.entidades.some(function (e) { return e.file_id === rec.file_id && e.tipo === rec.tipo && ((e.identificadores && e.identificadores[0]) || null) === id0; });
  if (!dup) { var base = newEntidade(); for (var k in rec) base[k] = rec[k]; m.entidades.push(base); }
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, mapa: m, duplicate: dup };
}

/** Marca arquivo como STAGED (idempotente). */
function markStaged(mapa, fileId, dadosStaging, nowIso) {
  var i = _idx(mapa.arquivos, 'file_id', fileId);
  if (i === -1) return _failM(['arquivo não mapeado: ' + fileId]);
  var m = _cloneM(mapa);
  m.arquivos[i].estado_no_acervo = 'STAGED';
  if (dadosStaging !== undefined) m.arquivos[i].dados_staging = dadosStaging;
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, mapa: m };
}

/** Registra movimento (ledger append-only, idempotente por movimento_id). */
function recordMovimento(mapa, rec, nowIso) {
  if (!rec || !rec.file_id) return _failM(['movimento sem file_id']);
  var m = _cloneM(mapa);
  if (rec.movimento_id) {
    var exists = m.movimentos.some(function (x) { return x.movimento_id === rec.movimento_id; });
    if (exists) return { ok: true, mapa: m, duplicate: true }; // idempotente
  }
  var base = newMovimento(); for (var k in rec) base[k] = rec[k];
  m.movimentos.push(base);
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, mapa: m, duplicate: false };
}

/** Índice file_id → registro (mesmos objetos do MAPA; alterar o registro altera o MAPA). */
function mapaIndex(mapa) {
  var idx = {};
  (mapa.arquivos || []).forEach(function (a) { if (a.file_id) idx[a.file_id] = a; });
  return idx;
}

function findArquivo(mapa, fileId) { var i = _idx(mapa.arquivos, 'file_id', fileId); return i === -1 ? null : mapa.arquivos[i]; }

/** Decide se um arquivo precisa de (re)leitura: ausente, ou não suficientemente conhecido,
 *  ou com modified_time_origem diferente do último conhecido. (fail-open p/ leitura) */
function needsRead(mapa, fileId, modifiedTimeAtual) {
  var a = findArquivo(mapa, fileId);
  if (!a) return true;
  if (['MAPEADO', 'PARCIAL'].indexOf(a.status_leitura) === -1) return true;
  if (modifiedTimeAtual && a.modified_time_origem && modifiedTimeAtual !== a.modified_time_origem) return true;
  return false;
}

/** Validação estrutural + vocabulários. */
function validateMapa(mapa) {
  var errors = [];
  ['arquivos', 'entidades', 'pastas', 'movimentos'].forEach(function (k) { if (!Array.isArray(mapa[k])) errors.push('área ausente/!array: ' + k); });
  (mapa.arquivos || []).forEach(function (a, i) {
    if (!a.file_id) errors.push('arquivos[' + i + '] sem file_id');
    if (MAPA_VOCAB.status_leitura.indexOf(a.status_leitura) === -1) errors.push('arquivos[' + i + '] status_leitura inválido');
    if (MAPA_VOCAB.estado_no_acervo.indexOf(a.estado_no_acervo) === -1) errors.push('arquivos[' + i + '] estado_no_acervo inválido');
  });
  (mapa.pastas || []).forEach(function (p, i) { if (!p.folder_id) errors.push('pastas[' + i + '] sem folder_id'); if (MAPA_VOCAB.pasta_status.indexOf(p.status) === -1) errors.push('pastas[' + i + '] status inválido'); });
  (mapa.entidades || []).forEach(function (e, i) { if (!e.file_id) errors.push('entidades[' + i + '] sem file_id'); if (MAPA_VOCAB.entidade_tipo.indexOf(e.tipo) === -1) errors.push('entidades[' + i + '] tipo inválido'); });
  (mapa.movimentos || []).forEach(function (mv, i) { if (!mv.file_id) errors.push('movimentos[' + i + '] sem file_id'); });
  return errors.length ? _failM(errors) : { ok: true, errors: [] };
}

/* ---- MapaStore: persistência JSON no Drive (Advanced Drive v3). Não testado por node. ---- */
function mapaReadFromDrive(fileId) { return JSON.parse(driveGetText(fileId)); }
function mapaWriteToDrive(fileId, mapa) {
  // compacto: o MAPA é regravado a cada movimento e cresce com o acervo
  DriveApp.getFileById(fileId).setContent(JSON.stringify(mapa));
  return { id: fileId };
}
function mapaCreateFileInDrive(parentFolderId, nowIso) {
  var f = DriveApp.getFolderById(parentFolderId).createFile('MAPA_BANCO_DE_DADOS.json', JSON.stringify(createMapa(nowIso), null, 2), 'application/json');
  return { id: f.getId(), name: f.getName() };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    MAPA_VOCAB: MAPA_VOCAB, createMapa: createMapa, newArquivo: newArquivo, newPasta: newPasta,
    newEntidade: newEntidade, newMovimento: newMovimento, upsertArquivo: upsertArquivo, upsertPasta: upsertPasta,
    addEntidade: addEntidade, markStaged: markStaged, recordMovimento: recordMovimento,
    findArquivo: findArquivo, needsRead: needsRead, validateMapa: validateMapa, mapaIndex: mapaIndex
  };
}
