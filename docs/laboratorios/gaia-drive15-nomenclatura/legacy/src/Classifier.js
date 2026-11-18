/**
 * Classifier — decide QUAL regra de nomenclatura se aplica a um arquivo. Puro.
 *
 * Automático (sem humano) só quando for determinístico:
 *   1) âncoras da regra encontradas no TEXTO (base ou aprendidas), com resultado único; ou
 *   2) o TÍTULO do documento (primeiras linhas) começa com o tipo da regra, com resultado único; ou
 *   3) o NOME atual do arquivo já segue o padrão aprovado de uma regra (ex.: renomeado à mão).
 * Caso contrário → REVISAO, com sugestões por pontuação (só para ajudar o operador).
 */

/** Monta o regex que reconhece um nome de arquivo já no padrão da regra. */
function clBuildNameMatcher(rule) {
  var pattern = String(rule.approved_pattern || '');
  if (!pattern) return null;
  var ext = txExt(pattern);
  var body = ext ? txStem(pattern) : pattern; // a extensão real do arquivo pode ser outra (.jpg, .docx)
  var fmt = {};
  (rule.variables || []).forEach(function (v) { fmt[v.name] = v.format; });
  var parts = body.split(/(\{[A-Z0-9_]+\})/);
  var src = '', vars = [], literal = 0;
  parts.forEach(function (p) {
    if (!p) return;
    var ph = p.match(/^\{([A-Z0-9_]+)\}$/);
    if (ph) {
      vars.push(ph[1]);
      src += '(' + _clShape(fmt[ph[1]]) + ')';
      return;
    }
    var lit = txStrip(p);
    literal += lit.replace(/[^A-Za-z0-9]/g, '').length;
    var chunk = '', inSep = false;
    for (var i = 0; i < lit.length; i++) {
      var c = lit[i];
      if (/[\s_\-]/.test(c)) { if (!inSep) { chunk += '[\\s_\\-]+'; inSep = true; } }
      else { chunk += txEscapeRe(c); inSep = false; }
    }
    src += chunk;
  });
  if (literal < 3 && !(vars.length === 0 && literal >= 2)) return null; // "RG" sozinho ainda é específico
  var re = new RegExp('^(?:\\d{3}[\\s_\\-]+)?' + src + '(?:\\.[A-Za-z0-9]{1,6})?$', 'i');
  return { re: re, vars: vars, literal: literal };
}

function _clShape(format) {
  switch (format) {
    case 'DD-MM-AAAA': return '\\d{2}[\\-_.]\\d{2}[\\-_.]\\d{4}';
    case 'AAAA': return '\\d{4}';
    case 'NN': return '\\d{1,2}';
    case 'NNN': return '\\d{3}';
    case 'CNPJ': return '\\d{14}';
    case 'ORDINAL': return '\\d{1,3}';
    case 'VALOR_INTEIRO_BRL': return '\\d+';
    default: return '[A-Za-z0-9][A-Za-z0-9._\\-]*?'; // sem espaço/parênteses: "dbe (1).pdf" não vira protocolo "(1)"
  }
}

function _clNormVar(format, v) {
  if (format === 'DD-MM-AAAA') return v.replace(/[_.]/g, '-');
  if (format === 'NN') return txPad(Number(v), 2);
  return v;
}

/** Regras cujo padrão casa com o nome atual do arquivo (mais específica primeiro). */
function clMatchByFilename(rules, fileName) {
  var name = txStrip(String(fileName || '')).trim();
  if (!name) return [];
  var out = [];
  (rules || []).forEach(function (r) {
    if (r.status !== 'VIGENTE') return;
    var mm = r._nameMatcher !== undefined ? r._nameMatcher : clBuildNameMatcher(r);
    if (!mm) return;
    var m = name.match(mm.re);
    if (!m) return;
    var fmt = {}, provided = {}, ok = true;
    (r.variables || []).forEach(function (v) { fmt[v.name] = v.format; });
    mm.vars.forEach(function (n, i) {
      var val = _clNormVar(fmt[n], m[i + 1]);
      if (fmt[n] && !validateFormat(val, fmt[n])) ok = false;
      provided[n] = val;
    });
    if (ok) out.push({ rule: r, provided: provided, literal: mm.literal });
  });
  out.sort(function (a, b) { return b.literal - a.literal; });
  return out;
}

var CL_HEAD_CHARS = 250;
var CL_STOP = { DE: 1, DA: 1, DO: 1, DAS: 1, DOS: 1, PARA: 1, COM: 1, SEM: 1, UMA: 1, UM: 1, REFERENTE: 1, DOCUMENTO: 1, ELETRONICA: 1 };

/** Pontuação de apoio (sugestões na Revisão). Nunca decide sozinha. */
function clScoreRules(rules, keyText, topN) {
  if (!keyText) return [];
  var out = [];
  // Cabeçalho (título) do documento: o tipo escrito ali vale mais que o mesmo texto citado no corpo.
  var head = keyText.slice(0, CL_HEAD_CHARS);
  (rules || []).forEach(function (r) {
    if (r.status !== 'VIGENTE') return;
    var score = 0, matched = [], tipo = false;
    var dt = normKey(r.document_type);
    if (dt.length >= 6 && txHas(keyText, dt)) {
      score += 100; matched.push(dt); tipo = true;
      if (txHas(head, dt)) score += 60;
    }
    var sigs = ((r.recognition && r.recognition.signals) || []).concat((r.recognition && r.recognition.required_all) || []);
    (r.recognition_alternatives || []).forEach(function (a) { sigs = sigs.concat(a.required_all || []); });
    var sigScore = 0, seen = {};
    sigs.forEach(function (s) {
      var k = normKey(s);
      if (k.length < 3 || seen[k]) return;
      seen[k] = 1;
      if (txHas(keyText, k)) { sigScore += 15; matched.push(k); }
    });
    score += Math.min(sigScore, 60);
    var toks = {};
    normKey(r.identification).split(' ').forEach(function (t) { if (t.length >= 4 && !CL_STOP[t]) toks[t] = 1; });
    var tk = Object.keys(toks);
    if (tk.length >= 3) {
      var hits = tk.filter(function (t) { return txHas(keyText, t); }).length;
      score += Math.round((hits / tk.length) * 40);
    }
    if (score >= 30) out.push({ rule_id: r.rule_id, document_type: r.document_type, score: score, tipo_no_texto: tipo, matched: matched.slice(0, 6) });
  });
  out.sort(function (a, b) { return b.score - a.score; });
  return out.slice(0, topN || 5);
}

var CL_TITLE_LINES = 15;

/**
 * Reconhecimento pelo TÍTULO: uma das primeiras linhas do documento COMEÇA com o tipo da regra
 * (ex.: "AUTO DE FISCALIZAÇÃO Nº ..." → NOM-003). Título quebrado em até 3 linhas curtas é juntado.
 * Citar o tipo no meio de uma frase não conta. Com tipos aninhados, vale o mais longo.
 * @return {Object[]} regras (0, 1 ou mais)
 */
function clMatchByTitle(rules, rawText, ext) {
  var lines = String(rawText || '').split(/\r?\n/).map(normKey).filter(Boolean).slice(0, CL_TITLE_LINES);
  if (!lines.length) return [];
  var heads = [];
  lines.forEach(function (l, i) {
    heads.push(l);
    var acc = l;
    for (var j = i + 1; j < Math.min(i + 3, lines.length) && acc.split(' ').length <= 4; j++) {
      acc += ' ' + lines[j];
      heads.push(acc);
    }
  });
  var key = normKey(rawText);
  var hits = [];
  (rules || []).forEach(function (r) {
    if (r.status !== 'VIGENTE') return;
    if (r.extension && ext && r.extension !== ext) return;
    var dt = normKey(r.document_type);
    if (dt.length < 10 || dt.split(' ').length < 2) return;
    var forb = (r.recognition && r.recognition.forbidden_any) || [];
    if (forb.some(function (f) { var k = normKey(f); return k && txHas(key, k); })) return;
    var ok = heads.some(function (h) { return h === dt || h.indexOf(dt + ' ') === 0; });
    if (ok) hits.push({ rule: r, dt: dt });
  });
  hits = hits.filter(function (h) {
    return !hits.some(function (o) { return o !== h && o.dt.length > h.dt.length && o.dt.indexOf(h.dt) === 0; });
  });
  return hits.map(function (h) { return h.rule; });
}

/**
 * @param {Object[]} rules regras de runtime (base + aprendidas).
 * @param {{text:string, fileName:string}} input
 * @return {{status:'OK', rule:Object, via:string, provided:Object} | {status:'REVISAO', motivo:string, candidatos?:string[], sugestoes:Object[]}}
 */
function clClassify(rules, input) {
  var key = normKey(input.text || '');
  var ext = txExt(input.fileName || '');
  var textM = key ? matchRulesScored(rules, [key]) : [];
  // Mesmo documento com versões .pdf/.docx (ex.: NOM-041 x NOM-042): a extensão real desempata.
  if (textM.length > 1 && ext) {
    var byExt = textM.filter(function (m) { return !m.rule.extension || m.rule.extension === ext; });
    if (byExt.length) textM = byExt;
  }
  var nameM = clMatchByFilename(rules, input.fileName);
  var nameTop = null;
  if (nameM.length === 1 || (nameM.length > 1 && nameM[0].literal > nameM[1].literal)) nameTop = nameM[0];

  var sug = function () { return clScoreRules(rules, key, 5); };

  if (textM.length === 1) {
    var r = textM[0].rule;
    if (nameTop && nameTop.rule.rule_id !== r.rule_id) {
      return { status: 'REVISAO', motivo: 'CONFLITO_TEXTO_X_NOME', candidatos: [r.rule_id, nameTop.rule.rule_id], sugestoes: sug() };
    }
    return { status: 'OK', rule: r, via: 'TEXTO', provided: nameTop ? nameTop.provided : {} };
  }
  if (textM.length > 1) {
    if (nameTop) {
      var same = textM.filter(function (m) { return m.rule.rule_id === nameTop.rule.rule_id; })[0];
      if (same) return { status: 'OK', rule: same.rule, via: 'TEXTO+NOME', provided: nameTop.provided };
    }
    textM.sort(function (a, b) { return b.strength - a.strength; });
    if (textM[0].strength >= textM[1].strength + 10) {
      return { status: 'OK', rule: textM[0].rule, via: 'TEXTO_MAIS_ESPECIFICO', provided: {} };
    }
    return { status: 'REVISAO', motivo: 'AMBIGUO', candidatos: textM.map(function (m) { return m.rule.rule_id; }), sugestoes: sug() };
  }
  var titleM = key ? clMatchByTitle(rules, input.text, ext) : [];
  if (titleM.length === 1) {
    if (nameTop && nameTop.rule.rule_id !== titleM[0].rule_id) {
      return { status: 'REVISAO', motivo: 'CONFLITO_TEXTO_X_NOME', candidatos: [titleM[0].rule_id, nameTop.rule.rule_id], sugestoes: sug() };
    }
    return { status: 'OK', rule: titleM[0], via: 'TITULO', provided: nameTop ? nameTop.provided : {} };
  }
  if (nameTop) return { status: 'OK', rule: nameTop.rule, via: 'NOME', provided: nameTop.provided };
  if (titleM.length > 1) {
    return { status: 'REVISAO', motivo: 'AMBIGUO', candidatos: titleM.map(function (x) { return x.rule_id; }), sugestoes: sug() };
  }
  if (nameM.length > 1) {
    return { status: 'REVISAO', motivo: 'AMBIGUO', candidatos: nameM.map(function (m) { return m.rule.rule_id; }), sugestoes: sug() };
  }
  return { status: 'REVISAO', motivo: key ? 'TIPO_NAO_RECONHECIDO' : 'SEM_TEXTO', sugestoes: sug() };
}
