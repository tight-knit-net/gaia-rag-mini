/**
 * 01_Guards — verificações de sanidade que rodam ANTES de qualquer mutação.
 *
 * Motivo: existem DUAS árvores com os mesmos nomes de pasta — o Drive 15 REAL
 * (0AGmKeZ9nIOLYUk9PVA) e uma cópia legada em "SCRIPT LEGADO-16-09-2026"
 * (0AB-8ECf4S4aYUk9PVA). Os nomes são idênticos e os IDs não. Se alguém
 * reapontar o 00_Config para a cópia, o sistema passaria a mover documentos de
 * cliente dentro do lugar errado sem nenhum sintoma visível.
 *
 * Este guard resolve isso do único jeito confiável: perguntando ao Drive em qual
 * driveId cada raiz configurada realmente vive, e travando a execução se não bater.
 */

var DRIVE11_ID = '0AEBDECWAwhg0Uk9PVA'; // 11-ACERVO DE ARQUIVOS (origem da importação assistida)

var GD_CACHE = null; // resultado por execução (o guard não precisa rodar por arquivo)

/** driveId real de um item, ou null se estiver em "Meu Drive". */
function gdDriveIdOf(fileId) {
  var m = Drive.Files.get(fileId, { fields: 'id,name,driveId,trashed', supportsAllDrives: true });
  return { id: m.id, name: m.name, driveId: m.driveId || null, trashed: !!m.trashed };
}

/** Raízes que precisam estar no Drive 15 real, e a chave de config de cada uma. */
function gdAlvos() {
  return [
    { chave: 'ROOTS.CLIENTES', id: ROOTS.CLIENTES, drive: DRIVE15_ID },
    { chave: 'ROOTS.OPERACAO', id: ROOTS.OPERACAO, drive: DRIVE15_ID },
    { chave: 'ROOTS.TRANSICAO', id: ROOTS.TRANSICAO, drive: DRIVE15_ID },
    { chave: 'ROOTS.BANCO_DE_DADOS', id: ROOTS.BANCO_DE_DADOS, drive: DRIVE15_ID },
    { chave: 'ROOTS.OFFICE_KNOWLEDGE', id: ROOTS.OFFICE_KNOWLEDGE, drive: DRIVE15_ID },
    { chave: 'NOMENCLATURA.FOLDER', id: NOMENCLATURA.FOLDER, drive: DRIVE15_ID },
    { chave: 'MANIFESTO.FOLDER', id: MANIFESTO.FOLDER, drive: DRIVE15_ID },
    { chave: 'STAGING.DRIVE11_CLIENT_STAGING', id: STAGING.DRIVE11_CLIENT_STAGING, drive: DRIVE11_ID }
  ];
}

/**
 * Confere que toda raiz configurada está no Drive Compartilhado esperado.
 * Roda uma vez por execução. Lança erro (interrompe tudo) se alguma divergir.
 * @return {{ok:true, conferidas:number}}
 */
function gdAssertDrives(log) {
  if (GD_CACHE) return GD_CACHE;

  var problemas = [];
  gdAlvos().forEach(function (alvo) {
    if (!alvo.id) { problemas.push(alvo.chave + ': não configurado (vazio)'); return; }
    var m;
    try {
      m = gdDriveIdOf(alvo.id);
    } catch (e) {
      problemas.push(alvo.chave + ' (' + alvo.id + '): não consegui ler — ' + String(e && e.message || e));
      return;
    }
    if (m.trashed) { problemas.push(alvo.chave + ' ("' + m.name + '"): está na lixeira'); return; }
    if (m.driveId !== alvo.drive) {
      problemas.push(
        alvo.chave + ' ("' + m.name + '", id ' + alvo.id + ') está no drive ' +
        (m.driveId || 'MEU DRIVE (não é Drive Compartilhado)') + ', mas deveria estar em ' + alvo.drive
      );
    }
  });

  if (problemas.length) {
    throw new Error(
      'DRIVE_ERRADO: a configuração aponta para fora do Drive esperado. ' +
      'Lembre que existe uma cópia legada com os MESMOS nomes de pasta em ' +
      '"SCRIPT LEGADO-16-09-2026" (0AB-8ECf4S4aYUk9PVA) — os IDs em 00_Config.js ' +
      'devem ser os do Drive 15 real (' + DRIVE15_ID + '). Nada foi movido. Problemas: ' +
      problemas.join(' | ')
    );
  }

  GD_CACHE = { ok: true, conferidas: gdAlvos().length };
  if (log) log('info', 'Drives conferidos: ' + GD_CACHE.conferidas + ' raízes no Drive certo.');
  return GD_CACHE;
}

/** Para rodar sozinho no editor e ver o diagnóstico sem executar nada. */
function test_drivesConferem() {
  var alvos = gdAlvos().map(function (a) {
    var out = { chave: a.chave, id: a.id, esperado: a.drive };
    try {
      var m = gdDriveIdOf(a.id);
      out.nome = m.name; out.driveId_real = m.driveId; out.bate = (m.driveId === a.drive);
    } catch (e) { out.erro = String(e && e.message || e); out.bate = false; }
    return out;
  });
  Logger.log(JSON.stringify(alvos, null, 2));
  return alvos;
}
