/**
 * Main — pontos de entrada para rodar no editor do Apps Script (após autorizar).
 * Provam: (1) acesso real ao Drive via Advanced Drive v3; (2) a lógica rodando no Google.
 *
 * Como usar: abra o projeto no editor, selecione a função e clique em Executar.
 * Na primeira execução o Google pede autorização (escopo Drive) — é esperado.
 */

/**
 * (0) AUTORIZAR — rode esta função UMA vez no editor depois de cada atualização que
 * pedir novas permissões (Drive, Documentos e Document AI para o OCR, cache/travas). Só lê.
 */
function autorizar() {
  // Pede de novo qualquer permissão que falte (o Google deixa marcar/desmarcar cada uma).
  ScriptApp.requireAllScopes(ScriptApp.AuthMode.FULL);
  // Teste real do Google Docs (usado pelo OCR): abre um README do acervo só para ler o nome.
  var docTeste = 'nenhum Google Doc no acervo para testar';
  var itDoc = DriveApp.getFolderById(ROOTS.BANCO_DE_DADOS).getFilesByType(MimeType.GOOGLE_DOCS);
  if (itDoc.hasNext()) docTeste = 'OK — abriu "' + DocumentApp.openById(itDoc.next().getId()).getName() + '"';
  var r = {
    acervo: DriveApp.getFolderById(ROOTS.BANCO_DE_DADOS).getName(),
    clientes: DriveApp.getFolderById(ROOTS.CLIENTES).getName(),
    novas_regras: DriveApp.getFolderById(NOMENCLATURA.NOVAS_REGRAS_FOLDER).getName(),
    office_knowledge: DriveApp.getFolderById(ROOTS.OFFICE_KNOWLEDGE).getName(),
    drive_api_v3: getMeta(ROOTS.BANCO_DE_DADOS, 'id,name').name,
    documentos_ocr: docTeste,
    document_ai: ocrDocAiStatus(),
    cache: !!CacheService.getScriptCache(),
    trava: !!LockService.getScriptLock(),
    execucao_atual: jbGet()
  };
  Logger.log(JSON.stringify(r, null, 2));
  return r;
}

/** Diagnóstico: lê o texto de UM arquivo (não altera o MAPA). Ex.: testarOcr('ID_DO_ARQUIVO') */
function testarOcr(fileId) {
  var m = dsMeta(fileId);
  var res = ocrReadText(fileId, m.mimeType);
  Logger.log('%s (%s) → %s, %s caracteres', m.name, m.mimeType, res.method, (res.text || '').length);
  Logger.log(res.ok ? res.text.slice(0, 1500) : ('ERRO: ' + res.erro));
  return { nome: m.name, metodo: res.method, ok: res.ok, caracteres: (res.text || '').length, erro: res.erro || null };
}

/** (1) Prova de acesso ao Drive: lê metadados da pasta de Nomenclatura e lista o conteúdo. */
function test_driveAcesso() {
  var folder = getMeta(NOMENCLATURA.FOLDER, 'id,name,mimeType');
  Logger.log('Pasta: %s (%s)', folder.name, folder.id);
  var filhos = listChildren(NOMENCLATURA.FOLDER);
  Logger.log('Itens na 02_NOMENCLATURA: %s', filhos.length);
  filhos.forEach(function (f) { Logger.log(' - %s [%s]', f.name, f.id); });
  return { ok: true, folder: folder.name, count: filhos.length };
}

/** (2) Prova da lógica no Google: nomeia alguns exemplos usando as 56 regras embutidas. */
function test_nomear() {
  var exemplos = [
    { rule_id: 'NOM-001', provided: { DATA: '03-08-2026' }, clientNNN: '27' },
    { rule_id: 'NOM-018', rawFields: { inscricao_imobiliaria_completa: '24.56.060.0600.006.157' }, clientNNN: '27' },
    { signals: ['DOCUMENTO BASICO DE ENTRADA DO CNPJ', 'PROTOCOLO REDESIM'], provided: { PROTOCOLO_REDESIM: 'REDE123' }, clientNNN: '27' },
    { signals: ['documento estranho'], clientNNN: '27' }
  ];
  exemplos.forEach(function (inp) {
    var r = resolveNome(NOMENCLATURE_RULES, inp);
    Logger.log('%s -> %s', JSON.stringify(inp), JSON.stringify(r));
  });
  return { ok: true, total_regras: NOMENCLATURE_RULES.length };
}

/** (3) Implanta o MAPA_BANCO_DE_DADOS.json na raiz do Banco (se ainda não existir). */
function implantarMapa() {
  var existente = findChildByName(BANCO.ROOT_FOLDER, 'MAPA_BANCO_DE_DADOS.json');
  if (existente) { Logger.log('MAPA já existe: %s', existente.id); return { ok: true, already: true, id: existente.id }; }
  var created = createJson('MAPA_BANCO_DE_DADOS.json', BANCO.ROOT_FOLDER, createMapa(nowIso()));
  Logger.log('MAPA criado: %s', created.id);
  return { ok: true, created: true, id: created.id };
}

/** (4) Sobe as 56 regras normalizadas para a pasta de Nomenclatura (fonte de verdade no Drive). */
function implantarRegrasNoDrive() {
  var existente = findChildByName(NOMENCLATURA.FOLDER, 'nomenclature_rules.normalized.json');
  var doc = { schema: 'gaia-nomenclature-normalized/1.0', rule_count: NOMENCLATURE_RULES.length, rules: NOMENCLATURE_RULES };
  if (existente) { writeJson(existente.id, doc); Logger.log('Regras atualizadas: %s', existente.id); return { ok: true, updated: true, id: existente.id }; }
  var created = createJson('nomenclature_rules.normalized.json', NOMENCLATURA.FOLDER, doc);
  Logger.log('Regras criadas no Drive: %s', created.id);
  return { ok: true, created: true, id: created.id };
}

/**
 * (5) TESTE SEGURO (só leitura): pergunta ao próprio Google se dá para MOVER a
 * pasta Porto 45 para fora do Drive Compartilhado. NÃO move nada — só lê as
 * "capabilities" e o driveId. Rode e veja os Registros de execução.
 */
function test_capacidadeMoverPorto45() {
  var PORTO45_DRIVE11 = '10H8OsxKoZzlnrR7CLndLfgptfF1M_mjr'; // .../11/ONEDRIVE_PESSOAL/GAIA LICENCIAMENTO/1- CLIENTES ATIVOS/1 - CLIENTES 2025 B/PORTO 45
  return test_capacidadeMover(PORTO45_DRIVE11);
}

/** Versão genérica: checa capabilities de mover de qualquer item (arquivo/pasta). */
function test_capacidadeMover(fileId) {
  var m = Drive.Files.get(fileId, {
    fields: 'id,name,driveId,mimeType,capabilities(canEdit,canMoveItemWithinDrive,canMoveItemOutOfDrive,canMoveChildrenWithinDrive,canDelete),parents',
    supportsAllDrives: true
  });
  var cap = m.capabilities || {};
  Logger.log('Item: %s (%s)', m.name, m.id);
  Logger.log('driveId (Compartilhado se preenchido): %s', m.driveId || '(Meu Drive)');
  Logger.log('canMoveItemOutOfDrive (mover p/ FORA do compartilhado): %s', cap.canMoveItemOutOfDrive);
  Logger.log('canMoveItemWithinDrive (mover DENTRO do mesmo drive): %s', cap.canMoveItemWithinDrive);
  Logger.log('canEdit: %s | canDelete: %s', cap.canEdit, cap.canDelete);
  return { name: m.name, driveId: m.driveId || null, capabilities: cap };
}

/** Helper: acha filho por nome exato (arquivo ou pasta) dentro de parentId. Via DriveApp (Shared Drive). */
function findChildByName(parentId, name) {
  var folder = DriveApp.getFolderById(parentId);
  var fi = folder.getFilesByName(name);
  if (fi.hasNext()) { var f = fi.next(); return { id: f.getId(), name: f.getName() }; }
  var fo = folder.getFoldersByName(name);
  if (fo.hasNext()) { var d = fo.next(); return { id: d.getId(), name: d.getName() }; }
  return null;
}
