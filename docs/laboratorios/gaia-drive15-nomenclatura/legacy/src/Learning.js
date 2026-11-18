/**
 * Learning — aba Revisão: o operador nomeia um arquivo que o sistema não reconheceu,
 * marca frases do documento (âncoras) e clica "Aprender e seguir".
 *
 * Resultado:
 *  1) regra nova (NOM-057+) ou ajuste de regra existente em 01_NOVAS_REGRAS;
 *  2) registro append-only em 5-OFFICE KNOWLEDGE;
 *  3) o arquivo segue o fluxo (nome final + pasta do cliente) na mesma ação;
 *  4) outros arquivos da Revisão voltam para a fila e são reconhecidos na próxima execução.
 */

var LN_MOTIVOS_RECHECAR = /^(TIPO_NAO_RECONHECIDO|AMBIGUO|CONFLITO_TEXTO_X_NOME|VARIAVEIS_FALTANTES|FORMATO_INVALIDO|EXTRACAO_PENDENTE|DESTINO_NAO_DEFINIDO|CONTEXTO_AMBIGUO|DARE_SUBTIPO|FAMILIA_DARE)/;

/* ---------------- Puro ---------------- */

function lnFormatForVar(name) {
  var n = String(name || '').toUpperCase();
  if (/^DATA/.test(n)) return 'DD-MM-AAAA';
  if (/^ANO/.test(n)) return 'AAAA';
  if (/^CNPJ/.test(n)) return 'CNPJ';
  return 'TEXTO';
}

/**
 * Transforma o nome digitado em padrão: datas, CNPJ e números que aparecem no texto
 * viram variáveis ({DATA}, {CNPJ}, {NUMERO}); o resto fica fixo.
 * @return {{pattern:string, variables:Array<{name,format,value}>}}
 */
function lnProposePattern(name, rawText) {
  name = txSafeName(String(name || '').replace(/^\d{3}[\s_\-]+/, ''));
  var ext = txExt(name), stem = txStem(name);
  var key = normKey(rawText);
  var dates = txFindDates(rawText);
  var cnpjs = txFindCnpjs(rawText);
  var vars = [], used = {};
  var add = function (base, format, value) {
    var n = base, i = 2;
    while (used[n]) n = base + '_' + (i++);
    used[n] = true;
    vars.push({ name: n, format: format, value: value });
    return '{' + n + '}';
  };
  stem = stem.replace(/(\d{2})[\-_.](\d{2})[\-_.](\d{4})/g, function (all, d, m, y) {
    var v = d + '-' + m + '-' + y;
    return dates.indexOf(v) !== -1 ? add('DATA', 'DD-MM-AAAA', v) : all;
  });
  stem = stem.replace(/\d{14}/g, function (all) { return cnpjs.indexOf(all) !== -1 ? add('CNPJ', 'CNPJ', all) : all; });
  stem = stem.replace(/(^|[^A-Za-z0-9{])([A-Za-z0-9]*\d[A-Za-z0-9.\-]*[A-Za-z0-9])(?=$|[^A-Za-z0-9}])/g, function (all, pre, tok) {
    if (tok.replace(/[^A-Za-z0-9]/g, '').length < 4) return all;
    if (!txHas(key, tok)) return all;
    if (/^(19|20)\d{2}$/.test(tok)) return pre + add('ANO', 'AAAA', tok);
    return pre + add('NUMERO', 'TEXTO', tok);
  });
  return { pattern: stem + ext, variables: vars };
}

/** "ATESTADO_DE_REGULARIZACAO_{DATA}.pdf" → "ATESTADO DE REGULARIZACAO" (nome do tipo quando o operador não informa). */
function lnTypeFromPattern(pattern) {
  var p = String(pattern || '');
  var ext = txExt(p);
  if (ext) p = p.slice(0, p.length - ext.length);
  return p.replace(/\{[A-Z0-9_]+\}/g, ' ').replace(/[_.]+/g, ' ').replace(/\s-\s|^-|-$/g, ' ').replace(/\s+/g, ' ').trim();
}

/** Placeholders de um padrão, na ordem. */
function lnPatternVars(pattern) {
  var out = [], m, re = /\{([A-Z0-9_]+)\}/g;
  while ((m = re.exec(String(pattern || ''))) !== null) if (out.indexOf(m[1]) === -1) out.push(m[1]);
  return out;
}

/** Rótulo (até 4 palavras) que aparece logo antes do valor no texto. */
function lnLabelFor(value, format, rawText) {
  var nt = normText(rawText);
  var pos = -1, m, re;
  if (format === 'DD-MM-AAAA') {
    re = new RegExp(TX_DATE_SHAPE, 'g');
    while ((m = re.exec(nt)) !== null) { if (txParseDate(m[0]) === value) { pos = m.index; break; } }
  } else if (format === 'CNPJ') {
    re = /\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}/g;
    while ((m = re.exec(nt)) !== null) { if (txDigits(m[0]) === value) { pos = m.index; break; } }
  } else {
    var parts = String(value || '').toUpperCase().split(/[^A-Z0-9]+/).filter(Boolean);
    if (!parts.length) return null;
    m = new RegExp('(?:^|[^A-Z0-9])(' + parts.map(txEscapeRe).join('[^A-Z0-9]{0,2}') + ')(?![A-Z0-9])').exec(nt);
    if (m) pos = m.index + m[0].indexOf(m[1]);
  }
  if (pos < 0) return null;
  var wordsOf = function (s) { return normKey(s).split(' ').filter(function (w) { return w && !/\d/.test(w); }); };
  var lineStart = nt.lastIndexOf('\n', pos - 1) + 1;
  var words = wordsOf(nt.slice(Math.max(lineStart, pos - 60), pos));
  if (!words.length && lineStart > 0) { // rótulo na linha de cima
    var prevStart = nt.lastIndexOf('\n', lineStart - 2) + 1;
    words = wordsOf(nt.slice(prevStart, lineStart));
  }
  var TAIL = { N: 1, NO: 1, NR: 1, NUM: 1, O: 1, A: 1 };
  while (words.length && TAIL[words[words.length - 1]]) words.pop();
  var lab = words.slice(-4);
  while (lab.length && TX_STOP[lab[0]]) lab.shift();
  var s = lab.join(' ');
  return s.length >= 3 ? s : null;
}

/** Âncoras: pelo menos 2, todas presentes no texto. */
function lnValidateAnchors(anchors, keyText) {
  var list = (anchors || []).map(normKey).filter(function (a, i, arr) { return a && arr.indexOf(a) === i; });
  if (list.length < 2) return { ok: false, erro: 'Marque pelo menos 2 frases do documento.' };
  var missing = list.filter(function (a) { return !txHas(keyText, a); });
  if (missing.length) return { ok: false, erro: 'Estas frases não estão no texto lido: ' + missing.join(' | ') };
  var weak = list.filter(function (a) { return a.replace(/ /g, '').length < 5; });
  if (weak.length === list.length) return { ok: false, erro: 'As frases são curtas demais para reconhecer o documento com segurança.' };
  return { ok: true, anchors: list };
}

/* ---------------- Drive ---------------- */

function _lnErr(msg) { return { ok: false, erro: msg }; }

function _lnRuleView(r) {
  return {
    rule_id: r.rule_id, document_type: r.document_type, approved_pattern: r.approved_pattern, status: r.status,
    variables: (r.variables || []).filter(function (v) { return v.required && !(v.name === 'TEOR' && r.family); })
      .map(function (v) { return { name: v.name, format: v.format }; }),
    destino: r.destination_bucket || (ROTAS_CFG.TABELA[r.rule_id] !== 'CONTEXTUAL' ? ROTAS_CFG.TABELA[r.rule_id] : null) || null,
    auto: (r.recognition && ((r.recognition.required_all || []).length || (r.recognition.required_groups || []).length)) || (r.recognition_alternatives || []).length ? true : false,
    aprendida: !!r.aprendida
  };
}

/** Dados do cartão de Revisão de um arquivo. */
function lnDetalhe(fileId, ctxOpt) {
  var ctx = ctxOpt || plLoadContext({ id: 'DETALHE' });
  var r = ctx.idx[fileId];
  if (!r) return _lnErr('Arquivo não encontrado no MAPA.');
  var text = ctx.textFor(r);
  var key = normKey(text);
  var meta = null;
  try { meta = dsMeta(fileId); } catch (e) { meta = { name: r.nome_arquivo }; }
  var info = crInfoFor(ctx, r.acervo_cliente_folder_id);
  var nomeAtual = meta.name || r.nome_arquivo;
  var renomeado = nomeAtual !== r.nome_arquivo;
  var porNome = clMatchByFilename(ctx.rules, nomeAtual);
  // só pré-seleciona com evidência forte (regra já reconhecida, nome no padrão, ou tipo escrito no documento)
  // sugestões recalculadas com as regras de agora (o texto já está em cache)
  var sugestoes = key ? clScoreRules(ctx.rules, key, 5).map(function (s) {
    return { rule_id: s.rule_id, document_type: s.document_type, score: s.score, tipo_no_texto: s.tipo_no_texto };
  }) : (r.sugestoes || []);
  var forte = sugestoes.filter(function (s) { return s.score >= 100 && s.tipo_no_texto; })[0];
  var sel = r.rule_id || (porNome[0] && porNome[0].rule.rule_id) || (forte && forte.rule_id) || null;
  var vars = {};
  if (r.variaveis) for (var k in r.variaveis) vars[k] = r.variaveis[k];
  if (porNome[0] && porNome[0].rule.rule_id === sel) for (var k2 in porNome[0].provided) vars[k2] = porNome[0].provided[k2];
  var candidatos = r.candidatos || {};
  if (sel && ctx.ruleById[sel] && text) {
    var ex = exExtractVariables(ctx.ruleById[sel], text);
    for (var k3 in ex.provided) if (vars[k3] === undefined) vars[k3] = ex.provided[k3];
    for (var k4 in ex.candidates) if (!candidatos[k4]) candidatos[k4] = ex.candidates[k4];
  }
  var nnnCliente = ctx.clientesIndex.vinculos[r.acervo_cliente_folder_id] || null;
  return {
    ok: true,
    arquivo: {
      file_id: r.file_id, nome: nomeAtual, nome_original: r.nome_arquivo, renomeado: renomeado, cliente: r.acervo_cliente_nome,
      cliente_nnn: nnnCliente, etapa: r.etapa, motivo: r.motivo_revisao, rule_id: r.rule_id, reconhecido_por: r.reconhecido_por,
      mime: r.mime, link: 'https://drive.google.com/file/d/' + r.file_id + '/view', leitura: r.metodo_leitura
    },
    texto: text.slice(0, 15000), texto_total: text.length,
    ancoras: txAnchorCandidates(text, info.excluir_ancoras, 30),
    precisa_ancoras: !!key && (!r.reconhecido_por || r.reconhecido_por === 'NOME'),
    selecionada: sel,
    modo_sugerido: sel ? 'EXISTENTE' : 'NOVO', // sem tipo provável: o operador digita o nome
    sugestoes: sugestoes,
    candidatos_regra: r.candidatos_regra || [],
    variaveis: vars,
    candidatos: candidatos,
    proposta: renomeado ? lnProposePattern(nomeAtual, text) : null,
    regras: ctx.rules.filter(function (x) { return x.status === 'VIGENTE'; }).map(_lnRuleView),
    revisao_externa: rxView(r.revisao_externa)
  };
}

/** Valores e candidatos das variáveis de UMA regra para o arquivo (quando o operador troca o tipo no cartão). */
function lnExtrair(fileId, ruleId) {
  var ctx = plLoadContext({ id: 'EXTRAIR' });
  var r = ctx.idx[fileId];
  var rule = ctx.ruleById[ruleId];
  if (!r || !rule) return _lnErr('Arquivo ou regra não encontrados.');
  var text = ctx.textFor(r);
  var ex = text ? exExtractVariables(rule, text) : { provided: {}, candidates: {} };
  var porNome = clMatchByFilename([rule], (function () { try { return dsMeta(fileId).name; } catch (e) { return r.nome_arquivo; } })());
  var vars = {};
  for (var k in ex.provided) vars[k] = ex.provided[k];
  if (porNome[0]) for (var k2 in porNome[0].provided) if (vars[k2] === undefined) vars[k2] = porNome[0].provided[k2];
  if (r.rule_id === ruleId && r.variaveis) for (var k3 in r.variaveis) vars[k3] = r.variaveis[k3];
  return { ok: true, rule_id: ruleId, variaveis: vars, candidatos: ex.candidates || {} };
}

/** Pré-visualiza o padrão que será aprendido a partir de um nome digitado. */
function lnPreview(fileId, nome) {
  var ctx = plLoadContext({ id: 'PREVIEW' });
  var r = ctx.idx[fileId];
  if (!r) return _lnErr('Arquivo não encontrado.');
  var p = lnProposePattern(nome, ctx.textFor(r));
  var pk = normKey(p.pattern);
  var igual = ctx.rules.filter(function (x) { return normKey(x.approved_pattern) === pk; })[0];
  return { ok: true, pattern: p.pattern, variables: p.variables, regra_igual: igual ? igual.rule_id : null };
}

/**
 * "Aprender e seguir".
 * payload: {file_id, modo:'EXISTENTE'|'NOVO', rule_id?, document_type?, nome_final?, padrao?,
 *           variaveis:{}, ancoras:[], destino?, sempre_destino?, comentario?,
 *           origem?:'CHATGPT'|'PAINEL', revisao_externa_id?}
 */
function lnAprender(p) {
  p = p || {};
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(90000)) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  var job = { id: 'APRENDER-' + jbStamp() };
  var logLines = [];
  var log = function (n, m) { logLines.push({ n: n, m: m }); console.log('[' + n + '] ' + m); };
  try {
    var ctx = plLoadContext(job);
    var r = ctx.idx[p.file_id];
    if (!r) return _lnErr('Arquivo não encontrado no MAPA.');
    if (r.etapa !== 'REVISAO') return _lnErr('Este arquivo não está mais em Revisão (etapa: ' + r.etapa + '). Atualize a lista.');
    var meta = dsMeta(r.file_id);
    if (meta.trashed) return _lnErr('O arquivo está na lixeira.');
    r.nome_arquivo = meta.name;
    var text = ctx.textFor(r);
    var key = normKey(text);
    var now = nowIso();
    var comentario = String(p.comentario || '').trim();
    var info = crInfoFor(ctx, r.acervo_cliente_folder_id);
    var destino = p.destino && CLIENTES_CFG.BUCKETS.indexOf(p.destino) !== -1 ? p.destino : null;

    var anchors = [];
    var needAnchors = !!key && (p.modo === 'NOVO' || !(r.rule_id === p.rule_id && r.reconhecido_por && r.reconhecido_por !== 'NOME'));
    if ((p.ancoras || []).length || needAnchors) {
      var va = lnValidateAnchors(p.ancoras, key);
      if (!va.ok) return _lnErr(va.erro);
      anchors = va.anchors;
      var doCliente = _lnAncorasDoCliente(info, anchors);
      if (doCliente.length) return _lnErr('Estas frases são dados do cliente, não do tipo de documento: ' + doCliente.join(' | '));
    }
    // preenchido pelo ChatGPT? só vale se for a revisão em aberto deste arquivo
    var ext = p.origem === 'CHATGPT' && p.revisao_externa_id && r.revisao_externa && r.revisao_externa.id === p.revisao_externa_id ? r.revisao_externa : null;

    var docs = rsLoadDocs();
    var rule, doc, vars = {};
    if (p.modo === 'NOVO') {
      if (!String(p.nome_final || p.padrao || '').trim()) return _lnErr('Digite o nome do documento.');
      if (!destino) return _lnErr('Escolha a pasta de destino (Documentos, Societário ou Imóveis).');
      var nomeFinal = txSafeName(String(p.nome_final || '').replace(/^\d{3}[\s_\-]+/, ''));
      var prop = lnProposePattern(nomeFinal || p.padrao, text);
      var pattern = txSafeName(p.padrao || prop.pattern);
      if (!pattern || !/[A-Za-z]{3}/.test(pattern.replace(/\{[A-Z0-9_]+\}/g, ''))) return _lnErr('Padrão de nome inválido.');
      // o nome do tipo é opcional: sem ele, vale o nome que o operador deu ao documento
      var docType = String(p.document_type || '').trim() || lnTypeFromPattern(pattern);
      var pk = normKey(pattern);
      var clash = ctx.rules.filter(function (x) { return normKey(x.approved_pattern) === pk; })[0];
      if (clash && clash.status !== 'VIGENTE') return _lnErr('A regra ' + clash.rule_id + ' (desativada) tem esse padrão. Reative-a na aba Aprendizado ou use outro nome.');
      if (clash) return _lnErr('Já existe a regra ' + clash.rule_id + ' com esse padrão. Use "Tipo existente" e escolha ' + clash.rule_id + '.');
      var propVals = {};
      prop.variables.forEach(function (v) { propVals[v.name] = v; });
      var variables = lnPatternVars(pattern).map(function (n) {
        var fmt = propVals[n] ? propVals[n].format : lnFormatForVar(n);
        var val = (p.variaveis && p.variaveis[n]) || (propVals[n] && propVals[n].value) || null;
        if (val !== null) vars[n] = fmt === 'CNPJ' ? txDigits(val) : txSafeName(val);
        return { name: n, format: fmt, source: 'CONTEUDO_DOCUMENTAL_COMPROVADO; NAO_USAR_METADADOS_DO_DRIVE', required: true };
      });
      var newId = rsNextRuleId(ctx.rules);
      rule = {
        rule_id: newId, status: 'VIGENTE', document_type: docType, identification: comentario || null,
        recognition: { required_all: [], required_groups: [], forbidden_any: [], signals: anchors.slice() },
        auto_match: anchors.length >= 2, approved_pattern: pattern, variables: variables,
        extension: txExt(pattern) || null, syntax: { spaces_allowed_in_pattern: /\s/.test(pattern), case: 'AS_IS' },
        date_kind: null, example_approved: nomeFinal || null, supersedes_rule_id: null, provenance: 'painel_aprendizado',
        human_decision_evidence: { file_id: r.file_id, nome_anterior: r.nome_arquivo, nome_aprovado: nomeFinal, comentario: comentario || null, em: now },
        notes: comentario
      };
      doc = rsNewDoc(newId, 'NOVA', now);
      doc.regra = rule;
      doc.destination_bucket = destino;
    } else {
      rule = ctx.ruleById[p.rule_id];
      if (!rule) return _lnErr('Escolha o tipo de documento (regra).');
      doc = JSON.parse(JSON.stringify(docs.filter(function (d) { return d.rule_id === rule.rule_id; })[0] || rsNewDoc(rule.rule_id, 'AJUSTE', now)));
      delete doc._file_id;
      (rule.variables || []).forEach(function (v) {
        if (!v.required) return;
        var val = p.variaveis ? p.variaveis[v.name] : null;
        if (val === undefined || val === null || String(val).trim() === '') return;
        vars[v.name] = v.format === 'CNPJ' ? txDigits(val) : txSafeName(String(val).trim());
      });
      if (destino && (p.sempre_destino || !rtBucketFor(rule, key).bucket)) doc.destination_bucket = destino;
    }

    // o que foi ensinado
    var acoes = [];
    if (anchors.length >= 2) {
      doc.recognition_alternatives.push({ required_all: anchors, required_groups: [], forbidden_any: [], aprendido_de: { file_id: r.file_id, nome: r.nome_arquivo }, em: now });
      acoes.push('reconhecimento por ' + anchors.length + ' frases');
    }
    (rule.variables || []).forEach(function (v) {
      var val = vars[v.name];
      if (!val || !text) return;
      var label = lnLabelFor(val, v.format, text);
      if (!label) return;
      var check = exExtractOne(normText(text), rule, v, [{ label: label }]);
      if (check.value !== val) return;
      doc.variable_hints[v.name] = doc.variable_hints[v.name] || [];
      if (!doc.variable_hints[v.name].some(function (h) { return h.label === label; })) {
        doc.variable_hints[v.name].push({ label: label, em: now });
        acoes.push(v.name + ' vem depois de "' + label + '"');
      }
    });
    if (doc.destination_bucket) acoes.push('destino ' + doc.destination_bucket);
    var exemplo = { file_id: r.file_id, nome_anterior: r.nome_arquivo, cliente: r.acervo_cliente_nome, em: now, origem: ext ? 'CHATGPT' : 'PAINEL' };
    if (ext) { exemplo.revisao_id = ext.id; exemplo.resultado_file_id = ext.resultado_file_id || null; }
    doc.exemplos.push(exemplo);
    if (comentario) doc.comentarios.push({ em: now, texto: comentario });
    doc.atualizado_em = now;

    // conflito: as frases também reconheceriam arquivos já classificados como outro tipo?
    if (anchors.length) {
      var conflitos = _lnConflitos(ctx, rule.rule_id, anchors, r.file_id);
      if (conflitos.length) return _lnErr('Essas frases também aparecem em arquivo(s) de outro tipo: ' + conflitos.slice(0, 3).join(', ') + '. Escolha frases mais específicas.');
    }

    // valida o nome ANTES de gravar qualquer coisa
    var trial = rsApplyLearned(NOMENCLATURE_RULES, docs.filter(function (d) { return d.rule_id !== doc.rule_id; }).concat([doc]));
    plSetRules(ctx, trial);
    var effRule = ctx.ruleById[rule.rule_id];
    r.rule_id = effRule.rule_id;
    r.variaveis = vars;
    r.raw_fields = r.raw_fields || {};
    var test = cmComposeName(ctx.rules, effRule, r, text, '000');
    if (test.status !== 'OK') return _lnErr('Ainda falta informação para montar o nome: ' + cmMotivo(test));
    var bucket = destino || rtBucketFor(effRule, key).bucket;
    if (!bucket) return _lnErr('Escolha a pasta de destino.');
    exemplo.nome_proposto = test.finalFilename.replace(/^000_/, '');
    exemplo.destino = bucket;

    rsSaveDoc(doc);
    sysWriteKnowledgeDelta({
      schema: 'gaia-delta-nomenclatura/1.0', rule_id: rule.rule_id, tipo: doc.tipo,
      acao: p.modo === 'NOVO' ? 'NOVA_REGRA' : 'AJUSTE_DE_REGRA', ensinado: acoes, document_type: effRule.document_type,
      approved_pattern: effRule.approved_pattern, ancoras: anchors, destino: doc.destination_bucket || bucket,
      evidencia: { file_id: r.file_id, nome_anterior: r.nome_arquivo, cliente: r.acervo_cliente_nome }, comentario: comentario || null,
      em: now, origem: 'painel Gaia Office — Aprender e seguir' + (ext ? ' (preenchido pelo ChatGPT, revisão ' + ext.id + ')' : ''),
      revisao_id: ext ? ext.id : null
    });

    r.tipo_documental = effRule.rule_id;
    r.destino_bucket = bucket;
    r.reconhecido_por = 'OPERADOR';
    r.pertencimento_confirmado = true;
    r.nome_proposto = test.finalFilename.replace(/^000_/, '');
    r.motivo_revisao = null;
    r.etapa = 'PRONTO';
    r.aprendido_em = now;
    if (ext) { ext.status = 'APLICADO'; ext.aplicado_em = now; }
    var st;
    try { st = cmCommit(ctx, r, log); }
    catch (e) { r.etapa = 'PRONTO'; st = 'ERRO: ' + (e && e.message || e); }

    // Reconfere na hora os outros arquivos da Revisão com o que acabou de ser aprendido.
    // Reconhecidos ficam PRONTOS (o painel dispara a execução para movê-los); os demais continuam na Revisão.
    var reconhecidos = 0, pendentes = 0, t0 = Date.now();
    var quiet = function (n, m) { if (n === 'ok') log(n, m); };
    ctx.mapa.arquivos.forEach(function (x) {
      if (x.etapa !== 'REVISAO' || x.file_id === r.file_id || !x.ocr_ref || !LN_MOTIVOS_RECHECAR.test(String(x.motivo_revisao || ''))) return;
      var motivoAntes = x.motivo_revisao;
      x.etapa = 'LIDO';
      x.motivo_revisao = null;
      if (Date.now() - t0 > 20000) { pendentes++; return; }
      try {
        plStepClassify(ctx, x, quiet);
        if (x.etapa === 'PRONTO') reconhecidos++;
      } catch (e) {
        // o aprendizado já foi gravado; este arquivo só continua na Revisão
        x.etapa = 'REVISAO';
        x.motivo_revisao = motivoAntes;
        console.log('Reconferência falhou em ' + x.nome_arquivo + ': ' + e);
      }
    });
    ctx.saveMapa();

    var cur = jbGet();
    if (cur) {
      var jl = jbLogger(cur);
      jl('aprendi', 'Aprendido ' + effRule.rule_id + ' (' + effRule.document_type + '): ' + acoes.join('; '));
      logLines.forEach(function (l) { jl(l.n, l.m); });
    }
    return {
      ok: true, rule_id: effRule.rule_id, novo: p.modo === 'NOVO', acoes: acoes, status: st,
      nome_final: r.nome_final || r.nome_proposto, destino: r.destino_caminho || null, motivo: r.motivo_revisao,
      reconhecidos_agora: reconhecidos, reprocessar: pendentes, log: logLines
    };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

/** Frases que são dados do cliente (nome, CPF, endereço…). */
function _lnAncorasDoCliente(info, anchors) {
  return anchors.filter(function (a) {
    return (info.excluir_ancoras || []).some(function (x) { var xk = normKey(x); return xk && (txHas(a, xk) || txHas(xk, a)); });
  });
}

/** Arquivos já classificados como OUTRO tipo (vigente) que essas frases também reconheceriam. */
function _lnConflitos(ctx, ruleId, anchors, exceptFileId) {
  var conflitos = [];
  var vigente = function (id) { var r = ctx.ruleById[id]; return !r || r.status === 'VIGENTE'; };
  ctx.mapa.arquivos.filter(function (x) { return x.rule_id && x.rule_id !== ruleId && vigente(x.rule_id) && x.ocr_ref && x.file_id !== exceptFileId; })
    .slice(-25).forEach(function (x) {
      var t = normKey(ctx.textFor(x));
      if (t && anchors.every(function (a) { return txHas(t, a); })) conflitos.push(x.nome_final || x.nome_arquivo);
    });
  return conflitos;
}

/** Deixa o arquivo no acervo e tira da Revisão. */
function lnIgnorar(fileId) {
  return _lnMutate(fileId, function (r) { r.etapa = 'IGNORADO'; r.ignorado_em = nowIso(); });
}

/** Volta o arquivo para a fila (relê o texto só se não houver cache). */
function lnReprocessar(fileId) {
  return _lnMutate(fileId, function (r) {
    var ctl = r.controle;
    var keepOcr = r.ocr_ref, keepMd5 = r.ocr_md5, own = r.ocr_ref_proprio;
    plResetRecord(r, ctl);
    r.ocr_ref = keepOcr; r.ocr_md5 = keepMd5; r.ocr_ref_proprio = own;
    if (keepOcr && !ctl) r.etapa = 'LIDO';
  });
}

function _lnMutate(fileId, fn) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(90000)) return _lnErr('O sistema está ocupado. Tente de novo em alguns segundos.');
  try {
    var ctx = plLoadContext({ id: 'EDITAR' });
    var r = ctx.idx[fileId];
    if (!r) return _lnErr('Arquivo não encontrado.');
    fn(r);
    ctx.saveMapa();
    return { ok: true, etapa: r.etapa };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

/* ---------------- Aba Aprendizado: histórico e revisão ---------------- */

/**
 * Um cartão por aprendizado (cada "Aprender e seguir" e cada correção), mais recentes primeiro.
 * @param {Array} docs documentos aprendidos (rsLoadDocs)
 * @param {Object} base regras do código por rule_id
 * @param {Object} idx registros do MAPA por file_id
 */
function lnEventos(docs, base, idx) {
  var out = [];
  var docInfo = function (fileId, nomeAnterior, cliente, extra) {
    var rec = (idx || {})[fileId] || null;
    return {
      file_id: fileId || null, nome_anterior: nomeAnterior || (rec && rec.nome_arquivo) || null, cliente: cliente || (rec && rec.acervo_cliente_nome) || null,
      nome_final: (rec && (rec.nome_final || rec.nome_proposto)) || (extra && extra.nome_proposto) || null,
      local: (rec && rec.destino_caminho) || null, etapa: (rec && rec.etapa) || null,
      link: fileId ? 'https://drive.google.com/file/d/' + fileId + '/view' : null
    };
  };
  (docs || []).forEach(function (d) {
    var r = d.regra || (base || {})[d.rule_id] || {};
    var head = {
      rule_id: d.rule_id, tipo_regra: d.tipo, document_type: r.document_type || null, padrao: r.approved_pattern || null,
      regra_status: d.regra ? d.regra.status : 'VIGENTE', destino_atual: d.destination_bucket || null
    };
    var alts = d.recognition_alternatives || [], revog = d.revogados || [];
    var dicasEm = function (em) {
      var o = [];
      Object.keys(d.variable_hints || {}).forEach(function (v) {
        (d.variable_hints[v] || []).forEach(function (h) { if (h.em === em) o.push(v + ' vem depois de "' + h.label + '"'); });
      });
      return o;
    };
    var comEm = function (em) { return (d.comentarios || []).filter(function (c) { return c.em === em; }).map(function (c) { return c.texto; }); };
    (d.exemplos || []).forEach(function (ex) {
      var e = JSON.parse(JSON.stringify(head));
      e.id = d.rule_id + '@' + ex.em;
      e.em = ex.em;
      e.evento = d.tipo === 'NOVA' && ex.em === d.criado_em ? 'REGRA_NOVA' : 'AJUSTE';
      e.origem = ex.origem || 'PAINEL';
      e.revisao_id = ex.revisao_id || null;
      e.resultado_link = ex.resultado_file_id ? 'https://drive.google.com/file/d/' + ex.resultado_file_id + '/view' : null;
      e.documento = docInfo(ex.file_id, ex.nome_anterior, ex.cliente, ex);
      e.ancoras = alts.filter(function (a) { return a.em === ex.em; }).map(function (a) { return a.required_all || []; });
      e.ancoras_removidas = revog.filter(function (x) { return x.tipo === 'ANCORAS' && x.item && x.item.em === ex.em; })
        .map(function (x) { return x.item.required_all || []; });
      e.dicas = dicasEm(ex.em);
      e.destino = ex.destino || d.destination_bucket || null;
      e.comentarios = comEm(ex.em);
      e.correcoes = (d.correcoes || []).filter(function (c) { return c.evento_em === ex.em; }).length;
      e.revisavel = true;
      out.push(e);
    });
    (d.correcoes || []).forEach(function (c) {
      var e = JSON.parse(JSON.stringify(head));
      var ex = (d.exemplos || []).filter(function (x) { return x.em === c.evento_em; })[0] || {};
      e.id = d.rule_id + '@' + c.em;
      e.em = c.em;
      e.evento = 'CORRECAO';
      e.origem = 'PAINEL';
      e.corrige_em = c.evento_em;
      e.revisao_id = ex.revisao_id || null;
      e.documento = docInfo(c.file_id || ex.file_id, ex.nome_anterior, ex.cliente, ex);
      e.ancoras = alts.filter(function (a) { return a.em === c.em; }).map(function (a) { return a.required_all || []; });
      e.ancoras_removidas = [];
      e.dicas = [];
      e.mudancas = c.mudancas || [];
      e.comentarios = [c.comentario];
      e.revisavel = !!ex.em;
      out.push(e);
    });
  });
  return out.sort(function (a, b) { return String(b.em).localeCompare(String(a.em)); });
}

function lnAprendizado() {
  var base = {};
  NOMENCLATURE_RULES.forEach(function (r) { base[r.rule_id] = r; });
  var eventos = lnEventos(rsLoadDocs(), base, mapaIndex(_pMapa()));
  return { ok: true, total: eventos.length, eventos: eventos };
}

/** Contexto para revisar um aprendizado: frases do documento que podem virar novas âncoras. */
function lnAprendizadoContexto(ruleId, em) {
  var doc = rsFindDoc(ruleId);
  if (!doc) return _lnErr('Regra aprendida não encontrada.');
  var ex = (doc.exemplos || []).filter(function (x) { return x.em === em; })[0];
  if (!ex) return _lnErr('Aprendizado não encontrado. Atualize a lista.');
  var ctx = plLoadContext({ id: 'APRENDIZADO' });
  var rec = ctx.idx[ex.file_id];
  var text = rec ? ctx.textFor(rec) : '';
  var info = rec ? crInfoFor(ctx, rec.acervo_cliente_folder_id) : { excluir_ancoras: [] };
  return {
    ok: true, tem_texto: !!normKey(text), texto_total: text.length,
    ancoras: text ? txAnchorCandidates(text, info.excluir_ancoras, 30) : []
  };
}

/**
 * Corrige um aprendizado. Nada é apagado: o que sai vai para "revogados", tudo fica em "correcoes"
 * e no registro append-only de 5-OFFICE KNOWLEDGE. Arquivos já movidos não são renomeados.
 * p: {rule_id, evento_em, comentario, remover_ancoras?, remover_dicas?, novas_ancoras?[], destino?,
 *     document_type?, padrao?, desativar?, reativar?}
 */
function lnCorrigir(p) {
  p = p || {};
  var comentario = String(p.comentario || '').trim();
  if (!comentario) return _lnErr('Explique o que estava errado (fica no histórico).');
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(90000)) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  try {
    var orig = rsLoadDocs().filter(function (d) { return d.rule_id === p.rule_id; })[0];
    if (!orig) return _lnErr('Regra aprendida não encontrada.');
    var doc = JSON.parse(JSON.stringify(orig));
    delete doc._file_id;
    var ev = (doc.exemplos || []).filter(function (x) { return x.em === p.evento_em; })[0];
    if (!ev) return _lnErr('Aprendizado não encontrado. Atualize a lista.');
    var ctx = plLoadContext({ id: 'CORRIGIR' });
    var now = nowIso(), mudancas = [];
    doc.revogados = doc.revogados || [];
    doc.correcoes = doc.correcoes || [];
    doc.comentarios = doc.comentarios || [];
    doc.recognition_alternatives = doc.recognition_alternatives || [];

    if (p.remover_ancoras) {
      var fica = [], sai = [];
      doc.recognition_alternatives.forEach(function (a) { (a.em === ev.em ? sai : fica).push(a); });
      if (sai.length) {
        doc.recognition_alternatives = fica;
        sai.forEach(function (a) { doc.revogados.push({ em: now, tipo: 'ANCORAS', item: a, motivo: comentario }); });
        mudancas.push('frases removidas: ' + sai.map(function (a) { return (a.required_all || []).join(' + '); }).join(' | '));
      }
    }
    if (p.remover_dicas) {
      Object.keys(doc.variable_hints || {}).forEach(function (v) {
        var keep = [];
        (doc.variable_hints[v] || []).forEach(function (h) {
          if (h.em !== ev.em) { keep.push(h); return; }
          doc.revogados.push({ em: now, tipo: 'DICA', variavel: v, item: h, motivo: comentario });
          mudancas.push('dica removida: ' + v + ' depois de "' + h.label + '"');
        });
        doc.variable_hints[v] = keep;
      });
    }
    if ((p.novas_ancoras || []).length) {
      var rec = ctx.idx[ev.file_id];
      var key = rec ? normKey(ctx.textFor(rec)) : '';
      if (!key) return _lnErr('Não tenho o texto deste documento para conferir as frases novas.');
      var va = lnValidateAnchors(p.novas_ancoras, key);
      if (!va.ok) return _lnErr(va.erro);
      var doCliente = _lnAncorasDoCliente(crInfoFor(ctx, rec.acervo_cliente_folder_id), va.anchors);
      if (doCliente.length) return _lnErr('Estas frases são dados do cliente, não do tipo de documento: ' + doCliente.join(' | '));
      var conflitos = _lnConflitos(ctx, doc.rule_id, va.anchors, ev.file_id);
      if (conflitos.length) return _lnErr('Essas frases também aparecem em arquivo(s) de outro tipo: ' + conflitos.slice(0, 3).join(', ') + '.');
      doc.recognition_alternatives.push({
        required_all: va.anchors, required_groups: [], forbidden_any: [],
        aprendido_de: { file_id: ev.file_id, nome: ev.nome_anterior }, em: now, correcao_de: ev.em
      });
      mudancas.push('frases novas: ' + va.anchors.join(' + '));
    }
    if (p.destino && p.destino !== doc.destination_bucket) {
      if (CLIENTES_CFG.BUCKETS.indexOf(p.destino) === -1) return _lnErr('Pasta de destino inválida.');
      mudancas.push('destino ' + (doc.destination_bucket || 'pelo contexto') + ' → ' + p.destino);
      doc.destination_bucket = p.destino;
    }
    if (doc.tipo === 'NOVA' && doc.regra) {
      var tipo = String(p.document_type || '').trim();
      if (tipo && tipo !== doc.regra.document_type) {
        mudancas.push('nome do tipo "' + doc.regra.document_type + '" → "' + tipo + '"');
        doc.regra.document_type = tipo;
      }
      var padrao = p.padrao ? txSafeName(String(p.padrao)) : '';
      if (padrao && padrao !== doc.regra.approved_pattern) {
        if (!/[A-Za-z]{3}/.test(padrao.replace(/\{[A-Z0-9_]+\}/g, ''))) return _lnErr('Padrão de nome inválido.');
        var pk = normKey(padrao);
        var clash = ctx.rules.filter(function (x) { return x.rule_id !== doc.rule_id && normKey(x.approved_pattern) === pk; })[0];
        if (clash) return _lnErr('A regra ' + clash.rule_id + ' já usa esse padrão.');
        var velhas = {};
        (doc.regra.variables || []).forEach(function (v) { velhas[v.name] = v; });
        doc.regra.variables = lnPatternVars(padrao).map(function (n) {
          return velhas[n] || { name: n, format: lnFormatForVar(n), source: 'CONTEUDO_DOCUMENTAL_COMPROVADO; NAO_USAR_METADADOS_DO_DRIVE', required: true };
        });
        doc.regra.extension = txExt(padrao) || null;
        mudancas.push('padrão ' + doc.regra.approved_pattern + ' → ' + padrao);
        doc.regra.approved_pattern = padrao;
      }
      if (p.desativar && doc.regra.status === 'VIGENTE') { doc.regra.status = 'REVOGADA'; mudancas.push('regra desativada'); }
      if (p.reativar && doc.regra.status !== 'VIGENTE') { doc.regra.status = 'VIGENTE'; mudancas.push('regra reativada'); }
    }
    if (!mudancas.length) return _lnErr('Nenhuma mudança marcada.');

    doc.correcoes.push({ em: now, evento_em: ev.em, file_id: ev.file_id, mudancas: mudancas, comentario: comentario });
    doc.comentarios.push({ em: now, texto: 'Correção: ' + comentario });
    doc.atualizado_em = now;
    rsSaveDoc(doc);
    sysWriteKnowledgeDelta({
      schema: 'gaia-delta-nomenclatura/1.0', rule_id: doc.rule_id, tipo: doc.tipo, acao: 'CORRECAO_DE_APRENDIZADO',
      corrige: ev.em, mudancas: mudancas, revisao_id: ev.revisao_id || null,
      evidencia: { file_id: ev.file_id, nome_anterior: ev.nome_anterior, cliente: ev.cliente }, comentario: comentario,
      em: now, origem: 'painel Gaia Office — Aprendizado › Revisar'
    });
    var cur = jbGet();
    if (cur) jbLogger(cur)('aprendi', 'Correção em ' + doc.rule_id + ': ' + mudancas.join('; '));
    return { ok: true, rule_id: doc.rule_id, mudancas: mudancas };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}
