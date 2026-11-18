/**
 * RevisaoExterna — revisão com ajuda do ChatGPT, conduzida pelo operador.
 *
 * O sistema NÃO conversa com o ChatGPT. Ele só:
 *  1) monta um prompt completo para UM arquivo da Revisão (identificação, regras, modelo,
 *     pasta e nome exatos do resultado) e marca a revisão como "aguardando arquivo";
 *  2) quando o operador pede, acha o arquivo gravado pelo ID da revisão, confere se é
 *     deste documento e devolve os campos para preencher o cartão da Revisão.
 * O OK final continua no painel ("Aprender e seguir").
 *
 * Estado no MAPA (registro do arquivo): revisao_externa = {id, arquivo, pasta_id, modelo_id,
 *   gerado_em, status: AGUARDANDO|CARREGADO|APLICADO, carregado_em, resultado_file_id, anteriores[]}
 */

var RX_SCHEMA = 'gaia-revisao-chatgpt/1.0';
var RX_CAMINHO_PASTA = 'Drive compartilhado "15 - Gaia Operacional e Clientes" › 4– BANCO DE DADOS › _SISTEMA › REVISAO_CHATGPT';

/* ---------------- Puro ---------------- */

/** Modelo padronizado (a mesma estrutura que o cartão da Revisão envia ao "Aprender e seguir"). */
function rxModelo() {
  return {
    schema: RX_SCHEMA,
    revisao_id: '(preenchido pelo sistema — não alterar)',
    file_id: '(preenchido pelo sistema — não alterar)',
    documento: '(preenchido pelo sistema — não alterar)',
    modo: 'EXISTENTE ou NOVO',
    rule_id: 'NOM-000 — só no modo EXISTENTE (no modo NOVO: null)',
    variaveis: { NOME_DA_VARIAVEL: 'valor lido no documento — só no modo EXISTENTE' },
    nome_documento: 'só no modo NOVO: nome do arquivo SEM o ID do cliente, com a extensão',
    nome_do_tipo: 'opcional, só no modo NOVO: nome do tipo de documento',
    destino: 'DOCUMENTOS, SOCIETARIO ou IMOVEIS',
    sempre_destino: false,
    ancoras: ['frase copiada do documento', 'outra frase copiada do documento'],
    comentario: 'regra ou explicação combinada na conversa (fica gravada no aprendizado)',
    resumo: { interpretacao: 'o que é o documento, em 1 a 3 frases', pontos_de_atencao: ['o que o operador deve conferir'] }
  };
}

/** Cópia do modelo com a identificação desta revisão já preenchida. */
function rxModeloPreenchido(id, fileId, nome) {
  return {
    schema: RX_SCHEMA, revisao_id: id, file_id: fileId, documento: nome,
    modo: null, rule_id: null, variaveis: {}, nome_documento: null, nome_do_tipo: null,
    destino: null, sempre_destino: false, ancoras: [], comentario: null,
    resumo: { interpretacao: null, pontos_de_atencao: [] }
  };
}

function rxNovoId(fileId, stamp, rnd) {
  return 'RV-' + stamp + '-' + String(fileId || '').replace(/[^A-Za-z0-9]/g, '').slice(-6) + (rnd ? '-' + rnd : '');
}

function rxNomeArquivo(id) { return REVISAO_EXTERNA_CFG.PREFIXO + id + '.json'; }

function rxMotivoTxt(m) {
  m = String(m || '');
  var T = [
    [/^TIPO_NAO_RECONHECIDO/, 'documento ainda não conhecido pelo sistema'], [/^SEM_TEXTO/, 'sem texto legível'],
    [/^AMBIGUO/, 'parece mais de um tipo'], [/^CONFLITO_TEXTO_X_NOME/, 'o texto e o nome do arquivo indicam tipos diferentes'],
    [/^VARIAVEIS_FALTANTES/, 'falta dado para montar o nome'], [/^FORMATO_INVALIDO/, 'dado em formato inválido'],
    [/^LEITURA_FALHOU/, 'o sistema não conseguiu ler o arquivo'], [/^PERTENCIMENTO/, 'pode ser de outro cliente'],
    [/^COLISAO_NOME/, 'já existe outro arquivo com esse nome'], [/CONTEXTO_AMBIGUO|DESTINO_NAO_DEFINIDO/, 'falta definir a pasta de destino'],
    [/^MULTI/, 'cliente com mais de uma empresa/imóvel']
  ];
  for (var i = 0; i < T.length; i++) if (T[i][0].test(m)) return T[i][1] + ' (' + m + ')';
  return m || '—';
}

/**
 * Monta o prompt.
 * @param {Object} x {id, arquivo, gerado_em, detalhe (lnDetalhe), caminho, tamanho, pasta_id, modelo_id}
 */
function rxMontarPrompt(x) {
  var d = x.detalhe, a = d.arquivo;
  var L = [];
  var p = function (s) { L.push(s === undefined ? '' : s); };
  var nnn = a.cliente_nnn ? a.cliente_nnn : 'ainda não criado (o sistema define o próximo da sequência)';
  var arquivoRes = x.arquivo;

  p('# Gaia Office — revisão de documento com ajuda do ChatGPT');
  p('Revisão: ' + x.id + ' · gerado em ' + x.gerado_em + ' (horário de Brasília)');
  p();
  p('Você vai me ajudar a revisar UM documento do sistema Gaia Office. Trabalhe só com este documento e siga as 3 etapas da seção 2, na ordem.');
  p();
  p('## 1. Documento (identificação — não altere)');
  p('- ID da revisão: ' + x.id);
  p('- Documento: ' + a.nome + (a.renomeado ? ' (nome original: ' + a.nome_original + ')' : ''));
  p('- file_id no Google Drive: ' + a.file_id);
  p('- Abrir: ' + a.link);
  p('- Onde está: Drive compartilhado "15 - Gaia Operacional e Clientes" › 4– BANCO DE DADOS › ' + (x.caminho || a.cliente));
  p('- Cliente (pasta no acervo): ' + a.cliente + ' — ID do cliente: ' + nnn);
  p('- Tipo de arquivo: ' + (a.mime || '—') + (x.tamanho ? ' · ' + Math.max(1, Math.round(Number(x.tamanho) / 1024)) + ' KB' : ''));
  p('- Por que está em revisão: ' + rxMotivoTxt(a.motivo));
  p('- Texto lido pelo sistema: ' + (d.texto_total || 0) + ' caracteres' + (a.leitura ? ' (' + a.leitura + ')' : '') + ' — está na seção 7.');
  p();
  p('Se o documento que você abrir tiver outro nome ou outro file_id, pare e me avise. Nunca use informação de outro documento.');
  p();
  p('## 2. Como vamos trabalhar');
  p('**Etapa A — análise e conversa.** Leia o documento (pelo link; se não conseguir abrir, use o texto da seção 7). Diga em poucas linhas o que entendeu: que documento é, qual tipo da seção 5 se aplica (ou se é um tipo novo), o nome que seria aplicado e a pasta de destino. Depois espere. Eu posso explicar regras da empresa ou como interpretar o documento: considere tudo o que eu disser nesta conversa antes do resultado final. Nesta etapa não gere o arquivo.');
  p();
  p('**Etapa B — aplicar (só com a minha autorização).** Só quando eu disser claramente algo como "OK, vamos aplicar":');
  p('1. use o modelo padronizado da seção 6, com a mesma estrutura (sem acrescentar nem remover campos);');
  p('2. preencha só os campos desta revisão (a identificação já vem preenchida e não muda);');
  p('3. deixe o arquivo pronto aqui no ChatGPT, com o nome da seção 3, e mostre o JSON;');
  p('4. mostre um resumo curto: o que interpretou; tipo escolhido (rule_id) ou tipo novo; nome que será aplicado; variáveis; pasta de destino; frases de reconhecimento (aprendizado); pontos que eu devo conferir.');
  p('Não grave nada no Google Drive nesta etapa. Se eu corrigir algo, gere de novo e mostre de novo.');
  p();
  p('**Etapa C — gravar (só com uma nova autorização).** Só quando eu disser claramente algo como "OK, está correto. Pode gravar":');
  p('1. use exatamente o último arquivo que eu aprovei;');
  p('2. grave na pasta e com o nome da seção 3 — não escolha outra pasta nem outro nome;');
  p('3. não altere, não sobrescreva e não apague nenhum outro arquivo (nem o documento, nem o modelo);');
  p('4. confirme: "Gravado: _SISTEMA/REVISAO_CHATGPT/' + arquivoRes + '".');
  p('Se você não conseguir gravar no Google Drive, diga isso claramente e me entregue o arquivo para download com esse mesmo nome — eu mesmo coloco na pasta.');
  p();
  p('## 3. Onde gravar o resultado (definido pelo sistema)');
  p('- Pasta: ' + RX_CAMINHO_PASTA);
  p('- ID da pasta: ' + x.pasta_id);
  p('- Link da pasta: https://drive.google.com/drive/folders/' + x.pasta_id);
  p('- Nome exato do arquivo: ' + arquivoRes);
  p('- Conteúdo: somente o JSON (UTF-8), sem texto antes ou depois.');
  p();
  p('## 4. Regras do sistema (valem sempre)');
  p('- Nome final no Drive = ID do cliente + "_" + nome do documento. O sistema coloca o ID sozinho: nunca inclua o ID do cliente no nome.');
  p('- Tipo que já existe (modo "EXISTENTE"): use o rule_id da seção 5 e preencha em "variaveis" só as variáveis daquele padrão, com valores lidos no documento. Não crie sinônimo, abreviação nem variação do padrão.');
  p('- Tipo novo (modo "NOVO", só se nenhum tipo da lista servir): em "nome_documento" escreva o nome do arquivo sem o ID do cliente, com a extensão (ex.: .pdf), no estilo dos padrões da lista (MAIÚSCULAS, palavras separadas por "_"). Datas e números que mudam de um documento para outro devem ser os valores reais deste documento — o sistema transforma em partes variáveis.');
  p('- Datas no formato DD-MM-AAAA. CNPJ com 14 dígitos. Nunca invente valor: se não encontrar, deixe null e avise nos pontos de atenção.');
  p('- "destino": DOCUMENTOS (documentos pessoais do cliente), SOCIETARIO (empresa) ou IMOVEIS (imóvel/edificação). "sempre_destino": true só se esse tipo deve ir sempre para essa pasta.');
  p('- "ancoras" (frases de reconhecimento): pelo menos 2, copiadas do texto do documento, que aparecem em TODO documento desse tipo (título, órgão emissor). Nunca use nome, CPF/CNPJ, endereço ou números do cliente. Prefira as frases sugeridas na seção 5.');
  p('- "comentario": 1 ou 2 frases com a regra ou explicação combinada nesta conversa (fica gravado no aprendizado do sistema).');
  p('- Quem aprova no sistema sou eu: o arquivo só preenche a tela de revisão, e eu confiro antes de dar o OK.');
  if ((REVISAO_EXTERNA_CFG.CONHECIMENTO || []).length) {
    p();
    p('### Conhecimento operacional da Gaia');
    REVISAO_EXTERNA_CFG.CONHECIMENTO.forEach(function (c) { p('- ' + c); });
  }
  p();
  var regras = d.regras || [];
  p('## 5. Tipos de documento que já existem (' + regras.length + ')');
  p('rule_id | tipo | padrão do nome | variáveis | pasta');
  regras.forEach(function (r) {
    var vars = (r.variables || []).map(function (v) { return v.name + ' (' + v.format + ')'; }).join(', ') || '—';
    p(r.rule_id + ' | ' + r.document_type + ' | ' + r.approved_pattern + ' | ' + vars + ' | ' + (r.destino || 'pelo contexto'));
  });
  p();
  var sug = (d.sugestoes || []).map(function (s) { return s.rule_id + ' ' + s.document_type + ' (pontos ' + s.score + ')'; });
  p('Sugestões do sistema para este documento: ' + (sug.length ? sug.join('; ') : 'nenhuma') + '.');
  if (d.selecionada) p('Tipo pré-selecionado pelo sistema: ' + d.selecionada + ' (confira).');
  var anc = (d.ancoras || []).slice(0, 20).map(function (x) { return '"' + x.texto + '"'; });
  p('Frases sugeridas (do topo do documento): ' + (anc.length ? anc.join('; ') : 'nenhuma') + '.');
  p();
  p('## 6. Modelo padronizado (não altere a estrutura)');
  p('- Local do modelo: _SISTEMA/REVISAO_CHATGPT/' + REVISAO_EXTERNA_CFG.MODELO + (x.modelo_id ? ' — https://drive.google.com/file/d/' + x.modelo_id + '/view' : ''));
  p('- Descrição dos campos (igual ao arquivo do modelo):');
  p('```json');
  p(JSON.stringify(rxModelo(), null, 2));
  p('```');
  p('- Cópia para preencher (identificação já preenchida):');
  p('```json');
  p(JSON.stringify(rxModeloPreenchido(x.id, a.file_id, a.nome), null, 2));
  p('```');
  p();
  var texto = String(d.texto || '');
  var max = REVISAO_EXTERNA_CFG.MAX_TEXTO;
  p('## 7. Texto lido pelo sistema' + (texto.length > max || (d.texto_total || 0) > texto.length ? ' (primeiros ' + Math.min(max, texto.length) + ' de ' + d.texto_total + ' caracteres)' : ''));
  p('<<<INÍCIO DO TEXTO');
  p(texto ? texto.slice(0, max) : '(o sistema não conseguiu ler texto deste arquivo — use o link da seção 1)');
  p('FIM DO TEXTO>>>');
  return L.join('\n');
}

/** Extrai o JSON do conteúdo do arquivo (aceita cerca ```json e BOM). */
function rxParse(conteudo) {
  var t = String(conteudo || '').replace(/^﻿/, '').trim();
  var m = t.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (m) t = m[1].trim();
  var i = t.indexOf('{'), j = t.lastIndexOf('}');
  if (i === -1 || j <= i) return { ok: false, erro: 'O arquivo não contém um JSON.' };
  try { return { ok: true, json: JSON.parse(t.slice(i, j + 1)) }; }
  catch (e) { return { ok: false, erro: 'O JSON do arquivo está inválido: ' + e.message }; }
}

function _rxStr(v) { return v === null || v === undefined ? '' : String(v).trim(); }

/**
 * Confere o resultado contra a revisão esperada e normaliza os campos do cartão.
 * @param {Object} esperado {revisao_id, file_id}
 * @param {string} keyText texto do documento já normalizado (normKey)
 */
function rxValidar(json, esperado, rules, keyText) {
  if (!json || typeof json !== 'object' || Array.isArray(json)) return { ok: false, erro: 'O arquivo não segue o modelo.' };
  var avisos = [];
  if (json.schema && json.schema !== RX_SCHEMA) return { ok: false, erro: 'O arquivo segue outro modelo (' + json.schema + ').' };
  if (!json.schema) avisos.push('O arquivo não informa o modelo (schema); conferi pelos campos.');
  if (_rxStr(json.revisao_id) !== esperado.revisao_id) {
    return { ok: false, erro: 'O arquivo é de outra revisão (' + (_rxStr(json.revisao_id) || 'sem ID') + '). Esta revisão é ' + esperado.revisao_id + '.' };
  }
  if (_rxStr(json.file_id) !== esperado.file_id) {
    return { ok: false, erro: 'O arquivo fala de outro documento (file_id ' + (_rxStr(json.file_id) || 'vazio') + '). Nada foi preenchido.' };
  }
  var modo = _rxStr(json.modo).toUpperCase();
  if (modo !== 'EXISTENTE' && modo !== 'NOVO') return { ok: false, erro: 'Campo "modo" precisa ser EXISTENTE ou NOVO (veio "' + _rxStr(json.modo) + '").' };
  var campos = { modo: modo, rule_id: null, variaveis: {}, nome_final: null, document_type: null };

  if (modo === 'EXISTENTE') {
    var rid = _rxStr(json.rule_id).toUpperCase();
    var m = rid.match(/^NOM-?(\d{1,4})$/);
    if (m) rid = 'NOM-' + txPad(Number(m[1]), 3);
    var rule = (rules || []).filter(function (r) { return r.rule_id === rid && r.status === 'VIGENTE'; })[0];
    if (!rule) return { ok: false, erro: 'O tipo "' + (_rxStr(json.rule_id) || 'vazio') + '" não existe (ou não está vigente) no sistema.' };
    campos.rule_id = rid;
    var esperadas = (rule.variables || []).filter(function (v) { return v.required && !(v.name === 'TEOR' && rule.family); }).map(function (v) { return v.name; });
    var vin = json.variaveis && typeof json.variaveis === 'object' ? json.variaveis : {};
    Object.keys(vin).forEach(function (k) {
      var val = _rxStr(vin[k]);
      if (esperadas.indexOf(k) === -1) { if (val) avisos.push('Variável "' + k + '" não faz parte do padrão de ' + rid + ' — ignorada.'); return; }
      if (val) campos.variaveis[k] = val;
    });
    var faltam = esperadas.filter(function (k) { return !campos.variaveis[k]; });
    if (faltam.length) avisos.push('Faltam variáveis: ' + faltam.join(', ') + '.');
  } else {
    var nome = _rxStr(json.nome_documento);
    if (!nome) return { ok: false, erro: 'No modo NOVO o campo "nome_documento" é obrigatório.' };
    var semId = nome.replace(/^\d{3}[\s_\-]+/, '');
    if (semId !== nome) avisos.push('Tirei o ID do cliente do começo do nome (' + nome.slice(0, nome.length - semId.length) + ').');
    campos.nome_final = semId;
    campos.document_type = _rxStr(json.nome_do_tipo) || null;
    if (_rxStr(json.rule_id) && _rxStr(json.rule_id).toLowerCase() !== 'null') avisos.push('No modo NOVO o rule_id é ignorado.');
  }

  var dk = normKey(json.destino).replace(/ /g, '');
  campos.destino = CLIENTES_CFG.BUCKETS.indexOf(dk) !== -1 ? dk : null;
  if (_rxStr(json.destino) && !campos.destino) avisos.push('Pasta de destino "' + _rxStr(json.destino) + '" não existe — escolha no passo 3.');
  campos.sempre_destino = json.sempre_destino === true;

  var vistos = {}, fora = [];
  campos.ancoras = [];
  (Array.isArray(json.ancoras) ? json.ancoras : []).forEach(function (a) {
    var k = normKey(a);
    if (!k || vistos[k]) return;
    vistos[k] = true;
    if (keyText && txHas(keyText, k)) campos.ancoras.push(k); else fora.push(_rxStr(a));
  });
  if (fora.length) avisos.push('Frases que não estão no texto lido (não marquei): ' + fora.join(' | '));
  if (keyText && campos.ancoras.length < 2) avisos.push('Menos de 2 frases de reconhecimento válidas — marque no passo 4.');
  campos.comentario = _rxStr(json.comentario).slice(0, 1000);

  var rs = json.resumo && typeof json.resumo === 'object' ? json.resumo : {};
  var pts = rs.pontos_de_atencao;
  if (!Array.isArray(pts)) pts = _rxStr(pts) ? [_rxStr(pts)] : [];
  var resumo = {
    interpretacao: _rxStr(rs.interpretacao || (typeof json.resumo === 'string' ? json.resumo : '')).slice(0, 2000),
    pontos_de_atencao: pts.map(_rxStr).filter(Boolean).slice(0, 20)
  };
  return { ok: true, campos: campos, resumo: resumo, avisos: avisos };
}

/** O que o painel mostra sobre a revisão externa. */
function rxView(ext) {
  if (!ext || !ext.id) return null;
  return {
    id: ext.id, arquivo: ext.arquivo, status: ext.status, gerado_em: ext.gerado_em, carregado_em: ext.carregado_em || null,
    pasta_link: ext.pasta_id ? 'https://drive.google.com/drive/folders/' + ext.pasta_id : null,
    resultado_link: ext.resultado_file_id ? 'https://drive.google.com/file/d/' + ext.resultado_file_id + '/view' : null
  };
}

/* ---------------- Drive ---------------- */

/** Garante o modelo na pasta. O modelo é do sistema: se alguém alterou, volta ao original. */
function rxGarantirModelo(pastaId) {
  var conteudo = JSON.stringify(rxModelo(), null, 2);
  var f = dsFindByName(pastaId, REVISAO_EXTERNA_CFG.MODELO)[0];
  if (!f) return createJson(REVISAO_EXTERNA_CFG.MODELO, pastaId, rxModelo()).id;
  var file = DriveApp.getFileById(f.id);
  if (file.getBlob().getDataAsString() !== conteudo) file.setContent(conteudo);
  return f.id;
}

/** Arquivos da pasta cujo nome contém o ID (mais recente primeiro). */
function rxProcurar(pastaId, id) {
  var folder = DriveApp.getFolderById(pastaId), it, out = [];
  try { it = folder.searchFiles('title contains ' + quoteQ(id) + ' and trashed = false'); }
  catch (e) { it = folder.getFiles(); }
  while (it.hasNext()) {
    var f = it.next();
    if (f.isTrashed() || f.getName().indexOf(id) === -1) continue;
    out.push({ id: f.getId(), name: f.getName(), mime: f.getMimeType(), size: _ppSize(f), updated: _ppIso(f.getLastUpdated()) });
  }
  return out.sort(function (a, b) { return String(b.updated).localeCompare(String(a.updated)); });
}

function rxLerConteudo(f) {
  if (f.mime === 'application/vnd.google-apps.document') return DocumentApp.openById(f.id).getBody().getText();
  if (f.size && Number(f.size) > REVISAO_EXTERNA_CFG.MAX_BYTES) throw new Error('O arquivo é grande demais para um resultado de revisão (' + f.size + ' bytes).');
  return DriveApp.getFileById(f.id).getBlob().getDataAsString();
}

function _rxLock() {
  var lock = LockService.getScriptLock();
  return lock.tryLock(60000) ? lock : null;
}

/**
 * Gera (ou mostra de novo) o prompt de um arquivo da Revisão.
 * @param {boolean} novo true = descarta o ID anterior (o arquivo do prompt antigo deixa de valer)
 */
function rxGerarPrompt(fileId, novo) {
  var lock = _rxLock();
  if (!lock) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  try {
    var ctx = plLoadContext({ id: 'CHATGPT' });
    var r = ctx.idx[fileId];
    if (!r) return _lnErr('Arquivo não encontrado no MAPA.');
    if (r.etapa !== 'REVISAO') return _lnErr('Este arquivo não está mais em Revisão (etapa: ' + r.etapa + '). Atualize a lista.');
    var d = lnDetalhe(fileId, ctx);
    if (!d.ok) return d;
    var pasta = sysFolders().chatgpt;
    var modeloId = rxGarantirModelo(pasta);
    var ext = r.revisao_externa;
    var reutilizado = !novo && !!ext && !!ext.id && (ext.status === 'AGUARDANDO' || ext.status === 'CARREGADO');
    if (!reutilizado) {
      var anteriores = ext && ext.id ? (ext.anteriores || []).concat([ext.id]).slice(-10) : [];
      var id = rxNovoId(r.file_id, jbStamp(), Utilities.getUuid().replace(/-/g, '').slice(0, 4));
      ext = r.revisao_externa = {
        id: id, arquivo: rxNomeArquivo(id), pasta_id: pasta, modelo_id: modeloId, gerado_em: nowIso(),
        status: 'AGUARDANDO', carregado_em: null, resultado_file_id: null, anteriores: anteriores
      };
      ctx.saveMapa();
    }
    var prompt = rxMontarPrompt({
      id: ext.id, arquivo: ext.arquivo, detalhe: d, caminho: r.caminho_snapshot, tamanho: r.tamanho,
      pasta_id: ext.pasta_id || pasta, modelo_id: modeloId,
      gerado_em: Utilities.formatDate(new Date(ext.gerado_em), 'America/Sao_Paulo', 'dd/MM/yyyy HH:mm')
    });
    return { ok: true, prompt: prompt, revisao: rxView(ext), reutilizado: reutilizado };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

/** "Carregar resultado": acha o arquivo desta revisão, confere e devolve os campos do cartão. */
function rxCarregar(fileId) {
  var lock = _rxLock();
  if (!lock) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  try {
    var ctx = plLoadContext({ id: 'CHATGPT' });
    var r = ctx.idx[fileId];
    if (!r) return _lnErr('Arquivo não encontrado no MAPA.');
    if (r.etapa !== 'REVISAO') return _lnErr('Este arquivo não está mais em Revisão (etapa: ' + r.etapa + ').');
    var ext = r.revisao_externa;
    if (!ext || !ext.id) return _lnErr('Gere o prompt do ChatGPT primeiro.');

    // Veio por lote: o rxCarregarLote já validou este item (mesmo rxValidar) e
    // guardou os campos. O cartão da Revisão abre igual e o operador continua
    // aprovando um a um — o lote só acelerou a produção do parecer.
    if (ext.resultado_lote && ext.resultado_lote.campos) {
      return {
        ok: true, campos: ext.resultado_lote.campos, resumo: ext.resultado_lote.resumo,
        avisos: (ext.resultado_lote.avisos || []).concat(['Resultado veio do lote ' + (ext.lote_id || '?') + '.']),
        revisao: rxView(ext), de_lote: ext.lote_id || null,
        arquivo: ext.resultado_file_id
          ? { id: ext.resultado_file_id, nome: ext.lote_arquivo || null, link: 'https://drive.google.com/file/d/' + ext.resultado_file_id + '/view' }
          : null
      };
    }

    var pasta = ext.pasta_id || sysFolders().chatgpt;
    var achados = rxProcurar(pasta, ext.id);
    if (!achados.length) {
      var antigo = null;
      (ext.anteriores || []).slice().reverse().some(function (old) { var a = rxProcurar(pasta, old); if (a.length) antigo = old; return !!a.length; });
      if (antigo) return { ok: false, aguardando: true, erro: 'Achei só o arquivo de um prompt anterior (' + antigo + '), que não vale mais. No ChatGPT, use o prompt atual (' + ext.id + ') e grave de novo.' };
      return { ok: false, aguardando: true, erro: 'Ainda não encontrei ' + ext.arquivo + ' na pasta _SISTEMA/REVISAO_CHATGPT. Confira se o ChatGPT confirmou a gravação (ou coloque lá o arquivo baixado, com esse nome).' };
    }
    var f = achados[0];
    var avisos = [];
    if (achados.length > 1) avisos.push('Há ' + achados.length + ' arquivos com este ID; usei o mais recente (' + f.name + ').');
    var parsed = rxParse(rxLerConteudo(f));
    if (!parsed.ok) return _lnErr(parsed.erro + ' (' + f.name + ')');
    var v = rxValidar(parsed.json, { revisao_id: ext.id, file_id: r.file_id }, ctx.rules, normKey(ctx.textFor(r)));
    if (!v.ok) return _lnErr(v.erro + ' (' + f.name + ')');
    ext.status = 'CARREGADO';
    ext.carregado_em = nowIso();
    ext.resultado_file_id = f.id;
    ctx.saveMapa();
    return {
      ok: true, campos: v.campos, resumo: v.resumo, avisos: avisos.concat(v.avisos), revisao: rxView(ext),
      arquivo: { id: f.id, nome: f.name, link: 'https://drive.google.com/file/d/' + f.id + '/view' }
    };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { rxModelo: rxModelo, rxNovoId: rxNovoId, rxNomeArquivo: rxNomeArquivo, rxParse: rxParse, rxValidar: rxValidar, rxMontarPrompt: rxMontarPrompt };
}
