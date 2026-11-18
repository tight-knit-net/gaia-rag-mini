/**
 * WorkflowEngine — máquina de estados S0→S10 do fluxo documental de cliente.
 * Pura: gerencia o WORKFLOW_CHECKPOINT (schema 2.0), aplica os GATES e a
 * idempotência. Não toca no Drive (os efeitos reais entram via DriveService depois).
 *
 * Regras honradas: sequência com gates; autorização HUMANA explícita e específica
 * para o COMMIT (S6); manifesto no mesmo ciclo (S7); reconciliação (S8);
 * checkpoint na troca de contexto; idempotência.
 */

var STATES = [
  'S0_BOOTSTRAP_MEMORY', 'S1_CLIENT_RESOLUTION', 'S2_DISCOVERY', 'S3_STAGING_ACTIVE',
  'S4_READY_FOR_COMMIT', 'S5_AWAITING_HUMAN_APPROVAL', 'S6_COMMIT_CLIENTES',
  'S7_MANIFEST_SYNC', 'S8_RECONCILE_AND_CLEAN', 'S9_MEMORY_LEARNING', 'S10_CLOSED'
];
var PHASE = {
  S0_BOOTSTRAP_MEMORY: 'BOOTSTRAP', S1_CLIENT_RESOLUTION: 'CLIENT_RESOLUTION', S2_DISCOVERY: 'DISCOVERY',
  S3_STAGING_ACTIVE: 'STAGING', S4_READY_FOR_COMMIT: 'READY', S5_AWAITING_HUMAN_APPROVAL: 'AWAITING_APPROVAL',
  S6_COMMIT_CLIENTES: 'COMMIT', S7_MANIFEST_SYNC: 'MANIFEST_SYNC', S8_RECONCILE_AND_CLEAN: 'RECONCILE',
  S9_MEMORY_LEARNING: 'MEMORY_LEARNING', S10_CLOSED: 'CLOSED'
};

function _cw(o) { return JSON.parse(JSON.stringify(o)); }
function _idxState(s) { return STATES.indexOf(s); }
function _blocked(reason, missing) { return { ok: false, reason: reason, missing: missing || [] }; }

/** Cria a instância WORKFLOW_CHECKPOINT (schema 2.0). */
function createCheckpoint(workflowId, clientStagingKey, nowIso) {
  return {
    schema_version: '2.0',
    workflow_id: workflowId || null,
    client_staging_key: clientStagingKey || null,
    state: 'S0_BOOTSTRAP_MEMORY',
    current_phase: 'BOOTSTRAP',
    active_context: { root: null, role: null, write_policy: null, required_reads: [], rules_loaded: false, entered_at: null },
    exit_condition: null,
    last_safe_checkpoint: { at: null, state: null, active_context: null, summary: null },
    processed_file_ids: [], staged_file_ids: [], pending_file_ids: [], rejected_file_ids: [],
    pending_questions: [], exceptions: [], next_action: null, transition_log: [],
    idempotency: { completed_operations: [], do_not_repeat: [] },
    provenance_refs: [], updated_at: nowIso || null
  };
}

/** Gates de ENTRADA por estado. Recebe (cp, gate) e retorna {ok, missing[]}. */
var GATES = {
  S1_CLIENT_RESOLUTION: function () { return { ok: true, missing: [] }; },
  S2_DISCOVERY: function (cp, g) { return _need(g, ['client_resolved']); },
  S3_STAGING_ACTIVE: function (cp, g) { return _need(g, ['discovery_done']); },
  S4_READY_FOR_COMMIT: function (cp, g) {
    return _need(g, ['client_resolved', 'staging_reconciled', 'draft_valid', 'destinations_resolved', 'naming_resolved', 'duplicates_resolved', 'no_silent_pending']);
  },
  S5_AWAITING_HUMAN_APPROVAL: function (cp, g) {
    var r = _need(g, ['package_presented']);
    if (r.ok && !g.package_ref) return _blocked('PACOTE_SEM_REFERENCIA', ['package_ref']);
    return r;
  },
  S6_COMMIT_CLIENTES: function (cp, g) {
    // autorização HUMANA explícita e específica para o pacote apresentado em S5
    var s5 = _lastLogTo(cp, 'S5_AWAITING_HUMAN_APPROVAL');
    if (!s5 || !s5.meta || !s5.meta.package_ref) return _blocked('SEM_PACOTE_APRESENTADO');
    if (g.authorized !== true) return _blocked('AUTORIZACAO_HUMANA_AUSENTE');
    if (g.authorization_scope === 'GENERICA') return _blocked('AUTORIZACAO_GENERICA_NAO_BASTA');
    if (g.package_ref !== s5.meta.package_ref) return _blocked('AUTORIZACAO_NAO_CORRESPONDE_AO_PACOTE', [String(g.package_ref) + ' != ' + String(s5.meta.package_ref)]);
    if (g.preflight_ok !== true) return _blocked('PREFLIGHT_INCOMPLETO');
    return { ok: true, missing: [] };
  },
  S7_MANIFEST_SYNC: function (cp, g) { return _need(g, ['commit_done']); },
  S8_RECONCILE_AND_CLEAN: function (cp, g) { return _need(g, ['manifest_synced']); },
  S9_MEMORY_LEARNING: function (cp, g) { return _need(g, ['reconciled']); },
  S10_CLOSED: function (cp, g) { return _need(g, ['no_silent_pending']); }
};

function _need(gate, flags) {
  gate = gate || {};
  var missing = flags.filter(function (f) { return gate[f] !== true; });
  return missing.length ? _blocked('GATE_BLOQUEADO', missing) : { ok: true, missing: [] };
}
function _lastLogTo(cp, state) {
  for (var i = cp.transition_log.length - 1; i >= 0; i--) if (cp.transition_log[i].to === state) return cp.transition_log[i];
  return null;
}

/**
 * Transição de estado. Avanço só para o PRÓXIMO estado (com gate); retrocesso
 * para qualquer estado anterior é permitido com motivo (nova evidência/conflito).
 * @return {{ok:true, checkpoint}|{ok:false, reason, missing}}
 */
function transition(cp, toState, gate, nowIso) {
  gate = gate || {};
  if (_idxState(toState) === -1) return _blocked('ESTADO_INVALIDO', [toState]);
  var from = cp.state, fi = _idxState(from), ti = _idxState(toState);

  if (ti > fi + 1) return _blocked('PULO_DE_ESTADO_PROIBIDO', [from + ' -> ' + toState]);
  var backward = ti <= fi;
  if (backward && !gate.reason) return _blocked('RETROCESSO_EXIGE_MOTIVO');

  if (!backward) {
    var gk = GATES[toState];
    var res = gk ? gk(cp, gate) : { ok: true, missing: [] };
    if (!res.ok) return res;
  }

  var m = _cw(cp);
  var entry = { from: from, to: toState, at: nowIso || null, summary: gate.summary || null };
  if (toState === 'S5_AWAITING_HUMAN_APPROVAL') entry.meta = { package_ref: gate.package_ref };
  if (backward) entry.meta = { backward: true, reason: gate.reason };
  m.transition_log.push(entry);
  m.state = toState;
  m.current_phase = PHASE[toState] || null;
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, checkpoint: m };
}

/** Troca de contexto (raiz): checkpointar → declarar contexto → carregar governança. */
function enterContext(cp, ctx, nowIso) {
  var m = _cw(cp);
  // checkpoint seguro antes de trocar
  m.last_safe_checkpoint = { at: nowIso || null, state: m.state, active_context: _cw(m.active_context), summary: (ctx && ctx.summary) || 'context_switch' };
  m.active_context = {
    root: ctx.root || null, role: ctx.role || null, write_policy: ctx.write_policy || null,
    required_reads: ctx.required_reads || [], rules_loaded: ctx.rules_loaded === true, entered_at: nowIso || null
  };
  m.updated_at = nowIso || m.updated_at;
  return m;
}

/** Idempotência. */
function markOperationDone(cp, opKey, nowIso) {
  var m = _cw(cp);
  if (m.idempotency.completed_operations.indexOf(opKey) === -1) m.idempotency.completed_operations.push(opKey);
  m.updated_at = nowIso || m.updated_at;
  return m;
}
function isOperationDone(cp, opKey) { return cp.idempotency.completed_operations.indexOf(opKey) !== -1; }
function addDoNotRepeat(cp, opKey) { var m = _cw(cp); if (m.idempotency.do_not_repeat.indexOf(opKey) === -1) m.idempotency.do_not_repeat.push(opKey); return m; }

/** Rastreamento de arquivos e exceções. */
function trackFile(cp, bucket, fileId, nowIso) {
  var valid = { processed: 'processed_file_ids', staged: 'staged_file_ids', pending: 'pending_file_ids', rejected: 'rejected_file_ids' };
  var key = valid[bucket];
  if (!key) return { ok: false, reason: 'BUCKET_INVALIDO' };
  var m = _cw(cp);
  if (m[key].indexOf(fileId) === -1) m[key].push(fileId);
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, checkpoint: m };
}
function recordException(cp, ex, nowIso) { var m = _cw(cp); m.exceptions.push(ex); m.updated_at = nowIso || m.updated_at; return m; }
function addPendingQuestion(cp, q, nowIso) { var m = _cw(cp); m.pending_questions.push(q); m.updated_at = nowIso || m.updated_at; return m; }

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    STATES: STATES, GATES: GATES, createCheckpoint: createCheckpoint, transition: transition,
    enterContext: enterContext, markOperationDone: markOperationDone, isOperationDone: isOperationDone,
    addDoNotRepeat: addDoNotRepeat, trackFile: trackFile, recordException: recordException, addPendingQuestion: addPendingQuestion
  };
}
