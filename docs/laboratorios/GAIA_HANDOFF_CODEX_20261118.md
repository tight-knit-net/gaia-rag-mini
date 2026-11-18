# HANDOFF CODEX — GAIA Drive15 / OCR Sérgio / RAG Mini

Data da conciliação: **18/11/2026**. Estado: **snapshots isolados e auditados, sem integração automática ao runtime do RAG**.

## 1. Repositório e branches de destino

**GitHub privado:** https://github.com/tight-knit-net/gaia-rag-mini

- `feat/catalogacao-triagem-isolada` — origem `will-iaguzeski/gaia-drive15-nomenclatura-lab`, `main@70fb5ed09b7f883ded7497f1e84b8ffca1b8b1a1`. Snapshot completo em `docs/laboratorios/gaia-drive15-nomenclatura/`. **88/88 blobs equivalentes à origem** (hash Git comparado), incluindo código, históricos, ZIP 100% sintético, testes e relatórios.
- `feat/ocr-documental-isolado` — origem worktree local `feature/ocr-iloveapi@c96b4731a1af783d52b5addcc8adcdfcdfd032b3`. Código independente em `ocr-engine/` (**14/14 hashes Git correspondem à origem**), importado no commit anterior `6fa5680`; os **8 contratos de ponte** de `main@70fb5ed` estão em `docs/laboratorios/gaia-drive15-ocr-bridge/` (**8/8 blobs equivalentes à origem**).

Os **100 arquivos/objetos preexistentes da árvore base do RAG R06 foram preservados**, incluindo .dockerignore, Dockerfile, CODEOWNERS, pipelines, skill, app, src e políticas. Nenhum merge com `main` ou `feat/r06-lifecycle-skill-staging`; nenhum deployment ou publicação GHCR.

**Importante:** o `.dockerignore` do RAG já excluía `docs/`. Por isso, os snapshots adicionados sob `docs/laboratorios/` NÃO integram o Docker build da aplicação RAG.

## 2. Infraestrutura existente (não migrada)

EC2 Test Lab (via GAIA MCP SSH alias `gaia-m7i`):
- Nomenclatura/main: `/home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-nomenclatura-20261118`
- OCR worktree: `/home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-ocr-isolated`
- Sandbox privada dos lotes: `/home/ubuntu/gaia-test-lab-homologacao/pilots`
- Evidências de testes: subdiretório `artifacts/` no mesmo laboratório.
- O worktree OCR não publicou sua branch remota via SSH: erro `Permission denied (publickey)`. O código foi conferido no repositório RAG por hashes.

Linode Test Lab (GAIA MCP SSH alias `gogetterhub-testlab`):
- Pasta OCR principal: `/home/ubuntu/gaia-test-lab-homologacao/gaia-ocr-engine-lab`
- Canary Tesseract: `/home/ubuntu/gaia-test-lab-homologacao/gaia-ocr-e2e-candidate`
- REST principal: `127.0.0.1:18788/healthz` => provider `mock`
- MCP: `127.0.0.1:18789/mcp`
- PostgreSQL: `127.0.0.1:18790`
- Canary real Tesseract: `127.0.0.1:18791/healthz` => provider `tesseract`
- Containers REST, MCP, PostgreSQL e canary confirmados em execução na última consulta; esses resultados podem mudar.

Não copiar `.env`, backup SQL, dados reais de clientes, credenciais nem arquivos runtime para o GitHub.

## 3. Contrato funcional por etapa

Drive 1 (somente leitura por conector nativo, com escopo e identidade comprovados)
→ inventário e versões/fingerprints
→ cópias temporárias na EC2, conferidas por SHA-256
→ OCR real local, ou texto nativo, com proveniência por arquivo e página
→ PostgreSQL temporário com limite de retenção
→ revisão de campos documentais e vínculos, jamais só pelo nome do arquivo
→ regras NOM em modo PREVIEW
→ boletins JSON encadeados por SHA-256 e relatórios MD
→ preservação do relatório aprovado
→ descarte **separado** de `raw/` e banco SQL
→ proposta de memória GAIA RAG, revisão humana e readback.

Shared Drive 1-CLIENTES: `0ALBFaLnE8ZPHUk9PVA`.
Triagem: `1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-`.
Não alterar Google Drive com MOVE/RENAME/DELETE ou renomeações.

## 4. Evidências confirmadas e limites

- NOM/piloto: 17 documentos sintéticos (15 PDF, 2 DOCX); 7 nomes em prévia/cópias renomeadas localmente, 10 bloqueios esperados; **86/86 testes**.
- OCR: arquivo totalmente fictício com **zero texto nativo** processado no Tesseract; evidência de **6/6 campos, 8/8 checagens REST/SQL e 5/5 MCP**. O teste iLoveAPI foi simulado, sem autenticação real.
- PostgreSQL 16 tmpfs no EC2: iniciou, permitiu consulta e foi removido após ensaio sintético. O PostgreSQL do OCR na Linode usa `pgdata` persistente e não é o mesmo banco de teste.
- Não foi executado piloto real de cliente nesta integração, nem há comprovação de E2E OCR→NOM real. A atividade prévia de triagem da cliente 009 é um processo paralelo e não deve ser misturada com estes resultados.

## 5. Bugs/contratos a revisar primeiro

1. `pilot/ocr_bridge.js` só reconhece `mock` e `iloveapi`; homologar `tesseract` e divergência de endpoint 18788/18791.
2. Revisar o retorno OCR para entregar texto/páginas com hashes e evidências sem promover automaticamente NOM, vínculo ou identidade.
3. Resolver acesso entre EC2 e Linode com autenticação mútua, menor privilégio e sem publicar MCP/SQL na Internet.
4. Confirmar isolamento real por cliente no OCR; `tenant` em query/body sem autorização de identidade suficiente não prova ACL.
5. Compor corretamente os serviços: banco de teste tmpfs vs Compose OCR `network_mode: host` + `pgdata`; versionar solução sem reusar DB de produção.
6. Testar DOCX por extrator nativo e PDFs por OCR/página; evitar OCR de tudo.
7. Versão observada do Drive pelo conector é fingerprint `OBS_`, **não** revision/ETag real. Confirmar re-read antes de ação.
8. Regras NOM originais são 56; o índice federado de 60 não é release operacional. Rever NOM-012, NOM-033 e NOM-057..060 antes de ativar.
9. `pilot/ocr_batch.js` CLI bloqueia documentos reais sem orquestrador específico de aprovação e IDs.
10. Garantir que nenhum documento/trecho OCR bruto seja persistido em Qdrant automaticamente. SQL full-text do OCR **não é** memória vetorial RAG.

## 6. Gates de revisão

- G00: baselines, commits, hashes e compatibilidade.
- G01: cliente, escopo, manifesto e autorização.
- G02: inventário, hash e cópias controladas.
- G03: OCR real local, política de provedor externo e isolamento.
- G04: PostgreSQL temporário, segredos, backup e descarte.
- G05: ensaio sintético escaneado OCR→NOM ponta a ponta.
- G06: NOM 56/60, evidências por campo e revisão.
- G07: topologia e boletins encadeados.
- G08: piloto de cliente somente quando autorizado e homologado.
- G09: relatório MD/JSON e readback.
- G10: descarte do staging e PostgreSQL após preservação conferida.
- G11: memória Qdrant apenas por proposta, aprovação humana e readback.

## 7. GAIA RAG: memória de estado, não documento

Processo: `GAIA-DRIVE1-OCR-NOM-PILOTO-20261118`.
Memória aprovada e recuperada: point `55c40019-814b-5cf7-97d2-f74f86cce929`.
Memória de OCR independente também aprovada: point
`4b5823e6-1bc8-52a5-aa87-afeca057e3e8`.
Essas memórias são checkpoints históricos; consultar o repositório e o estado
atual das máquinas para afirmar a versão operacional.

## 8. Ordem para Codex

1. Analisar **cada branch isoladamente**, sem merge ou deploy.
2. Comparar integridade de snapshots e contratos; não duplicar a lógica normativa RAG.
3. Gerar matriz compatibilidade OCR/NOM/DB/MCP/Qdrant.
4. Consertar defeitos em commits revisáveis, acompanhados de testes sintéticos.
5. Preparar plano de integração por PR draft, impacto, rollback e gates.
6. Nunca iniciar OCR externo com cliente real, MOVE/RENAME no Drive,
   persistência no Qdrant ou deploy sem autorização separada.

**Decisão de arquitetura:** GAIA RAG Mini permanece responsável pela memória
institucional aprovada; GAIA OCR, SQL e NOM são subsistemas operacionais
independentes, a integrar por contratos e gates, não por import automático
de dados pessoais.
