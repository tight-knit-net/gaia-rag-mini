# R07 — Runbook condicionado de implantação autenticada, backup e rollback

**Versão:** 1.0.0 — MINUTA OPERACIONAL (NÃO EXECUTADA / NÃO HOMOLOGADA).
**Emissão:** 18/11/2026, 21:03:59, America/Sao_Paulo.
**Relógio:** widget de hora local do ChatGPT; retornou `2026-11-18T21:03:59-03:00`.
**Ramo exclusivo:** `tight-knit-net/gaia-rag-mini`, `feat/r07-office-knowledge-assimilation`, PR #5, base R06.
**Evidência técnica S7:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44425781548
**Escopo:** planejamento de futura ativação, prova E2E e rollback. Este documento **NÃO AUTORIZA** deploy, teste em dados reais, publicação GHCR, Cloudflare/DNS, escrita/migração de Qdrant ou desligamento legado.

## 1. Baseline disponível (somente CI)

- Imagem da candidata construída em runner GitHub Actions com base Python 3.12-slim por digest `sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`.
- Dependências Python do runtime fixadas em `requirements.lock`, 29 distribuições, SHA-256 do arquivo `f5c6b0757685093c77c2f994cb7b104e900b81077f0f0c43d196f1a857f8df82`. Confirmação `pip check` e comparação exata das versões instaladas no contêiner; **não** existe bloqueio de hashes de wheels ou atestado completo de vulnerabilidades.
- `Dockerfile`: usuário não privilegiado UID/GID 10001, `HEALTHCHECK /healthz`, `--no-access-log`, nenhum segredo dentro da imagem. Arquivos `.env`, chaves, estado e backups fora do contexto de build por `.dockerignore`.
- GitHub Actions: criação efêmera apenas, sem push GHCR; workflows históricos de publicação/implantação continuam sob `if: ${{ false }}`.
- Configuração histórica de compose demonstra root filesystem `read_only`, volume `/state` persistente, `/tmp` temporário, limites de CPU/PIDs, `cap_drop ALL`, porta ligada a `127.0.0.1`. **Não reutilizar automaticamente host/endereços legados**; a topologia de destino será definida e aprovada em etapa independente.
- CI S7: 10/10 jobs PASS; SQLite WAL 5/5; Qdrant descartável 4/4 testes adicionais de exportação lógica/restauração/rollback; E2E sintético total 71.

## 2. Pré-requisitos para gate operacional futuro (aprovação humana separada)

1. Nomear **destino novo e isolado** (não TestLab abandonado), operador, janela de trabalho, plano de rede e limite de custo. Conferir que não seja serviço público/legado.
2. Conferir novamente PR #5, commit exato, base R06, CI daquele commit, permissões e revisão independente. Publicação de artefato GHCR requer autorização própria.
3. Materializar imagem imutável identificada por digest, sem adotar tag flutuante; verificar Dockerfile e lock SHA256 do mesmo commit. Preservar SBOM/atestado de dependências antes do GO operacional.
4. Preparar separadamente pastas/volumes: **SQLite `/state` RW persistente**; aprovação documental (`GAIA_RAG_APPROVED_DOCS_FILE`) somente leitura; allowlist de proprietários (`GAIA_RAG_OWNER_SUBJECTS_FILE`) somente leitura; arquivo de chave Qdrant (`QDRANT_API_KEY_FILE`) somente leitura. Não registrar os conteúdos em logs.
5. Controlar segredos pelo serviço autorizado, com rotação, identidade auditável, ACL/permissions restritivas; evitar `QDRANT_API_KEY` em texto aberto no env quando um arquivo protegido é possível. Nenhum segredo em GitHub, relatório, screenshot ou prompt.
6. Configurar `CF_ACCESS_TEAM_DOMAIN` com issuer HTTPS Cloudflare Access, `CF_ACCESS_AUD` específico, allowlist de e-mails do titular, origem HTTPS exata em `GAIA_RAG_REVIEW_BASE_URL`, `GAIA_RAG_CSRF_SECRET` exclusivo e suficientemente longo, `QDRANT_URL` HTTPS e coleção autorizada. `process_id` identifica processo, **não bloqueia** acesso do proprietário entre clientes.
7. Manter `GAIA_RAG_ENABLE_REVIEW` **desativado** até terminar validação de identidade e aprovação documental. A variável `ready_for_real_data=false` na candidata permanece evidência de não homologação.
8. Aprovar a estratégia de disponibilidade/backup: volumes, quota e persistência, RPO/RTO definidos pelo titular, criptografia, retenção/expiração de backup, teste de restauração, monitoramento e rollback. Sem prazos inventados.

## 3. Gate de segurança e autenticação antes de abrir escrita

| Prova | Esperado | Falha = |
| --- | --- | --- |
| `/healthz` | Identidade R07, sem segredos; revisão desativada | NO-GO |
| MCP sem JWT | HTTP 401 / nenhuma memória | NO-GO |
| JWT com issuer/audience falsificados ou expirado | Recusa | NO-GO |
| JWT válido de **não proprietário** | Ferramentas e recursos de skill, memória e portal negados | NO-GO |
| JWT válido do proprietário | Busca global aprovadas, consulta por processo exato, skills permitidas | NO-GO |
| Rotas MCP de aprovação/descarte direto | Inexistentes; apenas link para portal humano | NO-GO |
| Documento sem aprovação verificável | Proposta não preparada / nenhum ponto Qdrant novo | NO-GO |
| Fluxo manual | Portal protegido; CSRF + origem + clique `Salvar memória — Aprovar e gravar`; gravação UMA vez | NO-GO |
| Retentativa do clique | Idempotente pelo point_id estável, sem duplicatas | NO-GO |
| Readback após o clique | SHA da aprovação/documento, fonte, processo, conteúdo, ponto e status conferidos | NO-GO |
| Crise de comunicação após PUT | Estado `approving` auditado; reconciliação manual, sem replay cego | NO-GO |
| Skill host | Seleção, hashes, chunk, carregamento efetivo da skill no ChatGPT | PENDENTE até host real |

**Crítico:** aprovação **documental** e aprovação **de memória** são dois eventos distintos. Nenhuma skill ou LLM, inclusive GroqCloud, pode autorizar automaticamente escrita real. Não ligar Groq sem avaliação LGPD/custo/retenção independente.

## 4. Backup/recuperação — sequência PREPARATÓRIA, não executada

### SQLite do ledger (propostas e audit)

- Usar API online `sqlite3.Connection.backup` para snapshot consistente em operação WAL; não copiar apenas o arquivo `.sqlite3` aberto ignorando WAL/SHM.
- Conferir `PRAGMA integrity_check = ok`, contagem de propostas por status (`pending`, `approving`, `approved`, `discarded`), sequência de auditoria, SHA-256 lógico, ownership e cópia externa criptografada sob custódia autorizada.
- R06/legado podem ter constraint CHECK sem estado `discarded`. A R07 **bloqueia** a ação com `DISCARD_SCHEMA_MIGRATION_REQUIRED`; mudança de esquema exige backup, roteiro transacional, dry-run, rollback e autorização separados.
- Restauração demonstrativa S7 abriu um **novo** arquivo SQLite, verificou hash de linhas e estados e **não substituiu** o banco ativo. Em recuperação real, jamais sobrescrever arquivo com aprovações posteriores sem reconciliação.

### Qdrant de memórias aprovadas

- Antes de migração futura, identificar coleção, endpoint, namespace, quantidade exata, IDs, paginação completa, fontes, status, autoria, data e distinção entre ponto aprovado e proposta pendente.
- Preparar snapshot **nativo** Qdrant/exportação autorizada no ambiente futuro, cópia segura, integridade, restauração em coleção isolada e leitura/readback de índices e vetores. **S7 testou somente exportação lógica e restauração em coleção auxiliar descartável; snapshot nativo e restore cross-host ainda PENDENTES.**
- Quando legado e candidata compartilham a mesma coleção Qdrant, **não copiar cegamente**; comparar os pontos completos e testar a leitura antes de afirmar necessidade de migração.
- Preservar UUIDs, origem, status, data, autor, SHA do documento, vínculos de linhagem e `approved=true` como condição do acervo de memórias. Nunca promover propostas `pending` ou `approving` a aprovadas pelo corte.

## 5. Ordem obrigatória de migração/corte — gates futuros

1. **Homologar candidata R07 operacional isolada** e provar Access real e botão Salvar, com dados de teste autorizados e rollback.
2. **Depois** fazer inventário e backup completo da memória anterior e ledger, reconciliando aprovado vs pendente com readback e contagens.
3. **Depois, mediante autorização distinta**, migrar somente o necessário, validar integridade, pontuação, identidade/processos, linhagem, contagem e leitura. Se falhar, NO-GO e legado mantido.
4. **Por último e com autorização explícita própria**, direcionar operação e eventualmente desativar o serviço legado, preservando-o para recuperação. Nunca desabilitar ou apagar repositório/serviço durante a candidata.

## 6. Roteiro de falha, reversão e evidência

- Falha no pacote: impedir promoção, manter PR draft e rollback de código **só na R07** com HEAD revisado.
- Falha de autenticação/portal: manter flag de revisão desligada e serviço legado ativo; corrigir fora da produção.
- Falha de persistência ou readback: suspender novos cliques, comparar idempotent key/point_id/registro SQL com Qdrant; **não reaprovar** ou apagar pontos às cegas.
- Falha de restauração: NO-GO; guardar backups intactos e evidência de hashes e assinaturas; não sobrescrever dados posteriores.
- Evidência mínima: commit, CI, manifesto de artefato, identidade do operador, runtime, ações autorizadas e recibos, prova de backup/restauração, cenários negativos, tempo efetivo e decisão GO/NO-GO.

## 7. Próximo gate sugerido

**S8 — Revisão independente final da candidata e matriz de prontidão para homologação externa, somente leitura / CI.** Auditar contratos MCP, código de revisão, pacote, dependências, artefatos de CI, recuperação, lacunas residuais (wheel hashes, varredura de vulnerabilidades, snapshot nativo), risco de bloqueios reais e planejamento do host. Produzir checklist GO/NO-GO. **Não executar** deploy, Cloudflare, Qdrant real, migração ou desativação. O próximo gate não está disparado por este runbook.

**Estado:** proposta técnica pronta para futura revisão humana; operação real não iniciada.

## Adendo S8 — validação de supply chain e prioridade de snapshot (18/11/2026)

- **SBOM Python**: `R07_SBOM_PYTHON_LOCK_S8.cdx.json`, CycloneDX 1.6, 29 componentes a partir de `requirements.lock`; o CI o regenera e compara com o arquivo armazenado. Não abrange biblioteca nativa de SO, binários nem as wheels reais por hash.
- **Auditoria de vulnerabilidades**: `pip-audit==2.10.1` consulta advisories públicos para as 29 versões fixadas. Em 18/11/2026, a consulta CI retornou zero vulnerabilidades conhecidas; isso é fotografia temporal da base PyPI, não garantia de ausência de riscos ou cobertura de SO.
- **Hashes de wheels**: ainda não estão em `requirements.lock`; sem `pip install --require-hashes`, pinagem é por versão, não bytes. S9 precisa obter hashes apropriados, prender artefatos e demonstrar rebuild isolado.
- **Qdrant snapshot nativo**: fonte oficial https://qdrant.tech/documentation/snapshots/ ; criar em `POST /collections/{collection}/snapshots` e restaurar para nome **inexistente** via upload com `priority=snapshot`; a prioridade padrão `replica` pode deixar uma coleção nova sem pontos (conforme documentação Qdrant). Endpoint upload pode **sobrescrever** coleção existente. Nunca testá-lo em coleção de produção/legado sem autorização específica.
- **Protocolo fail-closed em R07**: `native_snapshot_plan.preflight` exige coleção de destino distinta e ausente, checksum SHA-256 verificado, manifest completo, backup do ledger e contagens idênticas de pontos aprovados. Testes S8 são **apenas sintéticos**, e o contrato nunca considera o host homologado nem autoriza migração.
- **Replay de aprovação**: nova rotina `_verify_approved_point` reconsulta Qdrant mesmo se o ledger SQLite já indicar `approved`; confere ID, status, namespace, processo, source_ref, documento e texto. Se faltar ponto/ocorrer divergência, não declarar `stored=True`. O clique humano original com CSRF continua obrigatório.
- **Fontes API**: https://api.qdrant.tech/api-reference/snapshots/create-snapshot e https://api.qdrant.tech/api-reference/snapshots/recover-from-uploaded-snapshot . As URLs são fonte de especificação, não ações executadas.

**S8 foi um gate de CI/auditoria sem snapshot Qdrant nativo executado.** A futura decisão de host, backup real, migração e corte não está autorizada.
