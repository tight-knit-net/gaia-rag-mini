/**
 * RuleStore — regras de nomenclatura em uso = 56 regras do código (RulesData)
 * + o que foi aprendido no painel (arquivos APRENDIDO__NOM-XXX.json em 01_NOVAS_REGRAS).
 *
 * Um arquivo aprendido pode:
 *  - tipo NOVA: trazer uma regra inteira (NOM-057 em diante);
 *  - tipo AJUSTE: acrescentar a uma regra existente novas âncoras de reconhecimento,
 *    dicas de onde achar cada variável e a pasta de destino.
 */

var RS_SCHEMA = 'gaia-regra-aprendida/1.0';
var RS_PREFIX = 'APRENDIDO__';

/* ---------------- Puro ---------------- */

function rsNewDoc(ruleId, tipo, now) {
  return {
    schema: RS_SCHEMA, rule_id: ruleId, tipo: tipo, criado_em: now, atualizado_em: now, regra: null,
    recognition_alternatives: [], variable_hints: {}, destination_bucket: null, exemplos: [], comentarios: []
  };
}

/** Aplica os documentos aprendidos sobre uma cópia das regras base. */
function rsApplyLearned(baseRules, docs) {
  var rules = JSON.parse(JSON.stringify(baseRules || []));
  var byId = {};
  rules.forEach(function (r) { byId[r.rule_id] = r; });
  (docs || []).forEach(function (d) {
    if (!d || d.schema !== RS_SCHEMA || !d.rule_id) return;
    var target = byId[d.rule_id];
    if (!target && d.tipo === 'NOVA' && d.regra && d.regra.rule_id === d.rule_id) {
      target = JSON.parse(JSON.stringify(d.regra));
      rules.push(target);
      byId[target.rule_id] = target;
    }
    if (!target) return;
    target.recognition_alternatives = (target.recognition_alternatives || []).concat(d.recognition_alternatives || []);
    target.variable_hints = target.variable_hints || {};
    Object.keys(d.variable_hints || {}).forEach(function (v) {
      target.variable_hints[v] = (target.variable_hints[v] || []).concat(d.variable_hints[v] || []);
    });
    if (d.destination_bucket) target.destination_bucket = d.destination_bucket;
    if (target.recognition_alternatives.length) target.auto_match = true;
    target.aprendida = true;
    target.aprendizado = {
      tipo: d.tipo, atualizado_em: d.atualizado_em, exemplos: (d.exemplos || []).length,
      comentarios: (d.comentarios || []).map(function (c) { return c.texto; }).slice(-5)
    };
  });
  return rules;
}

/** Próximo NOM-XXX livre. */
function rsNextRuleId(rules) {
  var max = 0;
  (rules || []).forEach(function (r) { var m = String(r.rule_id || '').match(/^NOM-(\d+)$/); if (m) max = Math.max(max, Number(m[1])); });
  return 'NOM-' + txPad(max + 1, 3);
}

/* ---------------- Drive ---------------- */

function rsLoadDocs() {
  var cache = CacheService.getScriptCache();
  var hit = cache.get('GAIA_RULES_LEARNED');
  if (hit) { try { return JSON.parse(hit); } catch (e) { /* relê */ } }
  var docs = [];
  dsListFiles(NOMENCLATURA.NOVAS_REGRAS_FOLDER).forEach(function (f) {
    if (f.name.indexOf(RS_PREFIX) !== 0 || !/\.json$/i.test(f.name)) return;
    try {
      var d = readJson(f.id);
      if (d && d.schema === RS_SCHEMA) { d._file_id = f.id; docs.push(d); }
    } catch (e) { console.log('Regra aprendida ilegível: ' + f.name + ' — ' + e.message); }
  });
  docs.sort(function (a, b) { return String(a.rule_id).localeCompare(String(b.rule_id)); });
  try { cache.put('GAIA_RULES_LEARNED', JSON.stringify(docs), 600); } catch (e) { /* grande demais: sem cache */ }
  return docs;
}

function rsRuntimeRules() {
  return rsApplyLearned(NOMENCLATURE_RULES, rsLoadDocs());
}

function rsFindDoc(ruleId) {
  return rsLoadDocs().filter(function (d) { return d.rule_id === ruleId; })[0] || null;
}

function rsSaveDoc(doc) {
  var name = RS_PREFIX + doc.rule_id + '.json';
  var clean = JSON.parse(JSON.stringify(doc));
  delete clean._file_id;
  var existing = dsFindByName(NOMENCLATURA.NOVAS_REGRAS_FOLDER, name)[0];
  var id = existing ? writeJson(existing.id, clean).id : createJson(name, NOMENCLATURA.NOVAS_REGRAS_FOLDER, clean).id;
  CacheService.getScriptCache().remove('GAIA_RULES_LEARNED');
  return id;
}
