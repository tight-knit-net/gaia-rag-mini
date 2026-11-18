/**
 * OcrService — lê o texto de um arquivo UMA vez (depois fica em cache).
 *
 *  - Google Docs: leitura nativa.
 *  - PDF / imagem até 2 MB: OCR do Google Drive (conversão temporária para Google Docs em português;
 *    o temporário vai para a lixeira). Se o Drive falhar ou ler quase nada → Document AI.
 *  - PDF / imagem acima de 2 MB: Google Document AI (processador "gaia-ocr-processor", primeiras 15 páginas).
 *  - Word/ODT/RTF/HTML: conversão temporária sem OCR.
 *  - Texto puro: lido direto.
 */

var OCR_IMAGE_MIMES = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/tiff'];
var OCR_MULTIPAGE_MIMES = ['application/pdf', 'image/tiff'];
var OCR_CONVERT_MIMES = [
  'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.oasis.opendocument.text', 'application/rtf', 'text/rtf', 'text/html'
];
var OCR_GDOC = 'application/vnd.google-apps.document';

function ocrMethodFor(mime) {
  if (mime === OCR_GDOC) return 'NATIVO_GDOC';
  if (OCR_IMAGE_MIMES.indexOf(mime) !== -1) return 'OCR_DRIVE';
  if (OCR_CONVERT_MIMES.indexOf(mime) !== -1) return 'CONVERSAO_DRIVE';
  if (/^text\//.test(mime || '')) return 'TEXTO';
  return 'NAO_SUPORTADO';
}

function _ocrMb(bytes) { return (bytes / 1048576).toFixed(1); }

/** @return {{ok:boolean, text:string, method:string, erro?:string, motivo?:string, paginas?:number}} */
function ocrReadText(fileId, mime) {
  var method = ocrMethodFor(mime);
  try {
    if (method === 'NATIVO_GDOC') return { ok: true, method: method, text: _ocrDocText(DocumentApp.openById(fileId)) };
    if (method === 'TEXTO') return { ok: true, method: method, text: DriveApp.getFileById(fileId).getBlob().getDataAsString('UTF-8') };
    if (method === 'NAO_SUPORTADO') return { ok: false, method: method, text: '', erro: 'Formato não suportado para leitura: ' + mime };
    if (method === 'CONVERSAO_DRIVE') return { ok: true, method: method, text: _ocrViaTempDoc(fileId, false) };

    // PDF / imagem
    var file = DriveApp.getFileById(fileId);
    var size = Number(file.getSize()) || 0;
    if (size > OCR_CFG.DRIVE_MAX_BYTES) {
      return _ocrDocAi(file, mime, 'arquivo com ' + _ocrMb(size) + ' MB (o OCR do Drive só lê até 2 MB)');
    }
    var drive = null, erroDrive = null;
    try { drive = _ocrViaTempDoc(fileId, true); }
    catch (e) {
      erroDrive = String(e && e.message || e);
      if (plIsAuthError(erroDrive)) throw e; // permissão do Google: não adianta tentar outro leitor
    }
    if (drive !== null && drive.replace(/\s+/g, '').length >= OCR_CFG.MIN_CHARS) return { ok: true, method: 'OCR_DRIVE', text: drive };

    var ai = _ocrDocAi(file, mime, erroDrive ? 'o OCR do Drive falhou: ' + erroDrive : 'o OCR do Drive quase não leu texto');
    if (ai.ok || plIsAuthError(ai.erro) || drive === null) {
      if (!ai.ok && erroDrive) ai.erro = 'Drive: ' + erroDrive + ' | ' + ai.erro;
      return ai;
    }
    return { ok: true, method: 'OCR_DRIVE', text: drive, motivo: 'Document AI indisponível: ' + ai.erro }; // fica com o pouco que o Drive leu
  } catch (e) {
    return { ok: false, method: method, text: '', erro: String(e && e.message || e) };
  }
}

/** Texto do documento: cabeçalho (onde às vezes fica o título) + corpo + rodapé. */
function _ocrDocText(doc) {
  var parts = [];
  try { var h = doc.getHeader(); if (h) parts.push(h.getText()); } catch (e) { /* sem cabeçalho */ }
  parts.push(doc.getBody().getText());
  try { var f = doc.getFooter(); if (f) parts.push(f.getText()); } catch (e) { /* sem rodapé */ }
  return parts.filter(function (t) { return t && t.trim(); }).join('\n');
}

function _ocrViaTempDoc(fileId, useOcr) {
  var blob = DriveApp.getFileById(fileId).getBlob();
  var meta = { name: '__TMP_OCR__' + fileId, mimeType: OCR_GDOC, parents: [sysFolders().tmp] };
  var opts = { supportsAllDrives: true, fields: 'id' };
  if (useOcr) opts.ocrLanguage = 'pt';
  var temp = null;
  try {
    temp = Drive.Files.create(meta, blob, opts);
    return _ocrDocText(DocumentApp.openById(temp.id));
  } finally {
    if (temp && temp.id) {
      try { Drive.Files.update({ trashed: true }, temp.id, null, { supportsAllDrives: true, fields: 'id' }); }
      catch (e) { try { DriveApp.getFileById(temp.id).setTrashed(true); } catch (e2) { /* fica em TMP_OCR (pasta ignorada) */ } }
    }
  }
}

function _ocrDocAiUrl(suffix) {
  return 'https://' + OCR_CFG.DOCAI_LOCATION + '-documentai.googleapis.com/v1/projects/' + OCR_CFG.DOCAI_PROJECT +
    '/locations/' + OCR_CFG.DOCAI_LOCATION + '/processors/' + OCR_CFG.DOCAI_PROCESSOR + (suffix || '');
}

function _ocrDocAiCall(url, method, body) {
  var params = {
    method: method, muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': OCR_CFG.DOCAI_PROJECT }
  };
  if (body) { params.contentType = 'application/json'; params.payload = JSON.stringify(body); }
  var resp = UrlFetchApp.fetch(url, params);
  var code = resp.getResponseCode(), j = null;
  try { j = JSON.parse(resp.getContentText()); } catch (e) { j = null; }
  if (code === 200 && j) return { ok: true, json: j };
  var err = j && j.error ? (j.error.status || j.error.code) + ': ' + j.error.message : 'HTTP ' + code;
  return { ok: false, erro: 'Document AI ' + err };
}

/** Lê PDF/imagem pelo Google Document AI (leitura online, primeiras 15 páginas). */
function _ocrDocAi(file, mime, motivo) {
  var size = Number(file.getSize()) || 0;
  if (size > OCR_CFG.DOCAI_MAX_BYTES) {
    return { ok: false, method: 'DOCUMENT_AI', text: '', erro: 'arquivo com ' + _ocrMb(size) + ' MB: acima do limite de leitura (' + _ocrMb(OCR_CFG.DOCAI_MAX_BYTES) + ' MB)' };
  }
  var body = { rawDocument: { content: Utilities.base64Encode(file.getBlob().getBytes()), mimeType: mime } };
  if (OCR_MULTIPAGE_MIMES.indexOf(mime) !== -1) body.processOptions = { fromStart: OCR_CFG.DOCAI_MAX_PAGES };
  var r = _ocrDocAiCall(_ocrDocAiUrl(':process'), 'post', body);
  if (!r.ok || !r.json.document) return { ok: false, method: 'DOCUMENT_AI', text: '', erro: r.erro || 'Document AI sem resposta' };
  var doc = r.json.document;
  return { ok: true, method: 'DOCUMENT_AI', text: doc.text || '', paginas: (doc.pages || []).length, motivo: motivo };
}

/** Diagnóstico (usado por autorizar): o processador responde para esta conta? */
function ocrDocAiStatus() {
  var r = _ocrDocAiCall(_ocrDocAiUrl(''), 'get', null);
  if (!r.ok) return r.erro;
  return 'OK — ' + (r.json.displayName || OCR_CFG.DOCAI_PROCESSOR) + ' (' + r.json.state + ')';
}
