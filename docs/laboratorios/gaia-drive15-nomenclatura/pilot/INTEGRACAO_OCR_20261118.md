# GAIA — Preparação da integração OCR + nomenclatura + PostgreSQL temporário

Data: 2026-11-18. Estado: **OCR integrado por contrato e testes mock; OCR real NÃO HOMOLOGADO**.

## Inspeção executada

- Repositório de nomenclatura: GitHub privado will-iaguzeski/gaia-drive15-nomenclatura-lab, main.
- Código OCR localizado na EC2 em /home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-ocr-isolated/ocr-engine; branch local feature/ocr-iloveapi no commit f02e99e. Não alterado por este trabalho.
- Motor OCR define REST em http://127.0.0.1:18788, MCP em http://127.0.0.1:18789/mcp (localhost), e PostgreSQL 16. Banco armazena original_bytes, normalized_pdf, ocr_pdf, ocr_text, sha256 e status.
- API REST: POST /v1/documents (multipart tenant/file), POST /v1/documents/{uuid}/ocr?tenant=..., GET /v1/documents/{uuid}, GET /healthz; a API usa Bearer configurado externamente.
- OCR_PROVIDER=mock por padrão. OCR_PROVIDER=iloveapi exige segredo e OCR_ALLOW_REAL_DOCUMENTS=1. Chamadas para API externa transmitem conteúdo sensível e podem cobrar créditos.
- No momento da inspeção, **nenhum container OCR estava ativo** na EC2; não havia o arquivo local de configuração .env. Na inspeção inicial faltava restore.py, porém **o commit OCR 1421e3e acrescentou o arquivo e sanou essa pendência específica**. Ainda faltam a configuração .env e os contêineres OCR ativos. A configuração OCR atual (network_mode: host + volume nomeado pgdata) não está ligada ao PostgreSQL temporário da ponte: alinhar DATABASE_URL, rede privada e política de retenção antes de operar com cliente. MCP ligado apenas em 127.0.0.1:18789, sem autenticação própria demonstrada: NÃO publicar externamente.

## Implementação no repositório de nomenclatura

1. pilot/ocr_bridge.js: cliente HTTP restrito ao loopback ou serviço interno de Docker; verifica SHA256 de entrada, a resposta de upload, tenant, ID do documento, provider, limite de PDF, e autorização para OCR externo. A API não dispõe de token compartilhado no GitHub. As regras detectadas em texto OCR são candidatas não homologadas.
2. pilot/ocr_batch.js: acopla o resultado da leitura ao catálogo/inventário e produz BOLETIM_OCR.md e OCR_REVISAO.json com hashes e regras candidatas, sem guardar o texto OCR integral no MD e sem aprovar automaticamente nenhuma variável. O plano original de renomeação permanece somente prévia e bloqueado.
3. pilot/ocr_postgres_tmpfs.compose.yaml: banco PostgreSQL 16 em tmpfs 512 MiB, sem porta publicada, rede interna, secrets via arquivo temporário e sem volumes persistentes; teste SQL passou.
4. pilot/scripts/temp_pg.sh: inicia banco por run_id com segredo criado sob pasta protegida, uid 70 / chmod 0600; comando stop exige --commit e relatório BOLETIM.md e destrói o container, rede e secret. Um teste completo start/query/stop foi realizado sem documentos reais.
5. pilot/purge.js: continua responsável pela pasta raw local; sua execução não remove dados ainda armazenados no banco PostgreSQL.

## Limites antes do primeiro cliente

- PDF/JPEG/PNG estão previstos no OCR engine; o pipeline de nomenclatura, neste estágio, envia somente PDF. DOCX usa a fila DOCX_NATIVE_READING_PENDING até existir extrator nativo.
- OCR mock pode extrair texto nativo de PDFs, mas **isso não é OCR de escaneamento**.
- O OCR real exige serviço efetivo respondendo ao endpoint, provedor validado, política de envio a terceiros e autorização específica do lote. Não usar chave iLoveAPI sem autorização.
- É preciso homologar a imagem e credenciais do OCR independente, ajustar rede/banco para usar o Postgres tmpfs no piloto, executar teste real de PDF escaneado e comprovar descarte de banco e cópias. Evitar volume persistente pgdata no piloto de cliente; o compose original da equipe OCR utiliza volume nomeado.
- A leitura do OCR nunca substitui confirmação do cliente 009, índice de cadastro, manifesto ativo, evidências da entidade, fonte da regra NOM e topologia do destino.
- Não afirmar que não há cópias remanescentes em cache, swap, logs, backup ou no provedor OCR externo: limpeza tmpfs/SQL é descarte lógico do ambiente de teste, não prova de apagamento físico.
- O conector Google Drive do Drive 1 permanece somente leitura. Sem MOVE, RENAME, DELETE, upload de documentos ao GitHub ou Dropbox.

## Resultados verificados

- Testes offline com servidor REST OCR falso validaram 9 cenários, inclusive falhas de SHA, permissão de cliente, consentimento externo, candidato NOM e proteção contra OCR mock.
- Pipeline OCR por lote passou em 3 cenários com PDF e DOCX sintéticos.
- Suite total regressiva: 86/86 testes na EC2, sem OCR real.
- postgres:16-alpine baixado no laboratório; banco isolado criado, query SQL e descartado.
- O **primeiro lote REAL de cliente ainda não foi processado**. O OCR externo também não foi ativado.

## Procedimento planejado (somente lote fictício ou explicitamente autorizado)

Primeiro criar o piloto com pilot/purge.js setup. Depois iniciar o banco com pilot/scripts/temp_pg.sh start RUN_ID. O OCR API deverá ser iniciado pela equipe responsável, usando DATABASE_URL apontando para o PostgreSQL temporário e credenciais via segredo, na mesma rede interna. O operador informa pasta/ID exatos; o conector nativo Google Drive baixa cópias para raw. pilot/ocr_batch.js consome esses arquivos por SHA256 e emite OCR_REVISAO.json e BOLETIM_OCR.md. A revisão humana ou de regras confirmadas preenche metadados documentais verificados. O pipeline de NOM produz prévias. Salvar o relatório autorizado antes do descarte de raw e SQL, cada um por rotina separada.

Nota: o script CLI pilot/ocr_batch.js intencionalmente aceita apenas GAIA_OCR_SYNTHETIC=1. O fluxo de cliente real exige um orquestrador que delimite explicitamente os file IDs aprovados e o consentimento para eventual OCR externo.
