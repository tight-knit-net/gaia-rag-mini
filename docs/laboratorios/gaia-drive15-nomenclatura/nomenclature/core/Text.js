/**
 * Text — normalização de texto e utilitários puros (sem Drive).
 *
 *  - normKey: chave de comparação (sem acento, MAIÚSCULA, só letras/dígitos separados por 1 espaço).
 *  - normText: texto sem acento e em MAIÚSCULA, mas preservando pontuação (para extrair valores).
 *  - txHas: contém a frase como PALAVRAS inteiras (evita "RG" casar dentro de "CARGO").
 *  - CPF/CNPJ/datas, candidatos a âncora e helpers de nome de arquivo.
 */

/** Remove acentos preservando o tamanho da string (1 char → 1 char). */
function txStrip(s) {
  return String(s === null || s === undefined ? '' : s)
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[ºª°]/g, function (c) { return c === 'ª' ? 'a' : 'o'; });
}

function normKey(s) {
  return txStrip(s).toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();
}

function normText(s) {
  return txStrip(s).toUpperCase().replace(/[ \t ]+/g, ' ').replace(/ *\r?\n */g, '\n').trim();
}

/** hayKey deve estar em normKey. */
function txHas(hayKey, phrase) {
  var p = normKey(phrase);
  if (!p) return false;
  return (' ' + hayKey + ' ').indexOf(' ' + p + ' ') !== -1;
}

function txDigits(s) { return String(s === null || s === undefined ? '' : s).replace(/\D/g, ''); }

function txPad(n, len) { var s = String(n); while (s.length < len) s = '0' + s; return s; }

function txEscapeRe(s) { return String(s).replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&'); }

/* ---------------- CPF / CNPJ ---------------- */

function txIsCpf(d) {
  d = txDigits(d);
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  for (var t = 9; t < 11; t++) {
    var s = 0;
    for (var i = 0; i < t; i++) s += Number(d[i]) * (t + 1 - i);
    var r = ((s * 10) % 11) % 10;
    if (r !== Number(d[t])) return false;
  }
  return true;
}

function txIsCnpj(d) {
  d = txDigits(d);
  if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false;
  var calc = function (len) {
    var w = len === 12 ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    var s = 0;
    for (var i = 0; i < len; i++) s += Number(d[i]) * w[i];
    var r = s % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return calc(12) === Number(d[12]) && calc(13) === Number(d[13]);
}

function _txUniqueValid(text, re, validator) {
  var out = [], m;
  var s = String(text || '');
  while ((m = re.exec(s)) !== null) {
    var d = txDigits(m[1] || m[0]);
    if (validator(d) && out.indexOf(d) === -1) out.push(d);
  }
  return out;
}

/** CNPJs válidos (formatados, ou 14 dígitos logo após o rótulo CNPJ). */
function txFindCnpjs(text) {
  var a = _txUniqueValid(text, /(\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2})/g, txIsCnpj);
  var b = _txUniqueValid(txStrip(text).toUpperCase(), /CNPJ[^0-9]{0,12}(\d{14})(?!\d)/g, txIsCnpj);
  b.forEach(function (x) { if (a.indexOf(x) === -1) a.push(x); });
  return a;
}

/** CPFs válidos (formatados, ou 11 dígitos logo após o rótulo CPF). */
function txFindCpfs(text) {
  var a = _txUniqueValid(text, /(?:^|[^\d.])(\d{3}\.\d{3}\.\d{3}-\d{2})(?![\d])/g, txIsCpf);
  var b = _txUniqueValid(txStrip(text).toUpperCase(), /CPF[^0-9]{0,12}(\d{11})(?!\d)/g, txIsCpf);
  b.forEach(function (x) { if (a.indexOf(x) === -1) a.push(x); });
  return a;
}

/* ---------------- Datas ---------------- */

var TX_MESES = { JANEIRO: 1, FEVEREIRO: 2, MARCO: 3, ABRIL: 4, MAIO: 5, JUNHO: 6, JULHO: 7, AGOSTO: 8, SETEMBRO: 9, OUTUBRO: 10, NOVEMBRO: 11, DEZEMBRO: 12 };

/** Forma de data aceita nos regex (numérica ou por extenso), sem grupos de captura. */
var TX_DATE_SHAPE = '(?:\\d{1,2}\\s?[\\/.\\-]\\s?\\d{1,2}\\s?[\\/.\\-]\\s?\\d{4}|\\d{1,2}\\s+DE\\s+[A-Z]{4,9}\\s+DE\\s+\\d{4})';

/** Converte uma data encontrada no texto para DD-MM-AAAA (ou null se inválida). */
function txParseDate(str) {
  var s = txStrip(str).toUpperCase().trim();
  var d, m, y, g;
  if ((g = s.match(/^(\d{1,2})\s?[\/.\-]\s?(\d{1,2})\s?[\/.\-]\s?(\d{4})$/))) { d = +g[1]; m = +g[2]; y = +g[3]; }
  else if ((g = s.match(/^(\d{1,2})\s+DE\s+([A-Z]{4,9})\s+DE\s+(\d{4})$/))) { d = +g[1]; m = TX_MESES[g[2]] || 0; y = +g[3]; }
  else return null;
  if (d < 1 || d > 31 || m < 1 || m > 12 || y < 1900 || y > 2100) return null;
  return txPad(d, 2) + '-' + txPad(m, 2) + '-' + y;
}

/** Todas as datas distintas do texto, na ordem em que aparecem (DD-MM-AAAA). */
function txFindDates(text) {
  var re = new RegExp(TX_DATE_SHAPE, 'g');
  var s = normText(text), out = [], m;
  while ((m = re.exec(s)) !== null) {
    var v = txParseDate(m[0]);
    if (v && out.indexOf(v) === -1) out.push(v);
  }
  return out;
}

/* ---------------- Nome de arquivo ---------------- */

function txExt(name) { var m = String(name || '').match(/\.([A-Za-z0-9]{1,6})$/); return m ? '.' + m[1].toLowerCase() : ''; }

function txStem(name) { var e = txExt(name); var s = String(name || ''); return e ? s.slice(0, s.length - e.length) : s; }

/** Troca caracteres proibidos em nome de arquivo por "-". */
function txSafeName(v) { return String(v === null || v === undefined ? '' : v).replace(/[\\\/:*?"<>|\r\n\t]+/g, '-').replace(/\s{2,}/g, ' ').trim(); }

/** Chave de nome de pasta: MAIÚSCULA sem acento, com "_" entre as palavras. */
function txFolderKey(s, maxLen) {
  var k = normKey(s).replace(/ /g, '_');
  return maxLen ? k.slice(0, maxLen) : k;
}

/* ---------------- Âncoras ---------------- */

var TX_STOP = { DE: 1, DA: 1, DO: 1, DAS: 1, DOS: 1, E: 1, A: 1, O: 1, AS: 1, OS: 1, EM: 1, NO: 1, NA: 1, PARA: 1, COM: 1, POR: 1, UM: 1, UMA: 1 };

/**
 * Propõe frases-âncora a partir das linhas do texto OCR: linhas curtas, com
 * palavras (não números), sem dados do cliente. Mais cedo no documento = melhor.
 * @param {string} rawText
 * @param {string[]} excludePhrases nomes/endereços do cliente (qualquer formato).
 * @param {number} max
 * @return {Array<{texto:string, linha:number}>}
 */
// Linhas que trazem dado de uma pessoa/imóvel (não servem para reconhecer o TIPO de documento).
var TX_ANCHOR_SKIP = /^(E ?MAIL|EMAIL|LOGRADOURO|BAIRRO|CIDADE|MUNICIPIO|CEP|COMPLEMENTO|TELEFONE|CELULAR|NOME( COMPLETO)?|ENDERECO|RAZAO SOCIAL|NOME FANTASIA|NOME DA EDIFICACAO)( |$)| (GMAIL|HOTMAIL|OUTLOOK|YAHOO|HTTPS?|WWW)( |$)/;

function txAnchorCandidates(rawText, excludePhrases, max) {
  var excl = (excludePhrases || []).map(normKey).filter(function (x) { return x && x.length >= 4; });
  var lines = String(rawText || '').split(/\r?\n/).filter(function (l) { return normKey(l); });
  // título quebrado em linhas curtas no topo ("AUTO DE" / "FISCALIZAÇÃO") vira uma frase só
  var joined = [];
  for (var j = 0; j + 1 < Math.min(lines.length, 12); j++) {
    var a = normKey(lines[j]), b = normKey(lines[j + 1]);
    if (a.split(' ').length <= 3 && b.split(' ').length <= 3) joined.push({ raw: lines[j] + ' ' + lines[j + 1], i: j });
  }
  var items = joined.concat(lines.map(function (l, n) { return { raw: l, i: n }; }));
  var seen = {}, cands = [];
  for (var p = 0; p < items.length; p++) {
    var raw = items[p].raw, i = items[p].i;
    // sem numeração de seção na frente ("5 CRONOGRAMA", "3 1 DETALHES", "X DEIXAR")
    // ... nem número no fim ("PROCESSO ADMINISTRATIVO INFRACIONAL Nº 457716")
    var k = normKey(raw).replace(/^((\d+|[IVX]+|[A-Z]) )+/, '').replace(/( (N|NO|NR|NUM|NUMERO))?( [A-Z]*\d[A-Z0-9]*)+$/, '');
    if (!k || seen[k]) continue;
    if (TX_ANCHOR_SKIP.test(k) || /\d/.test(k)) continue; // dado pessoal, valor, número de protocolo
    var words = k.split(' ');
    var digits = k.replace(/[^0-9]/g, '').length;
    var strongWords = words.filter(function (w) { return w.length >= 3 && !TX_STOP[w] && !/\d/.test(w); }).length;
    if (words.length < 2 || words.length > 10 || k.length < 8 || k.length > 80) continue;
    if (digits / k.length > 0.15 || strongWords < 2) continue;
    var hitsClient = excl.some(function (x) { return (' ' + k + ' ').indexOf(' ' + x + ' ') !== -1 || (' ' + x + ' ').indexOf(' ' + k + ' ') !== -1; });
    if (hitsClient) continue;
    seen[k] = true;
    var letters = String(raw).replace(/[^A-Za-zÀ-ÿ]/g, '');
    var upper = letters && letters === letters.toUpperCase() ? 8 : 0;
    cands.push({ texto: k, linha: i, score: Math.max(0, 40 - i) + upper + Math.min(words.length, 6) });
  }
  cands.sort(function (a, b) { return b.score - a.score || a.linha - b.linha; });
  return cands.slice(0, max || 30).map(function (c) { return { texto: c.texto, linha: c.linha }; });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    txStrip: txStrip, normKey: normKey, normText: normText, txHas: txHas, txDigits: txDigits, txPad: txPad,
    txEscapeRe: txEscapeRe, txIsCpf: txIsCpf, txIsCnpj: txIsCnpj, txFindCnpjs: txFindCnpjs, txFindCpfs: txFindCpfs,
    TX_DATE_SHAPE: TX_DATE_SHAPE, txParseDate: txParseDate, txFindDates: txFindDates, txExt: txExt, txStem: txStem,
    txSafeName: txSafeName, txFolderKey: txFolderKey, txAnchorCandidates: txAnchorCandidates
  };
}
