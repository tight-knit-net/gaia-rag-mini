# GAIA OCR Engine — laboratório isolado

Módulo experimental independente da nomenclatura. Não edita arquivos no Drive.
- Postgres guarda os PDFs originais (BYTEA), PDFs OCR, hashes, textos, metadados e status.
- Mock OCR sem cobrança para ensaios. Integração real com iLoveAPI via X-Api-Key, **desligada por padrão**.
- REST: localhost:18788 ; MCP HTTP: localhost:18789/mcp (somente loopback; NÃO conectar diretamente à Internet).
- Limite de 15 MiB por arquivo; até 10 páginas por documento na API real por padrão.
- Pesquisa: índice textual SQL (NÃO embeddings / RAG semântico).
- Backup portátil: GET /v1/export?tenant=test gera ZIP de JSON + arquivos.
- As credenciais ficam em .env ignorado pelo Git, nunca em commits.

## Endpoints
POST /v1/documents (multipart: file, tenant=test)
POST /v1/documents/{id}/ocr?tenant=test
GET /v1/documents/{id}?tenant=test
GET /v1/documents/{id}/file?tenant=test&kind=original|ocr
GET /v1/search?tenant=test&q=texto
GET /v1/export?tenant=test
GET /healthz
Todos menos healthz requerem Authorization: Bearer $GAIA_OCR_TOKEN.
MCP tools: ocr_process, ocr_document, ocr_search. Porta MCP não publicada externamente.

Para testes:
  docker compose up -d --build
  docker compose ps
  docker compose logs api mcp --tail 40
  curl -fsS http://127.0.0.1:18788/healthz

**Reais**: habilitar somente após autorização e chaves iLoveAPI configuradas:
  OCR_PROVIDER=iloveapi
  ILOVEAPI_SECRET=...
  OCR_ALLOW_REAL_DOCUMENTS=1

Não habilitar processamento real automaticamente: cada arquivo transmitido à iLoveAPI
consome créditos, e dados sensíveis saem da infraestrutura local.


## Restauracao / migracao
O ZIP exportado inclui manifest.json e arquivos por UUID. A ferramenta `restore.py`
valida SHA-256 antes de qualquer alteracao:
```bash
python restore.py gaia-ocr-test.zip           # valida apenas
python restore.py gaia-ocr-test.zip --apply   # exige DATABASE_URL da base destino
```
No Test Lab as tres portas usam **loopback do host** (18788 API, 18789 MCP,
18790 PostgreSQL) porque o roteamento WARP da VM impede o egress na bridge Docker.
Nao ha porta publicada para acesso externo nem OAuth configurado no MCP.

## OCR verdadeiro, documento sintético - 18/11/2026
A branch possui um terceiro provedor OCR_PROVIDER=tesseract destinado
à homologação local de OCR de pixels sem transmitir arquivos a terceiros.
O Dockerfile instala Tesseract (português/inglês) e Poppler. A API REST,
o PostgreSQL e as tools MCP mantêm o mesmo contrato; o modo real externo
OCR_PROVIDER=iloveapi continua disponível, mas ainda sem homologação autenticada.

No Test Lab Linode foi processado 1 PDF que continha somente imagem
(0 caracteres extraíveis antes do OCR). Resultado: 6/6 campos,
8/8 verificações de REST/PDF/PostgreSQL/isolamento/exportação, 5/5 verificações MCP,
e teste de contrato HTTP falso com start/upload/process/download. Evidências
ficam em ocr-engine/evidence/. Scripts reproduzíveis em ocr-engine/tests/.

Limite: o E2E com Tesseract comprova OCR real dentro do container;
não valida a iLoveAPI externa, chave ou cobrança. Não processar
documentos de clientes até conclusão do controle de acesso por cliente,
regras de retenção, backups criptografados, requisitos LGPD e revisão
de fornecedor externo. A porta do MCP permanece restrita ao loopback.

Em produção nunca disponibilize segredos no Git. Para usar iLoveAPI,
configurar ILOVEAPI_SECRET, OCR_PROVIDER=iloveapi e habilitar
OCR_ALLOW_REAL_DOCUMENTS=1 apenas após aprovação de dados reais.
