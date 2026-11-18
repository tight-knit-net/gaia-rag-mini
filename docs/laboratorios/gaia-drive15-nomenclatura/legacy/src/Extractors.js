/**
 * Extractors — extrai as variáveis do nome ({DATA}, {PROTOCOLO}, {CNPJ}...) do texto OCR.
 * Puro (sem Drive). Nunca inventa: valor só entra se for ÚNICO para o rótulo ou no
 * documento; senão devolve "candidates" para o operador escolher na Revisão.
 *
 * Ordem: dicas aprendidas (variable_hints da regra) → rótulos padrão → valor único no texto.
 */

var EX_DATE_LABELS = {
  EMISSAO: ['DATA DE EMISSAO', 'DATA DA EMISSAO', 'DATA EMISSAO', 'EMITIDO EM', 'EMITIDA EM', 'EMITIDO NO DIA', 'GERADO EM', 'EMISSAO'],
  VALIDADE: ['VALIDO ATE', 'VALIDA ATE', 'DATA DE VALIDADE', 'VALIDADE'],
  VENCIMENTO: ['PAGAR ESTE DOCUMENTO ATE', 'DATA DE VENCIMENTO', 'DATA DO VENCIMENTO', 'VENCIMENTO'],
  ASSINATURA: ['ASSINADO DIGITALMENTE EM', 'ASSINADO ELETRONICAMENTE EM', 'DATA DA ASSINATURA', 'DATA DE ASSINATURA', 'ASSINADO EM'],
  REGISTRO: ['CERTIFICO O REGISTRO EM', 'CERTIFICO REGISTRO EM', 'REGISTRADO EM', 'DATA DO REGISTRO'],
  EFEITOS: ['DATA DOS EFEITOS']
};

var EX_YEAR_LABELS = ['ANO DE VIGENCIA', 'ANO BASE', 'EXERCICIO', 'VALIDO PARA O ANO', 'VIGENCIA', 'ANO'];

var EX_TOKEN = '(?=[A-Z0-9.\\/\\-]*\\d)[A-Z0-9][A-Z0-9.\\/\\-]{2,30}[A-Z0-9]';
var EX_TOKEN_GAP = '[^A-Z0-9\\n]{0,4}(?:N(?:O|UMERO|R)?[^A-Z0-9\\n]{0,3})?';

var EX_TOKEN_SPECS = {
  PROTOCOLO_REDESIM: { labels: ['PROTOCOLO REDESIM', 'NUMERO DO PROTOCOLO', 'PROTOCOLO'], shape: '[A-Z]{2,4}\\d{6,14}' },
  PROTOCOLO: { labels: ['NUMERO DO PROTOCOLO', 'PROTOCOLO'], shape: EX_TOKEN },
  NUMERO_OFICIAL: { labels: ['NUMERO DA SOLICITACAO', 'NUMERO DO PROTOCOLO', 'PROTOCOLO', 'SOLICITACAO'], shape: EX_TOKEN },
  NUMERO_ART: { labels: ['NUMERO DA ART', 'ART NUMERO', 'ART'], shape: '\\d{6,14}(?:-\\d)?' },
  NUMERO_DOCUMENTO: { labels: ['NUMERO DO DOCUMENTO', 'NR DO DOCUMENTO', 'NOSSO NUMERO'], shape: EX_TOKEN },
  NUMERO: { labels: ['NUMERO DO PROCESSO', 'PROCESSO'], shape: EX_TOKEN }
};

function exDateLabelsFor(dateKind) {
  var k = String(dateKind || '').toUpperCase(), g = [];
  if (k.indexOf('VALIDADE') >= 0) g.push('VALIDADE');
  if (k.indexOf('VENCIMENTO') >= 0) g.push('VENCIMENTO');
  if (k.indexOf('EMISSAO') >= 0) g.push('EMISSAO');
  if (k.indexOf('ASSINATURA') >= 0 || k.indexOf('FIRMA') >= 0) g.push('ASSINATURA');
  if (k.indexOf('INSTRUMENTO') >= 0) g.push('ASSINATURA', 'EFEITOS', 'REGISTRO');
  if (k.indexOf('DOCUMENTAL') >= 0) g.push('EMISSAO', 'ASSINATURA');
  var out = [];
  g.forEach(function (x) { (EX_DATE_LABELS[x] || []).forEach(function (l) { if (out.indexOf(l) === -1) out.push(l); }); });
  return out;
}

function exLabelPattern(label) {
  return normKey(label).split(' ').map(txEscapeRe).join('[^A-Z0-9]{1,3}');
}

/** Valores distintos encontrados logo depois de um rótulo. nt = normText. */
function exAfterLabel(nt, label, shape, gap) {
  if (!normKey(label)) return [];
  var re = new RegExp('(?:^|[^A-Z0-9])' + exLabelPattern(label) + gap + '(' + shape + ')', 'g');
  var out = [], m;
  while ((m = re.exec(nt)) !== null) {
    if (out.indexOf(m[1]) === -1) out.push(m[1]);
    if (m[0].length === 0) re.lastIndex++;
  }
  return out;
}

function _exUniq(arr) { var o = []; (arr || []).forEach(function (x) { if (x !== null && x !== undefined && o.indexOf(x) === -1) o.push(x); }); return o; }

/** Percorre rótulos em ordem; o primeiro com exatamente 1 valor vence. */
function _exByLabels(nt, labels, shape, gap, transform) {
  var cands = [];
  for (var i = 0; i < labels.length; i++) {
    var vals = _exUniq(exAfterLabel(nt, labels[i], shape, gap).map(transform || function (x) { return x; }));
    if (vals.length === 1) return { value: vals[0], via: 'ROTULO:' + labels[i] };
    vals.forEach(function (v) { if (cands.indexOf(v) === -1) cands.push(v); });
  }
  return { value: null, candidates: cands };
}

function _hintLabels(hints) { return (hints || []).map(function (h) { return h && h.label; }).filter(Boolean); }

function exExtractDate(nt, dateKind, hints) {
  var labels = _hintLabels(hints).concat(exDateLabelsFor(dateKind));
  var r = _exByLabels(nt, labels, TX_DATE_SHAPE, '[^0-9]{0,40}?', txParseDate);
  if (r.value) return r;
  var all = txFindDates(nt);
  if (all.length === 1) return { value: all[0], via: 'DATA_UNICA' };
  return { value: null, candidates: _exUniq(r.candidates.concat(all)).slice(0, 15) };
}

function _exYearOf(d) { return d ? d.slice(-4) : null; }

function exExtractYear(nt, dateKind, hints) {
  var r = _exByLabels(nt, _hintLabels(hints).concat(EX_YEAR_LABELS), '(?:19|20)\\d{2}(?!\\d)', '[^0-9]{0,20}?');
  if (r.value) return r;
  var d = exExtractDate(nt, dateKind || 'EMISSAO', []);
  if (d.value) return { value: _exYearOf(d.value), via: 'ANO_DA_DATA:' + d.via };
  var years = _exUniq(txFindDates(nt).map(_exYearOf));
  if (years.length === 1) return { value: years[0], via: 'ANO_UNICO' };
  return { value: null, candidates: _exUniq(r.candidates.concat(years)).slice(0, 10) };
}

function exExtractCnpj(nt, hints) {
  var r = _exByLabels(nt, _hintLabels(hints), '\\d{2}\\.?\\d{3}\\.?\\d{3}\\/?\\d{4}-?\\d{2}', '[^0-9]{0,20}?', txDigits);
  if (r.value && txIsCnpj(r.value)) return r;
  var all = txFindCnpjs(nt);
  if (all.length === 1) return { value: all[0], via: 'CNPJ_UNICO' };
  return { value: null, candidates: all };
}

function exExtractOrdinal(nt) {
  var PAL = { PRIMEIRA: 1, SEGUNDA: 2, TERCEIRA: 3, QUARTA: 4, QUINTA: 5, SEXTA: 6, SETIMA: 7, OITAVA: 8, NONA: 9, DECIMA: 10 };
  var vals = [], m;
  var re = /(?:^|[^0-9])(\d{1,3})\s*(?:A|O|\.)?\s*ALTERACAO/g;
  while ((m = re.exec(nt)) !== null) vals.push(String(Number(m[1])));
  var re2 = /\b(PRIMEIRA|SEGUNDA|TERCEIRA|QUARTA|QUINTA|SEXTA|SETIMA|OITAVA|NONA|DECIMA)\s+ALTERACAO/g;
  while ((m = re2.exec(nt)) !== null) vals.push(String(PAL[m[1]]));
  vals = _exUniq(vals);
  return vals.length === 1 ? { value: vals[0], via: 'ORDINAL' } : { value: null, candidates: vals };
}

function _exMoneyToInt(s) {
  var t = String(s).replace(/R\$\s*/, '').replace(/\./g, '');
  return t.split(',')[0];
}

function exExtractMoney(nt, hints) {
  var labels = _hintLabels(hints).concat(['VALOR TOTAL RECEBIDO', 'VALOR RECEBIDO', 'VALOR TOTAL', 'TOTAL A PAGAR', 'VALOR']);
  return _exByLabels(nt, labels, '(?:R\\$\\s*)?\\d{1,3}(?:\\.\\d{3})*(?:,\\d{2})?', '[^0-9]{0,20}?', _exMoneyToInt);
}

function exExtractParcela(nt, hints) {
  return _exByLabels(nt, _hintLabels(hints).concat(['NUMERO DA PARCELA', 'PARCELA']), '\\d{1,2}(?!\\d)', '[^0-9\\n]{0,6}?',
    function (x) { return txPad(Number(x), 2); });
}

function exExtractAnoParcela(nt, hints) {
  var r = _exByLabels(nt, _hintLabels(hints).concat(['PERIODO DE APURACAO', 'COMPETENCIA']), '\\d{2}\\/(?:19|20)\\d{2}', '[^0-9]{0,20}?',
    function (x) { return x.slice(-4); });
  if (r.value) return r;
  return exExtractYear(nt, null, []);
}

/** Campo bruto usado por extração declarada na regra (ex.: NOM-018 inscrição imobiliária). */
function exExtractRawField(nt, sourceField) {
  if (sourceField === 'inscricao_imobiliaria_completa') {
    return _exByLabels(nt, ['INSCRICAO IMOBILIARIA', 'INSCRICAO CADASTRAL', 'INSCRICAO'], '\\d[\\d.\\-\\/]{10,30}\\d', '[^0-9\\n]{0,12}?');
  }
  return { value: null, candidates: [] };
}

function _exShapeFor(format) {
  switch (format) {
    case 'DD-MM-AAAA': return { shape: TX_DATE_SHAPE, gap: '[^0-9]{0,40}?', tr: txParseDate };
    case 'AAAA': return { shape: '(?:19|20)\\d{2}(?!\\d)', gap: '[^0-9]{0,20}?' };
    case 'CNPJ': return { shape: '\\d{2}\\.?\\d{3}\\.?\\d{3}\\/?\\d{4}-?\\d{2}', gap: '[^0-9]{0,20}?', tr: txDigits };
    case 'NN': return { shape: '\\d{1,2}(?!\\d)', gap: '[^0-9\\n]{0,6}?', tr: function (x) { return txPad(Number(x), 2); } };
    case 'NNN': return { shape: '\\d{3}(?!\\d)', gap: '[^0-9\\n]{0,6}?' };
    case 'ORDINAL': return { shape: '\\d{1,3}(?!\\d)', gap: '[^0-9\\n]{0,6}?' };
    case 'VALOR_INTEIRO_BRL': return { shape: '(?:R\\$\\s*)?\\d{1,3}(?:\\.\\d{3})*(?:,\\d{2})?', gap: '[^0-9]{0,20}?', tr: _exMoneyToInt };
    default: return { shape: EX_TOKEN, gap: '[^A-Z0-9]{0,6}(?:N(?:O|UMERO|R)?[^A-Z0-9]{0,3})?' }; // rótulo aprendido pode estar na linha de cima
  }
}

/** Extrai UMA variável. */
function exExtractOne(nt, rule, v, hints) {
  var f = v.format, n = v.name;
  if (f === 'DD-MM-AAAA') return exExtractDate(nt, rule.date_kind, hints);
  if (f === 'AAAA') return n === 'ANO_PARCELA' ? exExtractAnoParcela(nt, hints) : exExtractYear(nt, rule.date_kind, hints);
  if (f === 'CNPJ') return exExtractCnpj(nt, hints);
  if (f === 'ORDINAL') { var h = _exFromHints(nt, f, hints); return h.value ? h : exExtractOrdinal(nt); }
  if (f === 'VALOR_INTEIRO_BRL') return exExtractMoney(nt, hints);
  if (f === 'NN' && /PARCELA/.test(n)) return exExtractParcela(nt, hints);
  var fromHints = _exFromHints(nt, f, hints);
  if (fromHints.value) return fromHints;
  var spec = EX_TOKEN_SPECS[n];
  if (spec) {
    var r = _exByLabels(nt, spec.labels, spec.shape, EX_TOKEN_GAP, txSafeName);
    r.candidates = _exUniq((fromHints.candidates || []).concat(r.candidates || []));
    return r;
  }
  return fromHints;
}

function _exFromHints(nt, format, hints) {
  var labels = _hintLabels(hints);
  if (!labels.length) return { value: null, candidates: [] };
  var s = _exShapeFor(format);
  return _exByLabels(nt, labels, s.shape, s.gap, s.tr || txSafeName);
}

/**
 * Extrai todas as variáveis obrigatórias de uma regra.
 * @return {{provided:Object, missing:string[], candidates:Object, rawFields:Object}}
 */
function exExtractVariables(rule, rawText) {
  var nt = normText(rawText);
  var key = normKey(rawText);
  var hints = (rule && rule.variable_hints) || {};
  var provided = {}, missing = [], candidates = {}, rawFields = {};
  ((rule && rule.variables) || []).forEach(function (v) {
    if (!v.required) return;
    if (v.name === 'TEOR' && rule.family) return; // resolvido pela família DARE (resolveNome)
    if (v.extraction) {
      var src = v.extraction.source_field;
      var rf = exExtractRawField(nt, src);
      if (rf.value) rawFields[src] = rf.value;
      else { missing.push(v.name); if (rf.candidates && rf.candidates.length) candidates[v.name] = rf.candidates; }
      return;
    }
    var res = exExtractOne(nt, rule, v, hints[v.name] || []);
    if (res.value !== null && res.value !== undefined && validateFormat(res.value, v.format)) provided[v.name] = res.value;
    else {
      missing.push(v.name);
      if (res.candidates && res.candidates.length) candidates[v.name] = res.candidates.slice(0, 15);
    }
  });
  if (rule && rule.variant_when_consolidated && (txHas(key, 'CONSOLIDACAO DO CONTRATO SOCIAL') || txHas(key, 'CONTRATO SOCIAL CONSOLIDADO'))) {
    provided.consolidado = true;
  }
  return { provided: provided, missing: missing, candidates: candidates, rawFields: rawFields };
}
