/**
 * Router — decide a subpasta de destino (DOCUMENTOS / SOCIETARIO / IMOVEIS) e
 * checa se o documento pertence ao cliente. Puro.
 */

/** Resumo do MANIFESTO_CLIENTE.json usado pelo roteamento e pela checagem de pertencimento. */
function rtManifestInfo(manifest) {
  manifest = manifest || {};
  var c = manifest.cliente || {};
  var info = {
    cliente: { nome: c.nome_completo || null, cpf: txDigits(c.cpf) || null },
    empresas: (manifest.empresas || []).map(function (e) {
      return { cnpj: txDigits(e.cnpj) || null, razao_social: e.razao_social || null, nome_fantasia: e.nome_fantasia || null };
    }),
    imoveis: (manifest.imoveis || []).map(function (m) {
      return {
        inscricao: txDigits(m.inscricao_imobiliaria) || null, codigo: m.codigo_do_imovel || m.property_key || null,
        matricula: txDigits(m.matricula_do_imovel) || null, logradouro: m.logradouro || null, numero: m.numero || null
      };
    })
  };
  var ids = [], names = [];
  if (info.cliente.cpf) ids.push(info.cliente.cpf);
  if (info.cliente.nome) names.push(info.cliente.nome);
  info.empresas.forEach(function (e) {
    if (e.cnpj) ids.push(e.cnpj);
    if (e.razao_social) names.push(String(e.razao_social).replace(/^[\d.\s]+/, ''));
  });
  (manifest.empresas || []).forEach(function (e) {
    (e.socios || []).forEach(function (s) { if (s && s.cpf) ids.push(txDigits(s.cpf)); if (s && s.nome_completo) names.push(s.nome_completo); });
  });
  info.ids = ids.filter(function (x, i, a) { return x && a.indexOf(x) === i; });
  info.nomes = names.filter(function (x, i, a) { return x && normKey(x).length >= 6 && a.indexOf(x) === i; });
  // termos que não podem virar âncora (são do cliente, não do tipo de documento)
  var excl = info.nomes.slice();
  info.empresas.forEach(function (e) { if (e.nome_fantasia) excl.push(e.nome_fantasia); });
  info.imoveis.forEach(function (m) { if (m.logradouro) excl.push(m.logradouro); });
  info.excluir_ancoras = excl;
  return info;
}

/** Subpasta-base do cliente para a regra. */
function rtBucketFor(rule, keyText) {
  if (rule.destination_bucket) return { bucket: rule.destination_bucket, via: 'REGRA_APRENDIDA' };
  var t = ROTAS_CFG.TABELA[rule.rule_id];
  if (t && t !== 'CONTEXTUAL') return { bucket: t, via: 'TABELA' };
  if (!t) {
    var dt = normKey(rule.document_type);
    if (ROTAS_CFG.TIPOS_PESSOAIS.some(function (p) { return txHas(dt, p); })) return { bucket: 'DOCUMENTOS', via: 'TIPO_PESSOAL' };
  }
  // contexto: vence o lado com clara maioria de palavras (2 a mais); empate ou quase empate → Revisão
  var emp = ROTAS_CFG.ANCORAS_EMPRESA.filter(function (a) { return txHas(keyText, a); }).length;
  var imo = ROTAS_CFG.ANCORAS_IMOVEL.filter(function (a) { return txHas(keyText, a); }).length;
  if (emp && !imo || emp >= imo + 2) return { bucket: 'SOCIETARIO', via: 'CONTEXTO_EMPRESA' };
  if (imo && !emp || imo >= emp + 2) return { bucket: 'IMOVEIS', via: 'CONTEXTO_IMOVEL' };
  return { bucket: null, via: t === 'CONTEXTUAL' ? 'CONTEXTO_AMBIGUO' : 'DESTINO_NAO_DEFINIDO' };
}

/**
 * Com mais de uma empresa/imóvel no manifesto, escolhe a subpasta da entidade citada no documento.
 * @return {{ok:true, sub:?string} | {ok:false, motivo:string}}
 */
function rtEntityTarget(bucket, rawText, keyText, info, nnn) {
  info = info || { empresas: [], imoveis: [] };
  var digits = txDigits(rawText);
  if (bucket === 'SOCIETARIO' && info.empresas.length > 1) {
    var cnpjs = txFindCnpjs(rawText);
    var emp = info.empresas.filter(function (e) {
      return (e.cnpj && cnpjs.indexOf(e.cnpj) !== -1) || (e.razao_social && txHas(keyText, e.razao_social));
    });
    if (emp.length !== 1) return { ok: false, motivo: 'MULTIEMPRESA_NAO_RESOLVIDA' };
    return { ok: true, sub: nnn + '_' + txFolderKey(String(emp[0].razao_social || emp[0].cnpj).replace(/^[\d.\s]+/, ''), 60) };
  }
  if (bucket === 'IMOVEIS' && info.imoveis.length > 1) {
    var imo = info.imoveis.filter(function (m) {
      return (m.inscricao && m.inscricao.length >= 8 && digits.indexOf(m.inscricao) !== -1) ||
        (m.matricula && m.matricula.length >= 4 && txHas(keyText, 'MATRICULA ' + m.matricula)) ||
        (m.codigo && txHas(keyText, m.codigo)) ||
        (m.logradouro && m.numero && txHas(keyText, m.logradouro + ' ' + m.numero));
    });
    if (imo.length !== 1) return { ok: false, motivo: 'MULTIIMOVEL_NAO_RESOLVIDO' };
    return { ok: true, sub: nnn + '_' + txFolderKey((imo[0].logradouro || 'IMOVEL') + ' ' + (imo[0].numero || 'SN'), 60) };
  }
  return { ok: true, sub: null };
}

/**
 * Pertencimento: o arquivo está na pasta do cliente, mas se o texto só cita
 * CPF/CNPJ de OUTRA pessoa/empresa (e nada do cliente), vai para Revisão.
 */
function rtBelonging(info, rawText, keyText) {
  if (!info || (!info.ids.length && !info.nomes.length)) return { status: 'SEM_DADOS_DO_CLIENTE' };
  var found = txFindCnpjs(rawText).concat(txFindCpfs(rawText));
  var mine = found.filter(function (d) { return info.ids.indexOf(d) !== -1; });
  var nameHit = info.nomes.some(function (n) { return txHas(keyText, n); });
  if (mine.length || nameHit) return { status: 'PROVADO' };
  if (found.length) return { status: 'OUTRO_CLIENTE', ids: found.slice(0, 5) };
  return { status: 'SEM_PROVA' };
}
