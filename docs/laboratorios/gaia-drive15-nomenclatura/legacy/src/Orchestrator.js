/**
 * Orchestrator — o fluxo por arquivo, executado em etapas curtas (ticks).
 *
 *   INVENTÁRIO (pasta por pasta do acervo) → para cada arquivo:
 *   NOVO → LIDO (OCR, uma vez só) → PRONTO (regra + variáveis + destino) → MOVIDO
 *                                 ↘ REVISAO (não reconhecido / falta dado)   ↘ DUPLICADO
 *
 * Estado de cada arquivo fica no MAPA_BANCO_DE_DADOS.json (campo "etapa").
 * Reexecutar é seguro: nada é lido, nomeado ou movido duas vezes.
 */

var PL_FILA = ['NOVO', 'LIDO', 'PRONTO', 'ERRO'];
// Muda quando o reconhecimento melhora: itens da Revisão classificados por versão anterior são reavaliados (sem OCR novo).
var PL_CLASSIFICADOR_VERSAO = '2026-09-17-titulo';

/* ---------------- Helpers puros ---------------- */

/** true enquanto (nowMs - startMs) < limitMs. */
function ppWithinBudget(startMs, nowMs, limitMs) { return (nowMs - startMs) < limitMs; }

/** Erro de autorização do Google (falta escopo/permissão), não do arquivo. */
function plIsAuthError(msg) {
  return /permiss[aã]o para chamar|n[aã]o tem permiss|authorization is required|permission to call|auth\/documents|auth\/drive|PERMISSION_DENIED|UNAUTHENTICATED|insufficient authentication scopes|ACCESS_TOKEN_SCOPE_INSUFFICIENT/i.test(String(msg || ''));
}

/** Arquivos que não são documentos de cliente (ficam fora da classificação). */
function plControlKind(f) {
  var n = String(f.name || ''), m = String(f.mimeType || '');
  if (/^MANIFESTO_CLIENTE.*\.json$/i.test(n)) return 'MANIFESTO';
  if (m === 'application/json' || /\.json$/i.test(n)) return 'JSON';
  if (/^RELATORIO_.*\.txt$/i.test(n)) return 'RELATORIO';
  if (/^[_~.]/.test(n)) return 'SISTEMA';
  if (m === 'application/vnd.google-apps.shortcut') return 'ATALHO';
  if (/^application\/vnd\.google-apps\.(form|site|map|drawing|script|folder|jam)/.test(m)) return 'GOOGLE_NAO_DOCUMENTO';
  return null;
}

function plResetRecord(r, ctl) {
  r.etapa = ctl ? 'CONTROLE' : 'NOVO';
  r.controle = ctl || null;
  r.estado_no_acervo = 'ATIVO';
  r.status_leitura = 'NAO_CLASSIFICADO';
  ['rule_id', 'tipo_documental', 'variaveis', 'raw_fields', 'candidatos', 'nome_proposto', 'nome_final', 'destino_bucket',
    'destino_folder_id', 'destino_caminho', 'motivo_revisao', 'sugestoes', 'candidatos_regra', 'simulacao', 'simulado_job',
    'erro', 'erro_job', 'tentativas', 'etapa_retomar', 'reconhecido_por', 'duplicado_de', 'pertencimento_confirmado',
    'movido_em', 'cliente_nnn', 'ignorado_em', 'classificador_versao', 'pacote', 'aprovacao'].forEach(function (k) { r[k] = null; });
  r.observacoes = null;
}

function plNewRecord(f, parentId, clientFolder, path, ctl) {
  var r = newArquivo();
  r.file_id = f.id;
  r.parent_folder_id = parentId;
  r.caminho_snapshot = path + '/' + f.name;
  r.nome_arquivo = f.name;
  r.mime = f.mimeType;
  r.tamanho = f.size;
  r.modified_time_origem = f.modifiedTime;
  r.data_leitura = null;
  r.acervo_cliente_folder_id = clientFolder.id;
  r.acervo_cliente_nome = clientFolder.name;
  plResetRecord(r, ctl);
  return r;
}

/** Fila de trabalho da execução. */
function plQueue(mapa, job) {
  return (mapa.arquivos || []).filter(function (r) {
    if (PL_FILA.indexOf(r.etapa) === -1) return false;
    if (job.folderId && r.acervo_cliente_folder_id !== job.folderId) return false;
    if (r.erro_job === job.id) return false;
    if (r.etapa === 'PRONTO' && r.simulado_job === job.id) return false;
    if (r.etapa === 'ERRO' && (r.tentativas || 0) >= PIPELINE_CFG.MAX_TENTATIVAS_ERRO) return false;
    return true;
  }).sort(function (a, b) {
    return String(a.acervo_cliente_nome).localeCompare(String(b.acervo_cliente_nome)) ||
      (plIsCopyName(a.nome_arquivo) - plIsCopyName(b.nome_arquivo)) ||
      String(a.nome_arquivo).localeCompare(String(b.nome_arquivo));
  });
}

/** "arquivo (1).pdf", "arquivo - Cópia.pdf": cópias vão depois do original (o original é que vai para o cliente). */
function plIsCopyName(name) {
  return /(\s\(\d+\)|\s-\s(c[oó]pia|copy)(\s\(\d+\))?)(\.[A-Za-z0-9]{1,6})?$/i.test(String(name || '')) ? 1 : 0;
}

/** Contagem por etapa (para o painel). */
function plCountByEtapa(mapa, folderId) {
  var out = {};
  (mapa.arquivos || []).forEach(function (r) {
    if (folderId && r.acervo_cliente_folder_id !== folderId) return;
    var e = r.etapa || 'NOVO';
    out[e] = (out[e] || 0) + 1;
  });
  return out;
}

/* ---------------- Contexto (Drive) ---------------- */

/** Localiza (ou cria) o MAPA_BANCO_DE_DADOS.json na raiz do acervo. */
function _ppLoadOrCreateMapa(acervoRoot) {
  var existing = findChildByName(acervoRoot, 'MAPA_BANCO_DE_DADOS.json');
  if (existing) return { mapaId: existing.id, mapa: mapaReadFromDrive(existing.id) };
  var iso = nowIso();
  var created = mapaCreateFileInDrive(acervoRoot, iso);
  return { mapaId: created.id, mapa: createMapa(iso) };
}

function plLoadContext(job) {
  var loaded = _ppLoadOrCreateMapa(ROOTS.BANCO_DE_DADOS);
  var mapa = loaded.mapa;
  ['arquivos', 'entidades', 'pastas', 'movimentos'].forEach(function (k) { if (!Array.isArray(mapa[k])) mapa[k] = []; });
  var ctx = {
    jobId: job.id, simular: !!job.simular, mapa: mapa, mapaId: loaded.mapaId, dirty: false,
    idx: mapaIndex(mapa), textCache: {}, md5Ocr: {},
    cont: { lidos: 0, reconhecidos: 0, movidos: 0, duplicados: 0, revisao: 0, erros: 0, simulados: 0, aguardando: 0 }
  };
  mapa.arquivos.forEach(function (r) { if (r.ocr_ref && r.ocr_md5) ctx.md5Ocr[r.ocr_md5] = r.ocr_ref; });
  plSetRules(ctx, rsRuntimeRules());
  ctx.clientesIndex = sysLoadClientesIndex();
  ctx.textFor = function (r) {
    if (ctx.textCache[r.file_id] !== undefined) return ctx.textCache[r.file_id];
    var c = sysOcrLoad(r.ocr_ref);
    var t = (c && typeof c.text === 'string') ? c.text : '';
    ctx.textCache[r.file_id] = t;
    return t;
  };
  ctx.saveMapa = function () {
    mapa.updated_at = nowIso();
    var v = validateMapa(mapa);
    if (!v.ok) throw new Error('MAPA inválido — não gravado: ' + v.errors.slice(0, 5).join('; '));
    mapaWriteToDrive(ctx.mapaId, mapa);
    ctx.dirty = false;
  };
  return ctx;
}

function plSetRules(ctx, rules) {
  ctx.rules = rules;
  ctx.ruleById = {};
  rules.forEach(function (r) { ctx.ruleById[r.rule_id] = r; });
}

/** Pastas de cliente do acervo (ignora pastas técnicas que começam com "_"). */
function plClientFolders() {
  return dsListFolders(ROOTS.BANCO_DE_DADOS).filter(function (f) { return !/^[_.]/.test(f.name); })
    .sort(function (a, b) { return a.name.localeCompare(b.name); });
}

/* ---------------- Etapas ---------------- */

function plInventoryClient(ctx, folder, log) {
  var st = { total: 0, novos: 0, alterados: 0, rever: 0, sairam: 0 };
  var vistos = {};
  var walk = function (fid, path, depth) {
    dsListFiles(fid).forEach(function (f) {
      st.total++;
      vistos[f.id] = true;
      var ctl = plControlKind(f);
      var r = ctx.idx[f.id];
      if (!r) {
        r = plNewRecord(f, fid, folder, path, ctl);
        ctx.mapa.arquivos.push(r);
        ctx.idx[f.id] = r;
        st.novos++;
        return;
      }
      var legacy = !r.etapa;
      var voltou = r.etapa === 'MOVIDO' || r.estado_no_acervo === 'MOVIDO' || (r.etapa === 'IGNORADO' && !!r.saiu_do_acervo_em);
      var mudou = r.tamanho !== null && r.tamanho !== undefined && f.size !== null && String(r.tamanho) !== String(f.size);
      var semPermissao = r.etapa === 'REVISAO' && /^LEITURA_FALHOU/.test(String(r.motivo_revisao || '')) && plIsAuthError(r.motivo_revisao);
      // renomeado à mão no Drive enquanto esperava: o nome novo pode seguir o padrão de uma regra
      var renomeado = r.etapa === 'REVISAO' && !!r.nome_arquivo && f.name !== r.nome_arquivo;
      if (legacy || voltou || mudou || semPermissao) {
        if (voltou) log('aviso', 'Arquivo voltou ao acervo e será processado de novo: ' + f.name);
        plResetRecord(r, ctl);
        r.saiu_do_acervo_em = null;
        if (legacy) st.novos++; else st.alterados++;
      } else if (r.etapa === 'REVISAO' && r.ocr_ref && (renomeado || (r.classificador_versao !== PL_CLASSIFICADOR_VERSAO &&
        LN_MOTIVOS_RECHECAR.test(String(r.motivo_revisao || ''))))) {
        r.etapa = 'LIDO'; // texto já lido: só reconhece de novo
        r.motivo_revisao = null;
        st.rever++;
      }
      r.nome_arquivo = f.name;
      r.parent_folder_id = fid;
      r.caminho_snapshot = path + '/' + f.name;
      r.mime = f.mimeType;
      r.tamanho = f.size;
      r.modified_time_origem = f.modifiedTime;
      r.acervo_cliente_folder_id = folder.id;
      r.acervo_cliente_nome = folder.name;
    });
    if (depth < PIPELINE_CFG.MAX_DEPTH) {
      dsListFolders(fid).forEach(function (d) { walk(d.id, path + '/' + d.name, depth + 1); });
    }
  };
  walk(folder.id, folder.name, 0);
  // registros desta pasta cujo arquivo não está mais no acervo (movido por fora ou apagado):
  // saem da fila e da Revisão. PRONTO fica: o commit reconcilia um movimento que não chegou a ser gravado.
  ctx.mapa.arquivos.forEach(function (r) {
    if (r.acervo_cliente_folder_id !== folder.id || vistos[r.file_id]) return;
    var etapa = r.etapa === 'ERRO' ? (r.etapa_retomar || 'NOVO') : r.etapa;
    if (['NOVO', 'LIDO', 'REVISAO'].indexOf(etapa) === -1) return;
    r.etapa = 'IGNORADO';
    r.saiu_do_acervo_em = nowIso();
    r.observacoes = 'não está mais na pasta do cliente no acervo';
    st.sairam++;
  });
  var up = upsertPasta(ctx.mapa, {
    folder_id: folder.id, parent: ROOTS.BANCO_DE_DADOS, caminho_snapshot: folder.name, nome: folder.name,
    status: 'COMPLETA', ultimo_inventario: nowIso(), quantidade_observada: st.total
  }, nowIso());
  if (up.ok) { ctx.mapa.pastas = up.mapa.pastas; }
  ctx.dirty = true;
  return st;
}

function plStepRead(ctx, r, log) {
  var meta = dsMeta(r.file_id);
  if (meta.trashed) { r.etapa = 'IGNORADO'; r.observacoes = 'arquivo está na lixeira'; return; }
  r.md5 = meta.md5Checksum || null;

  var reuse = null;
  if (r.ocr_ref && r.md5 && r.ocr_md5 === r.md5) reuse = r.ocr_ref;
  else if (r.md5 && ctx.md5Ocr[r.md5]) reuse = ctx.md5Ocr[r.md5];
  if (reuse) {
    var c = sysOcrLoad(reuse);
    if (c && typeof c.text === 'string') {
      if (reuse !== r.ocr_ref) { r.ocr_ref = reuse; r.ocr_ref_proprio = false; }
      r.ocr_md5 = r.md5;
      ctx.textCache[r.file_id] = c.text;
      r.status_leitura = c.text.trim() ? 'MAPEADO' : 'PARCIAL';
      r.etapa = 'LIDO';
      log('info', 'Texto reaproveitado (já lido antes): ' + r.nome_arquivo);
      return;
    }
  }

  var res = ocrReadText(r.file_id, r.mime);
  if (!res.ok && plIsAuthError(res.erro)) {
    // falta de permissão não é problema do arquivo: para a execução e avisa
    throw new Error('PERMISSAO: ' + res.erro);
  }
  r.metodo_leitura = res.method;
  r.data_leitura = nowIso();
  if (!res.ok) {
    r.status_leitura = 'ERRO';
    ctx.cont.revisao++;
    log('revisao', r.nome_arquivo + ' → Revisão (leitura falhou: ' + res.erro + ')');
    cmToReview(r, 'LEITURA_FALHOU: ' + res.erro);
    return;
  }
  var text = String(res.text || '').slice(0, PIPELINE_CFG.MAX_OCR_CHARS);
  var ref = sysOcrSave(r.ocr_ref_proprio ? r.ocr_ref : null, {
    schema: 'gaia-ocr/1.0', file_id: r.file_id, md5: r.md5, nome_arquivo: r.nome_arquivo, mime: r.mime,
    metodo: res.method, text_length: String(res.text || '').length, lido_em: r.data_leitura, text: text
  });
  r.ocr_ref = ref;
  r.ocr_ref_proprio = true;
  r.ocr_md5 = r.md5;
  if (r.md5) ctx.md5Ocr[r.md5] = ref;
  ctx.textCache[r.file_id] = text;
  r.status_leitura = text.trim() ? 'MAPEADO' : 'PARCIAL';
  r.uso_ocr_visao = res.method === 'OCR_DRIVE' || res.method === 'DOCUMENT_AI';
  r.paginas_lidas = res.paginas || null;
  r.leitura_obs = res.motivo || null;
  r.resumo_curto = text.replace(/\s+/g, ' ').trim().slice(0, 160) || null;
  r.etapa = 'LIDO';
  ctx.cont.lidos++;
  log('info', 'Lido (' + res.method + ', ' + text.length + ' caracteres' + (res.paginas ? ', ' + res.paginas + ' pág.' : '') + '): ' + r.nome_arquivo +
    (res.motivo ? ' — ' + res.motivo : ''));
}

function plStepClassify(ctx, r, log) {
  var text = ctx.textFor(r);
  var cls = clClassify(ctx.rules, { text: text, fileName: r.nome_arquivo });
  r.classificador_versao = PL_CLASSIFICADOR_VERSAO;
  if (cls.status !== 'OK') {
    // nada de uma classificação anterior (ex.: antes de renomear) pode sobrar no registro
    r.rule_id = null; r.tipo_documental = null; r.reconhecido_por = null; r.variaveis = null; r.candidatos = null;
    r.candidatos_regra = cls.candidatos || null;
    r.sugestoes = (cls.sugestoes || []).map(function (s) { return { rule_id: s.rule_id, document_type: s.document_type, score: s.score }; });
    ctx.cont.revisao++;
    log('revisao', r.nome_arquivo + ' → Revisão (' + cls.motivo + (r.sugestoes.length ? '; sugestão ' + r.sugestoes[0].rule_id : '') + ')');
    cmToReview(r, cls.motivo);
    return;
  }
  var rule = cls.rule;
  var ex = exExtractVariables(rule, text);
  // Reconhecido pelo NOME (renomeado à mão): valores do nome mandam. Pelo TEXTO: o texto manda, o nome só completa.
  var first = cls.via === 'NOME' ? ex.provided : cls.provided;
  var second = cls.via === 'NOME' ? cls.provided : ex.provided;
  var provided = {};
  for (var k in first) provided[k] = first[k];
  for (var k2 in second) provided[k2] = second[k2];
  r.rule_id = rule.rule_id;
  r.tipo_documental = rule.rule_id;
  r.reconhecido_por = cls.via;
  r.variaveis = provided;
  r.raw_fields = ex.rawFields;
  r.candidatos = ex.candidates;

  var test = cmComposeName(ctx.rules, rule, r, text, '000');
  if (test.status !== 'OK') {
    ctx.cont.revisao++;
    log('revisao', r.nome_arquivo + ' → Revisão (' + rule.rule_id + ' reconhecido, mas ' + cmMotivo(test) + ')');
    cmToReview(r, cmMotivo(test));
    return;
  }
  var route = rtBucketFor(rule, normKey(text));
  if (!route.bucket) {
    ctx.cont.revisao++;
    log('revisao', r.nome_arquivo + ' → Revisão (' + rule.rule_id + ': ' + route.via + ')');
    cmToReview(r, route.via);
    return;
  }
  r.destino_bucket = route.bucket;
  r.nome_proposto = test.finalFilename.replace(/^000_/, '');
  r.motivo_revisao = null;
  r.etapa = 'PRONTO';
  ctx.cont.reconhecidos++;
  log('ok', 'Reconhecido ' + rule.rule_id + ' (' + cls.via + '): ' + r.nome_arquivo + ' → ' + r.nome_proposto + ' [' + route.bucket + ']');
}

function plAdvance(ctx, r, job, log) {
  try {
    if (r.etapa === 'ERRO') r.etapa = r.etapa_retomar || 'NOVO';
    if (r.etapa === 'NOVO') plStepRead(ctx, r, log);
    if (r.etapa === 'LIDO') plStepClassify(ctx, r, log);
    if (r.etapa === 'PRONTO') {
      var st = cmCommit(ctx, r, log);
      if (st === 'SIMULADO') r.simulado_job = job.id;
      if (st === 'REVISAO') ctx.cont.revisao++;
      // AGUARDANDO: o arquivo ficou no portão S5 esperando o operador aprovar o
      // pacote (aba Aprovação). Sai da fila desta execução e não é movido aqui.
    }
    r.erro = null;
  } catch (e) {
    var msg = String(e && e.message || e);
    if (/^PERMISSAO: /.test(msg)) throw e; // interrompe a execução inteira (ver jbTick)
    r.etapa_retomar = r.etapa;
    r.etapa = 'ERRO';
    r.erro = msg;
    r.erro_job = job.id;
    r.tentativas = (r.tentativas || 0) + 1;
    ctx.cont.erros++;
    if (r.tentativas >= PIPELINE_CFG.MAX_TENTATIVAS_ERRO) {
      cmToReview(r, 'ERRO_REPETIDO: ' + msg);
      log('erro', r.nome_arquivo + ' → Revisão após ' + r.tentativas + ' erros: ' + msg);
    } else {
      log('erro', 'Erro em ' + r.nome_arquivo + ' (tentativa ' + r.tentativas + '): ' + msg);
    }
  }
  ctx.dirty = true;
}

/**
 * Uma etapa curta de trabalho.
 * @return {{job:Object, done:boolean, parado:boolean}}
 */
function plRunTick(job, log, budgetMs) {
  var start = Date.now();
  var within = function () { return ppWithinBudget(start, Date.now(), budgetMs); };
  var ctx = plLoadContext(job);
  var parado = false, done = false, ok = false;
  try {
    if (job.fase === 'INVENTARIO') {
      while (job.pastas_pendentes.length && within()) {
        if (jbStopRequested()) { parado = true; break; }
        var fid = job.pastas_pendentes[0];
        var folder = null;
        try {
          if (dsIsLiveFolder(fid)) folder = { id: fid, name: DriveApp.getFolderById(fid).getName() };
        } catch (e) { folder = null; }
        if (!folder) {
          job.pastas_pendentes.shift();
          log('aviso', 'Pasta de cliente não encontrada no acervo (apagada ou sem acesso) — pulada: ' + fid);
          continue;
        }
        var st = plInventoryClient(ctx, folder, log);
        log('info', 'Pasta ' + folder.name + ': ' + st.total + ' arquivo(s)' + (st.novos ? ', ' + st.novos + ' novo(s)' : '') +
          (st.alterados ? ', ' + st.alterados + ' alterado(s)' : '') +
          (st.rever ? ', ' + st.rever + ' da Revisão para reconhecer de novo' : '') +
          (st.sairam ? ', ' + st.sairam + ' não estão mais no acervo (saíram da fila)' : ''));
        job.pastas_pendentes.shift();
        job.contadores.pastas++;
      }
      if (!parado && !job.pastas_pendentes.length) {
        job.fase = 'PROCESSAR';
        var q0 = plQueue(ctx.mapa, job);
        job.fila_total = q0.length;
        log('info', q0.length ? ('Fila de trabalho: ' + q0.length + ' arquivo(s)') : 'Nada novo para processar.');
      }
    }

    if (!parado && job.fase === 'PROCESSAR') {
      var queue = plQueue(ctx.mapa, job);
      for (var i = 0; i < queue.length; i++) {
        if (!within()) break;
        if (jbStopRequested()) { parado = true; break; }
        plAdvance(ctx, queue[i], job, log);
      }
      job.fila_restante = plQueue(ctx.mapa, job).length;
      done = !parado && job.fila_restante === 0;
    }
    if (ctx.dirty) ctx.saveMapa();
    ok = true;
  } finally {
    // mesmo se a etapa cair no meio: grava o que já foi feito (OCR lido, movimentos) e soma os contadores
    if (!ok && ctx.dirty) { try { ctx.saveMapa(); } catch (e2) { console.log('MAPA não gravado após erro: ' + e2); } }
    for (var k in ctx.cont) job.contadores[k] = (job.contadores[k] || 0) + ctx.cont[k];
    if (ctx.clientesCriados) job.contadores.clientes_novos = (job.contadores.clientes_novos || 0) + ctx.clientesCriados;
  }
  return { job: job, done: done, parado: parado };
}

/** Para rodar pelo editor do Apps Script (sem o painel): processa por até ~5 min. */
function processarPastas(opts) {
  var st = jbStart(opts || {});
  if (!st.ok) { Logger.log(st.erro); return st; }
  var t0 = Date.now(), res = st;
  while (Date.now() - t0 < 280000) {
    res = jbTick();
    if (!res.ok || !res.job || res.job.status !== 'RODANDO') break;
  }
  Logger.log(JSON.stringify(res.job && res.job.contadores));
  return res;
}
