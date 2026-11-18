/**
 * Painel — Web App do Gaia Office. As funções painel*() são chamadas pela página
 * (PainelApp.html) via google.script.run e rodam no servidor com a conta do operador.
 *
 * Fluxo: Executar → etapas curtas com log ao vivo → reconhecidos vão sozinhos para
 * 1-CLIENTES → não reconhecidos ficam na aba Revisão → "Aprender e seguir".
 */

function doGet(e) {
  if (e && e.parameter && e.parameter.gaia_auth === '1') {
    var target = 'https://drive.gogetterhub.com/console/?gaia_auth=ok';
    var html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<title>Gaia Office — Autenticação</title></head><body style="font-family:Arial,sans-serif;background:#0f1720;color:#e8eef4;display:grid;place-items:center;min-height:100vh;margin:0">' +
      '<div style="text-align:center;padding:24px"><h2>Autenticação concluída</h2><p>Voltando para o Gaia Office…</p></div>' +
      '<script>(function(){var t=' + JSON.stringify(target) + ';try{if(window.opener&&!window.opener.closed){window.opener.postMessage({gaiaAuth:"ok"},"https://drive.gogetterhub.com");setTimeout(function(){window.close();},250);setTimeout(function(){location.replace(t);},1200);return;}}catch(e){}location.replace(t);}());<\/script>' +
      '</body></html>';
    return HtmlService.createHtmlOutput(html)
      .setTitle('Gaia Office — Autenticação')
      .setFaviconUrl('https://drive.gogetterhub.com/console/favicon-48.png')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
  }

  return HtmlService.createHtmlOutputFromFile('src/PainelApp')
    .setTitle('Gaia Office — Painel')
    .setFaviconUrl('https://drive.gogetterhub.com/console/favicon-48.png')
    // o app (drive.gogetterhub.com/console) mostra o painel por dentro; a página trava em qualquer outro site
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function _pWrap(fn) {
  try { return fn(); } catch (e) { return { ok: false, erro: String(e && e.message || e) }; }
}

function _pMapa() {
  var f = findChildByName(ROOTS.BANCO_DE_DADOS, 'MAPA_BANCO_DE_DADOS.json');
  return f ? mapaReadFromDrive(f.id) : createMapa(null);
}

/* ---------------- Execução ---------------- */

function painelIniciar(opts) { return _pWrap(function () { return jbStart(opts || {}); }); }
function painelTick() { return _pWrap(jbTick); }
function painelStatus(sinceSeq) { return _pWrap(function () { return jbStatus(sinceSeq); }); }
function painelParar() { return _pWrap(jbStop); }

/* ---------------- Resumo ---------------- */

function painelResumo() {
  return _pWrap(function () {
    var mapa = _pMapa();
    var idx = sysLoadClientesIndex();
    var pastas = plClientFolders().map(function (f) {
      var nnn = idx.vinculos[f.id] || null;
      return { id: f.id, nome: f.name, nnn: nnn, cliente: nnn && idx.clientes[nnn] ? idx.clientes[nnn].nome : null, etapas: plCountByEtapa(mapa, f.id) };
    });
    var clientes = Object.keys(idx.clientes).sort().map(function (n) {
      var c = idx.clientes[n];
      return { nnn: n, nome: c.nome, folder_id: c.folder_id, link: 'https://drive.google.com/drive/folders/' + c.folder_id };
    });
    return { ok: true, totais: plCountByEtapa(mapa), pastas: pastas, clientes: clientes, job: jbGet(), movimentos: (mapa.movimentos || []).length };
  });
}

/* ---------------- Revisão ---------------- */

function painelRevisaoLista() {
  return _pWrap(function () {
    var itens = (_pMapa().arquivos || []).filter(function (r) { return r.etapa === 'REVISAO'; }).map(function (r) {
      var s = (r.sugestoes || [])[0] || null;
      return {
        file_id: r.file_id, nome: r.nome_arquivo, cliente: r.acervo_cliente_nome, motivo: r.motivo_revisao,
        rule_id: r.rule_id || null, sugestao: s ? s.rule_id + ' — ' + s.document_type : null,
        externo: r.revisao_externa && r.revisao_externa.id ? r.revisao_externa.status : null
      };
    }).sort(function (a, b) { return String(a.cliente).localeCompare(String(b.cliente)) || String(a.nome).localeCompare(String(b.nome)); });
    return { ok: true, total: itens.length, itens: itens };
  });
}

function painelRevisaoDetalhe(fileId) { return _pWrap(function () { return lnDetalhe(fileId); }); }
function painelExtrair(fileId, ruleId) { return _pWrap(function () { return lnExtrair(fileId, ruleId); }); }
function painelPreviewPadrao(fileId, nome) { return _pWrap(function () { return lnPreview(fileId, nome); }); }
function painelAprender(payload) { return _pWrap(function () { return lnAprender(payload); }); }
function painelIgnorar(fileId) { return _pWrap(function () { return lnIgnorar(fileId); }); }
function painelReprocessar(fileId) { return _pWrap(function () { return lnReprocessar(fileId); }); }

/* Revisão com ChatGPT: o painel só gera o prompt e depois carrega o arquivo que o ChatGPT gravou. */
function painelChatgptPrompt(fileId, novo) { return _pWrap(function () { return rxGerarPrompt(fileId, !!novo); }); }
function painelChatgptCarregar(fileId) { return _pWrap(function () { return rxCarregar(fileId); }); }

/* Revisão EM LOTE: um .md por grupo, com o cabeçalho fixo uma vez só. */
function painelLoteGerar(opts) { return _pWrap(function () { return rxGerarPromptLote(opts || {}); }); }
function painelLoteCarregar(loteId) { return _pWrap(function () { return rxCarregarLote(loteId); }); }
function painelLoteLista() {
  return _pWrap(function () {
    var lotes = rxlListarLotes(_pMapa());
    return { ok: true, total: lotes.length, lotes: lotes };
  });
}
/* Aplicar o lote inteiro. Um item por chamada, porque cada lnAprender grava a
   regra, monta o pacote e ainda reconfere os outros arquivos da Revisão — 36
   numa execução só estouraria os 6 minutos. O painel chama em sequência. */
function painelLoteAplicaveis(loteId) { return _pWrap(function () { return rxAplicaveis(loteId); }); }
function painelLoteAplicarUm(loteId, fileId) { return _pWrap(function () { return rxAplicarUm(loteId, fileId); }); }

/** Conteúdo do .md do lote, para o botão "copiar" do painel. */
function painelLoteTexto(fileId) {
  return _pWrap(function () {
    if (!fileId) return { ok: false, erro: 'Arquivo do lote não informado.' };
    var meta = getMeta(fileId, 'id,name,parents,mimeType');
    if ((meta.parents || []).indexOf(sysFolders().chatgpt) === -1) {
      return { ok: false, erro: 'Segurança: só leio arquivos de _SISTEMA/REVISAO_CHATGPT.' };
    }
    return { ok: true, nome: meta.name, texto: DriveApp.getFileById(fileId).getBlob().getDataAsString() };
  });
}

/* ---------------- Aprovação (portão S6) ---------------- */

/** Pacotes esperando o OK do operador. Só leitura — não move nada. */
function painelPacotes() {
  return _pWrap(function () {
    var pacotes = apMontarPacotes(_pMapa());
    return {
      ok: true,
      portao_ligado: !!PIPELINE_CFG.EXIGIR_APROVACAO_HUMANA,
      total_pacotes: pacotes.length,
      total_itens: pacotes.reduce(function (n, p) { return n + p.total; }, 0),
      pacotes: pacotes
    };
  });
}

/** Autoriza UM pacote específico e executa os moves. É a única porta para 1-CLIENTES. */
function painelAprovarPacote(ref) {
  return _pWrap(function () {
    if (!ref) return { ok: false, erro: 'Referência do pacote ausente.' };
    return apAprovarPacote(ref);
  });
}

/** Devolve os itens do pacote para a Revisão. Nada é movido. */
function painelRejeitarPacote(ref, motivo) {
  return _pWrap(function () {
    if (!ref) return { ok: false, erro: 'Referência do pacote ausente.' };
    return apRejeitarPacote(ref, motivo || null);
  });
}

/* ---------------- Movimentação ---------------- */

function painelMovimentacao() {
  return _pWrap(function () {
    var itens = (_pMapa().arquivos || []).filter(function (r) {
      return r.etapa === 'MOVIDO' || r.etapa === 'DUPLICADO' || (r.etapa === 'PRONTO' && r.simulacao);
    }).map(function (r) {
      return {
        etapa: r.etapa, nome_original: r.nome_arquivo, nome_final: r.nome_final || (r.simulacao && r.simulacao.nome_final),
        destino: r.destino_caminho || (r.simulacao && r.simulacao.destino) ||
          (r.etapa === 'DUPLICADO' ? 'ficou no acervo (igual a um arquivo que já está no cliente)' : null), cliente_nnn: r.cliente_nnn,
        rule_id: r.rule_id, em: r.movido_em || (r.simulacao && r.simulacao.em) || null, file_id: r.file_id,
        link: 'https://drive.google.com/file/d/' + r.file_id + '/view'
      };
    }).sort(function (a, b) { return String(b.em).localeCompare(String(a.em)); });
    return { ok: true, total: itens.length, itens: itens.slice(0, 400) };
  });
}

/* ---------------- Nomenclatura e aprendizado ---------------- */

function painelRegras() {
  return _pWrap(function () {
    var docs = rsLoadDocs(), porId = {};
    docs.forEach(function (d) { porId[d.rule_id] = d; });
    var list = rsRuntimeRules().map(function (r) {
      var v = _lnRuleView(r), d = porId[r.rule_id] || null, ex = null;
      if (d && (d.exemplos || []).length) {
        var xs = (d.exemplos || []).slice().sort(function (a, b) { return String(a.em || '').localeCompare(String(b.em || '')); });
        var e = xs[xs.length - 1];
        ex = { file_id: e.file_id || null, nome: e.nome_anterior || null, cliente: e.cliente || null, em: e.em || null };
      }
      v.exemplo = ex;
      return v;
    });
    return { ok: true, total: list.length, regras: list };
  });
}

function painelAprendizado() { return _pWrap(lnAprendizado); }
function painelAprendizadoContexto(ruleId, em) { return _pWrap(function () { return lnAprendizadoContexto(ruleId, em); }); }
function painelCorrigirAprendizado(payload) { return _pWrap(function () { return lnCorrigir(payload); }); }

/* ============ IMPORTAÇÃO ASSISTIDA (Drive 11 → acervo Drive 15) ============ */

/** Lista as pastas de cliente dentro do CLIENT_STAGING (Drive 11). Só leitura. */
function painelStagingClientes() {
  try {
    var itens = listChildren(STAGING.DRIVE11_CLIENT_STAGING)
      .filter(function (f) { return f.mimeType === 'application/vnd.google-apps.folder'; })
      .map(function (f) { return { id: f.id, nome: f.name }; })
      .sort(function (a, b) { return String(a.nome).localeCompare(String(b.nome)); });
    return { ok: true, total: itens.length, itens: itens };
  } catch (e) { return { ok: false, erro: String(e && e.message || e) }; }
}

/** Indexa (só lista) o conteúdo de uma pasta de cliente do staging. Não abre documentos. */
function painelStagingDocs(folderId) {
  try {
    if (!folderId) return { ok: false, erro: 'folderId ausente' };
    var meta = getMeta(folderId, 'id,name,parents,mimeType');
    if (!meta.parents || meta.parents.indexOf(STAGING.DRIVE11_CLIENT_STAGING) === -1)
      return { ok: false, erro: 'Essa pasta não está no CLIENT_STAGING.' };
    var idx = stagingIndexRows(listChildren(folderId));
    return { ok: true, nome: meta.name, total: idx.rows.length, itens: idx.rows, manifesto: idx.manifesto, subpastas: idx.subpastas };
  } catch (e) { return { ok: false, erro: String(e && e.message || e) }; }
}

/**
 * IMPORTAR = MOVER a pasta de cliente inteira do staging (Drive 11) para o acervo (Drive 15).
 * MOVE ONLY: se o Google barrar (trava entre Drives Compartilhados), falha e avisa — NUNCA copia.
 */
function painelImportarStaging(folderId) {
  try {
    if (!folderId) return { ok: false, erro: 'folderId ausente' };
    var meta = getMeta(folderId, 'id,name,parents,mimeType');
    if (meta.mimeType !== 'application/vnd.google-apps.folder') return { ok: false, erro: 'Só pastas de cliente podem ser importadas.' };
    if (!meta.parents || meta.parents.indexOf(STAGING.DRIVE11_CLIENT_STAGING) === -1)
      return { ok: false, erro: 'Segurança: só importo pastas que estão dentro do CLIENT_STAGING do Drive 11.' };
    var origem = meta.parents[0];

    var manifesto = null;
    listChildren(folderId).forEach(function (c) {
      if (c.mimeType === 'application/json' && /MANIFESTO_CLIENTE/i.test(c.name || '')) manifesto = { id: c.id, nome: c.name };
    });

    var res = moveFileOnly(folderId, STAGING.DESTINO_IMPORT, origem);

    return {
      ok: true, nome: meta.name, folder_id: folderId,
      destino_folder_id: STAGING.DESTINO_IMPORT, novos_parents: res.parents || [],
      manifesto: manifesto,
      aviso: 'Pasta movida para o acervo. Clique em Executar para processar.'
    };
  } catch (e) {
    return { ok: false, erro: String(e && e.message || e),
      dica: 'Se citou permissão/move, pode ser a trava do Google para mover entre Drives Compartilhados — precisa ser Gerente nos dois drives e a organização permitir "mover para fora".' };
  }
}

/* ---------------- Helper puro (testável em node) ---------------- */

/** Monta as linhas de índice do conteúdo de uma pasta (pastas primeiro), detecta o manifesto. */
function stagingIndexRows(children) {
  var rows = [], manifesto = null, subpastas = 0;
  (children || []).forEach(function (c) {
    var isFolder = c.mimeType === 'application/vnd.google-apps.folder';
    if (isFolder) subpastas++;
    if (!isFolder && /MANIFESTO_CLIENTE/i.test(c.name || '')) manifesto = { id: c.id, nome: c.name };
    rows.push({ nome: c.name, tipo: isFolder ? 'pasta' : (c.mimeType || ''), tamanho: c.size || null, isFolder: isFolder });
  });
  rows.sort(function (a, b) { if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1; return String(a.nome).localeCompare(String(b.nome)); });
  return { rows: rows, manifesto: manifesto, subpastas: subpastas };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { stagingIndexRows: stagingIndexRows };
}
