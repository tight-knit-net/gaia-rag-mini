/**
 * NomenclatureRefinements — capacidades extras da nomenclatura, todas
 * baseadas em dados JÁ estruturados no corpus (sem inferir):
 *   - resolveDareSubtype: família DARE-SC (NOM-026) -> TEOR, por âncoras.
 *   - composeConsolidatedAware: variante consolidada (NOM-016).
 *   - deriveExtractedVariables: extração por regex declarada (ex.: NOM-018).
 *   - suggestManualRules: ranqueia candidatas p/ as regras legadas (o operador confirma).
 *
 * Depende de NomenclatureEngine (composeFinalFilename). Pura lógica, sem Drive.
 */

/* eslint-disable no-var */
var _ENG = (typeof module !== 'undefined' && module.exports)
  ? require('./NomenclatureEngine.js')
  : null; // no Apps Script, as funções são globais no mesmo projeto.

function _compose(rule, provided, clientId) {
  return _ENG ? _ENG.composeFinalFilename(rule, provided, clientId) : composeFinalFilename(rule, provided, clientId);
}
function _pending(reason, extra) { var o = { status: 'PENDENTE_NOMENCLATURA', reason: reason }; if (extra) for (var k in extra) o[k] = extra[k]; return o; }
var _NR_TX = (typeof module !== 'undefined' && module.exports) ? require('./Text.js') : null;
/** Busca sem acento e por palavras inteiras (mesma regra do NomenclatureEngine). */
function _hasIn(signals) {
  var T = _NR_TX || { normKey: normKey, txHas: txHas };
  var hay = (signals || []).map(T.normKey).filter(Boolean);
  return function (term) { return hay.some(function (h) { return T.txHas(h, term); }); };
}

/**
 * Resolve o subtipo (TEOR) de uma regra-família DARE a partir dos sinais.
 * Usa rule.family.approved_subtypes (required_positive_anchors + required_any_additional_anchor).
 * @return {{ok:true, teor:string}|{status,reason,...}}
 */
function resolveDareSubtype(rule, signals) {
  var fam = rule && rule.family;
  if (!fam || !fam.approved_subtypes) return _pending('REGRA_NAO_E_FAMILIA');
  var has = _hasIn(signals);

  var famAnchors = (fam.recognition_criteria && fam.recognition_criteria.required_family_anchors) || [];
  if (famAnchors.length && !famAnchors.some(has)) return _pending('FAMILIA_DARE_NAO_RECONHECIDA');

  var matched = [];
  var subs = fam.approved_subtypes;
  Object.keys(subs).forEach(function (key) {
    var s = subs[key];
    var pos = (s.required_positive_anchors || []);
    if (pos.length && !pos.every(has)) return;
    var addl = s.required_any_additional_anchor;
    if (addl && addl.length && !addl.some(has)) return;
    matched.push(s.teor_exact_value || key);
  });

  if (matched.length === 1) return { ok: true, teor: matched[0] };
  if (matched.length === 0) return _pending(fam.unknown_subtype_result === 'PENDENTE_NOMENCLATURA' ? 'DARE_SUBTIPO_DESCONHECIDO' : 'DARE_SUBTIPO_DESCONHECIDO');
  return _pending('DARE_SUBTIPO_AMBIGUO', { candidates: matched });
}

/**
 * Compõe respeitando a variante consolidada (NOM-016).
 * provided.consolidado === true (comprovado) usa variant_when_consolidated.
 */
function composeConsolidatedAware(rule, provided, clientId) {
  if (rule.variant_when_consolidated && provided && provided.consolidado === true) {
    var clone = {};
    for (var k in rule) clone[k] = rule[k];
    clone.approved_pattern = rule.variant_when_consolidated.approved_pattern;
    return _compose(clone, provided, clientId);
  }
  return _compose(rule, provided, clientId);
}

/**
 * Deriva variáveis por extração declarada (regex) a partir de campos brutos.
 * Ex.: NOM-018 extrai UNIDADE_IPTU da inscrição imobiliária completa.
 * @param {Object} rule
 * @param {Object} rawFields mapa { source_field: valorBruto }.
 * @param {Object} provided (opcional) valores já resolvidos.
 * @return {{provided:Object, pending:string[]}}
 */
function deriveExtractedVariables(rule, rawFields, provided) {
  provided = provided ? JSON.parse(JSON.stringify(provided)) : {};
  rawFields = rawFields || {};
  var pending = [];
  (rule.variables || []).forEach(function (v) {
    if (!v.extraction) return;
    if (provided[v.name] !== undefined && provided[v.name] !== null && String(provided[v.name]).trim() !== '') return;
    var ex = v.extraction;
    var raw = rawFields[ex.source_field];
    if (raw === undefined || raw === null) { pending.push(v.name); return; }
    var re;
    try { re = new RegExp(ex.regex, 'g'); } catch (e) { pending.push(v.name); return; }
    var m, last = null;
    while ((m = re.exec(String(raw))) !== null) { last = m; if (m.index === re.lastIndex) re.lastIndex++; }
    if (!last) { pending.push(v.name); return; }
    var g = ex.selected_group != null ? ex.selected_group : 0;
    var val = last[g];
    if (val === undefined || val === null) { pending.push(v.name); return; }
    provided[v.name] = String(val); // preserva zeros à esquerda
  });
  return { provided: provided, pending: pending };
}

/**
 * Sugere regras candidatas para as regras que NÃO têm reconhecimento automático
 * (legadas). Ranqueia por quantos sinais/recognition.signals aparecem.
 * NÃO decide — apenas sugere para confirmação humana.
 * @return {Array<{rule_id, score, matched:string[]}>}
 */
function suggestManualRules(rules, signals, topN) {
  var has = _hasIn(signals);
  var out = (rules || [])
    .filter(function (r) { return !r.auto_match; })
    .map(function (r) {
      var sig = (r.recognition && r.recognition.signals) || [];
      var matched = sig.filter(has);
      return { rule_id: r.rule_id, document_type: r.document_type, score: matched.length, matched: matched };
    })
    .filter(function (x) { return x.score > 0; })
    .sort(function (a, b) { return b.score - a.score; });
  return topN ? out.slice(0, topN) : out;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    resolveDareSubtype: resolveDareSubtype,
    composeConsolidatedAware: composeConsolidatedAware,
    deriveExtractedVariables: deriveExtractedVariables,
    suggestManualRules: suggestManualRules
  };
}
