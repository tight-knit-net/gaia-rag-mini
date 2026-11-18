/**
 * ManifestEngine — cria, valida e muta o manifesto vivo do cliente,
 * respeitando o contrato: SCHEMA IMUTÁVEL; INSTÂNCIA MUTÁVEL.
 *
 * Permitido: preencher/atualizar valor de chave existente; adicionar item a
 * array canônico usando EXATAMENTE o template do item; atualizar status/updated_at.
 * Proibido: criar/renomear/remover chave estrutural, mudar tipo estrutural,
 * criar entidade vazia p/ satisfazer schema, inferir titularidade jurídica.
 *
 * Núcleo puro (injeta contract + templates). Leitura no Drive é opcional (v3).
 */

function _clone(o) { return JSON.parse(JSON.stringify(o)); }
function _isPlainObject(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
function _keys(o) { return Object.keys(o).sort(); }
function _sameKeySet(a, b) { var ka = _keys(a), kb = _keys(b); return ka.length === kb.length && ka.every(function (k, i) { return k === kb[i]; }); }
function _fail(errors) { return { ok: false, errors: errors }; }

/**
 * Valida a forma de um item de entidade contra seu template (igualdade de chaves).
 * Valida recursivamente arrays aninhados conhecidos (empresa.socios, empresa.cnaes).
 *
 * ESTRITA de propósito: vale para quando se ADICIONA um item novo a um array
 * canônico, e aí o contrato é taxativo — "adicionar item a array canonico usando
 * exatamente o template do item". Para conferir item que JÁ EXISTE em manifesto
 * antigo, use _formaDaEntidade(), que separa o que bloqueia do que só avisa.
 */
function validateEntityShape(item, template, entityTemplates, label) {
  var errors = [];
  label = label || 'item';
  if (!_isPlainObject(item)) return ['(' + label + ') não é objeto'];
  var it = _keys(item), tk = _keys(template);
  it.forEach(function (k) { if (tk.indexOf(k) === -1) errors.push('(' + label + ') chave desconhecida: ' + k); });
  tk.forEach(function (k) { if (it.indexOf(k) === -1) errors.push('(' + label + ') chave ausente: ' + k); });
  // arrays aninhados
  if (entityTemplates) {
    if (Array.isArray(item.socios) && entityTemplates.socio) {
      item.socios.forEach(function (s, i) { errors = errors.concat(validateEntityShape(s, entityTemplates.socio, entityTemplates, label + '.socios[' + i + ']')); });
    }
    if (Array.isArray(item.cnaes) && entityTemplates.cnae) {
      item.cnaes.forEach(function (c, i) { errors = errors.concat(validateEntityShape(c, entityTemplates.cnae, entityTemplates, label + '.cnaes[' + i + ']')); });
    }
  }
  return errors;
}

/**
 * Compara a forma de um item que JÁ EXISTE no manifesto com o template.
 * Diferença de chave não bloqueia: vira aviso. Só não ser objeto é erro.
 * @return {{errors:string[], avisos:string[]}}
 */
function _formaDaEntidade(item, template, entityTemplates, label) {
  var r = { errors: [], avisos: [] };
  label = label || 'item';
  if (!_isPlainObject(item)) { r.errors.push('(' + label + ') não é objeto'); return r; }
  var it = _keys(item), tk = _keys(template);
  it.forEach(function (k) { if (tk.indexOf(k) === -1) r.avisos.push('(' + label + ') chave própria da instância: ' + k); });
  tk.forEach(function (k) { if (it.indexOf(k) === -1) r.avisos.push('(' + label + ') chave do template que a instância não tem: ' + k); });
  if (entityTemplates) {
    if (Array.isArray(item.socios) && entityTemplates.socio) {
      item.socios.forEach(function (s, i) {
        var sub = _formaDaEntidade(s, entityTemplates.socio, entityTemplates, label + '.socios[' + i + ']');
        r.errors = r.errors.concat(sub.errors); r.avisos = r.avisos.concat(sub.avisos);
      });
    }
    if (Array.isArray(item.cnaes) && entityTemplates.cnae) {
      item.cnaes.forEach(function (c, i) {
        var sub = _formaDaEntidade(c, entityTemplates.cnae, entityTemplates, label + '.cnaes[' + i + ']');
        r.errors = r.errors.concat(sub.errors); r.avisos = r.avisos.concat(sub.avisos);
      });
    }
  }
  return r;
}

/**
 * Valida a estrutura de um manifesto que JÁ EXISTE.
 *
 * Por que isto não é uma igualdade de chaves com o template:
 *
 * O contrato (CLIENT_MANIFEST_CONTRACT.json) exige 10 chaves de topo, mas o
 * manifesto real dos clientes em operação é um SUPERCONJUNTO disso — o 001
 * traz 19 chaves (evidencias, contratos, processos, blocos_cbmsc,
 * _entity_shapes, _governance…) e entidades com campos próprios
 * (empresa_key, inscricao_municipal_cmc, rip_spu). Não falta nada: sobra.
 *
 * O próprio contrato diz o que fazer nesse caso, em existing_manifest_rule:
 * "o proprio objeto existente e o contrato estrutural: atualizar apenas chaves
 * ja existentes". Ou seja, preservar e preencher — não rejeitar. Quando a
 * validação tratava chave a mais como erro, ela contrariava o contrato que
 * diz defender, e travava a aprovação de todo cliente que já tinha manifesto.
 *
 * Então, aqui:
 *   ERRO  (bloqueia o commit) — não é objeto; falta chave EXIGIDA pelo
 *         contrato; tipo estrutural trocado (array virou objeto etc.).
 *   AVISO (não bloqueia, fica no log) — chave a mais, forma de entidade
 *         diferente do template. É a instância sendo o próprio contrato.
 *
 * O que impede estrago não é esta função e sim setValue(), que recusa criar
 * chave, renomear e mudar tipo — e o pipeline só escreve em
 * applied_package_fingerprints, que existe nos dois formatos.
 *
 * Para item NOVO em array canônico a regra continua estrita: veja
 * validateEntityShape(), usada por addEmpresa/addImovel/addSocio/addCnae.
 *
 * @return {{ok:boolean, errors:string[], avisos:string[]}}
 */
function validateManifestStructure(manifest, contract, manifestTemplate, entityTemplates) {
  var errors = [], avisos = [];
  if (!_isPlainObject(manifest)) return { ok: false, errors: ['manifesto não é objeto'], avisos: [] };

  var expected = (contract && contract.top_level_keys) ? contract.top_level_keys.slice().sort() : _keys(manifestTemplate);
  var got = _keys(manifest);
  expected.forEach(function (k) { if (got.indexOf(k) === -1) errors.push('chave de topo EXIGIDA ausente: ' + k); });
  got.forEach(function (k) { if (expected.indexOf(k) === -1) avisos.push('chave de topo própria da instância: ' + k); });

  // tipos das chaves de topo conforme template — isto continua bloqueando:
  // se 'empresas' deixou de ser array, o sistema quebra ao gravar.
  _keys(manifestTemplate).forEach(function (k) {
    if (manifest[k] === undefined) return;
    var tv = manifestTemplate[k], mv = manifest[k];
    if (Array.isArray(tv) && !Array.isArray(mv)) errors.push('tipo inválido em ' + k + ' (esperado array)');
    else if (_isPlainObject(tv) && !_isPlainObject(mv)) errors.push('tipo inválido em ' + k + ' (esperado objeto)');
  });

  // bloco cliente: diferença de chaves é da instância, não é defeito
  if (_isPlainObject(manifest.cliente) && _isPlainObject(manifestTemplate.cliente) && !_sameKeySet(manifest.cliente, manifestTemplate.cliente)) {
    var kc = _keys(manifest.cliente), kt = _keys(manifestTemplate.cliente);
    kc.forEach(function (k) { if (kt.indexOf(k) === -1) avisos.push('(cliente) chave própria da instância: ' + k); });
    kt.forEach(function (k) { if (kc.indexOf(k) === -1) avisos.push('(cliente) chave do template que a instância não tem: ' + k); });
  }

  // empresas / imoveis: forma comparada com o template, divergência vira aviso
  if (Array.isArray(manifest.empresas) && entityTemplates && entityTemplates.empresa) {
    manifest.empresas.forEach(function (e, i) {
      var r = _formaDaEntidade(e, entityTemplates.empresa, entityTemplates, 'empresas[' + i + ']');
      errors = errors.concat(r.errors); avisos = avisos.concat(r.avisos);
    });
  }
  if (Array.isArray(manifest.imoveis) && entityTemplates && entityTemplates.imovel) {
    manifest.imoveis.forEach(function (m, i) {
      var r = _formaDaEntidade(m, entityTemplates.imovel, entityTemplates, 'imoveis[' + i + ']');
      errors = errors.concat(r.errors); avisos = avisos.concat(r.avisos);
    });
  }
  return { ok: !errors.length, errors: errors, avisos: avisos };
}

/** Cria um manifesto novo a partir do template (instância limpa). */
function createManifest(manifestTemplate, clientNNN, nowIso) {
  var m = _clone(manifestTemplate);
  m.client_id = clientNNN || null;
  if (_isPlainObject(m.cliente)) m.cliente.id_do_cliente = clientNNN || null;
  m.status = m.status || 'EM_PREPARACAO';
  m.created_at = nowIso || null;
  m.updated_at = nowIso || null;
  return m;
}

/**
 * Define valor em chave EXISTENTE (fill/update). Proíbe criar chave e mudar tipo estrutural.
 * @param {string[]} pathArray ex.: ['cliente','nome_completo'] ou ['empresas',0,'cnpj'].
 * @return {{ok:boolean, manifest?:Object, errors?:string[]}}
 */
function setValue(manifest, pathArray, value, nowIso) {
  var m = _clone(manifest);
  var cur = m;
  for (var i = 0; i < pathArray.length - 1; i++) {
    var seg = pathArray[i];
    if (cur == null || cur[seg] === undefined) return _fail(['caminho inexistente: ' + pathArray.slice(0, i + 1).join('.') + ' (CRIAR_CHAVE_PROIBIDO)']);
    cur = cur[seg];
  }
  var leaf = pathArray[pathArray.length - 1];
  if (cur === null || typeof cur !== 'object' || !(leaf in cur)) {
    return _fail(['chave inexistente: ' + pathArray.join('.') + ' (CRIAR_CHAVE_PROIBIDO)']);
  }
  var old = cur[leaf];
  if (Array.isArray(old) || _isPlainObject(old)) {
    if (typeof old !== typeof value || Array.isArray(old) !== Array.isArray(value)) {
      return _fail(['mudança de tipo estrutural proibida em ' + pathArray.join('.') + ' (MUDAR_TIPO_PROIBIDO)']);
    }
  }
  cur[leaf] = value;
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, manifest: m };
}

function _addToArray(manifest, arrayName, item, template, entityTemplates, nowIso) {
  if (!Array.isArray(manifest[arrayName])) return _fail(['campo ' + arrayName + ' não é array canônico']);
  var errors = validateEntityShape(item, template, entityTemplates, arrayName + '[novo]');
  if (errors.length) return _fail(errors);
  var m = _clone(manifest);
  m[arrayName].push(_clone(item));
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, manifest: m };
}

function addEmpresa(manifest, empresaItem, entityTemplates, nowIso) {
  return _addToArray(manifest, 'empresas', empresaItem, entityTemplates.empresa, entityTemplates, nowIso);
}
function addImovel(manifest, imovelItem, entityTemplates, nowIso) {
  return _addToArray(manifest, 'imoveis', imovelItem, entityTemplates.imovel, entityTemplates, nowIso);
}
function addSocioToEmpresa(manifest, empresaIndex, socioItem, entityTemplates, nowIso) {
  if (!Array.isArray(manifest.empresas) || !manifest.empresas[empresaIndex]) return _fail(['empresa[' + empresaIndex + '] inexistente']);
  var errors = validateEntityShape(socioItem, entityTemplates.socio, entityTemplates, 'socio[novo]');
  if (errors.length) return _fail(errors);
  var m = _clone(manifest);
  m.empresas[empresaIndex].socios.push(_clone(socioItem));
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, manifest: m };
}
function addCnaeToEmpresa(manifest, empresaIndex, cnaeItem, entityTemplates, nowIso) {
  if (!Array.isArray(manifest.empresas) || !manifest.empresas[empresaIndex]) return _fail(['empresa[' + empresaIndex + '] inexistente']);
  var errors = validateEntityShape(cnaeItem, entityTemplates.cnae, entityTemplates, 'cnae[novo]');
  if (errors.length) return _fail(errors);
  var m = _clone(manifest);
  m.empresas[empresaIndex].cnaes.push(_clone(cnaeItem));
  m.updated_at = nowIso || m.updated_at;
  return { ok: true, manifest: m };
}

/** Cria uma instância vazia de entidade a partir do template (para preencher). */
function newEntity(entityTemplates, kind) { return _clone(entityTemplates[kind]); }

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    validateEntityShape: validateEntityShape,
    _formaDaEntidade: _formaDaEntidade,
    validateManifestStructure: validateManifestStructure,
    createManifest: createManifest,
    setValue: setValue,
    addEmpresa: addEmpresa,
    addImovel: addImovel,
    addSocioToEmpresa: addSocioToEmpresa,
    addCnaeToEmpresa: addCnaeToEmpresa,
    newEntity: newEntity
  };
}
