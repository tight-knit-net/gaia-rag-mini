/**
 * GaiaOffice — facade que integra os motores num pipeline de nomeação de ponta a ponta.
 * Pure (recebe as regras). Une: seleção/reconhecimento de regra, família DARE,
 * variante consolidada, extração por regex e composição fail-closed.
 */

var _E = (typeof module !== 'undefined' && module.exports) ? require('./NomenclatureEngine.js') : null;
var _R = (typeof module !== 'undefined' && module.exports) ? require('./NomenclatureRefinements.js') : null;
function _eng() { return _E || { matchRules: matchRules, composeFinalFilename: composeFinalFilename, resolveNomenclature: resolveNomenclature }; }
function _ref() { return _R || { resolveDareSubtype: resolveDareSubtype, composeConsolidatedAware: composeConsolidatedAware, deriveExtractedVariables: deriveExtractedVariables, suggestManualRules: suggestManualRules }; }
function _pend(reason, extra) { var o = { status: 'PENDENTE_NOMENCLATURA', reason: reason }; if (extra) for (var k in extra) o[k] = extra[k]; return o; }

/**
 * Pipeline completo de nomeação (fail-closed).
 * @param {Object[]} rules regras normalizadas VIGENTES.
 * @param {Object} input {rule_id?, signals?, provided?, rawFields?, clientNNN, consolidado?}
 * @return {{status, finalFilename?, rule_id?, reason?, ...}}
 */
function resolveNome(rules, input) {
  input = input || {};
  var E = _eng(), R = _ref();
  var provided = input.provided ? JSON.parse(JSON.stringify(input.provided)) : {};

  // 1) selecionar a regra
  var rule = null;
  if (input.rule_id) {
    rule = rules.filter(function (r) { return r.rule_id === input.rule_id; })[0];
    if (!rule) return _pend('REGRA_INEXISTENTE', { rule_id: input.rule_id });
  } else {
    var cands = E.matchRules(rules, input.signals || []);
    if (cands.length === 1) rule = cands[0];
    else if (cands.length > 1) return _pend('AMBIGUIDADE_DE_REGRA', { candidates: cands.map(function (r) { return r.rule_id; }) });
    else return _pend('TIPO_NAO_RECONHECIDO', { suggestions: R.suggestManualRules(rules, input.signals || [], 5) });
  }

  // 2) família DARE: resolver TEOR se ainda não veio
  if (rule.family && (provided.TEOR === undefined || provided.TEOR === null)) {
    var sub = R.resolveDareSubtype(rule, input.signals || []);
    if (!sub.ok) return sub; // já é PENDENTE com reason
    provided.TEOR = sub.teor;
  }

  // 3) extração por regex declarada (ex.: NOM-018 UNIDADE_IPTU)
  var needsExtraction = (rule.variables || []).some(function (v) { return v.extraction; });
  if (needsExtraction) {
    var der = R.deriveExtractedVariables(rule, input.rawFields || {}, provided);
    provided = der.provided;
    if (der.pending && der.pending.length) return _pend('EXTRACAO_PENDENTE', { missing: der.pending });
  }

  // 4) compor (consciente da variante consolidada)
  return R.composeConsolidatedAware(rule, provided, input.clientNNN);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { resolveNome: resolveNome };
}
