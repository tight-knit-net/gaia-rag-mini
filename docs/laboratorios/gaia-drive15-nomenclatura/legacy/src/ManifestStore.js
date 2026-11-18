/**
 * ManifestStore — liga o ManifestEngine (que era puro e não tinha chamador) ao Drive.
 *
 * Carrega o contrato e os templates de 01_MANIFESTO_CLIENTE, cria o manifesto do
 * cliente novo a partir do TEMPLATE_CLIENT_MANIFEST_DRAFT e valida qualquer
 * manifesto antes de gravar. É o passo S7_MANIFEST_SYNC do workflow: nenhum
 * commit fecha sem o manifesto reconciliado no mesmo ciclo.
 *
 * Princípio herdado do contrato: SCHEMA IMUTÁVEL; INSTÂNCIA MUTÁVEL.
 * Toda escrita passa por setValue()/addEmpresa()/... do ManifestEngine, que
 * recusa criar chave nova, renomear ou mudar tipo estrutural.
 */

/** Carrega contrato + templates do Drive uma vez por execução (guardado no ctx). */
function mfContrato(ctx) {
  if (ctx && ctx.manifestContrato) return ctx.manifestContrato;
  var c = { ok: false, erro: null, contract: null, draft: null, entityTemplates: null };
  try {
    c.contract = readJson(MANIFESTO.CONTRACT_FILE);
    c.draft = readJson(MANIFESTO.TEMPLATE_DRAFT_FILE);
    c.entityTemplates = {
      empresa: readJson(MANIFESTO.TEMPLATE_EMPRESA),
      socio: readJson(MANIFESTO.TEMPLATE_SOCIO),
      cnae: readJson(MANIFESTO.TEMPLATE_CNAE),
      imovel: readJson(MANIFESTO.TEMPLATE_IMOVEL)
    };
    c.ok = true;
  } catch (e) {
    c.erro = String(e && e.message || e);
  }
  if (ctx) ctx.manifestContrato = c;
  return c;
}

/** Nome do manifesto vivo do cliente dentro de NNN_DOCUMENTOS. */
function mfNomeArquivo(nnn) { return nnn + CLIENTES_CFG.MANIFESTO_SUFIXO; }

/** Quantos avisos cabem no log antes de virar ruído. */
var MF_MAX_AVISOS_NO_LOG = 6;

/**
 * Põe no log as diferenças entre o manifesto do cliente e o template.
 * Não é defeito: é a instância trazendo campos próprios, que o contrato manda
 * preservar. Fica registrado para ninguém achar que o sistema vai preenchê-los.
 */
function mfLogarAvisos(avisos, client, log) {
  if (!log || !avisos || !avisos.length) return;
  var quem = (client && client.nome) || (client && client.nnn) || 'cliente';
  var mostra = avisos.slice(0, MF_MAX_AVISOS_NO_LOG).join('; ');
  var resto = avisos.length > MF_MAX_AVISOS_NO_LOG ? ' (+' + (avisos.length - MF_MAX_AVISOS_NO_LOG) + ' outros)' : '';
  log('info', 'Manifesto de ' + quem + ': ' + avisos.length + ' campo(s) próprios da instância, preservados sem alteração — ' + mostra + resto);
}

/** Acha o manifesto vivo do cliente, ou null. */
function mfLocalizar(client) {
  var dest = client.subpastas && client.subpastas[CLIENTES_CFG.MANIFESTO_BUCKET];
  if (!dest) return null;
  var achados = dsFindByName(dest, mfNomeArquivo(client.nnn));
  return achados.length ? { id: achados[0].id, parentId: dest } : null;
}

/**
 * Garante que o cliente tem manifesto vivo e válido.
 * Cliente novo → cria a partir do template. Cliente existente → só valida.
 * Nunca migra schema em silêncio (regra do contrato).
 * @return {{ok:boolean, file_id?:string, criado?:boolean, erros?:string[], motivo?:string}}
 */
function mfGarantirManifesto(ctx, client, log) {
  var c = mfContrato(ctx);
  if (!c.ok) return { ok: false, motivo: 'CONTRATO_INDISPONIVEL: ' + c.erro };

  var atual = mfLocalizar(client);

  if (atual) {
    var jsonAtual = null;
    try { jsonAtual = readJson(atual.id); } catch (e) { return { ok: false, motivo: 'MANIFESTO_ILEGIVEL: ' + String(e && e.message || e) }; }
    var v = validateManifestStructure(jsonAtual, c.contract, c.draft, c.entityTemplates);
    if (!v.ok) {
      // Falta chave exigida ou o tipo estrutural mudou: NÃO migrar sozinho.
      // Bloqueia e pede decisão humana (regra do contrato).
      return { ok: false, file_id: atual.id, erros: v.errors, motivo: 'MANIFESTO_FORA_DO_CONTRATO (migração de versão é decisão humana separada)' };
    }
    // Chaves próprias da instância não bloqueiam (existing_manifest_rule), mas
    // ficam registradas: é o único lugar onde dá para enxergar que o manifesto
    // do cliente é mais rico que o template e que o sistema não vai tocar nelas.
    mfLogarAvisos(v.avisos, client, log);
    return { ok: true, file_id: atual.id, criado: false, avisos: v.avisos };
  }

  var novo = createManifest(c.draft, client.nnn, nowIso());
  var vn = validateManifestStructure(novo, c.contract, c.draft, c.entityTemplates);
  if (!vn.ok) return { ok: false, erros: vn.errors, motivo: 'TEMPLATE_FORA_DO_CONTRATO' };

  var dest = client.subpastas[CLIENTES_CFG.MANIFESTO_BUCKET];
  var f = createJson(mfNomeArquivo(client.nnn), dest, novo); // createJson(name, parentId, obj)
  if (log) log('ok', 'Manifesto criado para ' + client.nome + ': ' + mfNomeArquivo(client.nnn) + ' (schema ' + (novo.schema_version || '?') + ')');
  return { ok: true, file_id: f.id, criado: true };
}

/**
 * S7_MANIFEST_SYNC — registra no manifesto vivo que aquele pacote foi aplicado.
 * Usa applied_package_fingerprints, que já existe no contrato (top_level_keys),
 * então não cria chave nenhuma. Idempotente: fingerprint repetido não duplica.
 * @return {{ok:boolean, motivo?:string, erros?:string[]}}
 */
function mfRegistrarPacote(ctx, client, fingerprint, log) {
  var c = mfContrato(ctx);
  if (!c.ok) return { ok: false, motivo: 'CONTRATO_INDISPONIVEL: ' + c.erro };

  var alvo = mfLocalizar(client);
  if (!alvo) return { ok: false, motivo: 'MANIFESTO_AUSENTE' };

  var m;
  try { m = readJson(alvo.id); } catch (e) { return { ok: false, motivo: 'MANIFESTO_ILEGIVEL: ' + String(e && e.message || e) }; }

  var atuais = Array.isArray(m.applied_package_fingerprints) ? m.applied_package_fingerprints : null;
  if (atuais === null) return { ok: false, motivo: 'MANIFESTO_SEM_applied_package_fingerprints' };
  if (atuais.indexOf(fingerprint) !== -1) return { ok: true, repetido: true };

  var r = setValue(m, ['applied_package_fingerprints'], atuais.concat([fingerprint]), nowIso());
  if (!r.ok) return { ok: false, erros: r.errors, motivo: 'MUTACAO_RECUSADA_PELO_CONTRATO' };

  // A mutação só acrescentou um fingerprint num array que já existia; se mesmo
  // assim o manifesto ficou inválido, é sinal de estrago e não se grava.
  var v = validateManifestStructure(r.manifest, c.contract, c.draft, c.entityTemplates);
  if (!v.ok) return { ok: false, erros: v.errors, motivo: 'MANIFESTO_INVALIDO_APOS_MUTACAO' };

  writeJson(alvo.id, r.manifest);
  if (log) log('info', 'Manifesto de ' + client.nome + ' sincronizado (pacote ' + fingerprint + ').');
  return { ok: true, file_id: alvo.id };
}

/** Para rodar sozinho no editor: confere se contrato e templates estão legíveis e coerentes. */
function test_manifestoContrato() {
  var c = mfContrato(null);
  if (!c.ok) { Logger.log('FALHOU: ' + c.erro); return c; }
  var vazio = createManifest(c.draft, '001', nowIso());
  var v = validateManifestStructure(vazio, c.contract, c.draft, c.entityTemplates);
  var out = {
    contract_version: c.contract.contract_version,
    top_level_keys: (c.contract.top_level_keys || []).length,
    templates: Object.keys(c.entityTemplates),
    instancia_valida: v.ok,
    erros: v.errors,
    avisos: v.avisos
  };
  Logger.log(JSON.stringify(out, null, 2));
  return out;
}

/** Confere um cliente. Uso interno de test_manifestoDoCliente. */
function mfConferirCliente(c, idx, nnn) {
  var entry = idx && idx.clientes && idx.clientes[nnn];
  if (!entry) return { cliente: nnn, situacao: 'NAO_INDEXADO' };

  var alvo = mfLocalizar({ nnn: nnn, subpastas: entry.subpastas });
  if (!alvo) {
    return { cliente: nnn, nome: entry.nome || null, situacao: 'SEM_MANIFESTO (será criado do template na aprovação)', portao_deixa_passar: true };
  }

  var m;
  try { m = readJson(alvo.id); }
  catch (e) { return { cliente: nnn, nome: entry.nome || null, file_id: alvo.id, situacao: 'ILEGIVEL: ' + String(e && e.message || e), portao_deixa_passar: false }; }

  var v = validateManifestStructure(m, c.contract, c.draft, c.entityTemplates);
  return {
    cliente: nnn,
    nome: entry.nome || null,
    file_id: alvo.id,
    schema_version: m.schema_version || null,
    chaves_de_topo: Object.keys(m).length,
    portao_deixa_passar: v.ok,
    erros: v.errors,
    avisos: v.avisos
  };
}

/**
 * Confere o manifesto VIVO dos clientes contra o contrato. NÃO escreve nada.
 *
 * Rode antes de aprovar o primeiro pacote: responde, em uma tela, se o portão
 * vai deixar passar e quais campos são próprios de cada cliente.
 *
 * Sem argumento (é assim que o editor do Apps Script chama) → confere TODOS os
 * clientes do índice e fecha com um resumo. Com argumento → só aquele.
 */
function test_manifestoDoCliente(nnn) {
  var c = mfContrato(null);
  if (!c.ok) { Logger.log('FALHOU ao carregar o contrato: ' + c.erro); return c; }

  var idx = sysLoadClientesIndex();
  var todos = (idx && idx.clientes) ? Object.keys(idx.clientes).sort() : [];
  if (!todos.length) { Logger.log('Nenhum cliente no índice ainda.'); return { ok: true, clientes: [] }; }

  var alvos = nnn ? [String(nnn)] : todos;
  var resultados = alvos.map(function (n) { return mfConferirCliente(c, idx, n); });

  var barram = resultados.filter(function (r) { return r.portao_deixa_passar === false; });
  var resumo = {
    contract_version: c.contract.contract_version,
    clientes_conferidos: resultados.length,
    passam_no_portao: resultados.length - barram.length,
    barrados: barram.map(function (r) { return r.cliente + (r.situacao ? ' (' + r.situacao + ')' : ''); })
  };

  Logger.log(JSON.stringify({ resumo: resumo, detalhe: resultados }, null, 2));
  Logger.log(barram.length
    ? '>>> ' + barram.length + ' cliente(s) BARRADOS no portão — veja "erros" no detalhe acima.'
    : '>>> Todos os ' + resultados.length + ' clientes passam no portão. Os "avisos" são campos próprios de cada manifesto, preservados sem alteração.');

  return { ok: !barram.length, resumo: resumo, detalhe: resultados };
}
