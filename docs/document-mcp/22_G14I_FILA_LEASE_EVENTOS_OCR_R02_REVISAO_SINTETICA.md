# Gate G14-I — OCR R02, fila/lease sintéticos e captura provisória de conhecimento

**Versão:** 1.0.0 — relatório de execução técnica **sintética**, sem homologação de serviço.  
**Emissão aferida:** `2026-11-19T00:27:07-03:00` (`America/Sao_Paulo`), origem: ferramenta de tempo local do ChatGPT.  
**Disparo aferido:** `2026-11-19T00:18:03-03:00`, mesma origem.  
**Último gate anterior, G14-H:** commit documental `fc3b6ed9403f11525b52493fb096c5bc94fce15e` publicado `2026-11-19T02:56:35Z` = **18/11/2026 às 23:56:35 BRT**, relógio/metadados GitHub; o horário do disparo do G14-H foi `2026-11-18T23:44:11-03:00` aferido no relatório 21.  
**Repositório e branch autorizada:** `tight-knit-net/gaia-rag-mini`, **somente** `feat/gaia-document-mcp-isolado`, [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7) **Draft**.  
**Baseline:** `fc3b6ed9403f11525b52493fb096c5bc94fce15e`, PR base `feat/r07-office-knowledge-assimilation` (base SHA PR `6aa55823082842bbe4799773a8acfc2e4eebdea1`).  
**Commit técnico com testes verdes:** `2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0`, `2026-11-19T03:25:10Z` = 19/11/2026 às 00:25:10 BRT.  
**Fontes:** [relatório 21](21_G14H_AUDITORIA_PAGINACAO_EVENTOS_OCR_R02.md); GitHub/CI, diff da PR #7 e contrato OCR R02 transcrito pelo titular em chat (18/11/2026, **proposta não implementada**). Conector `Gaia_Rag___knowledge`: catálogo identificou `gaia-rag-processos-administrativos`; `gaia_skill_read(SKILL.md)` retornou vazio, portanto **carregamento da skill não comprovado**. `GAIA_RAG` legado: consulta de memórias aprovadas com `process_id=GAIA-DOCUMENT-MCP-PR7-2026`, 0 resultados; memória não usada como evidência viva.  
**Restrições:** nenhum acesso a arquivos de clientes, branch OCR `feat/ocr-documental-isolado`, R06/R07, outras branches, Drive, Linear, GitLab, Cloudflare, Qdrant, provedores OCR, TestLab real ou produção. Sem merge, deploy, DNS, migração, gravação de memória ou aprovação humana real.

## 1. Parecer e escopo

**GO para o laboratório de interoperabilidade sintética e o relatório do G14-I; NO-GO para integração ou implantação.** O laboratório **não executa OCR real**; simula o consumo dos metadados previstos no R02 e atua exclusivamente sobre SQLite em `TemporaryDirectory`, com relógio lógico controlado. Não há serviços REST/MCP autenticados, PostgreSQL real, provedor OCR, cobrança ou acesso a documentos de clientes.

**CI específica:** [run 44451300069](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451300069) `success` no commit técnico `2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0`: **353/353 testes sintéticos aprovados (100%)**, sendo **320/320 regressões anteriores + 33/33 G14-I**. [CI pull_request mesmo SHA 44451308545](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451308545) também `success`. Testes unitários e fixtures não constituem E2E autenticado nem aprovação institucional.

**CI herdada:** [run 44451308299](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451308299) **failure** no mesmo commit técnico: S7 e S8 **success**, mas job **R07 S9 Debian OS SBOM/Grype** `135315668140` **failure**. Baseline G14-H [44447922684](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447922684) também falhou em S9. **NO-GO de supply chain herdada**, sem correção nem reclassificação na branch Document MCP.

## 2. Alterações realizadas somente na PR #7

| Arquivo | Conteúdo / contrato | Evidência |
|---|---|---|
| `gaia_document_mcp/g14i_event_lab.py` | Subclasse aditiva de `G14GDisposableGate`; tabela SQLite DEMO de tarefas, histórico, ticks lógicos, claim/lease, retries limitados, reconciliação UNKNOWN e captura candidata; mantém flags de não aprovação. | [módulo pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0/gaia_document_mcp/g14i_event_lab.py) |
| `tests/test_g14i_event_lab.py` | **33 casos sintéticos** para metadados R02, idempotência, concorrência, recuperação, evidência por página, contexto processual e revisão em lote. | [testes pinados](https://github.com/tight-knit-net/gaia-rag-mini/blob/2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0/tests/test_g14i_event_lab.py) |
| `.github/workflows/gaia-document-mcp-isolated-ci.yml` | Trigger, compileall e execução da suíte G14-I somada às nove anteriores; jobs de publicação continuam desabilitados. | [CI pinada](https://github.com/tight-knit-net/gaia-rag-mini/blob/2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0/.github/workflows/gaia-document-mcp-isolated-ci.yml) |

**Diff verificado** G14-H `fc3b6ed9403f11525b52493fb096c5bc94fce15e` → G14-I `2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0`: dois commits e **três arquivos técnicos** apenas, sem alteração dos contratos públicos v2, JSON Schemas, dependências ou R06/R07. Não existe integração/implantação na branch.

## 3. Contratos sintéticos e invariantes

### 3.1 OCR R02 — evidência de páginas e assimilação

O produtor fictício de eventos fornece `process_id`, `process_key`, `document_id`, `source_ref`, `source_version`, `source_sha256`, formato, número de páginas, blocos, qualidades e fingerprints por página. O validador de metadados G14-H confere cobertura, blocos de até oito páginas no laboratório, estados por página e qualidade documental **separada do estado da tarefa**. A fila só aceita PDF nesse caminho; DWG/KML/SHP/GeoJSON devem ser roteados por componente próprio, não enviados indevidamente a OCR.

`enqueue` exige `process_registry` e uma observação DEMO independente de `g14g_source_observations` com mesma identidade, versão e digest; repetição da tarefa na mesma chave/processo requer **fingerprint idêntico**. Mudanças de qualidade/versão/fonte na mesma chave geram `OCR_JOB_IDEMPOTENCY_CONFLICT`. O processamento não recupera texto completo nem produz memória aprovada.

### 3.2 Fila, lease e recuperação

`claim` realiza transação SQLite `BEGIN IMMEDIATE`, seleciona tarefa elegível e concede lease de 1–10 ticks (relógio **sintético**), incremento de tentativas e token diferente por concessão. Somente o worker com token **corrente e não expirado** pode finalizar ou registrar falha. Expiração permite re-claim limitado; após esgotar o número de tentativas (1–3), a tarefa termina `FAILED_SYNTHETIC`. Falhas aceitas usam códigos fechados, evitando vazamento de mensagens brutas e segredos.

O método `finish` separa o estado durável `FINALIZING_UNKNOWN_SYNTHETIC` da efetiva preparação local do candidato. Se houver queda após a marcação e antes do recibo, **não há reprocessamento automático**, e o estado requer reconciliação humana/readback; essa é uma limitação explícita do laboratório, não prova de recuperação PostgreSQL real.

### 3.3 Candidatos provisórios e revisão agrupada

Para documento sintético completo e `LEGIBLE_ALL_PAGES`, `capture_observed_demo` pode criar **apenas candidato provisório** `PENDING_HUMAN_REVIEW`. Job concluído com `LOW_CONFIDENCE`, `EMPTY` ou `INCOMPLETE` segue `REVIEW_NEEDED_SYNTHETIC` **sem criar candidato nesse caminho**. `preview_grouped_review` agrega candidatos pendentes por `process_key` e remete a `review_batch_items` **como simulação**, permitindo `prepare_proposals` sem aprovar a memória.

O **operador é único**; processo/número oficial/órgão/jurisdição são identificadores de contexto e proveniência, não permissões por cliente. A recuperação transversal de memórias institucionais **aprovadas** permanece princípio arquitetural; caso semelhante de outro processo só pode servir como analogia, nunca fusão automática.

**Garantias negativas:** `memory_approved=false`, `qdrant_written=false`, `real_provider_authenticated=false`, `actual_ocr_performed=false`. Não há portal R06 autenticado, botão Salvar real ou readback Qdrant. Proposta documental ≠ aprovação de documento ≠ aprovação de memória.

## 4. Matriz dos 33 testes G14-I executados na CI

### OCR R02: contrato, origem e idempotência — 11/11 (100%)

| Método | Resultado |
|---|---|
| `test_enqueue_preserves_metadata_and_is_not_real_ocr` | **PASSOU — sintético** |
| `test_reenqueue_same_task_is_idempotent_without_duplicate` | **PASSOU — sintético** |
| `test_same_task_with_changed_page_quality_conflicts` | **PASSOU — sintético** |
| `test_same_key_other_process_is_separate_not_acl` | **PASSOU — sintético** |
| `test_missing_observation_does_not_enqueue` | **PASSOU — sintético** |
| `test_false_original_hash_does_not_enqueue` | **PASSOU — sintético** |
| `test_task_requires_registered_process` | **PASSOU — sintético** |
| `test_failed_ocr_metadata_is_not_legible` | **PASSOU — sintético** |
| `test_non_ocr_route_does_not_claim_ocr_queue` | **PASSOU — sintético** |
| `test_seventeen_page_metadata_is_accepted_in_chunks` | **PASSOU — sintético** |
| `test_missing_page_in_completed_job_is_rejected` | **PASSOU — sintético** |

### Fila, lease e recuperação sintéticos — 9/9 (100%)

| Método | Resultado |
|---|---|
| `test_one_worker_claims_other_worker_gets_none` | **PASSOU — sintético** |
| `test_expired_lease_reclaimed_and_old_token_rejected` | **PASSOU — sintético** |
| `test_failure_retry_is_explicit_and_bounded` | **PASSOU — sintético** |
| `test_expired_last_lease_fails_closed` | **PASSOU — sintético** |
| `test_not_expired_lease_cannot_be_reclaimed` | **PASSOU — sintético** |
| `test_invalid_failure_details_rejected_no_secret_recorded` | **PASSOU — sintético** |
| `test_clock_cannot_go_backward` | **PASSOU — sintético** |
| `test_invalid_lease_duration_rejected` | **PASSOU — sintético** |
| `test_wrong_worker_cannot_finish` | **PASSOU — sintético** |

### Assimilação provisória e revisão humana agrupada — 13/13 (100%)

| Método | Resultado |
|---|---|
| `test_legible_event_produces_only_pending_candidate` | **PASSOU — sintético** |
| `test_low_quality_completed_ocr_routes_to_review_no_candidate` | **PASSOU — sintético** |
| `test_incomplete_job_does_not_capture_pending_memory` | **PASSOU — sintético** |
| `test_wrong_source_version_does_not_complete` | **PASSOU — sintético** |
| `test_wrong_original_bytes_do_not_complete` | **PASSOU — sintético** |
| `test_simulated_crash_is_unknown_no_automatic_retry` | **PASSOU — sintético** |
| `test_reenqueue_unknown_never_performs_capture` | **PASSOU — sintético** |
| `test_receipt_survives_sqlite_connection_reopen` | **PASSOU — sintético** |
| `test_history_is_versioned_and_no_raw_document_logged` | **PASSOU — sintético** |
| `test_batch_group_stays_contextual_and_not_approved` | **PASSOU — sintético** |
| `test_batch_decisions_only_prepare_proposal` | **PASSOU — sintético** |
| `test_other_owner_fixture_cannot_claim_jobs` | **PASSOU — sintético** |
| `test_no_recorded_memory_approval_in_queue` | **PASSOU — sintético** |


**Regressões:** 49 contratos v2 + 13 híbrido OCR/NOM + 39 correlação + 39 G14-B + 46 G14-C + 32 G14-E + 32 G14-F + 37 G14-G + 33 G14-H + 33 G14-I = **353/353**, na mesma execução de CI. Os 18 testes originais do repasse OCR R02 **continuam não executados nesta branch OCR**; não misturar as duas matrizes.

### Histórico de falha corrigida, sem mascaramento

[Run 44451160909](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451160909), primeiro commit técnico `7363dd23d43c7126a1c908f1ab3a4f6414794d1b`: **320/320 regressões anteriores + 32/33 novos**, 1 erro de teste em `test_batch_group_stays_contextual_and_not_approved`: tentativa de enfileirar tarefa com tick lógico `0` após finalizar outra no tick `2`, corretamente rejeitada por `SYNTHETIC_TIME_REGRESSION`. Corrigida apenas a fixture para `now_tick=2` no commit `2b2e78e5e01cec0b004d5724c00f8bbe5fbff3c0`; proteção de tempo monotônico **mantida**. [CI 44451300069](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451300069) **353/353 PASSOU**, sem alterar contrato público v2.

## 5. Limitações, riscos, gates e GO/NO-GO

| ID | Risco/resíduo | Estado e dependência |
|---|---|---|
| I-R01 | Relógio é lógico e token lease é determinístico de bancada; não autentica worker REST/MCP nem suporta relógio real confiável | **PENDENTE — E2E isolado autorizado** |
| I-R02 | Finalização em duas transações não é atomicidade distribuída: captura pode ocorrer antes de recibo da fila, exigindo reconciliação do estado UNKNOWN | **PENDENTE — runbook e readback idempotente** |
| I-R03 | Página OCR tem qualidade/hash declarados em fixture, não medidos/assinados pelo motor OCR real | **PENDENTE — contrato/aceite do responsável OCR** |
| I-R04 | Lotes e `preview_batches` continuam locais; não há revisão autenticada R06, aprovação documental verificada ou readback Qdrant | **BLOQUEADO — gate externo separado** |
| I-R05 | SQLite `TemporaryDirectory` não comprova PostgreSQL em concorrência de workers, crash real, recuperação em restart nem backup | **PENDENTE — TestLab com autorização própria** |
| I-R06 | O G14-I não executa os 18 casos OCR R02 na branch própria; nem modifica sua API/retenção/LGPD, custo de provedor ou binários | **BLOQUEADO POR ESCOPO** |
| I-R07 | CI herdada R07 **falhou em S9 no commit técnico G14-I**, embora S7/S8 passaram; nenhuma mitigação na frente Document MCP | **BLOQUEADO — orquestrador R07** |

| Gate | Evidência | Estado |
|---|---|---|
| I0 — PR/HEAD/base e CI inicial | GitHub preflight no baseline e antes de cada update_ref | **PASSOU** |
| I1 — contrato OCR R02 e idempotência por processo | 11/11 testes de metadados, evento e origem DEMO | **PASSOU sintético** |
| I2 — claim/lease, retry e falha | 9/9 testes de concorrência/transições, sem provedor | **PASSOU sintético** |
| I3 — recuperação UNKNOWN, captura provisória e lote | 13/13 testes de finalização e revisão | **PASSOU sintético** |
| I4 — regressões v2 e suites anteriores | 353/353 em CI isolada | **PASSOU** |
| I5 — relatório Markdown, índice e readback | Conferir após publicação documental | **PENDENTE nesta versão inicial** |
| I6 — CI herdada/supply chain R07 | [run 44451308299](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451308299): S7/S8 sucesso, **S9 falhou** | **FALHOU — NO-GO supply chain** |
| I7 — OCR real/R06/Qdrant/implantação | Não executado ou autorizado | **NO-GO** |

**Contagem de gates nesta fotografia:** 5/8 = **62,5%** concluídos no escopo medido; o valor evolui após relatório e readback. **Prontidão operacional global não tem denominador homologado**. Não confundir 100% dos testes sintéticos com sistema pronto.

## 6. Rollback, próxima ação e preservação institucional

**Rollback:** após reconfirmar HEAD, reverter apenas commits G14-I em `feat/gaia-document-mcp-isolado` (laboratório, testes, CI própria, documentação). A base G14-H e outras branches não são alvos de reversão. Todos os dados SQLite DEMO são descartados em `TemporaryDirectory`; não houve gravação em Qdrant ou produção.

**Próximo gate recomendado G14-J (não iniciado):** revisar de forma independente a corrida entre `FINALIZING_UNKNOWN_SYNTHETIC` e a gravação candidata; preparar reconciliação com readback somente sintético e teste de idempotência durável após crash, sem integração OCR real. Documentar matriz de responsabilidades OCR R02 ↔ Document MCP ↔ revisão humana R06, paginador escalável e evidência de origem confiável, respeitando os contratos v2.

**Decisão final pretendida após readback:** **GO para G14-I técnico/sintético, NO-GO para integração operacional, deploy, migração, memória institucional e dados reais.** Publicação do relatório e CI devem ser verificadas no SHA efetivo do GitHub, não presumidas por esta minuta.
