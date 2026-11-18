/**
 * RevisaoLote — gera os prompts da Revisão EM LOTE e carrega o resultado de volta
 * num arquivo só.
 *
 * Por que existe: o prompt individual (RevisaoExterna.js) repete ~11,7 KB fixos em
 * cada arquivo — instruções, tabela das 56 regras e modelo. Com 36 documentos isso
 * é ~420 KB de texto idêntico copiado 36 vezes. Aqui o cabeçalho sai uma vez só e
 * cada documento vira um bloco curto.
 *
 * Três grupos, por motivo da revisão (cada um precisa de coisa diferente):
 *   TIPO    — não se sabe que documento é. Precisa da tabela inteira das 56 regras.
 *   CAMPOS  — a regra já está identificada, falta extrair variável. Só precisa
 *             daquela regra.
 *   DESTINO — a regra já está identificada, falta decidir a pasta. Só precisa
 *             daquela regra + a explicação dos três destinos.
 *
 * A volta é UM arquivo JSON com um array de itens. Cada item carrega revisao_id e
 * file_id, então o rxValidar() que já existe confere item a item — a proteção
 * contra troca de documento continua valendo igual.
 *
 * O operador continua aprovando um a um no cartão da Revisão. Isto acelera a
 * produção do parecer, não substitui o OK.
 */

var RXL_SCHEMA = 'gaia-revisao-chatgpt-lote/1.0';

/* ---------------- Puro (testável em node) ---------------- */

/** Grupo de um registro em Revisão. Decide quanto contexto o prompt precisa carregar. */
function rxlGrupo(rec) {
  var m = String(rec.motivo_revisao || '');
  var temRegra = !!rec.rule_id;
  if (temRegra && /^(VARIAVEIS_FALTANTES|FORMATO_INVALIDO|EXTRACAO_PENDENTE)/.test(m)) return 'CAMPOS';
  if (temRegra && /^(DESTINO_NAO_DEFINIDO|CONTEXTO_AMBIGUO|MULTI)/.test(m)) return 'DESTINO';
  return 'TIPO';
}

var RXL_GRUPO_TITULO = {
  TIPO: 'identificar o tipo do documento',
  CAMPOS: 'extrair os campos que faltam (o tipo já está definido)',
  DESTINO: 'decidir a pasta de destino (o tipo já está definido)'
};

/** Id do lote. */
function rxlNovoLoteId(stamp, grupo, seq) {
  return 'LT-' + stamp + '-' + grupo + '-' + String(seq < 10 ? '0' + seq : seq);
}

function rxlNomePrompt(loteId) { return REVISAO_LOTE_CFG.PREFIXO_PROMPT + loteId + '.md'; }
function rxlNomeResultado(loteId) { return REVISAO_LOTE_CFG.PREFIXO_RESULTADO + loteId + '.json'; }

/**
 * Divide os itens em arquivos respeitando teto de quantidade E de caracteres.
 * @param {Array} itens cada um com .custo (chars do bloco)
 * @return {Array<Array>}
 */
function rxlFatiar(itens, maxItens, maxChars) {
  var out = [], atual = [], soma = 0;
  itens.forEach(function (it) {
    var estoura = atual.length >= maxItens || (atual.length && soma + it.custo > maxChars);
    if (estoura) { out.push(atual); atual = []; soma = 0; }
    atual.push(it);
    soma += it.custo;
  });
  if (atual.length) out.push(atual);
  return out;
}

/** Ordena para que documentos do mesmo tipo suspeito fiquem lado a lado. */
function rxlOrdenar(itens) {
  return itens.slice().sort(function (a, b) {
    return String(a.chaveTipo).localeCompare(String(b.chaveTipo)) ||
      String(a.cliente).localeCompare(String(b.cliente)) ||
      String(a.nome).localeCompare(String(b.nome));
  });
}

/** Modelo de UM item do array de resultado. */
function rxlModeloItem() {
  var m = rxModelo();
  delete m.schema; // o schema fica no envelope do lote
  return m;
}

/** Envelope que o ChatGPT deve gravar. */
function rxlEnvelopeExemplo(loteId, exemplos) {
  return { schema: RXL_SCHEMA, lote_id: loteId, itens: exemplos };
}

/* ---------------- Montagem do prompt ---------------- */

/**
 * Monta o .md do lote.
 * @param {Object} x {loteId, grupo, gerado_em, itens[], regras[], regrasDoLote[]}
 */
function rxlMontarPrompt(x) {
  var L = [];
  var p = function (s) { L.push(s === undefined ? '' : s); };
  var grupo = x.grupo;

  p('# Gaia Office — revisão em lote (' + x.itens.length + ' documentos)');
  p('Lote: ' + x.loteId + ' · gerado em ' + x.gerado_em + ' (horário de Brasília)');
  p('Tarefa deste lote: **' + RXL_GRUPO_TITULO[grupo] + '**.');
  p();
  p('Você vai me ajudar a revisar ' + x.itens.length + ' documentos do sistema Gaia Office de uma vez.');
  p('Cada documento está na seção 5, numerado, com a identificação dele. Trate um por vez, na ordem, e não misture informação entre documentos.');
  p();

  p('## 1. Como vamos trabalhar');
  p('**Etapa A — análise.** Percorra os documentos e, para cada um, diga em 1 ou 2 linhas o que entendeu' +
    (grupo === 'TIPO' ? ' e qual tipo da seção 4 se aplica (ou se é tipo novo)' :
      grupo === 'CAMPOS' ? ' e quais valores você encontrou para as variáveis que faltam' :
        ' e para qual pasta ele deve ir') + '.');
  p('Depois **pare e me mostre a lista**, numerada, em formato de tabela curta. Nesta etapa não gere o JSON.');
  p();
  p('**Etapa B — perguntas.** Junte numa lista só TODAS as dúvidas que você tiver, indicando o número do documento. Eu respondo todas de uma vez. Se não tiver dúvida em nenhum, diga isso.');
  p();
  p('**Etapa C — gerar o arquivo (só com a minha autorização).** Quando eu disser algo como "OK, pode gerar":');
  p('1. produza **um único JSON** no formato da seção 3, com um item por documento, na mesma ordem;');
  p('2. `lote_id`, `revisao_id` e `file_id` vêm preenchidos e **não mudam** — copie exatamente;');
  p('3. se algum documento você não conseguiu resolver, inclua o item mesmo assim com `modo: null` e explique em `resumo.pontos_de_atencao`. Não omita item nem invente valor;');
  p('4. me entregue o JSON aqui no chat e também como arquivo para download com o nome da seção 2.');
  p();
  p('**Etapa D — gravar.** Se você conseguir gravar no Google Drive, grave na pasta da seção 2 com aquele nome exato, e confirme. Se não conseguir, tudo bem: eu baixo o arquivo e coloco lá.');
  p('Não altere, não sobrescreva e não apague nenhum outro arquivo.');
  p();

  p('## 2. Onde gravar o resultado (definido pelo sistema)');
  p('- Pasta: ' + RX_CAMINHO_PASTA);
  p('- ID da pasta: ' + x.pasta_id);
  p('- Link da pasta: https://drive.google.com/drive/folders/' + x.pasta_id);
  p('- Nome exato do arquivo: **' + rxlNomeResultado(x.loteId) + '**');
  p('- Conteúdo: somente o JSON (UTF-8), sem texto antes ou depois.');
  p();

  p('## 3. Formato do arquivo de resultado');
  p('Um envelope com o array `itens`. Cada item tem a mesma estrutura do modelo individual (sem acrescentar nem remover campos):');
  p('```json');
  p(JSON.stringify(rxlEnvelopeExemplo(x.loteId, [rxlModeloItem()]), null, 2));
  p('```');
  p();
  p('Identificação já preenchida de cada item deste lote (copie estes pares exatamente):');
  p('```json');
  p(JSON.stringify(x.itens.map(function (i) {
    return { revisao_id: i.revisao_id, file_id: i.file_id, documento: i.nome };
  }), null, 2));
  p('```');
  p();

  p('## 4. Regras do sistema (valem para todos os documentos deste lote)');
  p('- Nome final no Drive = ID do cliente + "_" + nome do documento. O sistema coloca o ID sozinho: **nunca inclua o ID do cliente no nome**.');
  if (grupo === 'TIPO') {
    p('- Tipo que já existe (modo "EXISTENTE"): use o `rule_id` da tabela abaixo e preencha em `variaveis` só as variáveis daquele padrão, com valores lidos no documento. Não crie sinônimo, abreviação nem variação do padrão.');
    p('- Tipo novo (modo "NOVO", só se nenhum tipo da tabela servir): em `nome_documento` escreva o nome sem o ID do cliente, com a extensão, no estilo dos padrões (MAIÚSCULAS, palavras separadas por "_"). Use os valores reais deste documento — o sistema transforma em partes variáveis.');
  } else {
    p('- O tipo de cada documento **já está decidido** e vem no bloco dele. Use modo "EXISTENTE" e o `rule_id` indicado. Não troque o tipo; se achar que está errado, não invente: diga na Etapa B.');
  }
  p('- Datas no formato DD-MM-AAAA. CNPJ com 14 dígitos. **Nunca invente valor**: se não encontrar, deixe `null` e avise em `resumo.pontos_de_atencao`.');
  p('- `destino`: DOCUMENTOS (documentos pessoais do cliente), SOCIETARIO (empresa) ou IMOVEIS (imóvel/edificação). `sempre_destino`: true só se esse tipo deve ir sempre para essa pasta.');
  p('- `ancoras`: pelo menos 2 frases copiadas do texto, que aparecem em TODO documento desse tipo (título, órgão emissor). **Nunca** use nome, CPF/CNPJ, endereço ou números do cliente.');
  p('- `comentario`: 1 ou 2 frases com a regra combinada nesta conversa (fica gravada no aprendizado do sistema).');
  p('- Quem aprova no sistema sou eu: o arquivo só preenche a tela de revisão, e eu confiro um a um antes do OK.');
  if ((REVISAO_EXTERNA_CFG.CONHECIMENTO || []).length) {
    p();
    p('### Conhecimento operacional da Gaia');
    REVISAO_EXTERNA_CFG.CONHECIMENTO.forEach(function (c) { p('- ' + c); });
  }
  p();

  var regras = grupo === 'TIPO' ? x.regras : x.regrasDoLote;
  p('### Tipos de documento ' + (grupo === 'TIPO' ? 'que já existem (' + regras.length + ')' : 'usados neste lote (' + regras.length + ')'));
  p('rule_id | tipo | padrão do nome | variáveis | pasta');
  regras.forEach(function (r) {
    var vars = (r.variables || []).map(function (v) { return v.name + ' (' + v.format + ')'; }).join(', ') || '—';
    p(r.rule_id + ' | ' + r.document_type + ' | ' + r.approved_pattern + ' | ' + vars + ' | ' + (r.destino || 'pelo contexto'));
  });
  p();

  p('## 5. Documentos (' + x.itens.length + ')');
  x.itens.forEach(function (i, n) {
    p();
    p('---');
    p();
    p('### ' + (n + 1) + '. ' + i.nome);
    p('- `revisao_id`: ' + i.revisao_id);
    p('- `file_id`: ' + i.file_id);
    p('- Abrir: ' + i.link);
    p('- Cliente: ' + i.cliente + ' — ID do cliente: ' + (i.cliente_nnn || 'ainda não criado'));
    p('- Tipo de arquivo: ' + (i.mime || '—'));
    p('- Por que está em revisão: ' + i.motivo_txt);
    if (i.rule_id) p('- **Tipo já definido**: ' + i.rule_id + (i.rule_tipo ? ' — ' + i.rule_tipo : ''));
    if (grupo === 'CAMPOS' && i.faltando && i.faltando.length) p('- **Variáveis que faltam**: ' + i.faltando.join(', '));
    if (grupo === 'CAMPOS' && i.variaveis_conhecidas) p('- Já preenchidas pelo sistema: ' + i.variaveis_conhecidas);
    if (grupo === 'TIPO' && i.sugestoes) p('- Sugestões do sistema: ' + i.sugestoes);
    if (i.ancoras) p('- Frases do topo do documento: ' + i.ancoras);
    p();
    p('Texto lido pelo sistema' + (i.texto_total > i.texto.length ? ' (primeiros ' + i.texto.length + ' de ' + i.texto_total + ' caracteres — se precisar de mais, abra pelo link)' : '') + ':');
    p('<<<INÍCIO ' + i.revisao_id);
    p(i.texto || '(o sistema não conseguiu ler texto deste arquivo — use o link acima)');
    p('FIM ' + i.revisao_id + '>>>');
  });
  p();
  p('---');
  p();
  p('Fim do lote ' + x.loteId + ' — ' + x.itens.length + ' documentos. Comece pela Etapa A.');
  return L.join('\n');
}

/* ---------------- Geração ---------------- */

/**
 * Gera os prompts em lote de tudo que está na Revisão.
 * @param {Object} opts {folderId?: só uma pasta de cliente, grupos?: ['TIPO',...], novo?: refaz ids}
 * @return {{ok:boolean, arquivos:[], total:number, por_grupo:{}}}
 */
function rxGerarPromptLote(opts) {
  opts = opts || {};
  var lock = _rxLock();
  if (!lock) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  try {
    var ctx = plLoadContext({ id: 'LOTE' });
    var pasta = sysFolders().chatgpt;
    var stamp = jbStamp();
    var maxTexto = REVISAO_LOTE_CFG.MAX_TEXTO;

    var candidatos = (ctx.mapa.arquivos || []).filter(function (r) {
      if (r.etapa !== 'REVISAO') return false;
      if (opts.folderId && r.acervo_cliente_folder_id !== opts.folderId) return false;
      return true;
    });
    if (!candidatos.length) return { ok: true, total: 0, arquivos: [], aviso: 'Nada na Revisão' + (opts.folderId ? ' nessa pasta' : '') + '.' };

    var gruposPedidos = opts.grupos && opts.grupos.length ? opts.grupos : null;
    var porGrupo = { TIPO: [], CAMPOS: [], DESTINO: [] };
    var pulados = [];

    candidatos.forEach(function (r) {
      var g = rxlGrupo(r);
      if (gruposPedidos && gruposPedidos.indexOf(g) === -1) return;
      var item = rxlItemDoRec(ctx, r, maxTexto, stamp, !!opts.novo);
      if (!item.ok) { pulados.push({ nome: r.nome_arquivo, motivo: item.erro }); return; }
      porGrupo[g].push(item.item);
    });

    var todasRegras = ctx.rules.filter(function (x) { return x.status === 'VIGENTE'; }).map(_lnRuleView);
    var arquivos = [];
    var geradoEm = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'dd/MM/yyyy HH:mm');

    ['TIPO', 'CAMPOS', 'DESTINO'].forEach(function (grupo) {
      var itens = rxlOrdenar(porGrupo[grupo]);
      if (!itens.length) return;
      var fatias = rxlFatiar(itens, REVISAO_LOTE_CFG.MAX_ITENS_ARQUIVO, REVISAO_LOTE_CFG.MAX_CHARS_ARQUIVO);
      fatias.forEach(function (fatia, i) {
        var loteId = rxlNovoLoteId(stamp, grupo, i + 1);
        var usados = {};
        fatia.forEach(function (it) { if (it.rule_id) usados[it.rule_id] = true; });
        var regrasDoLote = todasRegras.filter(function (r) { return usados[r.rule_id]; });

        var md = rxlMontarPrompt({
          loteId: loteId, grupo: grupo, gerado_em: geradoEm, itens: fatia,
          regras: todasRegras, regrasDoLote: regrasDoLote, pasta_id: pasta
        });

        var nome = rxlNomePrompt(loteId);
        var antigo = dsFindByName(pasta, nome)[0];
        var fid;
        if (antigo) { DriveApp.getFileById(antigo.id).setContent(md); fid = antigo.id; }
        else { fid = DriveApp.getFolderById(pasta).createFile(nome, md, 'text/markdown').getId(); }

        // amarra cada documento a este lote
        fatia.forEach(function (it) {
          var rec = ctx.idx[it.file_id];
          if (rec && rec.revisao_externa) {
            rec.revisao_externa.lote_id = loteId;
            rec.revisao_externa.lote_arquivo = rxlNomeResultado(loteId);
          }
        });

        arquivos.push({
          lote_id: loteId, grupo: grupo, nome: nome, file_id: fid, itens: fatia.length,
          chars: md.length, tokens_aprox: Math.round(md.length / 3.7),
          resultado_esperado: rxlNomeResultado(loteId),
          link: 'https://drive.google.com/file/d/' + fid + '/view'
        });
      });
    });

    ctx.dirty = true;
    ctx.saveMapa();

    var total = arquivos.reduce(function (n, a) { return n + a.itens; }, 0);
    return {
      ok: true, total: total, arquivos: arquivos, pulados: pulados,
      pasta_link: 'https://drive.google.com/drive/folders/' + pasta,
      por_grupo: { TIPO: porGrupo.TIPO.length, CAMPOS: porGrupo.CAMPOS.length, DESTINO: porGrupo.DESTINO.length }
    };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

/** Monta o bloco de UM documento (e garante o revisao_id dele). */
function rxlItemDoRec(ctx, r, maxTexto, stamp, novo) {
  try {
    var d = lnDetalhe(r.file_id, ctx);
    if (!d.ok) return { ok: false, erro: d.erro || 'detalhe indisponível' };
    var a = d.arquivo;

    var ext = r.revisao_externa;
    var reaproveita = !novo && ext && ext.id && (ext.status === 'AGUARDANDO' || ext.status === 'CARREGADO');
    if (!reaproveita) {
      var anteriores = ext && ext.id ? (ext.anteriores || []).concat([ext.id]).slice(-10) : [];
      var id = rxNovoId(r.file_id, stamp, Utilities.getUuid().replace(/-/g, '').slice(0, 4));
      ext = r.revisao_externa = {
        id: id, arquivo: rxNomeArquivo(id), pasta_id: sysFolders().chatgpt, modelo_id: null,
        gerado_em: nowIso(), status: 'AGUARDANDO', carregado_em: null, resultado_file_id: null,
        anteriores: anteriores, lote_id: null, lote_arquivo: null, resultado_lote: null
      };
    }

    var regra = r.rule_id && ctx.ruleById[r.rule_id] ? ctx.ruleById[r.rule_id] : null;
    var faltando = [];
    if (regra) {
      (regra.variables || []).forEach(function (v) {
        if (v.required && (d.variaveis[v.name] === undefined || d.variaveis[v.name] === null || d.variaveis[v.name] === '')) {
          faltando.push(v.name + ' (' + v.format + ')');
        }
      });
    }
    var conhecidas = Object.keys(d.variaveis || {}).filter(function (k) {
      return d.variaveis[k] !== null && d.variaveis[k] !== undefined && d.variaveis[k] !== '';
    }).map(function (k) { return k + '=' + d.variaveis[k]; }).join(', ');

    var texto = String(d.texto || '').slice(0, maxTexto);
    var item = {
      revisao_id: ext.id, file_id: r.file_id, nome: a.nome, link: a.link,
      cliente: a.cliente, cliente_nnn: a.cliente_nnn, mime: a.mime,
      motivo_txt: rxMotivoTxt(a.motivo), rule_id: r.rule_id || null,
      rule_tipo: regra ? regra.document_type : null,
      faltando: faltando, variaveis_conhecidas: conhecidas || null,
      sugestoes: (d.sugestoes || []).slice(0, 4).map(function (s) { return s.rule_id + ' ' + s.document_type + ' (' + s.score + ')'; }).join('; ') || null,
      ancoras: (d.ancoras || []).slice(0, 6).map(function (x) { return '"' + x.texto + '"'; }).join('; ') || null,
      texto: texto, texto_total: d.texto_total || 0,
      chaveTipo: r.rule_id || ((d.sugestoes || [])[0] || {}).rule_id || 'ZZZ'
    };
    item.custo = texto.length + 900; // texto + cabeçalho do bloco
    return { ok: true, item: item };
  } catch (e) {
    return { ok: false, erro: String(e && e.message || e) };
  }
}

/* ---------------- Carga do resultado ---------------- */

/**
 * Lê o arquivo de resultado de um lote e valida item a item.
 * Não aplica nada: só preenche o cartão de cada documento na Revisão.
 * @return {{ok:boolean, carregados:number, itens:[], erros:[]}}
 */
function rxCarregarLote(loteId) {
  var lock = _rxLock();
  if (!lock) return _lnErr('O sistema está ocupado processando. Tente de novo em alguns segundos.');
  try {
    if (!loteId) return _lnErr('Informe o lote.');
    var ctx = plLoadContext({ id: 'LOTE-CARGA' });
    var pasta = sysFolders().chatgpt;

    var achados = rxProcurar(pasta, REVISAO_LOTE_CFG.PREFIXO_RESULTADO + loteId).filter(function (f) { return !/\.md$/i.test(f.name); });
    if (!achados.length) {
      return { ok: false, aguardando: true, erro: 'Ainda não encontrei ' + rxlNomeResultado(loteId) + ' em _SISTEMA/REVISAO_CHATGPT. Confira se o ChatGPT gravou (ou coloque lá o arquivo baixado, com esse nome).' };
    }
    var f = achados[0];
    var parsed = rxParse(rxLerConteudo(f));
    if (!parsed.ok) return _lnErr(parsed.erro + ' (' + f.name + ')');

    var env = parsed.json;
    if (env.schema && env.schema !== RXL_SCHEMA) return _lnErr('O arquivo segue outro modelo (' + env.schema + ').');
    if (env.lote_id && env.lote_id !== loteId) return _lnErr('O arquivo é do lote ' + env.lote_id + ', não do ' + loteId + '.');
    var itens = env.itens;
    if (!Array.isArray(itens) || !itens.length) return _lnErr('O arquivo não traz a lista "itens".');

    var ok = [], erros = [];
    itens.forEach(function (raw, n) {
      var rotulo = '#' + (n + 1) + ' ' + (raw && raw.documento ? raw.documento : '(sem nome)');
      if (!raw || typeof raw !== 'object') { erros.push({ item: rotulo, erro: 'item não é objeto' }); return; }
      var rec = ctx.idx[_rxStr(raw.file_id)];
      if (!rec) { erros.push({ item: rotulo, erro: 'file_id ' + _rxStr(raw.file_id) + ' não está no MAPA' }); return; }
      if (rec.etapa !== 'REVISAO') { erros.push({ item: rotulo, erro: 'já não está em Revisão (etapa ' + rec.etapa + ')' }); return; }
      var ext = rec.revisao_externa;
      if (!ext || !ext.id) { erros.push({ item: rotulo, erro: 'sem revisão gerada' }); return; }

      // o rxValidar que já existe faz a conferência pesada, item a item
      var v = rxValidar(
        JSON.parse(JSON.stringify(raw)),
        { revisao_id: ext.id, file_id: rec.file_id },
        ctx.rules, normKey(ctx.textFor(rec))
      );
      if (!v.ok) { erros.push({ item: rotulo, erro: v.erro }); return; }

      ext.status = 'CARREGADO';
      ext.carregado_em = nowIso();
      ext.resultado_file_id = f.id;
      ext.lote_id = loteId;
      ext.resultado_lote = { campos: v.campos, resumo: v.resumo, avisos: v.avisos || [], em: nowIso() };
      ok.push({ item: rotulo, file_id: rec.file_id, nome: rec.nome_arquivo, revisao_id: ext.id });
    });

    ctx.dirty = true;
    ctx.saveMapa();

    return {
      ok: true, lote_id: loteId, carregados: ok.length, total_no_arquivo: itens.length,
      itens: ok, erros: erros,
      arquivo: { id: f.id, nome: f.name, link: 'https://drive.google.com/file/d/' + f.id + '/view' }
    };
  } catch (e) {
    return _lnErr(String(e && e.message || e));
  } finally {
    lock.releaseLock();
  }
}

/** Lotes gerados que ainda têm documentos esperando carga. */
function rxlListarLotes(mapa) {
  var porLote = {};
  (mapa.arquivos || []).forEach(function (r) {
    var e = r.revisao_externa;
    if (!e || !e.lote_id) return;
    var L = porLote[e.lote_id] = porLote[e.lote_id] || { lote_id: e.lote_id, arquivo: e.lote_arquivo, total: 0, carregados: 0 };
    L.total++;
    if (e.status === 'CARREGADO') L.carregados++;
  });
  return Object.keys(porLote).sort().reverse().map(function (k) { return porLote[k]; });
}

/* ==================== Aplicar o lote inteiro ====================
 *
 * Gerar o prompt em lote e carregar o resultado em lote resolvia metade do
 * problema: o operador ainda abria os 36 cartões um a um e apertava "Aprender
 * e seguir" em cada um — redigitando à mão exatamente o que o ChatGPT já tinha
 * entregado e o rxValidar já tinha conferido contra o texto do documento,
 * inclusive as duas frases de reconhecimento. O gargalo só mudou de lugar.
 *
 * Aqui o lote inteiro é aplicado de uma vez. Não há atalho na validação: cada
 * item passa pelo MESMO lnAprender do botão manual, com os mesmos campos. O
 * que muda é quem digita — ninguém.
 *
 * Um item por chamada, de propósito: lnAprender carrega o contexto, grava a
 * regra, monta o pacote e ainda reconfere os OUTROS arquivos da Revisão contra
 * o que acabou de aprender. É pesado; 36 numa execução só estouraria o limite
 * de 6 minutos do Apps Script. O painel chama em sequência e mostra o
 * progresso — e como cada aplicação costuma resolver outros arquivos em
 * cadeia, o laço vai pulando os que já saíram da Revisão.
 */

/**
 * O que impediria o lnAprender de aplicar este item sozinho.
 * É PRÉVIA para o operador decidir antes de começar, não a palavra final:
 * a verdade sai na aplicação, que roda a validação inteira.
 */
function rxlTravas(campos, rec, rule) {
  if (!campos) return ['resultado do lote ainda não carregado'];
  var travas = [];

  // lnAprender exige frases novas quando o arquivo não foi reconhecido por
  // conteúdo com essa mesma regra (e sempre, quando o tipo é novo).
  var jaReconhecidoPelaRegra = rec.rule_id === campos.rule_id &&
    rec.reconhecido_por && rec.reconhecido_por !== 'NOME';
  var precisaAncoras = campos.modo === 'NOVO' || !jaReconhecidoPelaRegra;
  if (precisaAncoras && (campos.ancoras || []).length < 2) {
    travas.push('o ChatGPT não trouxe 2 frases que existam no texto lido');
  }

  if (campos.modo === 'NOVO') {
    if (!campos.nome_final) travas.push('sem nome_documento');
    if (!campos.destino) travas.push('sem pasta de destino');
  } else {
    if (!campos.rule_id) travas.push('sem tipo (rule_id)');
    else if (rule) {
      var faltam = (rule.variables || []).filter(function (v) {
        if (!v.required || (v.name === 'TEOR' && rule.family)) return false;
        var val = campos.variaveis && campos.variaveis[v.name];
        return val === undefined || val === null || String(val).trim() === '';
      }).map(function (v) { return v.name; });
      if (faltam.length) travas.push('falta o valor de ' + faltam.join(', '));
    }
  }
  return travas;
}

/**
 * O que dá para aplicar de um lote. SÓ LEITURA — não grava nada.
 * @return {{ok:boolean, lote_id:string, total:number, prontos:number, travados:number, ja_resolvidos:number, itens:Object[]}}
 */
function rxAplicaveis(loteId) {
  loteId = String(loteId || '');
  if (!loteId) return _lnErr('Lote não informado.');
  var ctx = plLoadContext({ id: 'LOTE-PREVIA' });
  var itens = [];

  (ctx.mapa.arquivos || []).forEach(function (rec) {
    var ext = rec.revisao_externa;
    if (!ext || ext.lote_id !== loteId) return;

    var item = { file_id: rec.file_id, nome: rec.nome_arquivo };
    if (rec.etapa !== 'REVISAO') {
      item.situacao = 'JA_RESOLVIDO';
      item.detalhe = 'saiu da Revisão (etapa ' + rec.etapa + ')';
      itens.push(item);
      return;
    }
    var campos = ext.resultado_lote && ext.resultado_lote.campos;
    var rule = campos && campos.rule_id ? ctx.ruleById[campos.rule_id] : null;
    var travas = rxlTravas(campos, rec, rule);
    item.modo = campos ? campos.modo : null;
    item.rule_id = campos ? (campos.rule_id || null) : null;
    item.destino = campos ? (campos.destino || null) : null;
    item.situacao = travas.length ? 'TRAVADO' : 'PRONTO';
    if (travas.length) item.travas = travas;
    itens.push(item);
  });

  var conta = function (s) { return itens.filter(function (i) { return i.situacao === s; }).length; };
  return {
    ok: true, lote_id: loteId, total: itens.length,
    prontos: conta('PRONTO'), travados: conta('TRAVADO'), ja_resolvidos: conta('JA_RESOLVIDO'),
    itens: itens
  };
}

/**
 * Aplica UM item do lote, com os campos que o ChatGPT entregou e o rxValidar
 * já conferiu. Mesmíssimo caminho do botão "Aprender e seguir".
 */
function rxAplicarUm(loteId, fileId) {
  loteId = String(loteId || '');
  fileId = String(fileId || '');
  if (!loteId || !fileId) return { ok: false, erro: 'Lote ou arquivo não informado.' };

  // leitura leve: só o mapa; quem carrega regras e contexto é o lnAprender
  var mapa = _pMapa();
  var rec = null;
  (mapa.arquivos || []).some(function (x) { if (x.file_id === fileId) { rec = x; return true; } return false; });
  if (!rec) return { ok: false, file_id: fileId, erro: 'Arquivo não está no MAPA.' };

  var nome = rec.nome_arquivo;
  if (rec.etapa !== 'REVISAO') {
    return { ok: true, file_id: fileId, nome: nome, pulado: true, motivo: 'já saiu da Revisão (etapa ' + rec.etapa + ')' };
  }
  var ext = rec.revisao_externa;
  if (!ext || ext.lote_id !== loteId) {
    return { ok: true, file_id: fileId, nome: nome, pulado: true, motivo: 'não faz parte do lote ' + loteId };
  }
  var campos = ext.resultado_lote && ext.resultado_lote.campos;
  if (!campos) {
    return { ok: true, file_id: fileId, nome: nome, pulado: true, motivo: 'resultado do lote não carregado' };
  }

  var p = {
    file_id: fileId,
    modo: campos.modo,
    ancoras: campos.ancoras || [],
    destino: campos.destino || null,
    comentario: campos.comentario || '',
    variaveis: campos.variaveis || {},
    origem: 'CHATGPT',
    revisao_externa_id: ext.id
  };
  if (campos.modo === 'NOVO') {
    p.document_type = campos.document_type || '';
    p.nome_final = campos.nome_final || '';
  } else {
    p.rule_id = campos.rule_id;
    p.sempre_destino = !!campos.sempre_destino;
  }

  var r = lnAprender(p);
  if (!r || !r.ok) return { ok: false, file_id: fileId, nome: nome, erro: (r && r.erro) || 'falhou sem mensagem' };
  return {
    ok: true, file_id: fileId, nome: nome, aplicado: true,
    rule_id: r.rule_id, novo: !!r.novo, status: r.status,
    nome_final: r.nome_final || null, destino: r.destino || null,
    reconhecidos_agora: r.reconhecidos_agora || 0
  };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    rxlGrupo: rxlGrupo, rxlFatiar: rxlFatiar, rxlOrdenar: rxlOrdenar,
    rxlNovoLoteId: rxlNovoLoteId, rxlNomePrompt: rxlNomePrompt, rxlNomeResultado: rxlNomeResultado,
    rxlMontarPrompt: rxlMontarPrompt, rxlListarLotes: rxlListarLotes, rxlTravas: rxlTravas,
    RXL_SCHEMA: RXL_SCHEMA
  };
}
