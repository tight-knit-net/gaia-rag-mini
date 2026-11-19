# G14-G — replay versionado, evidência observada e paginação SQLite descartável

**Versão documental:** 1.0.0 — evidências de implementação e teste **somente sintéticos**, sem homologação operacional.  
**Emissão aferida:** 2026-11-18T23:26:18-03:00, fuso `America/Sao_Paulo`; origem: ferramenta de horário local do ChatGPT.  
**Início aferido deste gate:** 2026-11-18T23:19:11-03:00, mesma fonte.  
**Último gate anterior (G14-F):** commit GitHub `3b02e0a5b450d72b9eac01b1e3c5da7dd9951b8d`, `2026-11-19T01:35:54Z` = 18/11/2026 22:35:54 BRT.  
**Commit técnico G14-G:** `fe08893b132cac78bb77aa7886e0bf6592a64e2f` publicado em `2026-11-19T02:24:04Z` (18/11/2026 às 23:24:04 BRT); a hora de emissão documental não é hora do commit.  
**Repositório/branch:** `tight-knit-net/gaia-rag-mini`, SOMENTE `feat/gaia-document-mcp-isolado`, [PR #7 Draft](https://github.com/tight-knit-net/gaia-rag-mini/pull/7). Base observada: `feat/r07-office-knowledge-assimilation` @ `6aa55823082842bbe4799773a8acfc2e4eebdea1`.  
**Baseline pré-execução:** `3b02e0a5b450d72b9eac01b1e3c5da7dd9951b8d`.  
**Natureza:** escopo aditivo, v2 público e JSON Schemas inalterados. Nenhuma operação em R06/R07, GitLab, Linear, Google Drive, Cloudflare, Qdrant, outros branches, REST/OCR real, serviços externos ou infraestrutura; nenhuma publicação, merge, rebase ou deploy.

## 1. Resultado executivo e percentuais

**GO técnico somente para G14-G sintético; NO-GO operacional** até identidade real do operador e origem, OCR/NOM E2E controlado, portal R06 de revisão humana agrupada, Qdrant readback, paginação/retensão produtiva, reconciliação UNKNOWN e revisão de segurança/cadeia de suprimentos.

**Teste do commit técnico** [GitHub Actions 44444045976](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444045976), status `success`: **287/287 = 100% dos testes sintéticos**. Inclui **37/37 = 100%** novos casos G14-G, preservando os **250/250** anteriores. Os resultados se referem ao mesmo SHA técnico, sem runtime real.

| Suite | PASSOU | Total | Percentual |
|---|---:|---:|---:|
| Document MCP v2 | 49 | 49 | 100% |
| OCR/NOM híbrido | 13 | 13 | 100% |
| Correlação P0/P1 | 39 | 39 | 100% |
| G14-B operador/contexto | 39 | 39 | 100% |
| G14-C concorrência/SQLite | 46 | 46 | 100% |
| G14-E regressões P1 | 32 | 32 | 100% |
| G14-F contratos independentes | 32 | 32 | 100% |
| **G14-G versão/origem/paginação** | **37** | **37** | **100%** |
| **TOTAL** | **287** | **287** | **100%** |

**CI herdada R05/R07:** [run 44444052857](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444052857), estado **failure** no mesmo SHA técnico, por S9 (auditoria do sistema operacional com Grype, job `135291730201`). O log publicou `os_blocking_findings=78` e `ready_for_supply_chain_gate=false`. S7/S8 devem ser avaliados separadamente; **NO-GO de cadeia de suprimentos**, sem tocar nos scripts ou imagens da R07. Histórico do HEAD anterior: [44438125313](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44438125313) `failure` em cadeia de suprimentos herdada. Este gate não muda lock, SBOM, S7, S8 ou S9. A CI de pull request pode usar merge virtual/base diferentes do SHA da nossa branch; conferir o merge SHA para qualquer aceite.

**CI de supply chain G14-G (observação de falha):** [run 44444052857](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444052857), job S9 `135291730201`, com 78 ocorrências bloqueantes sinalizadas pelo scanner. Não equivale a 78 falhas do código Document MCP. O material de segurança pertence ao orquestrador R07; não classificar como saneado sem triagem específica. No HEAD documental final a CI será acionada novamente e precisará de readback separado.

## 2. Mudanças de contrato — somente laboratório

### 2.1 Replay e `expected_revision` vinculados (F-05)

O método `DisposableGate.reserve` compara agora o `expected_revision` do pedido repetido com o valor registrado **antes** de devolver um recibo de replay. A diferença dispara `IDEMPOTENCY_REVISION_CONFLICT`, mesmo que o payload fingerprint e a chave sejam iguais e mesmo após `COMMITTED_SYNTHETIC`. `reserve_from_event` incorpora a revisão esperada ao fingerprint do envelope e devolve `expected_revision` no recibo. Pedidos com chave diferente ainda passam pela verificação CAS da revisão atual.

**Risco preservado:** `reserve` do laboratório continua aceitando fingerprint fornecido pelo chamador por compatibilidade, e `commit_revision` apenas avança string de revisão em SQLite descartável; não executa ETag ou transação de provedor real.

### 2.2 Fonte documental observada em fixture separada (F-06 parcial)

Novo `G14GDisposableGate.observe_demo_source`: registra **separadamente** em SQLite descartável `process_key/process_id`, `source_ref`, `source_version`, hash calculado dos bytes DEMO e `observation_id` determinístico. Exige vínculo de processo registrado e recusa reobservação conflitante do mesmo par `source_ref+version`.

`capture_observed_demo` confronta o evento recebido com esse registro, confere SHA e bytes de documento fictício por `event_contract_preview` antes de preparar o candidato. A captura **não** aprova documento, não valida qualidade derivada, não autentica o provedor OCR/NOM, não aprova memória e não escreve Qdrant. `provider_origin_authenticated=false` e `derived_quality_attested=false` permanecem explícitos. Prefixo DEMO **não é** mecanismo de anonimização para dados reais.

### 2.3 Paginação transacional limitada em SQLite descartável (F-07 parcial)

Novo `page_pending` executa `SELECT COUNT(*)` e `SELECT ... ORDER BY process_key,candidate_id LIMIT ? OFFSET ?` no mesmo **snapshot de leitura SQLite**; 1 ≤ tamanho ≤ 25. O estado `g14g_pending_generation` é persistido **no banco temporário** e atualizado por triggers para INSERT/UPDATE/DELETE em `candidates`. O cursor contém digest determinístico do número de geração, total e escopo; qualquer mutação observada invalida cursor anterior com `PAGE_SNAPSHOT_STALE`.

`verify_disposable_page_sequence` compara snapshot, posição, continuidade, duplicatas e conclusão. `confirm_current_coverage` reconsulta a geração atual no mesmo laboratório: qualquer alteração após coletar as páginas bloqueia o aceite. **`process_key` é filtro contextual, NÃO ACL**. Páginas contêm metadados e SHA do resumo, não documentos completos; consulta transversal do operador permanece conceitualmente permitida.

**Limites:** OFFSET não é keyset/seek pagination de produção; cursor não é assinado nem verificação de autorização; geração vale apenas na instância SQLite DEMO. Não há TTL, política real de retenção, backups ou paginação Qdrant. `preview_batches` legado ainda usa `fetchall`, portanto a correção cobre apenas a nova interface `page_pending`.

## 3. Matriz de testes — cada caso executado no runner sintético

### 1. Replay / revisão esperada — 7/7 PASSOU (100%)

| Método de teste | Estado |
|---|---|
| `test_replay_same_key_and_expected_revision_is_idempotent` | **PASSOU — sintético** |
| `test_replay_new_expected_revision_is_conflict_even_with_same_payload` | **PASSOU — sintético** |
| `test_replay_new_expected_revision_is_conflict_after_commit` | **PASSOU — sintético** |
| `test_same_key_same_revision_changed_payload_is_conflict` | **PASSOU — sintético** |
| `test_new_key_stale_revision_is_cas_conflict` | **PASSOU — sintético** |
| `test_bound_event_reservation_rejects_changed_expected_revision` | **PASSOU — sintético** |
| `test_revision_expected_is_exposed_in_readback` | **PASSOU — sintético** |

### 2. Observação de evidência DEMO — 13/13 PASSOU (100%)

| Método de teste | Estado |
|---|---|
| `test_observation_requires_registered_administrative_process` | **PASSOU — sintético** |
| `test_observation_retains_sha_and_is_not_provider_auth` | **PASSOU — sintético** |
| `test_identical_observation_is_idempotent` | **PASSOU — sintético** |
| `test_same_source_version_different_bytes_fails` | **PASSOU — sintético** |
| `test_non_demo_bytes_are_rejected` | **PASSOU — sintético** |
| `test_oversized_demo_fixture_is_rejected` | **PASSOU — sintético** |
| `test_alternate_process_id_with_same_number_is_rejected` | **PASSOU — sintético** |
| `test_observed_capture_requires_observation` | **PASSOU — sintético** |
| `test_observed_capture_checks_original_bytes` | **PASSOU — sintético** |
| `test_observed_capture_checks_version` | **PASSOU — sintético** |
| `test_observed_capture_rejects_wrong_declared_original_hash` | **PASSOU — sintético** |
| `test_observed_capture_creates_only_pending_candidate` | **PASSOU — sintético** |
| `test_owner_other_subject_cannot_observe_or_capture` | **PASSOU — sintético** |

### 3. Paginação SQLite e cobertura — 17/17 PASSOU (100%)

| Método de teste | Estado |
|---|---|
| `test_empty_table_is_complete_with_zero_items` | **PASSOU — sintético** |
| `test_two_page_sql_cursor_reaches_full_coverage` | **PASSOU — sintético** |
| `test_page_limit_capped_at_25` | **PASSOU — sintético** |
| `test_page_cursor_rejects_malformed_values` | **PASSOU — sintético** |
| `test_new_candidate_invalidates_cursor` | **PASSOU — sintético** |
| `test_new_evidence_update_invalidates_cursor` | **PASSOU — sintético** |
| `test_reviewed_candidate_invalidates_cursor` | **PASSOU — sintético** |
| `test_sql_direct_update_invalidation_trigger` | **PASSOU — sintético** |
| `test_cursor_persists_across_reopened_sqlite_connection` | **PASSOU — sintético** |
| `test_cross_process_query_is_context_filter_not_acl` | **PASSOU — sintético** |
| `test_scope_specific_cursor_cannot_apply_globally` | **PASSOU — sintético** |
| `test_coverage_rejects_missing_final_page` | **PASSOU — sintético** |
| `test_coverage_rejects_duplicate_page` | **PASSOU — sintético** |
| `test_coverage_recheck_after_insertion_rejects_stale` | **PASSOU — sintético** |
| `test_coverage_owner_required` | **PASSOU — sintético** |
| `test_bad_scope_on_coverage_rejected` | **PASSOU — sintético** |
| `test_candidate_pagination_does_not_create_memory` | **PASSOU — sintético** |


**CI com logs por método:** [run 44444045976](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444045976) e [arquivo de 37 testes](https://github.com/tight-knit-net/gaia-rag-mini/blob/fe08893b132cac78bb77aa7886e0bf6592a64e2f/tests/test_g14g_isolated.py). A contagem aqui é **exata**, extraída das 37 funções da suíte e reconciliada com `Ran 37 tests / OK`.

## 4. Diff, evidências, gates

| Artefato alterado no commit técnico | Escopo | Fonte |
|---|---|---|
| `gaia_document_mcp/g14c_disposable.py` | Checagem de revisão do replay; fingerprint e recibo | [Código pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/fe08893b132cac78bb77aa7886e0bf6592a64e2f/gaia_document_mcp/g14c_disposable.py) |
| `gaia_document_mcp/g14g_isolated.py` | Registro de fonte DEMO, captura observada, paginação/trigger/cobertura | [Módulo pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/fe08893b132cac78bb77aa7886e0bf6592a64e2f/gaia_document_mcp/g14g_isolated.py) |
| `tests/test_g14g_isolated.py` | 37 ensaios, inclusive negativos, sem clientes reais | [Testes pinados](https://github.com/tight-knit-net/gaia-rag-mini/blob/fe08893b132cac78bb77aa7886e0bf6592a64e2f/tests/test_g14g_isolated.py) |
| `.github/workflows/gaia-document-mcp-isolated-ci.yml` | Trigger/compileall/suíte G14-G na CI já isolada | [Workflow pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/fe08893b132cac78bb77aa7886e0bf6592a64e2f/.github/workflows/gaia-document-mcp-isolated-ci.yml) |

Comparação GitHub do baseline `3b02e0a5...` → commit `fe08893b132cac78bb77aa7886e0bf6592a64e2f`: **1 commit, ahead=1, behind=0, exatamente quatro arquivos** exclusivos da frente Document MCP. Nenhum schema v2, R06/R07, lock, SBOM, workflow de release ou outra branch foi editado.

| Gate | Critério | Resultado |
|---|---|---|
| G0 | HEAD/PR #7/base/CI antes de escrever | **PASSOU** |
| G1 | Retry e revisão esperada, conflito sem efeito duplicado | **PASSOU sintético, 7/7** |
| G2 | Observação separada de fonte DEMO e coerência de bytes | **PASSOU sintético, 13/13** |
| G3 | Paginação SQL limitada, cursor, cobertura e invalidadores | **PASSOU sintético, 17/17** |
| G4 | Regressões v2 e anteriores sem alteração | **PASSOU sintético, 250/250** |
| G5 | Relatório Markdown e readback GitHub | **A conferir após publicar** |
| G6 | CI herdada e segurança da cadeia de suprimentos | **FALHOU em S9, 78 apontamentos bloqueantes; fora da alçada da branch** |
| G7 | Autenticação/E2E/Qdrant/produção | **BLOQUEADO, não autorizado** |

**Percentual aferido:** 287/287 = **100% de testes sintéticos**. A prontidão operacional não dispõe de denominador homologado e **não é 100%**; status `NO-GO`.

## 5. Riscos, dependências, rollback e próximo gate

**P1 não resolvidos:** origem/provedor real não autenticados; R06 não integra aprovação em lote; readback de pontos Qdrant não testado; estado UNKNOWN sem reconciliação de efeitos reais; OCR/NOM não emitindo eventos neste adaptador. O risco de supply chain herdada S9 permanece sob responsabilidade da R07. Separar eventos e aprovação documental da decisão humana de memória: coleta automática de candidatos não equivale a promoção Qdrant.

**P2 restantes:** cursor de SQLite não assinado e OFFSET de teste, retenção/volume/backup não homologados, similitude semântica entre requerimentos de órgãos e processos distintos precisa de proveniência e rótulos `ANALOGY_ONLY`. Nunca usar process_id como autorização cliente: o GAIA tem um operador.

**Rollback:** reverter **somente commits do G14-G** na branch `feat/gaia-document-mcp-isolado` após reconfirmar HEAD e diff. Banco SQLite DEMO será descartado pelo `TemporaryDirectory`; não há dados reais a restaurar. Nada foi alterado em R06/R07, GitLab, Linear, Cloudflare, Drive, Qdrant ou produção.

**Próximo gate sugerido (G14-H — NÃO EXECUTADO):** revisão de independência e contratos de erro nos cursores, melhorias no controle de leitura e evidências versionadas, e matriz de interoperabilidade com eventos OCR R02 e revisão humana em lote R06. Sem acesso a serviços reais/branches alheias, sem merge/deploy. Qualquer integração autenticada, homologação E2E e escrita de memória exigem autorização específica e gate próprio.

**Classificação documental:** prévia de relatório com checkpoint do commit técnico; publicação final, horários e eventuais mudanças de CI devem ser conferidos por readback após o commit Markdown. Não declarar aprovação operacional.
