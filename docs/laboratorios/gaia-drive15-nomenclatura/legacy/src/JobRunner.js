/**
 * JobRunner — execução em etapas curtas com log ao vivo e botão Parar.
 *
 * O painel chama jbStart() uma vez e depois jbTick() em sequência (cada chamada
 * trabalha ~1 min). Em paralelo, consulta jbStatus() a cada 2 s para mostrar o log.
 * Estado da execução: ScriptProperties. Log: CacheService (ao vivo) + arquivo em _SISTEMA/LOGS.
 */

var JB_KEY = 'GAIA_JOB';
var JB_STOP = 'GAIA_JOB_STOP';
var JB_LOG = 'GAIA_LOG_';
var JB_MAX_LINES = 250;

function jbGet() {
  try { return JSON.parse(PropertiesService.getScriptProperties().getProperty(JB_KEY) || 'null'); } catch (e) { return null; }
}

function jbPut(job) { PropertiesService.getScriptProperties().setProperty(JB_KEY, JSON.stringify(job)); }

function jbStopRequested() { return CacheService.getScriptCache().get(JB_STOP) === '1'; }

function jbStamp() { return Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyyMMdd-HHmmss'); }

/** Logger: cada linha vai na hora para o cache (o painel lê enquanto a etapa roda). */
function jbLogger(job) {
  var cache = CacheService.getScriptCache();
  var key = JB_LOG + job.id;
  var state = null;
  try { state = JSON.parse(cache.get(key) || 'null'); } catch (e) { state = null; }
  state = state || { seq: 0, lines: [] };
  var fresh = [];
  var fn = function (level, msg) {
    state.seq++;
    var line = { s: state.seq, t: Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'HH:mm:ss'), n: level, m: String(msg).slice(0, 300) };
    state.lines.push(line);
    fresh.push(line);
    if (state.lines.length > JB_MAX_LINES) state.lines = state.lines.slice(-JB_MAX_LINES);
    try { cache.put(key, JSON.stringify(state), 21600); } catch (e) { /* log ao vivo é conveniência */ }
    console.log('[' + level + '] ' + line.m);
  };
  fn.fresh = fresh;
  return fn;
}

/**
 * Inicia (ou retoma) uma execução.
 * @param {Object} opts {folderId?: string, simular?: boolean}
 */
function jbStart(opts) {
  opts = opts || {};
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(15000)) return { ok: false, erro: 'O sistema está ocupado (outra etapa rodando). Tente de novo em alguns segundos.' };
  try {
    var cur = jbGet();
    if (cur && cur.status === 'RODANDO' && (Date.now() - Date.parse(cur.atualizado_em)) < 5 * 60 * 1000) {
      return { ok: true, job: cur, retomado: true };
    }
    CacheService.getScriptCache().remove(JB_STOP);

    // Antes de qualquer coisa: as raízes configuradas estão mesmo no Drive 15 real?
    // (existe uma cópia legada com os MESMOS nomes de pasta — ver 01_Guards.js)
    try {
      gdAssertDrives(null);
    } catch (e) {
      return { ok: false, erro: String(e && e.message || e) };
    }

    var pastas = opts.folderId ? [opts.folderId] : plClientFolders().map(function (f) { return f.id; });
    var job = {
      id: jbStamp(), status: 'RODANDO', fase: 'INVENTARIO', simular: !!opts.simular, folderId: opts.folderId || null,
      pastas_pendentes: pastas, fila_total: null, fila_restante: null, ticks: 0, erros_seguidos: 0,
      contadores: { pastas: 0, lidos: 0, reconhecidos: 0, movidos: 0, duplicados: 0, revisao: 0, erros: 0, simulados: 0, aguardando: 0, clientes_novos: 0 },
      iniciado_em: nowIso(), atualizado_em: nowIso()
    };
    jbPut(job);
    var log = jbLogger(job);
    log('info', 'Execução ' + job.id + ' iniciada' + (job.simular ? ' em SIMULAÇÃO (nada será movido)' : '') + ': ' + pastas.length + ' pasta(s) de cliente.');
    if (!job.simular && PIPELINE_CFG.EXIGIR_APROVACAO_HUMANA) {
      log('info', 'Portão humano ligado: o que for reconhecido para na aba Aprovação. Nada vai para 1-CLIENTES sem o seu OK.');
    }
    try { sysAppendRunLog(job.id, log.fresh); } catch (e) { /* segue */ }
    return { ok: true, job: job };
  } finally {
    lock.releaseLock();
  }
}

/** Uma etapa de trabalho (~1 min). */
function jbTick() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(2000)) return { ok: true, ocupado: true, job: jbGet() };
  var job = jbGet();
  var log = null;
  try {
    if (!job || job.status !== 'RODANDO') return { ok: true, job: job };
    log = jbLogger(job);
    if (jbStopRequested()) {
      job.status = 'PARADO';
      log('aviso', 'Execução parada pelo operador.');
    } else {
      var res = plRunTick(job, log, PIPELINE_CFG.TICK_BUDGET_MS);
      job = res.job;
      job.erros_seguidos = 0;
      if (res.parado) {
        job.status = 'PARADO';
        log('aviso', 'Execução parada pelo operador.');
      } else if (res.done) {
        job.status = 'CONCLUIDO';
        job.terminado_em = nowIso();
        var c = job.contadores;
        log('fim', 'Concluído: ' + (c.aguardando ? c.aguardando + ' aguardando sua aprovação, ' : '') + c.movidos + ' movido(s), ' +
          c.duplicados + ' duplicado(s), ' + c.revisao + ' para Revisão, ' +
          c.lidos + ' lido(s) por OCR' + (c.simulados ? ', ' + c.simulados + ' simulado(s)' : '') + (c.erros ? ', ' + c.erros + ' erro(s)' : '') + '.');
        if (c.aguardando) log('fim', 'Abra a aba Aprovação para conferir e liberar o que vai para 1-CLIENTES.');
      }
    }
    job.ticks++;
    job.atualizado_em = nowIso();
    jbPut(job);
    return { ok: true, job: job };
  } catch (e) {
    var msg = String(e && e.message || e);
    if (job) {
      job.erros_seguidos = (job.erros_seguidos || 0) + 1;
      job.atualizado_em = nowIso();
      if (!log) log = jbLogger(job);
      var semPermissao = /^PERMISSAO: /.test(msg);
      if (semPermissao) {
        log('erro', 'O Google negou uma permissão: ' + msg.replace(/^PERMISSAO: /, '') +
          ' — abra o editor do Apps Script, rode a função "autorizar" e aceite as permissões. Depois clique em Executar de novo.');
        job.status = 'ERRO';
        job.erro = 'Falta autorização do Google (rode "autorizar" no editor).';
      } else {
        log('erro', 'Falha nesta etapa: ' + msg + (job.erros_seguidos >= 3 ? ' — execução interrompida.' : ' — vou tentar de novo.'));
        if (job.erros_seguidos >= 3) { job.status = 'ERRO'; job.erro = msg; }
      }
      jbPut(job);
    }
    return { ok: job ? job.status === 'RODANDO' : false, erro: msg, job: job };
  } finally {
    if (log) { try { sysAppendRunLog(job.id, log.fresh); } catch (e2) { /* segue */ } }
    lock.releaseLock();
  }
}

/** Estado + linhas de log novas (depois de sinceSeq). Não trava nada. */
function jbStatus(sinceSeq) {
  var job = jbGet();
  if (!job) return { ok: true, job: null, lines: [], seq: 0 };
  var state = null;
  try { state = JSON.parse(CacheService.getScriptCache().get(JB_LOG + job.id) || 'null'); } catch (e) { state = null; }
  state = state || { seq: 0, lines: [] };
  var since = Number(sinceSeq) || 0;
  return { ok: true, job: job, lines: state.lines.filter(function (l) { return l.s > since; }), seq: state.seq };
}

/** Pede para parar. Se nenhuma etapa estiver rodando, encerra na hora. */
function jbStop() {
  CacheService.getScriptCache().put(JB_STOP, '1', 3600);
  var lock = LockService.getScriptLock();
  if (lock.tryLock(1500)) {
    try {
      var job = jbGet();
      if (job && job.status === 'RODANDO') {
        job.status = 'PARADO';
        job.atualizado_em = nowIso();
        jbPut(job);
        jbLogger(job)('aviso', 'Execução parada pelo operador.');
      }
      return { ok: true, job: job };
    } finally { lock.releaseLock(); }
  }
  return { ok: true, pendente: true, job: jbGet() };
}
