/**
 * Committer — nome final (NNN_padrão) + MOVE ONLY para a subpasta do cliente.
 *  - Mesmo nome já no destino com o MESMO conteúdo (md5) → DUPLICADO (fica no acervo, nada é apagado).
 *  - Mesmo nome com conteúdo diferente → Revisão.
 *  - Movimento registrado no MAPA em duas fases (PENDENTE → CONCLUIDO) e o MAPA é salvo logo após.
 */

var CM_EXT_BY_MIME = {
  'application/pdf': '.pdf', 'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif', 'image/webp': '.webp',
  'image/tiff': '.tif', 'image/bmp': '.bmp', 'text/plain': '.txt',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx', 'application/msword': '.doc'
};

/** Ajusta a extensão do nome final para a extensão REAL do arquivo. */
function cmApplyExt(name, originalName, mime) {
  if (/^application\/vnd\.google-apps\./.test(mime || '')) return txExt(name) ? txStem(name) : name;
  var real = txExt(originalName) || CM_EXT_BY_MIME[mime] || '';
  var cur = txExt(name);
  if (!real) return name;
  if (!cur) return name + real;
  return cur === real ? name : txStem(name) + real;
}

/** Compõe o nome final com o NNN do cliente (usa o motor de nomenclatura). */
function cmComposeName(rules, rule, rec, text, nnn) {
  var key = normKey(text || '');
  var provided = {};
  var v = rec.variaveis || {};
  for (var k in v) provided[k] = v[k];
  var r = resolveNome(rules, { rule_id: rule.rule_id, signals: key ? [key] : [], provided: provided, rawFields: rec.raw_fields || {}, clientNNN: nnn });
  if (r.status !== 'OK') return r;
  return { status: 'OK', finalFilename: txSafeName(cmApplyExt(r.finalFilename, rec.nome_arquivo, rec.mime)), rule_id: rule.rule_id };
}

function cmMotivo(r) {
  var m = r.reason || 'PENDENTE';
  if (r.missing && r.missing.length) m += ': ' + r.missing.join(', ');
  if (r.invalid && r.invalid.length) m += ': ' + r.invalid.join(', ');
  if (r.candidates && r.candidates.length) m += ': ' + r.candidates.join(', ');
  return m;
}

function cmToReview(rec, motivo) {
  rec.etapa = 'REVISAO';
  rec.motivo_revisao = motivo;
  return 'REVISAO';
}

/**
 * Resolve TUDO que o move precisa — regra, pertencimento, cliente, nome final,
 * destino e duplicidade — mas NÃO move. É usado nas duas pontas:
 *   - no pipeline, para montar o pacote que vai ao operador;
 *   - na aprovação, como PREFLIGHT (re-resolve do zero e compara).
 *
 * @return {{status:'PRONTO_PARA_MOVER', finalName, destId, destLabel, client, rule, meta}}
 *       | {status:'REVISAO'|'DUPLICADO'|'IGNORADO'|'SIMULADO'|'MOVIDO'}
 */
function cmPrepare(ctx, rec, log) {
  var rule = ctx.ruleById[rec.rule_id];
  if (!rule) return { status: cmToReview(rec, 'REGRA_NAO_ENCONTRADA: ' + rec.rule_id) };

  var meta = dsMeta(rec.file_id);
  if (meta.trashed) { rec.etapa = 'IGNORADO'; rec.observacoes = 'arquivo está na lixeira'; return { status: 'IGNORADO' }; }

  var text = ctx.textFor(rec);
  var key = normKey(text);
  var info = crInfoFor(ctx, rec.acervo_cliente_folder_id);

  // antes de criar qualquer pasta: o documento é mesmo deste cliente?
  if (PIPELINE_CFG.CHECAR_PERTENCIMENTO && !rec.pertencimento_confirmado) {
    var b = rtBelonging(info, text, key);
    if (b.status === 'OUTRO_CLIENTE') {
      log('revisao', rec.nome_arquivo + ' → Revisão (cita outro CPF/CNPJ e nada do cliente)');
      return { status: cmToReview(rec, 'PERTENCIMENTO_DUVIDOSO: o texto cita ' + b.ids.join(', ') + ' e nenhum dado do cliente') };
    }
  }

  var client = crEnsureClient(ctx, rec.acervo_cliente_folder_id, rec.acervo_cliente_nome, log);
  if (!client.ok) { log('revisao', rec.nome_arquivo + ' → Revisão (' + client.motivo + ')'); return { status: cmToReview(rec, client.motivo) }; }

  var composed = cmComposeName(ctx.rules, rule, rec, text, client.nnn);
  if (composed.status !== 'OK') { log('revisao', rec.nome_arquivo + ' → Revisão (' + cmMotivo(composed) + ')'); return { status: cmToReview(rec, cmMotivo(composed)) }; }
  var finalName = composed.finalFilename;

  var bucket = rec.destino_bucket;
  if (!bucket) return { status: cmToReview(rec, 'DESTINO_NAO_DEFINIDO') };
  var ent = rtEntityTarget(bucket, text, key, info, client.nnn);
  if (!ent.ok) { log('revisao', rec.nome_arquivo + ' → Revisão (' + ent.motivo + ')'); return { status: cmToReview(rec, ent.motivo) }; }
  var destLabel = client.nome + '/' + client.nnn + '_' + bucket + (ent.sub ? '/' + ent.sub : '');

  if (ctx.simular || client.simulado) {
    rec.nome_final = finalName;
    rec.simulacao = { nome_final: finalName, destino: destLabel, em: nowIso() };
    ctx.cont.simulados++;
    log('sim', '[SIMULAÇÃO] ' + rec.nome_arquivo + ' → ' + destLabel + '/' + finalName);
    return { status: 'SIMULADO' };
  }

  var destId = ent.sub ? crEnsureEntityFolder(ctx, client, bucket, ent.sub) : client.subpastas[bucket];
  var parents = meta.parents || [];

  // Reconciliação: já foi movido numa execução que caiu antes de salvar o MAPA.
  if (parents.indexOf(destId) !== -1) {
    cmMarkMoved(ctx, rec, meta.name, destId, destLabel, client.nnn);
    log('ok', 'Reconciliado (já estava no destino): ' + meta.name);
    return { status: 'MOVIDO' };
  }
  if (parents.indexOf(rec.parent_folder_id) === -1) {
    return { status: cmToReview(rec, 'ARQUIVO_SAIU_DO_ACERVO: foi movido por fora do sistema') };
  }

  var same = dsFindByName(destId, finalName).filter(function (f) { return f.id !== rec.file_id; });
  if (same.length) {
    var other = dsMeta(same[0].id);
    if (other.md5Checksum && meta.md5Checksum && other.md5Checksum === meta.md5Checksum) {
      rec.etapa = 'DUPLICADO';
      rec.duplicado_de = same[0].id;
      rec.nome_final = finalName;
      ctx.cont.duplicados++;
      log('dup', 'Duplicado (mesmo conteúdo de ' + destLabel + '/' + finalName + '): ' + rec.nome_arquivo + ' ficou no acervo');
      return { status: 'DUPLICADO' };
    }
    log('revisao', rec.nome_arquivo + ' → Revisão (já existe outro "' + finalName + '" com conteúdo diferente)');
    return { status: cmToReview(rec, 'COLISAO_NOME: já existe "' + finalName + '" com conteúdo diferente no destino') };
  }

  return {
    status: 'PRONTO_PARA_MOVER',
    finalName: finalName, destId: destId, destLabel: destLabel,
    client: client, rule: rule, meta: meta, bucket: bucket
  };
}

/**
 * Executa o MOVE de um item já preparado E JÁ AUTORIZADO.
 * Só deve ser chamado por Approval.apAprovarPacote (portão S6) ou, quando
 * PIPELINE_CFG.EXIGIR_APROVACAO_HUMANA for false, pelo próprio cmCommit.
 * @return {'MOVIDO'}
 */
function cmExecutarMove(ctx, rec, prep, log) {
  var autorizacao = rec.aprovacao && rec.aprovacao.pacote_ref
    ? 'OPERADOR_APROVOU_PACOTE:' + rec.aprovacao.pacote_ref
    : (rec.reconhecido_por === 'OPERADOR' ? 'PAINEL_APRENDER_E_SEGUIR' : 'AUTO_REGRA_RECONHECIDA:' + prep.rule.rule_id);

  var mov = {
    movimento_id: 'MOV-' + rec.file_id + '-' + Date.now(), file_id: rec.file_id, nome_original: rec.nome_arquivo,
    origem_anterior_ao_staging: rec.parent_folder_id, origem_parent_path: rec.caminho_snapshot, cliente: prep.client.nnn,
    destino_final: prep.destId, nome_final: prep.finalName,
    autorizacao_operador: autorizacao,
    workflow_checkpoint_relacionado: prep.client.nnn,
    data_movimento: nowIso(), status: 'PENDENTE', observacoes: prep.destLabel
  };
  ctx.mapa.movimentos.push(mov);
  try {
    dsMoveRename(rec.file_id, prep.finalName, prep.destId, rec.parent_folder_id);
  } catch (e) {
    mov.status = 'FALHOU';
    mov.observacoes = String(e && e.message || e);
    throw e;
  }
  mov.status = 'CONCLUIDO';
  cmMarkMoved(ctx, rec, prep.finalName, prep.destId, prep.destLabel, prep.client.nnn);
  rec.pacote = null;
  ctx.saveMapa();
  log('ok', rec.nome_arquivo + ' → ' + prep.destLabel + '/' + prep.finalName);
  return 'MOVIDO';
}

/** Segura o arquivo no portão: monta o pacote e espera o operador. Não move nada. */
function cmAguardarAprovacao(ctx, rec, prep, log) {
  rec.etapa = 'AGUARDANDO_APROVACAO';
  rec.nome_final = prep.finalName;
  rec.motivo_revisao = null;
  rec.pacote = {
    nome_final: prep.finalName,
    destino_folder_id: prep.destId,
    destino_label: prep.destLabel,
    cliente_nnn: prep.client.nnn,
    cliente_nome: prep.client.nome,
    cliente_criado_agora: !!prep.client.criado,
    bucket: prep.bucket,
    rule_id: prep.rule.rule_id,
    proposto_em: nowIso()
  };
  ctx.cont.aguardando = (ctx.cont.aguardando || 0) + 1;
  ctx.dirty = true;
  log('pacote', rec.nome_arquivo + ' → pronto para ' + prep.destLabel + '/' + prep.finalName + ' (aguardando sua aprovação)');
  return 'AGUARDANDO';
}

/**
 * Leva um arquivo PRONTO até o portão de aprovação (ou até a pasta do cliente,
 * se o portão estiver desligado em PIPELINE_CFG.EXIGIR_APROVACAO_HUMANA).
 * @return {'MOVIDO'|'DUPLICADO'|'REVISAO'|'SIMULADO'|'IGNORADO'|'AGUARDANDO'}
 */
function cmCommit(ctx, rec, log) {
  var prep = cmPrepare(ctx, rec, log);
  if (prep.status !== 'PRONTO_PARA_MOVER') return prep.status;

  if (PIPELINE_CFG.EXIGIR_APROVACAO_HUMANA) return cmAguardarAprovacao(ctx, rec, prep, log);
  return cmExecutarMove(ctx, rec, prep, log);
}

function cmMarkMoved(ctx, rec, finalName, destId, destLabel, nnn) {
  rec.etapa = 'MOVIDO';
  rec.estado_no_acervo = 'MOVIDO';
  rec.nome_final = finalName;
  rec.destino_folder_id = destId;
  rec.destino_caminho = destLabel;
  rec.cliente_nnn = nnn;
  rec.movido_em = nowIso();
  rec.motivo_revisao = null;
  ctx.cont.movidos++;
  ctx.dirty = true;
}

/**
 * Leva o MANIFESTO_CLIENTE.json do acervo para NNN_DOCUMENTOS/NNN_Manifesto_cliente.json (uma vez).
 *
 * ÚNICA EXCEÇÃO AO PORTÃO S6 — e é proposital. Este move acontece dentro do job,
 * sem passar pela tela de aprovação, porque o manifesto precisa estar na pasta do
 * cliente ANTES de existir pacote para aprovar: é ele que o portão vai validar.
 * Exigir aprovação aqui seria pedir para aprovar o que ainda não pode ser montado.
 *
 * O que mantém isso seguro e auditável:
 *   - não é documento do cliente, é o arquivo de controle;
 *   - é 1 por cliente e idempotente (não repete se o destino já tem o nome);
 *   - fica em ctx.mapa.movimentos com autorizacao_operador
 *     'AUTO_MANIFESTO_DO_CLIENTE', que distingue dos moves aprovados
 *     ('OPERADOR_APROVOU_PACOTE:<ref>') na aba Movimentação;
 *   - aparece no log da execução com essa palavra, não escondido.
 *
 * Qualquer OUTRO move de arquivo para a pasta final do cliente continua exigindo
 * o portão (Approval.apAprovarPacote → cmExecutarMove).
 */
function cmMoveClientManifest(ctx, acervoFolderId, client, log) {
  var man = crAcervoManifest(ctx, acervoFolderId);
  if (!man || man.movido) return;
  man.movido = true;
  var name = client.nnn + CLIENTES_CFG.MANIFESTO_SUFIXO;
  var dest = client.subpastas[CLIENTES_CFG.MANIFESTO_BUCKET];
  if (dsFindByName(dest, name).length) {
    log('aviso', 'O cliente ' + client.nome + ' já tem ' + name + '; o manifesto do acervo ficou onde está.');
    return;
  }
  var j = man.json;
  if (j && typeof j === 'object') {
    if ('client_id' in j) j.client_id = client.nnn;
    if (j.cliente && typeof j.cliente === 'object' && 'id_do_cliente' in j.cliente) j.cliente.id_do_cliente = client.nnn;
    if ('updated_at' in j) j.updated_at = nowIso();
    writeJson(man.id, j);
  }
  dsMoveRename(man.id, name, dest, acervoFolderId);
  var rec = ctx.idx[man.id];
  if (rec) {
    rec.etapa = 'MOVIDO'; rec.estado_no_acervo = 'MOVIDO'; rec.nome_final = name; rec.destino_folder_id = dest;
    rec.destino_caminho = client.nome + '/' + client.nnn + '_' + CLIENTES_CFG.MANIFESTO_BUCKET; rec.cliente_nnn = client.nnn; rec.movido_em = nowIso();
  }
  ctx.mapa.movimentos.push({
    movimento_id: 'MOV-' + man.id + '-' + Date.now(), file_id: man.id, nome_original: man.name, cliente: client.nnn,
    destino_final: dest, nome_final: name, autorizacao_operador: 'AUTO_MANIFESTO_DO_CLIENTE', data_movimento: nowIso(), status: 'CONCLUIDO'
  });
  ctx.clientesIndex.clientes[client.nnn].manifesto_file_id = man.id;
  sysSaveClientesIndex(ctx.clientesIndex);
  ctx.saveMapa();
  log('ok', 'Arquivo de controle movido automaticamente (não passa pelo portão): manifesto → ' +
    client.nome + '/' + client.nnn + '_' + CLIENTES_CFG.MANIFESTO_BUCKET + '/' + name + ' (client_id = ' + client.nnn + ')');
}
