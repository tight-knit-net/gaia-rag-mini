/**
 * NomenclatureEngine — motor determinístico de nomenclatura (fail-closed).
 *
 * Autoridade: 2-OPERAÇÃO GAIA OFFICE/04_PADROES_OPERACIONAIS/02_NOMENCLATURA.
 * Contrato: FINAL_FILENAME = NNN + "_" + approved_pattern (preenchido).
 *
 * PRINCÍPIO: sem regra aplicável, variável comprovada ou reconhecimento único,
 * NÃO inventa nome — retorna PENDENTE_NOMENCLATURA. (fail-closed)
 *
 * Este arquivo é PURA LÓGICA: não lê nem escreve no Drive. Testável offline.
 * A fonte de regras (data/nomenclature_rules.normalized.json) é injetada.
 */

var NomenclatureStatus = {
  OK: 'OK',
  PENDENTE: 'PENDENTE_NOMENCLATURA'
};

/**
 * Normaliza o ID do cliente para exatamente 3 dígitos (NNN).
 * @param {string|number} clientId
 * @return {?string} "027" ou null se inválido.
 */
function normalizeNNN(clientId) {
  if (clientId === null || clientId === undefined) return null;
  var s = String(clientId).trim();
  if (!/^[0-9]{1,3}$/.test(s)) return null; // só dígitos, até 3
  return ('000' + s).slice(-3);
}

/**
 * Preenche os placeholders {VAR} do approved_pattern com as variáveis provadas.
 * @param {Object} rule regra normalizada.
 * @param {Object} provided mapa { NOME_DA_VARIAVEL: valorComprovado }.
 * @return {{ok:boolean, value?:string, missing?:string[]}}
 */
/**
 * Valida um valor contra o formato declarado da variável. Formatos desconhecidos
 * passam (não bloqueiam). Retorna true/false.
 */
function validateFormat(value, format) {
  var s = String(value);
  switch (format) {
    case 'DD-MM-AAAA': return /^\d{2}-\d{2}-\d{4}$/.test(s);
    case 'AAAA': return /^\d{4}$/.test(s);
    case 'NN': return /^\d{2}$/.test(s);
    case 'NNN': return /^\d{3}$/.test(s);
    case 'CNPJ': return /^\d{14}$/.test(s.replace(/\D/g, '')) && /^\d{14}$/.test(s);
    case 'ORDINAL': return /^\d{1,3}$/.test(s);
    case 'VALOR_INTEIRO_BRL': return /^\d+$/.test(s);
    default: return true; // TEXTO, SUBTIPO, formatos desconhecidos: não bloqueiam
  }
}

function fillPattern(rule, provided) {
  provided = provided || {};
  var pattern = rule.approved_pattern || '';
  var required = (rule.variables || []).filter(function (v) { return v.required; });
  var missing = [];
  var invalid = [];

  required.forEach(function (v) {
    var val = provided[v.name];
    if (val === undefined || val === null || String(val).trim() === '') {
      missing.push(v.name);
    } else if (!validateFormat(val, v.format)) {
      invalid.push(v.name + '(' + v.format + ')');
    }
  });
  if (missing.length) return { ok: false, missing: missing };
  if (invalid.length) return { ok: false, invalid: invalid };

  var out = pattern.replace(/\{([A-Z0-9_]+)\}/g, function (_, name) {
    var val = provided[name];
    return (val === undefined || val === null) ? ('{' + name + '}') : String(val);
  });

  // Se sobrou algum placeholder não resolvido, é lacuna → fail-closed.
  var leftover = out.match(/\{[A-Z0-9_]+\}/g);
  if (leftover) return { ok: false, missing: leftover.map(function (s) { return s.replace(/[{}]/g, ''); }) };

  return { ok: true, value: out };
}

/**
 * Compõe o nome final para UMA regra já resolvida.
 * @param {Object} rule regra normalizada (status VIGENTE).
 * @param {Object} provided variáveis comprovadas.
 * @param {string|number} clientId ID do cliente.
 * @return {{status:string, finalFilename?:string, reason?:string}}
 */
function composeFinalFilename(rule, provided, clientId) {
  if (!rule || rule.status !== 'VIGENTE') {
    return { status: NomenclatureStatus.PENDENTE, reason: 'REGRA_NAO_VIGENTE_OU_AUSENTE' };
  }
  var nnn = normalizeNNN(clientId);
  if (!nnn) {
    return { status: NomenclatureStatus.PENDENTE, reason: 'NNN_INVALIDO' };
  }
  var filled = fillPattern(rule, provided);
  if (!filled.ok) {
    if (filled.invalid) return { status: NomenclatureStatus.PENDENTE, reason: 'FORMATO_INVALIDO', invalid: filled.invalid };
    return { status: NomenclatureStatus.PENDENTE, reason: 'VARIAVEIS_FALTANTES', missing: filled.missing };
  }
  return { status: NomenclatureStatus.OK, finalFilename: nnn + '_' + filled.value, rule_id: rule.rule_id };
}

/**
 * Reconhece qual regra se aplica a um documento, a partir de sinais textuais.
 * Usa recognition.required_all / required_groups / forbidden_any.
 * Retorna 0, 1 ou N regras candidatas. Ambiguidade (N>1) = fail-closed.
 *
 * @param {Object[]} rules regras normalizadas VIGENTES.
 * @param {string[]} signals termos/campos detectados no documento.
 * @return {Object[]} candidatas.
 *
 * Runtime atual usa NOMENCLATURE_RULES + aprendizados do RuleStore; este módulo permanece testável em Node.
 */
function matchRules(rules, signals) {
  return matchRulesScored(rules, signals).map(function (m) { return m.rule; });
}

/**
 * Igual a matchRules, mas devolve também a "força" do casamento (soma do tamanho
 * das âncoras positivas do melhor conjunto que casou). Comparação sem acento e por
 * palavras inteiras. Uma regra casa se o reconhecimento base OU qualquer
 * recognition_alternatives (âncoras aprendidas no painel) casar.
 * @return {Array<{rule:Object, strength:number}>}
 */
function matchRulesScored(rules, signals) {
  var hay = (signals || []).map(_neKey).filter(Boolean);
  function has(term) { return hay.some(function (h) { return _neHas(h, term); }); }

  function setStrength(rec) {
    rec = rec || {};
    // Fail-closed: sem critério POSITIVO estruturado, o conjunto não reconhece nada.
    var hasPositive = (rec.required_all || []).length > 0 || (rec.required_groups || []).length > 0;
    if (!hasPositive) return 0;
    if ((rec.forbidden_any || []).some(has)) return 0;
    if (!(rec.required_all || []).every(has)) return 0;
    var strength = 0;
    (rec.required_all || []).forEach(function (t) { strength += _neKey(t).length; });
    for (var g = 0; g < (rec.required_groups || []).length; g++) {
      var hit = (rec.required_groups[g] || []).filter(has);
      if (!hit.length) return 0;
      strength += _neKey(hit[0]).length;
    }
    return strength;
  }

  var out = [];
  (rules || []).forEach(function (r) {
    if (r.status !== 'VIGENTE') return;
    var sets = [r.recognition].concat(r.recognition_alternatives || []);
    var best = 0;
    sets.forEach(function (s) { var v = setStrength(s); if (v > best) best = v; });
    if (best > 0) out.push({ rule: r, strength: best });
  });
  return out;
}

var _NE_TX = (typeof module !== 'undefined' && module.exports) ? require('./Text.js') : null;
function _neKey(s) { return _NE_TX ? _NE_TX.normKey(s) : normKey(s); }
function _neHas(hayKey, term) { return _NE_TX ? _NE_TX.txHas(hayKey, term) : txHas(hayKey, term); }

/**
 * API principal (fail-closed): resolve tipo + compõe nome final.
 * @param {Object} args {rules, signals, provided, clientId}
 * @return {{status:string, finalFilename?:string, rule_id?:string, reason?:string}}
 */
function resolveNomenclature(args) {
  var candidates = matchRules(args.rules, args.signals);
  if (candidates.length === 0) return { status: NomenclatureStatus.PENDENTE, reason: 'TIPO_NAO_RECONHECIDO' };
  if (candidates.length > 1) {
    return { status: NomenclatureStatus.PENDENTE, reason: 'AMBIGUIDADE_DE_REGRA', candidates: candidates.map(function (r) { return r.rule_id; }) };
  }
  return composeFinalFilename(candidates[0], args.provided, args.clientId);
}

// Export para testes em Node (ignorado no Apps Script).
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { NomenclatureStatus: NomenclatureStatus, normalizeNNN: normalizeNNN, validateFormat: validateFormat, fillPattern: fillPattern, composeFinalFilename: composeFinalFilename, matchRules: matchRules, matchRulesScored: matchRulesScored, resolveNomenclature: resolveNomenclature };
}
