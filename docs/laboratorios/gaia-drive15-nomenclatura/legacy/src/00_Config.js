/**
 * 00_Config — constantes e IDs das 5 raízes no Drive COMPARTILHADO
 * "15 - Gaia Operacional e Clientes".
 *
 * ⚠️ DRIVE 15 REAL (Shared Drive): driveId = 0AGmKeZ9nIOLYUk9PVA
 *    (NÃO confundir com 0AB-8ECf4S4aYUk9PVA, que é o "Meu Drive" da conta — cópias
 *     antigas ficaram lá; os IDs abaixo são os do Drive Compartilhado de verdade.)
 * Mapeado em 2026-09-16 via Drive API (fields=driveId) — todas as pastas abaixo têm
 * driveId = 0AGmKeZ9nIOLYUk9PVA. Toda chamada usa supportsAllDrives:true (DriveService).
 */

var DRIVE15_ID = '0AGmKeZ9nIOLYUk9PVA'; // id do Drive Compartilhado 15 (para referência)

var ROOTS = {
  CLIENTES:            '1Vu-AKQjEqXxDLmbO3ZUc1hK6Hrzts8Ea', // 1-CLIENTES
  OPERACAO:            '16UADkvaS47OtDNzhMtDdsbkjSZopJuvt', // 2-OPERAÇÃO GAIA OFFICE
  TRANSICAO:           '1PH4yIDIKtGnUiRerA_tcuF1f2Lq39F81', // 3-TRANSIÇÃO DE ARQUIVOS
  BANCO_DE_DADOS:      '1cOPjpPoMyewtVldXPgJ54RQB104dI4Jo', // 4– BANCO DE DADOS
  OFFICE_KNOWLEDGE:    '1ZzVDAFqLmAjS7ygCjB7UtNtPN-mZjQr9'  // 5-OFFICE KNOWLEDGE
};

var NOMENCLATURA = {
  FOLDER:              '1fWvi-SJ4kNKL9YJ926jgkW1KL1D_6nDc', // 02_NOMENCLATURA
  NOVAS_REGRAS_FOLDER: '14ZiB6-ZE9lREkVBwW6BESJQwHTpINi1t', // 01_NOVAS_REGRAS
  BASE_JSON_FILE:      '1ifPB38LWWLlUeYXAvg6Kg7-PvrSKNx7j', // BASE_NOMENCLATURA_DOCUMENTAL.json
  TEMPLATE_RULE_FILE:  '1nksIY_dQDBkEeBciTRdR0O-7T0ocuB2n'  // TEMPLATE_NOMENCLATURA_RULE.json
};

var BANCO = {
  ROOT_FOLDER:  '1cOPjpPoMyewtVldXPgJ54RQB104dI4Jo', // 4– BANCO DE DADOS
  MAPA_FILE:    null // MAPA_BANCO_DE_DADOS.json — NAO_IMPLANTADO (criado sob demanda pelo fluxo)
};

var MANIFESTO = {
  FOLDER:              '1Hvfwg-qZ156u-AqqdBo0OHePokTV3v6D', // 01_MANIFESTO_CLIENTE
  CONTRACT_FILE:       '1U5rsM8VBH25p9yTdNIJYtQE9tjDgHGF4', // CLIENT_MANIFEST_CONTRACT.json (contract_version 1.1.0)
  // Templates do contrato. SCHEMA IMUTÁVEL; INSTÂNCIA MUTÁVEL (ver ManifestEngine.js).
  TEMPLATE_DRAFT_FILE: '1ecRd3sEBBkzpJU0zyYQYr7R-44_R6lvB', // TEMPLATE_CLIENT_MANIFEST_DRAFT.json
  TEMPLATE_EMPRESA:    '1872Qinj0IN3KAiUKSCrfNGK4XxFlObid', // TEMPLATE_EMPRESA_ITEM.json
  TEMPLATE_SOCIO:      '1V-cqciPhvORxAr6227aCysaj2I8xierF', // TEMPLATE_SOCIO_ITEM.json
  TEMPLATE_CNAE:       '1GT2RDXgADKnzrZB72GuY71TVdE7oNAY4', // TEMPLATE_CNAE_ITEM.json
  TEMPLATE_IMOVEL:     '1zNGmQojbzXBaG6raEglMwh6Y87W0KoLs'  // TEMPLATE_IMOVEL_ITEM.json
};

// Importação assistida a partir do Drive 11 (acervo legado). Só LEITURA + 1 MOVE por clique.
// Destino da importação = 4– BANCO DE DADOS do Drive 15 REAL (onde o processarPastas varre).
var STAGING = {
  DRIVE11_CLIENT_STAGING: '1Wmgzp6CTKbZoKVwTMXI1zUbaE0cRQxgw', // 001_CLIENT_STAGING (Drive 11, driveId 0AEBDECWAwhg0Uk9PVA)
  DESTINO_IMPORT:         '1cOPjpPoMyewtVldXPgJ54RQB104dI4Jo'  // = ROOTS.BANCO_DE_DADOS (Drive 15 REAL)
};

// Estrutura de cliente em 1-CLIENTES:  NNN_<NOME>/ { NNN_DOCUMENTOS, NNN_SOCIETARIO, NNN_IMOVEIS }
// O manifesto do cliente vai para NNN_DOCUMENTOS como NNN_Manifesto_cliente.json.
var CLIENTES_CFG = {
  ROOT: '1Vu-AKQjEqXxDLmbO3ZUc1hK6Hrzts8Ea',  // = ROOTS.CLIENTES
  BUCKETS: ['DOCUMENTOS', 'SOCIETARIO', 'IMOVEIS'],
  ID_INICIAL: 1,                              // primeiro NNN quando 1-CLIENTES está vazia
  MANIFESTO_BUCKET: 'DOCUMENTOS',
  MANIFESTO_SUFIXO: '_Manifesto_cliente.json'
};

// Pastas técnicas do sistema dentro de 4– BANCO DE DADOS (ignoradas na varredura de clientes).
var SISTEMA_CFG = {
  FOLDER: '_SISTEMA',
  OCR: 'OCR',             // cache de texto por arquivo (<file_id>.json)
  TMP_OCR: 'TMP_OCR',     // Google Docs temporários da conversão (vão para a lixeira na hora)
  LOGS: 'LOGS',           // log de cada execução
  REVISAO_CHATGPT: 'REVISAO_CHATGPT', // modelo + resultados gravados pelo ChatGPT (revisão externa)
  CLIENTES_INDEX: 'CLIENTES_INDEX.json'
};

// Revisão com ajuda do ChatGPT (fora do sistema, conduzida pelo operador).
// O sistema só monta o prompt, espera o arquivo e preenche o cartão; o OK final é sempre no painel.
var REVISAO_EXTERNA_CFG = {
  MODELO: 'MODELO_REVISAO_CHATGPT.json',   // em _SISTEMA/REVISAO_CHATGPT (o sistema restaura se alguém alterar)
  PREFIXO: 'REVISAO_CHATGPT__',            // resultado: REVISAO_CHATGPT__<id da revisão>.json
  MAX_TEXTO: 12000,                        // quanto do texto lido vai no prompt
  MAX_BYTES: 1024 * 1024,
  // Conhecimento operacional da Gaia que acompanha todo prompt.
  CONHECIMENTO: [
    'Atestado de Funcionamento (Corpo de Bombeiros/CBMSC): na regra da Gaia, indica que o imóvel já tem o ATESTADO DE HABITE-SE aprovado e que a situação está regular perante o Corpo de Bombeiros. Isso influencia a classificação e a nomenclatura.',
    'Atestado de Edificação em Regularização (Corpo de Bombeiros/CBMSC): é outra situação. O imóvel pode ter ou não aprovação anterior, mas existe alguma necessidade de regularização — por exemplo substituição ou atualização de projeto, atualização ligada ao habite-se, ausência de projeto preventivo ou outra exigência do Corpo de Bombeiros. Exige atenção: se não for tratada, pode gerar autuação ou multa. Não confundir com Atestado de Funcionamento nem com Atestado de Habite-se.'
  ]
};

// Revisão em LOTE: um .md com o cabeçalho fixo uma vez só e N documentos depois,
// para o operador colar de uma vez no ChatGPT. O cabeçalho fixo (instruções +
// tabela das 56 regras + modelo) tem ~11,7 KB e hoje é repetido em cada prompt.
var REVISAO_LOTE_CFG = {
  MAX_TEXTO: 2500,          // por documento no lote (o prompt individual usa 12.000)
  MAX_ITENS_ARQUIVO: 25,    // acurácia é estável até lotes bem maiores, mas 25 mantém o paste utilizável
  MAX_CHARS_ARQUIVO: 150000,// ~38k tokens: corta em LOTE_02, LOTE_03... se passar
  PREFIXO_PROMPT: 'LOTE_',
  PREFIXO_RESULTADO: 'RESULTADO_LOTE_'
};

// Onde o aprendizado fica registrado (append-only) dentro de 5-OFFICE KNOWLEDGE.
var KNOWLEDGE_DELTA_PATH = ['00_ATUALIZACOES_E_DELTAS_APPEND_ONLY', '01_NOMENCLATURA_NOVAS_REGRAS'];

// Execução em etapas curtas (cada clique do painel roda ~1 min e devolve o log).
var PIPELINE_CFG = {
  TICK_BUDGET_MS: 50000,
  MAX_DEPTH: 8,
  MAX_OCR_CHARS: 100000,
  MAX_TENTATIVAS_ERRO: 3,
  CHECAR_PERTENCIMENTO: true,
  // Portão S6 do README: o move final para 1-CLIENTES exige autorização humana
  // explícita e específica do pacote apresentado. Com true, o pipeline PREPARA o
  // pacote (nome final + destino) e para em AGUARDANDO_APROVACAO; quem manda mover
  // é o operador, pela aba Aprovação do painel. Com false volta o move automático
  // antigo — que está fora do contrato escrito; só mude junto com o README.
  EXIGIR_APROVACAO_HUMANA: true
};

// Leitura de PDF/imagem: até 2 MB vai pelo OCR do Google Drive (grátis; lê só as 10 primeiras páginas).
// Acima disso — ou se o Drive falhar/ler quase nada — vai pelo Google Document AI (processador "gaia-ocr-processor").
var OCR_CFG = {
  DRIVE_MAX_BYTES: 2 * 1024 * 1024,
  MIN_CHARS: 20,                       // menos que isso = o Drive "não leu"
  DOCAI_PROJECT: 'go-getter-hub',
  DOCAI_LOCATION: 'us',
  DOCAI_PROCESSOR: '43e1aca513d213e2',
  DOCAI_MAX_BYTES: 35 * 1024 * 1024,   // limite do Document AI é 40 MB; o envio (base64) precisa caber em 50 MB
  DOCAI_MAX_PAGES: 15                  // leitura online: primeiras 15 páginas
};

// Destino por regra (portado do projeto legado 123 e completado para NOM-033..056).
// CONTEXTUAL = decide por palavras de empresa x imóvel no texto; empate vai para Revisão.
var ROTAS_CFG = {
  TABELA: {
    'NOM-002': 'SOCIETARIO', 'NOM-009': 'SOCIETARIO', 'NOM-010': 'SOCIETARIO', 'NOM-016': 'SOCIETARIO',
    'NOM-019': 'SOCIETARIO', 'NOM-020': 'SOCIETARIO', 'NOM-021': 'SOCIETARIO', 'NOM-026': 'SOCIETARIO',
    'NOM-027': 'SOCIETARIO', 'NOM-031': 'SOCIETARIO', 'NOM-032': 'SOCIETARIO', 'NOM-036': 'SOCIETARIO',
    'NOM-038': 'SOCIETARIO', 'NOM-039': 'SOCIETARIO', 'NOM-040': 'SOCIETARIO', 'NOM-041': 'SOCIETARIO',
    'NOM-042': 'SOCIETARIO', 'NOM-043': 'SOCIETARIO', 'NOM-045': 'SOCIETARIO', 'NOM-046': 'SOCIETARIO',
    'NOM-047': 'SOCIETARIO', 'NOM-048': 'SOCIETARIO', 'NOM-050': 'SOCIETARIO', 'NOM-051': 'SOCIETARIO',
    'NOM-052': 'SOCIETARIO', 'NOM-053': 'SOCIETARIO', 'NOM-054': 'SOCIETARIO', 'NOM-055': 'SOCIETARIO',
    'NOM-056': 'SOCIETARIO',
    'NOM-003': 'IMOVEIS', 'NOM-004': 'IMOVEIS', 'NOM-005': 'IMOVEIS', 'NOM-006': 'IMOVEIS', 'NOM-007': 'IMOVEIS',
    'NOM-012': 'IMOVEIS', 'NOM-014': 'IMOVEIS', 'NOM-015': 'IMOVEIS', 'NOM-017': 'IMOVEIS', 'NOM-018': 'IMOVEIS',
    'NOM-022': 'IMOVEIS', 'NOM-023': 'IMOVEIS', 'NOM-024': 'IMOVEIS', 'NOM-025': 'IMOVEIS', 'NOM-028': 'IMOVEIS',
    'NOM-029': 'IMOVEIS', 'NOM-030': 'IMOVEIS', 'NOM-035': 'IMOVEIS', 'NOM-044': 'IMOVEIS',
    'NOM-033': 'DOCUMENTOS', 'NOM-034': 'DOCUMENTOS', 'NOM-037': 'DOCUMENTOS', 'NOM-049': 'DOCUMENTOS',
    'NOM-001': 'CONTEXTUAL', 'NOM-008': 'CONTEXTUAL', 'NOM-011': 'CONTEXTUAL', 'NOM-013': 'CONTEXTUAL'
  },
  TIPOS_PESSOAIS: ['CNH', 'RG', 'CARTEIRA DE IDENTIDADE', 'CARTEIRA NACIONAL DE HABILITACAO', 'CERTIDAO DE NASCIMENTO',
    'CERTIDAO DE CASAMENTO', 'PROCURACAO', 'COMPROVANTE DE RESIDENCIA', 'CONTRATO DE PRESTACAO DE SERVICO'],
  ANCORAS_EMPRESA: ['FUNCIONAMENTO', 'EMPRESA', 'ATIVIDADE ECONOMICA', 'CONTRATO SOCIAL', 'ALVARA SANITARIO', 'RAZAO SOCIAL'],
  ANCORAS_IMOVEL: ['HABITE SE', 'PROJETO', 'EDIFICACAO', 'IMOVEL', 'PPCI', 'CONSTRUCAO', 'REFORMA', 'INSCRICAO IMOBILIARIA', 'MATRICULA']
};

// Estados canônicos do workflow (S0→S10).
var WORKFLOW_STATES = [
  'S0_BOOTSTRAP_MEMORY', 'S1_CLIENT_RESOLUTION', 'S2_DISCOVERY', 'S3_STAGING_ACTIVE',
  'S4_READY_FOR_COMMIT', 'S5_AWAITING_HUMAN_APPROVAL', 'S6_COMMIT_CLIENTES',
  'S7_MANIFEST_SYNC', 'S8_RECONCILE_AND_CLEAN', 'S9_MEMORY_LEARNING', 'S10_CLOSED'
];

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DRIVE15_ID: DRIVE15_ID, ROOTS: ROOTS, NOMENCLATURA: NOMENCLATURA, BANCO: BANCO, MANIFESTO: MANIFESTO, STAGING: STAGING, WORKFLOW_STATES: WORKFLOW_STATES,
    CLIENTES_CFG: CLIENTES_CFG, SISTEMA_CFG: SISTEMA_CFG, KNOWLEDGE_DELTA_PATH: KNOWLEDGE_DELTA_PATH, PIPELINE_CFG: PIPELINE_CFG, ROTAS_CFG: ROTAS_CFG, OCR_CFG: OCR_CFG, REVISAO_EXTERNA_CFG: REVISAO_EXTERNA_CFG };
}
