/**
 * RuleLoader — carrega e mescla as regras normalizadas de nomenclatura.
 *
 * Camadas (precedência crescente): corpus base normalizado + 01_NOVAS_REGRAS.
 * Resolve supersessão (supersedes_rule_id) de forma explícita.
 *
 * A parte de LEITURA no Drive usa o Advanced Drive Service (Drive API v3).
 * A parte de MESCLA/SUPERSESSÃO é pura (injetável) e testável offline.
 */

/**
 * Mescla regras e aplica supersessão. Puro (sem Drive).
 * @param {Object[]} baseRules regras normalizadas do corpus.
 * @param {Object[]} newRules regras de 01_NOVAS_REGRAS (normalizadas).
 * @return {{active:Object[], superseded:string[], conflicts:string[]}}
 */
function mergeAndResolve(baseRules, newRules) {
  var byId = {};
  var order = [];
  function put(r) { if (!(r.rule_id in byId)) order.push(r.rule_id); byId[r.rule_id] = r; }

  (baseRules || []).forEach(put);
  // Regras novas entram por cima (mesma rule_id substitui; nova rule_id adiciona).
  (newRules || []).forEach(put);

  var superseded = {};
  Object.keys(byId).forEach(function (id) {
    var sup = byId[id].supersedes_rule_id;
    if (sup) superseded[sup] = id;
  });

  var conflicts = [];
  var active = order
    .map(function (id) { return byId[id]; })
    .filter(function (r) {
      if (superseded[r.rule_id]) return false;          // superada por outra
      if (r.status === 'SUPERADA') return false;
      if (r.status === 'PENDENTE') { conflicts.push(r.rule_id); return false; } // bloqueada
      return r.status === 'VIGENTE';
    });

  return { active: active, superseded: Object.keys(superseded), conflicts: conflicts };
}

/**
 * Lê um arquivo JSON do Drive por fileId (Advanced Drive Service, API v3).
 * @param {string} fileId
 * @return {Object} conteúdo parseado.
 */
function readJsonFromDrive(fileId) {
  return JSON.parse(driveGetText(fileId)); // driveGetText usa DriveApp (funciona em Shared Drive)
}

/**
 * Carrega as regras normalizadas vigentes (base + novas), já resolvidas.
 * Requer que data/nomenclature_rules.normalized.json exista no Drive
 * (arquivo produzido pela etapa de conversão das 56 regras).
 * @param {string} normalizedFileId fileId do JSON normalizado da base.
 * @param {string[]} newRuleFileIds fileIds das regras novas (01_NOVAS_REGRAS).
 * @return {Object[]} regras ativas.
 */
function loadActiveRules(normalizedFileId, newRuleFileIds) {
  var base = readJsonFromDrive(normalizedFileId);
  var baseRules = base.rules || base; // aceita {rules:[...]} ou [...]
  var newRules = (newRuleFileIds || []).map(readJsonFromDrive);
  return mergeAndResolve(baseRules, newRules).active;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { mergeAndResolve: mergeAndResolve, readJsonFromDrive: readJsonFromDrive, loadActiveRules: loadActiveRules };
}
