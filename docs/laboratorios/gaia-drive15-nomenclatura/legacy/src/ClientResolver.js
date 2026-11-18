/**
 * ClientResolver — liga a pasta do cliente no acervo (4– BANCO DE DADOS) à pasta
 * definitiva em 1-CLIENTES (NNN_<NOME>), criando-a com o próximo ID livre se não existir.
 *
 * Ordem de resolução: vínculo já gravado → mesmo nome em 1-CLIENTES → mesmo CPF/CNPJ.
 * Mais de um candidato = ambíguo → arquivos vão para Revisão (nunca adivinha).
 */

/* ---------------- Puro ---------------- */

function crParseClientFolder(name) {
  var m = String(name || '').match(/^(\d{3})[\s_\-]+(.+)$/);
  return m ? { nnn: m[1], key: txFolderKey(m[2]) } : null;
}

function crNextNNN(usedList, start) {
  // ID do cliente = próximo da sequência (maior existente + 1); buracos não são reaproveitados
  var max = 0;
  (usedList || []).forEach(function (n) { var v = Number(n); if (v > max) max = v; });
  var n = max ? max + 1 : Math.max(1, Number(start) || 1);
  if (n > 999) throw new Error('Sem ID livre (NNN > 999).');
  return txPad(n, 3);
}

function crEmptyIndex() {
  return { schema: 'gaia-clientes-index/1.0', updated_at: null, clientes: {}, vinculos: {} };
}

/**
 * @param {Object} a {index, acervoFolderId, acervoKey, ids:string[], clientesFolders:[{id,name}]}
 * @return {{status:'EXISTENTE', nnn, folderId, via} | {status:'NOVO'} | {status:'AMBIGUO', candidatos}}
 */
function crResolvePure(a) {
  var index = a.index || crEmptyIndex();
  var folders = a.clientesFolders || [];
  var byId = {};
  folders.forEach(function (f) { byId[f.id] = f; });

  var vinc = index.vinculos[a.acervoFolderId];
  if (vinc && index.clientes[vinc] && byId[index.clientes[vinc].folder_id]) {
    return { status: 'EXISTENTE', nnn: vinc, folderId: index.clientes[vinc].folder_id, via: 'VINCULO' };
  }
  var byName = folders.filter(function (f) { var p = crParseClientFolder(f.name); return p && p.key === a.acervoKey; });
  if (byName.length === 1) return { status: 'EXISTENTE', nnn: crParseClientFolder(byName[0].name).nnn, folderId: byName[0].id, via: 'NOME' };
  if (byName.length > 1) return { status: 'AMBIGUO', candidatos: byName.map(function (f) { return f.name; }) };

  var ids = a.ids || [];
  if (ids.length) {
    var byIds = Object.keys(index.clientes).filter(function (nnn) {
      var c = index.clientes[nnn];
      return byId[c.folder_id] && (c.ids || []).some(function (x) { return ids.indexOf(x) !== -1; });
    });
    if (byIds.length === 1) return { status: 'EXISTENTE', nnn: byIds[0], folderId: index.clientes[byIds[0]].folder_id, via: 'CPF_CNPJ' };
    if (byIds.length > 1) return { status: 'AMBIGUO', candidatos: byIds };
  }
  return { status: 'NOVO' };
}

/* ---------------- Drive ---------------- */

/** Pastas diretas de 1-CLIENTES (cache por execução). */
function crListClientes(ctx) {
  if (!ctx.clientesFolders) {
    ctx.clientesFolders = dsListFolders(CLIENTES_CFG.ROOT).map(function (f) { return { id: f.id, name: f.name }; });
  }
  return ctx.clientesFolders;
}

/** Manifesto (MANIFESTO_CLIENTE*.json) da pasta do cliente no acervo, com cache por execução. */
function crAcervoManifest(ctx, acervoFolderId) {
  ctx.manifests = ctx.manifests || {};
  if (ctx.manifests[acervoFolderId] !== undefined) return ctx.manifests[acervoFolderId];
  var found = null;
  try {
    var files = dsListFiles(acervoFolderId).filter(function (f) { return /^MANIFESTO_CLIENTE.*\.json$/i.test(f.name); });
    if (files.length === 1) found = { id: files[0].id, name: files[0].name, json: readJson(files[0].id) };
  } catch (e) { found = null; }
  ctx.manifests[acervoFolderId] = found;
  return found;
}

function crInfoFor(ctx, acervoFolderId) {
  var man = crAcervoManifest(ctx, acervoFolderId);
  if (man && man.json) return rtManifestInfo(man.json);
  // cliente já criado: identificadores ficaram no índice
  var nnn = ctx.clientesIndex.vinculos[acervoFolderId];
  var c = nnn && ctx.clientesIndex.clientes[nnn];
  if (c && c.info) return c.info;
  return rtManifestInfo({});
}

/**
 * Garante a pasta do cliente em 1-CLIENTES e as subpastas-base.
 * @return {{ok:true, nnn, folderId, nome, subpastas:Object, criado:boolean} | {ok:false, motivo}}
 */
function crEnsureClient(ctx, acervoFolderId, acervoFolderName, log) {
  var idx = ctx.clientesIndex;
  var cached = ctx.clientCache && ctx.clientCache[acervoFolderId];
  if (cached) return cached;
  ctx.clientCache = ctx.clientCache || {};

  var info = crInfoFor(ctx, acervoFolderId);
  var key = txFolderKey(acervoFolderName);
  var res = crResolvePure({ index: idx, acervoFolderId: acervoFolderId, acervoKey: key, ids: info.ids, clientesFolders: crListClientes(ctx) });
  if (res.status === 'AMBIGUO') {
    var amb = { ok: false, motivo: 'CLIENTE_AMBIGUO: ' + res.candidatos.join(', ') };
    ctx.clientCache[acervoFolderId] = amb;
    return amb;
  }

  var nnn, folderId, nome, criado = false;
  if (res.status === 'EXISTENTE') {
    nnn = res.nnn; folderId = res.folderId;
    nome = (crListClientes(ctx).filter(function (f) { return f.id === folderId; })[0] || {}).name || (nnn + '_' + key);
    if (res.via !== 'VINCULO') log('info', 'Cliente ' + acervoFolderName + ' → pasta existente ' + nome + ' (por ' + res.via + ')');
  } else {
    var used = crListClientes(ctx).map(function (f) { var p = crParseClientFolder(f.name); return p ? p.nnn : null; }).filter(Boolean)
      .concat(Object.keys(idx.clientes));
    nnn = crNextNNN(used, CLIENTES_CFG.ID_INICIAL);
    nome = nnn + '_' + key;
    if (ctx.simular) {
      var sim = { ok: true, nnn: nnn, folderId: null, nome: nome, subpastas: {}, criado: true, simulado: true };
      ctx.clientCache[acervoFolderId] = sim;
      log('info', '[SIMULAÇÃO] Criaria o cliente ' + nome + ' em 1-CLIENTES');
      return sim;
    }
    folderId = DriveApp.getFolderById(CLIENTES_CFG.ROOT).createFolder(nome).getId();
    ctx.clientesFolders.push({ id: folderId, name: nome });
    criado = true;
    ctx.clientesCriados = (ctx.clientesCriados || 0) + 1;
    log('ok', 'Cliente novo criado: ' + nome + ' (ID ' + nnn + ')');
  }

  var entry = idx.clientes[nnn] || { nnn: nnn, folder_id: folderId, nome: nome, subpastas: {}, ids: [], criado_em: nowIso() };
  entry.folder_id = folderId;
  entry.nome = nome;
  entry.subpastas = entry.subpastas || {};
  if (!ctx.simular) {
    CLIENTES_CFG.BUCKETS.forEach(function (b) {
      var sid = entry.subpastas[b];
      if (sid && !dsIsLiveFolder(sid)) sid = null;
      if (!sid) sid = ensureFolder(folderId, nnn + '_' + b).id;
      entry.subpastas[b] = sid;
    });
  }
  info.ids.forEach(function (x) { if (entry.ids.indexOf(x) === -1) entry.ids.push(x); });
  entry.info = { cliente: info.cliente, empresas: info.empresas, imoveis: info.imoveis, ids: info.ids, nomes: info.nomes, excluir_ancoras: info.excluir_ancoras };
  idx.clientes[nnn] = entry;
  idx.vinculos[acervoFolderId] = nnn;
  idx.updated_at = nowIso();
  if (!ctx.simular) sysSaveClientesIndex(idx);

  var out = { ok: true, nnn: nnn, folderId: folderId, nome: nome, subpastas: entry.subpastas, criado: criado };
  ctx.clientCache[acervoFolderId] = out;
  // Exceção consciente ao portão S6: o manifesto tem que chegar na pasta do
  // cliente antes de haver pacote, porque é ele que o portão valida depois.
  // Ver o cabeçalho de cmMoveClientManifest em Committer.js.
  if (!ctx.simular) cmMoveClientManifest(ctx, acervoFolderId, out, log);
  return out;
}

/** Subpasta de entidade (multiempresa/multimóvel) dentro do bucket, criada sob demanda. */
function crEnsureEntityFolder(ctx, client, bucket, subName) {
  var idx = ctx.clientesIndex.clientes[client.nnn];
  idx.entidades = idx.entidades || {};
  var k = bucket + '/' + subName;
  if (idx.entidades[k] && dsIsLiveFolder(idx.entidades[k])) return idx.entidades[k];
  var id = ensureFolder(client.subpastas[bucket], subName).id;
  idx.entidades[k] = id;
  sysSaveClientesIndex(ctx.clientesIndex);
  return id;
}
