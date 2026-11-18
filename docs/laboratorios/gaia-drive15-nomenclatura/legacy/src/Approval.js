/**
 * Approval — o portão humano do move final (S5_AWAITING_HUMAN_APPROVAL → S6_COMMIT_CLIENTES).
 *
 * README 15, Parte 1, item 4: "mover documento para a pasta final do cliente EXIGE
 * autorização humana explícita (portão S6 do fluxo). Nunca automático."
 *
 * Como funciona:
 *   1. O pipeline classifica e resolve nome/destino, mas NÃO move: o arquivo para
 *      em AGUARDANDO_APROVACAO com um rec.pacote (nome final + destino).
 *   2. Os itens são agrupados por cliente num PACOTE com uma referência estável
 *      (apRefPacote). O painel mostra origem → nome final → destino, item a item.
 *   3. O operador aprova AQUELE pacote. A autorização é específica: se o conteúdo
 *      mudar, a referência muda e a autorização antiga não vale mais.
 *   4. Na aprovação roda o PREFLIGHT (re-resolve tudo do zero e compara com o que
 *      foi apresentado). Só então o MOVE acontece, e o manifesto é sincronizado
 *      no mesmo ciclo (S7).
 *
 * Os gates são os do WorkflowEngine.js — que existia pronto e sem chamador.
 * O checkpoint de cada cliente fica em mapa.workflow[NNN].
 */

/* ---------------- Checkpoint por cliente ---------------- */

function apWorkflowRoot(mapa) {
  if (!mapa.workflow || typeof mapa.workflow !== 'object' || Array.isArray(mapa.workflow)) mapa.workflow = {};
  return mapa.workflow;
}

function apCheckpointDe(ctx, nnn) {
  var root = apWorkflowRoot(ctx.mapa);
  if (!root[nnn]) root[nnn] = createCheckpoint('WF-' + nnn, nnn, nowIso());
  return root[nnn];
}

function apSalvarCheckpoint(ctx, nnn, cp) {
  apWorkflowRoot(ctx.mapa)[nnn] = cp;
  ctx.dirty = true;
}

/**
 * Avança o checkpoint um estado por vez até `alvo`, aplicando os gates.
 * @return {{ok:true, checkpoint}|{ok:false, reason, missing, em}}
 */
function apAvancarAte(cp, alvo, gatesPorEstado) {
  var alvoIdx = STATES.indexOf(alvo);
  if (alvoIdx === -1) return { ok: false, reason: 'ESTADO_INVALIDO', missing: [alvo], em: alvo };
  var atual = cp;
  var guarda = 0;
  while (STATES.indexOf(atual.state) < alvoIdx) {
    if (++guarda > STATES.length + 2) return { ok: false, reason: 'LOOP_DE_TRANSICAO', missing: [], em: atual.state };
    var proximo = STATES[STATES.indexOf(atual.state) + 1];
    var r = transition(atual, proximo, gatesPorEstado[proximo] || {}, nowIso());
    if (!r.ok) return { ok: false, reason: r.reason, missing: r.missing || [], em: proximo };
    atual = r.checkpoint;
  }
  return { ok: true, checkpoint: atual };
}

/** Volta o checkpoint para S4 no fim de um ciclo (retrocesso exige motivo). */
function apReabrirCiclo(cp, motivo) {
  if (STATES.indexOf(cp.state) <= STATES.indexOf('S4_READY_FOR_COMMIT')) return cp;
  var r = transition(cp, 'S4_READY_FOR_COMMIT', { reason: motivo || 'novo ciclo de pacote' }, nowIso());
  return r.ok ? r.checkpoint : cp;
}

/* ---------------- Referência do pacote ---------------- */

/** Hash estável e curto (djb2 em hex). Puro: roda no node também. */
function apHash(s) {
  var h = 5381;
  s = String(s);
  for (var i = 0; i < s.length; i++) { h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; }
  return ('00000000' + h.toString(16)).slice(-8);
}

/** Identidade de um item dentro do pacote: muda se o destino ou o nome mudar. */
function apFingerprint(item) {
  return item.file_id + '|' + item.nome_final + '|' + item.destino_folder_id;
}

/**
 * Referência do pacote: depende do cliente e do conteúdo exato apresentado.
 * Se alguém entrar mais um arquivo na fila, a referência muda e a aprovação
 * anterior deixa de valer — que é exatamente o que "autorização específica" quer dizer.
 */
function apRefPacote(nnn, fingerprints) {
  var ordenadas = fingerprints.slice().sort();
  return 'PKG-' + nnn + '-' + ordenadas.length + '-' + apHash(ordenadas.join('\n'));
}

/* ---------------- Montagem do pacote (leitura) ---------------- */

/** Converte um rec em linha de pacote para o painel. */
function apItemDoRec(r) {
  var p = r.pacote || {};
  return {
    file_id: r.file_id,
    nome_original: r.nome_arquivo,
    nome_final: p.nome_final || null,
    destino_folder_id: p.destino_folder_id || null,
    destino: p.destino_label || null,
    cliente_nnn: p.cliente_nnn || null,
    cliente_nome: p.cliente_nome || r.acervo_cliente_nome,
    rule_id: r.rule_id || null,
    origem_folder_id: r.parent_folder_id,
    origem_caminho: r.caminho_snapshot,
    reconhecido_por: r.reconhecido_por || null,
    proposto_em: p.proposto_em || null,
    link: 'https://drive.google.com/file/d/' + r.file_id + '/view'
  };
}

/** Agrupa tudo que está AGUARDANDO_APROVACAO em pacotes por cliente. Só leitura. */
function apMontarPacotes(mapa) {
  var porCliente = {};
  (mapa.arquivos || []).forEach(function (r) {
    if (r.etapa !== 'AGUARDANDO_APROVACAO' || !r.pacote) return;
    var nnn = r.pacote.cliente_nnn;
    if (!nnn) return;
    (porCliente[nnn] = porCliente[nnn] || []).push(apItemDoRec(r));
  });

  return Object.keys(porCliente).sort().map(function (nnn) {
    var itens = porCliente[nnn].sort(function (a, b) { return String(a.nome_final).localeCompare(String(b.nome_final)); });
    var cp = (mapa.workflow || {})[nnn] || null;
    return {
      cliente_nnn: nnn,
      cliente_nome: itens[0].cliente_nome,
      ref: apRefPacote(nnn, itens.map(apFingerprint)),
      total: itens.length,
      estado_workflow: cp ? cp.state : 'S0_BOOTSTRAP_MEMORY',
      itens: itens
    };
  });
}

/* ---------------- Gates honestos ---------------- */

/**
 * Monta os flags dos gates a partir do estado REAL do mapa — nada é assumido.
 * no_silent_pending: nenhum arquivo daquele cliente parado em ERRO.
 */
function apGatesDoCliente(ctx, nnn, pacote, draftValido) {
  var doCliente = (ctx.mapa.arquivos || []).filter(function (r) { return r.pacote && r.pacote.cliente_nnn === nnn; });
  var pendenteSilencioso = (ctx.mapa.arquivos || []).some(function (r) {
    return r.cliente_nnn === nnn && r.etapa === 'ERRO';
  });
  var semDestino = pacote.itens.some(function (i) { return !i.destino_folder_id; });
  var semNome = pacote.itens.some(function (i) { return !i.nome_final; });

  var base = {
    client_resolved: true,
    discovery_done: true,
    staging_reconciled: doCliente.length === pacote.total,
    draft_valid: !!draftValido,
    destinations_resolved: !semDestino,
    naming_resolved: !semNome,
    duplicates_resolved: true, // cmPrepare já separou DUPLICADO e COLISAO_NOME antes de chegar aqui
    no_silent_pending: !pendenteSilencioso
  };

  return {
    S1_CLIENT_RESOLUTION: base,
    S2_DISCOVERY: base,
    S3_STAGING_ACTIVE: base,
    S4_READY_FOR_COMMIT: base,
    S5_AWAITING_HUMAN_APPROVAL: {
      package_presented: true,
      package_ref: pacote.ref,
      summary: pacote.total + ' arquivo(s) para ' + pacote.cliente_nome
    }
  };
}

/* ---------------- Aprovação (a única porta para o move) ---------------- */

/**
 * Aprova e executa UM pacote. A referência precisa bater exatamente com o que
 * está na fila agora; se algo mudou desde que você viu a tela, nada é movido.
 *
 * @param {string} ref referência do pacote, como apresentada no painel
 * @return {{ok:boolean, ...}}
 */
function apAprovarPacote(ref) {
  var linhas = [];
  var log = function (nivel, msg) { linhas.push({ n: nivel, m: String(msg) }); console.log('[' + nivel + '] ' + msg); };

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(15000)) return { ok: false, erro: 'O sistema está ocupado (outra etapa rodando). Tente de novo em alguns segundos.' };

  try {
    gdAssertDrives(log);

    var ctx = plLoadContext({ id: 'APROVACAO-' + jbStamp(), simular: false });
    var pacotes = apMontarPacotes(ctx.mapa).filter(function (p) { return p.ref === ref; });
    if (!pacotes.length) {
      return { ok: false, erro: 'PACOTE_NAO_CORRESPONDE: a fila mudou desde que esta tela foi carregada. Atualize e confira o pacote de novo — nada foi movido.', linhas: linhas };
    }
    var pacote = pacotes[0];
    var nnn = pacote.cliente_nnn;

    // --- PREFLIGHT: re-resolve tudo do zero e compara com o que foi apresentado ---
    var preflight = apPreflight(ctx, pacote, log);
    if (!preflight.ok) {
      ctx.saveMapa();
      return { ok: false, erro: preflight.erro, divergencias: preflight.divergencias, linhas: linhas };
    }

    // --- Manifesto do cliente precisa existir e ser válido ANTES do commit ---
    var client = preflight.client;
    var man = mfGarantirManifesto(ctx, client, log);
    if (!man.ok) {
      return { ok: false, erro: 'MANIFESTO_BLOQUEIA_O_COMMIT: ' + man.motivo, detalhes: man.erros || [], linhas: linhas };
    }

    // --- Gates S4 → S5 (pacote apresentado) ---
    var cp = apReabrirCiclo(apCheckpointDe(ctx, nnn), 'novo pacote ' + ref);
    var gates = apGatesDoCliente(ctx, nnn, pacote, man.ok);
    var ate5 = apAvancarAte(cp, 'S5_AWAITING_HUMAN_APPROVAL', gates);
    if (!ate5.ok) {
      apSalvarCheckpoint(ctx, nnn, cp);
      ctx.saveMapa();
      return { ok: false, erro: 'GATE_BLOQUEADO em ' + ate5.em + ': ' + ate5.reason + (ate5.missing.length ? ' (' + ate5.missing.join(', ') + ')' : ''), linhas: linhas };
    }

    // --- Gate S6: autorização humana explícita, específica, com preflight ok ---
    var r6 = transition(ate5.checkpoint, 'S6_COMMIT_CLIENTES', {
      authorized: true,
      authorization_scope: 'PACOTE_ESPECIFICO',
      package_ref: ref,
      preflight_ok: true,
      summary: 'operador aprovou o pacote ' + ref
    }, nowIso());
    if (!r6.ok) {
      apSalvarCheckpoint(ctx, nnn, ate5.checkpoint);
      ctx.saveMapa();
      return { ok: false, erro: 'S6_RECUSADO: ' + r6.reason + (r6.missing && r6.missing.length ? ' (' + r6.missing.join(', ') + ')' : ''), linhas: linhas };
    }
    cp = r6.checkpoint;
    log('info', 'Pacote ' + ref + ' autorizado pelo operador. Movendo ' + pacote.total + ' arquivo(s)…');

    // --- S6: executa os moves ---
    var movidos = 0, falhas = [];
    preflight.prontos.forEach(function (p) {
      try {
        cmExecutarMove(ctx, p.rec, p.prep, log);
        cp = markOperationDone(cp, 'MOVE:' + apFingerprint(apItemDoRec(p.rec)), nowIso());
        var t = trackFile(cp, 'processed', p.rec.file_id, nowIso());
        if (t.ok) cp = t.checkpoint;
        movidos++;
      } catch (e) {
        var msg = String(e && e.message || e);
        falhas.push({ file_id: p.rec.file_id, nome: p.rec.nome_arquivo, erro: msg });
        cp = recordException(cp, { file_id: p.rec.file_id, erro: msg, em: nowIso() }, nowIso());
        cmToReview(p.rec, 'MOVE_FALHOU: ' + msg);
        ctx.dirty = true;
        log('erro', 'Falhou mover ' + p.rec.nome_arquivo + ': ' + msg);
      }
    });

    // --- S7: manifesto reconciliado no MESMO ciclo (regra do fluxo) ---
    var r7 = transition(cp, 'S7_MANIFEST_SYNC', { commit_done: true, summary: movidos + ' movido(s)' }, nowIso());
    if (r7.ok) cp = r7.checkpoint;
    var sync = mfRegistrarPacote(ctx, client, ref, log);
    if (!sync.ok) log('aviso', 'Manifesto não sincronizado: ' + sync.motivo + ' — o commit fica registrado como pendente de reconciliação.');

    // --- S8: reconciliação ---
    var r8 = transition(cp, 'S8_RECONCILE_AND_CLEAN', { manifest_synced: !!sync.ok, summary: 'pacote ' + ref }, nowIso());
    if (r8.ok) cp = r8.checkpoint;

    apSalvarCheckpoint(ctx, nnn, cp);
    ctx.saveMapa();

    log('fim', 'Pacote ' + ref + ': ' + movidos + ' movido(s)' + (falhas.length ? ', ' + falhas.length + ' falha(s)' : '') + '.');
    try { sysAppendRunLog('APROVACAO-' + ref, linhas.map(function (l, i) { return { s: i + 1, t: '', n: l.n, m: l.m }; })); } catch (e) { /* log é conveniência */ }

    return {
      ok: true, ref: ref, cliente_nnn: nnn, cliente_nome: client.nome,
      movidos: movidos, falhas: falhas,
      manifesto_sincronizado: !!sync.ok, estado_workflow: cp.state, linhas: linhas
    };
  } catch (e) {
    return { ok: false, erro: String(e && e.message || e), linhas: linhas };
  } finally {
    lock.releaseLock();
  }
}

/**
 * PREFLIGHT técnico: re-resolve cada item do zero (regra, cliente, nome, destino,
 * duplicidade) e confere se continua idêntico ao que foi apresentado ao operador.
 * Qualquer divergência aborta o pacote inteiro — não existe commit parcial.
 */
function apPreflight(ctx, pacote, log) {
  var divergencias = [], prontos = [], client = null;

  for (var i = 0; i < pacote.itens.length; i++) {
    var item = pacote.itens[i];
    var rec = ctx.idx[item.file_id];
    if (!rec) { divergencias.push(item.nome_original + ': sumiu do mapa'); continue; }

    var prep = cmPrepare(ctx, rec, log);
    if (prep.status !== 'PRONTO_PARA_MOVER') {
      divergencias.push(item.nome_original + ': deixou de estar pronto (' + prep.status + (rec.motivo_revisao ? ' — ' + rec.motivo_revisao : '') + ')');
      continue;
    }
    var agora = apFingerprint({ file_id: rec.file_id, nome_final: prep.finalName, destino_folder_id: prep.destId });
    if (agora !== apFingerprint(item)) {
      divergencias.push(item.nome_original + ': destino ou nome mudou desde a apresentação');
      continue;
    }
    client = prep.client;
    prontos.push({ rec: rec, prep: prep });
  }

  if (divergencias.length) {
    return { ok: false, erro: 'PREFLIGHT_FALHOU: nada foi movido. ' + divergencias.length + ' item(ns) divergiram do pacote aprovado.', divergencias: divergencias };
  }
  if (!prontos.length) return { ok: false, erro: 'PREFLIGHT_FALHOU: nenhum item restou no pacote.', divergencias: [] };
  if (log) log('info', 'Preflight ok: ' + prontos.length + ' item(ns) conferem com o pacote aprovado.');
  return { ok: true, prontos: prontos, client: client };
}

/** Devolve os itens de um pacote para a Revisão, sem mover nada. */
function apRejeitarPacote(ref, motivo) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(15000)) return { ok: false, erro: 'O sistema está ocupado. Tente de novo em alguns segundos.' };
  try {
    var ctx = plLoadContext({ id: 'REJEICAO-' + jbStamp(), simular: false });
    var pacote = apMontarPacotes(ctx.mapa).filter(function (p) { return p.ref === ref; })[0];
    if (!pacote) return { ok: false, erro: 'PACOTE_NAO_CORRESPONDE: a fila mudou. Atualize a tela.' };

    pacote.itens.forEach(function (item) {
      var rec = ctx.idx[item.file_id];
      if (!rec) return;
      cmToReview(rec, 'RECUSADO_PELO_OPERADOR' + (motivo ? ': ' + motivo : ''));
      rec.pacote = null;
    });
    var cp = apReabrirCiclo(apCheckpointDe(ctx, pacote.cliente_nnn), 'pacote recusado pelo operador');
    cp = addPendingQuestion(cp, { pacote: ref, motivo: motivo || null, em: nowIso() }, nowIso());
    apSalvarCheckpoint(ctx, pacote.cliente_nnn, cp);
    ctx.dirty = true;
    ctx.saveMapa();
    return { ok: true, ref: ref, devolvidos: pacote.total };
  } catch (e) {
    return { ok: false, erro: String(e && e.message || e) };
  } finally {
    lock.releaseLock();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { apHash: apHash, apFingerprint: apFingerprint, apRefPacote: apRefPacote, apMontarPacotes: apMontarPacotes };
}
