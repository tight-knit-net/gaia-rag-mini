# Gate G14-J — reconciliação da finalização UNKNOWN em SQLite descartável

**Versão documental:** 1.0.1 — execução de implementação sintética com **VALIDAÇÃO BLOQUEADA**; não é homologação operacional.  
**Emissão aferida:** `2026-11-19T01:17:34-03:00`, fuso `America/Sao_Paulo`. Fonte do relógio: widget local de tempo do ChatGPT.  
**Disparo aferido G14-J:** `2026-11-19T01:07:57-03:00`, mesma fonte.  
**Último gate G14-I:** commit documental `e83c791630e2e0682a161fcd2e9d5ef6d6363e3d` em `2026-11-19T03:30:57Z` = **19/11/2026 às 00:30:57 BRT** (metadados GitHub).  
**Repositório e limite de escrita:** `tight-knit-net/gaia-rag-mini`, somente `feat/gaia-document-mcp-isolado`, [PR #7 Draft](https://github.com/tight-knit-net/gaia-rag-mini/pull/7), base `feat/r07-office-knowledge-assimilation` @ `6aa55823082842bbe4799773a8acfc2e4eebdea1`.  
**HEAD de baseline:** `e83c791630e2e0682a161fcd2e9d5ef6d6363e3d`. **Commit técnico G14-J:** `7ed0e21d0edabc29de1ee732363edd3f6094d523`, criado às `2026-11-19T04:13:16Z` = 01:13:16 BRT.  
**Fontes:** relatório 22 G14-I, GitHub PR/HEAD/compare, teste-fonte no próprio ramo, GitHub Actions e status de checks. O catálogo `Gaia_Rag___knowledge` identificou skill `gaia-rag-processos-administrativos`; **carregamento efetivo pelo host não comprovado**. Não consultadas memórias ou serviços R06/R07 por restrição específica do gate.  
**Proteção:** dados inventados `DEMO`, `TemporaryDirectory`, SQLite local, relógio sintético. Não acessar nem alterar OCR, R06/R07, Qdrant, Drive, Cloudflare, GitLab, Linear, main ou outros ramos; sem merge, deploy, memória real, OCR real, autenticação externa ou documentação de clientes.

## 1. Parecer e percentuais

**NO-GO para homologação do G14-J e integração.** O código e os testes foram preparados e publicados na branch permitida, **mas nenhuma etapa de teste do commit G14-J pôde ser comprovadamente executada em GitHub Actions**. A infraestrutura devolveu falha antes de iniciar etapas; reexecução apresentou o mesmo bloqueio. Não é legítimo reportar que a suíte G14-J passou, nem afirmar que os novos testes falharam logicamente.

| Indicador | Aprovados ou verificáveis | Total real | Percentual |
|---|---:|---:|---:|
| Regressão G14-I no HEAD anterior — **histórico comprovado** | **353** | **353** | **100%** |
| Novos métodos G14-J preparados (contagem de arquivo) | **35 escritos** | **35 previstos** | **100% de autoria, sem execução** |
| **Novos G14-J com execução comprovada** | **0** | **35** | **0% verificado** |
| Execução completa no novo HEAD | **não aferível** | **388 métodos configurados na CI** | **SEM RESULTADO** |

**Nota:** 0/35 de execução comprovada **não significa 35 reprovações de assertivas**. A suíte atual pode conter erros de código ou de teste ainda não conhecidos. Só CI com logs e readback poderá elevar o percentual.

## 2. Diagnóstico real das falhas de CI

1. [run 44456806477](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44456806477), `push`, commit `7ed0e21d0edabc29de1ee732363edd3f6094d523`: `failure` em cerca de 3 segundos. Job `synthetic-contracts` inicialmente `135333699022`, sem etapas; a tentativa 2 `135334525406` repetiu `failure` com **zero etapas** e `steps=[]`. O endpoint de logs retornou erro `BlobNotFound`, **não os logs de unittest**.
2. [run 44456815519](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44456815519), `pull_request`, mesma SHA: job `synthetic-contracts` `failure`, **sem etapas registradas**.
3. [run herdado 44456815530](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44456815530), mesma SHA: **17 jobs falharam antes de registrar etapas**; job de aceite ficou skipped. O padrão simultâneo é compatível com indisponibilidade/configuração do runner ou limite de Actions, mas a **causa específica permanece INDETERMINADA**. Não classificar como defeito comprovado do módulo nem descartar a possibilidade de erro de pipeline.
4. Baseline anterior [run 44451988279](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451988279) `success` com logs legíveis e 353/353, **somente na SHA anterior**. Validação herdada pré-existente [44451988308](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451988308) `failure` em S9. Nenhuma mudança no workflow herdado ou na imagem base foi autorizada neste gate.

**Diagnóstico responsável:** **CI_BLOQUEADA_SEM_EXECUCAO_VERIFICAVEL**. Não ocultar falha e não chamar CI verde por analogia ao gate anterior.

## 3. Auditoria e implementação: contratos não operacionais

| ID | Achado, invariante ou risco | Estado após escrita |
|---|---|---|
| J-01 | `FINALIZING_UNKNOWN_SYNTHETIC` pode persistir depois de evento de captura mas antes de gravar recibo; existência de candidato semelhante não prova autoria da tarefa | **ENDEREÇADO NO NOVO CÓDIGO, AINDA NÃO TESTADO** |
| J-02 | Antes de tocar candidato, a nova API `begin_unknown` cria intenção vinculada a `process_key`, `process_id`, `task_key`, fingerprint do evento, SHA/versão/fonte e ID esperado, com transição de estado na mesma transação SQLite | **IMPLEMENTADO SINTETICAMENTE, NÃO VALIDADO** |
| J-03 | `simulate_effect_receipt` exercita captura DEMO e recibo separado; recusa apropriar-se de histórico anterior da mesma evidência (`AMBIGUOUS_PRIOR_CAPTURE`) | **IMPLEMENTADO SINTETICAMENTE, NÃO VALIDADO** |
| J-04 | `reconcile_unknown` exige recibo de efeito + candidato com identidade/fonte/versão/revisão + chave do evento e histórico, e serializa transição sem duplicá-la; sem prova conserva UNKNOWN e não efetua captura | **IMPLEMENTADO SINTETICAMENTE, NÃO VALIDADO** |
| J-05 | `audit_task_history` exige cadeia de estados, ticks não regressivos e estado terminal igual ao recibo da tarefa; não possui assinatura, WORM nem trilha auditável externa | **IMPLEMENTADO SINTETICAMENTE, NÃO VALIDADO** |
| J-06 | `review_preview_after_reconciliation` bloqueia revisão agrupada de processo com UNKNOWN pendente e nunca concede `memory_approved` ou `qdrant_written` | **IMPLEMENTADO SINTETICAMENTE, NÃO VALIDADO** |
| J-07 | Captura de candidato e gravação de recibo ainda ocorrem em **duas transações**. Crash entre elas não permite reconciliação automática; manter NO-GO e operação humana protegida | **LACUNA EXPLÍCITA / NÃO RESOLVIDA** |
| J-08 | Token/clock/owner continuam fixtures, sem comprovação de identidade do OCR, operador do portal R06, origem real ou integridade criptográfica do log | **PENDENTE POR ESCOPO** |
| J-09 | R06, Qdrant, approved=true, `prior_point_id`, fonte confiável e migração não foram utilizados nem testados | **BLOQUEADO POR ESCOPO** |

**Observação crítica:** o novo fluxo `begin_unknown` é **aditivo** à API G14-I, que permanece no módulo anterior e não é substituída automaticamente. A matriz não declara que todo o sistema passou a ter reconciliação. A API pública de `contracts.py`, schemas v2, workflows da R07 e fontes de clientes não foram alterados.

## 4. Testes G14-J escritos, mas não executados — discriminação exata

### J-01 — Intenção durável, origem e efeito UNKNOWN: 0/14 com execução comprovada (0%)

| Caso de teste | Estado probatório |
|---|---|
| `test_intent_atomic_unknown_persists_without_capture` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_no_proof_retains_unknown_and_never_recaptures` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_repeated_no_proof_readback_does_not_increment_history` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_matching_effect_receipt_allows_reconciliation` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_reconciliation_replay_does_not_duplicate_history` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_effect_receipt_replay_is_idempotent_without_recapture` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_crash_after_capture_but_before_proof_is_fail_closed` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_prior_same_event_from_other_task_is_not_effect_proof` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_no_old_worker_can_finalize_after_intent` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_unknown_not_claimable_after_expired_lease` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_wrong_document_bytes_are_rejected_before_intent` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_source_identity_mismatch_is_rejected_before_intent` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_task_alias_process_number_cannot_reconcile` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_wrong_event_fingerprint_cannot_record_effect` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |

### J-02 — Falsificação e divergência de provas: 0/7 com execução comprovada (0%)

| Caso de teste | Estado probatório |
|---|---|
| `test_changed_capture_receipt_candidate_is_not_accepted` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_changed_capture_receipt_event_is_not_accepted` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_changed_candidate_event_history_is_not_accepted` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_changed_candidate_revision_is_not_accepted` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_deleted_candidate_cannot_be_reconstructed_by_reconcile` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_changed_intent_source_version_invalidates_proof` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_changed_intent_digest_invalidates_receipt` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |

### J-03 — Concorrência, reinício e integridade do histórico: 0/7 com execução comprovada (0%)

| Caso de teste | Estado probatório |
|---|---|
| `test_repeated_reconcile_is_serialized_between_threads` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_concurrent_unknown_without_receipt_never_captures` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_proof_survives_reopening_disposable_connection` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_history_chain_has_correct_terminal_readback` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_broken_history_transition_is_detected` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_backward_history_tick_is_detected` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_history_terminal_state_change_is_detected` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |

### J-04 — Revisão agrupada e isolamento por operador/processo: 0/7 com execução comprovada (0%)

| Caso de teste | Estado probatório |
|---|---|
| `test_grouped_preview_is_blocked_while_unknown_no_effect` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_grouped_preview_is_blocked_even_after_unreconciled_effect` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_grouped_preview_after_verified_reconciliation_is_unapproved` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_batch_prepare_proposal_never_approves_qdrant` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_other_operator_cannot_reconcile_synthetic_fixture` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_wrong_case_process_cannot_see_pending_review` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |
| `test_no_approval_flag_in_reconciliation_readback` | **NÃO EXECUTADO/SEM LOG — CI BLOQUEADA** |


**Total de métodos sintéticos novos:** 35. As próximas execuções devem mostrar explicitamente `Ran 35 tests / OK` e **388/388** para considerar o conjunto integral aprovado — não pressupor que será esse o resultado.

## 5. Diff, gates e rollback

| Arquivo escrito | Finalidade | Fonte pinada ao commit técnico |
|---|---|---|
| `gaia_document_mcp/g14j_reconciliation.py` | Proposta de reconciliação fail-closed com recibo, intenção durável e readback SQLite | [código](https://github.com/tight-knit-net/gaia-rag-mini/blob/7ed0e21d0edabc29de1ee732363edd3f6094d523/gaia_document_mcp/g14j_reconciliation.py) |
| `tests/test_g14j_reconciliation.py` | 35 negativos e positivos por fixture | [testes](https://github.com/tight-knit-net/gaia-rag-mini/blob/7ed0e21d0edabc29de1ee732363edd3f6094d523/tests/test_g14j_reconciliation.py) |
| `.github/workflows/gaia-document-mcp-isolated-ci.yml` | Compilação e execução da nova suíte em CI isolada | [workflow](https://github.com/tight-knit-net/gaia-rag-mini/blob/7ed0e21d0edabc29de1ee732363edd3f6094d523/.github/workflows/gaia-document-mcp-isolated-ci.yml) |

**Diff verificado:** G14-I `e83c791630e2e0682a161fcd2e9d5ef6d6363e3d` → G14-J técnico `7ed0e21d0edabc29de1ee732363edd3f6094d523`: **um commit, três arquivos**, todos restritos à frente Document MCP. Commit HEAD e PR reconfirmados antes da escrita. A falha de CI foi observada, o rerun autorizado foi registrado e não houve mudanças em R06/R07, branch OCR, outros serviços ou infraestrutura.

| Gate | Critério | Estado |
|---|---|---|
| J0 | HEAD, PR #7, base e baseline CI antes da escrita | 🟢 **PASSOU** |
| J1 | Desenvolvimento de intenção/prova/readback sintéticos | 🔵 **IMPLEMENTADO, NÃO VALIDADO** |
| J2 | Testes negativos e concorrência (35 casos) | 🟡 **ESCRITOS, EXECUÇÃO BLOQUEADA** |
| J3 | CI do G14-J com logs de unittest | 🔴 **FALHOU ANTES DAS ETAPAS** |
| J4 | Regressões v2 no HEAD do G14-J | 🟡 **PENDENTE**, baseline histórico não comprova HEAD novo |
| J5 | Relatório MD, índice e readback GitHub | 🟢 **PASSOU no checkpoint documental**, readback confirmado |
| J6 | Cadeia de suprimentos herdada | 🔴 **FALHOU SEM LOGS**, além de riscos S9 anteriores |
| J7 | E2E OCR/R06/Qdrant/produção | 🔴 **NO-GO** |

**Contagem após publicação documental e readback:** **2/8 = 25%** dos critérios concluídos (J0 e J5). O desenvolvimento está processado, mas sem aceite da execução; J3 e J6 falharam sem etapas, J2/J4 pendentes e J7 NO-GO. Esse percentual não representa prontidão global; os testes G14-J permanecem **0/35 = 0% com execução comprovada**.

**Rollback autorizado conceitualmente (não executado):** reverter somente commit G14-J e documentação correspondente mediante prévia reconferência de HEAD, mantendo G14-I, R07, R06 e demais frentes. SQLite `TemporaryDirectory` não persiste em serviço real, portanto não requer restauração externa.

## 6. Próximo gate recomendado

**G14-JR (retomada controlada, NÃO EXECUTADO):** verificar formalmente a disponibilidade/configuração de GitHub Actions, com responsável pela infraestrutura se necessário; executar o próprio workflow da branch novamente, sem enfraquecer testes/segurança; se o runner voltar, corrigir quaisquer falhas reais **apenas na branch autorizada** e refazer 388/388 com logs. Depois, revisar corrida de gravação de recibo, cobertura de falhas entre transações e integridade da prévia de lote. Não iniciar G14-K, integração real ou merge antes do GO probatório.

**Encerramento de implementação:** código e testes publicados **não equivalem a teste aprovado**. Registre `VALIDACAO_PENDENTE_CI` e `NO-GO` até CI/run ID, console log, readback e aceite humano.

## 7. Checkpoint de publicação e CI no HEAD — aditivo v1.0.1

**Aferição:** `2026-11-19T01:19:34-03:00`, America/Sao_Paulo, relógio local do ChatGPT.  
**Primeira publicação documental:** commit `4faf10594dd3030c15ab449dd84e9c4ce445c771` às `2026-11-19T04:19:02Z` (19/11 às 01:19:02 BRT), conforme metadados GitHub.

**Readback confirmado:** HEAD da branch e da PR #7 em `4faf10594dd3030c15ab449dd84e9c4ce445c771`, PR Draft não mesclada, base `feat/r07-office-knowledge-assimilation`; relatório Markdown em `docs/document-mcp/23_G14J_RECONCILIACAO_UNKNOWN_PROVAS_CI_BLOQUEADA.md` (blob `5c56f832e2c6caa813c65513e7c6ff9fbab4d418`), contendo matriz de **35 casos sem execução comprovada**, indicador 0/35, marca `CI_BLOQUEADA_SEM_EXECUCAO_VERIFICAVEL` e decisão NO-GO; índice README com item 23. Diff entre G14-I `e83c791630e2e0682a161fcd2e9d5ef6d6363e3d` e `4faf10594dd3030c15ab449dd84e9c4ce445c771`: **2 commits, 5 arquivos**, exclusivos da frente Document MCP, sem modificações em schemas v2.

**CI documental no próprio SHA:** [push run 44457482146](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44457482146) e [PR run 44457488952](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44457488952), ambos `failure`; jobs `synthetic-contracts` com `steps=[]`, portanto **nenhum unittest executado de forma verificável**. [CI herdada 44457488967](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44457488967) `failure`. Não foi autorizado modificar a R07 ou a configuração de runners.

**Conclusão:** **G14-J implementação publicada, mas NO-GO probatório e operacional.** Os 353 testes aprovados no gate G14-I são apenas baseline histórica. Para GO técnico G14-J são necessários logs íntegros com todos os casos executados, reconciliação do histórico e testes regressivos, no **SHA exato**. A publicação deste aditivo gera outro SHA que exige readback separado.
