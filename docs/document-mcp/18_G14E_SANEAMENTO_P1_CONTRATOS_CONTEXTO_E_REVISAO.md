# G14-E — saneamento P1: contexto processual, evidência, idempotência e lotes

**Versão documental:** 1.0.0 — relatório de execução em CI sintética, sem homologação operacional.  
**Instante de emissão aferido:** 2026-11-18T22:12:29-03:00, fuso `America/Sao_Paulo`, origem: ferramenta local de horário do ChatGPT. Hora do commit GitHub é evidência independente de publicação.  
**Repositório autorizado:** `tight-knit-net/gaia-rag-mini` — branch `feat/gaia-document-mcp-isolado`, [PR #7 Draft](https://github.com/tight-knit-net/gaia-rag-mini/pull/7).  
**Baseline pré-gate:** `4f28b4b2b6d537fae03d36e29d9fb02f9bca2b9f`; relatório anterior: [17 — G14-D](17_G14D_AUDITORIA_CONTRATOS_FLUXO_SALVAR_MEMORIA.md).  
**Commit técnico aprovado na CI:** `8387ceeda417e48014846311eb312a89b793bbad`.  
**Escopo de alterações:** somente `gaia_document_mcp/g14c_disposable.py`, `gaia_document_mcp/process_learning.py`, `tests/test_g14e_safety.py`, CI própria e documentação `docs/document-mcp`. Sem alteração de `contracts.py`, JSON Schemas v2, `trust.py`, R06/R07, outras branches ou quaisquer serviços externos.  
**Fontes consultadas nesta rodada:** GitHub PR/HEAD/base/CI e arquivos **apenas da própria branch**; relatório G14-D já publicado. GitLab, Linear, Drive, Cloudflare, Qdrant, servidores, TestLab, R06 e R07 **não acessados**.  
**Dados:** exclusivamente DEMO em SQLite `TemporaryDirectory`; não há documentos reais, credenciais nem chamadas externas.

## 1. Decisão executiva e risco

**GO técnico apenas para saneamento e regressões em laboratório sintético. NO-GO para implantação, autenticação real, revisão humana no portal R06, gravação Qdrant, merge, integração com OCR/NOM real ou migração.**

Objetivos cumpridos no recorte sintético: preservar integridade da identidade do processo administrativo, reduzir falsas deduplicações, desbloquear complementação de evidências sem promover automaticamente memória, separar tentativas de evidência e permitir decisões diferenciadas por item de lote, mantendo recibos e idempotência.

**Operador único:** `process_id`, `client_id` e numeração da Prefeitura são informações de contexto/proveniência, **não ACL**. Processos distintos podem ter requerimentos quase idênticos; a consulta transversal de memórias institucionais aprovadas do proprietário não deve ser bloqueada por essas chaves. Nunca projetar identidade do cliente como permissão de leitura.

## 2. Matriz de reconciliação dos 12 achados G14-D

| ID | Prioridade | Estado após G14-E | Trabalho realizado / fonte | Limitação ou próximo contrato |
|---|---|---|---|---|
| G14D-01 | **P1** | **MITIGADO SINTÉTICO** | A decisão needs_more_evidence pode voltar a PENDING apenas com marcador de fonte/evidência novo; revision++ e candidate_history; operation_id novo não basta. | R06 real e prova de origem ainda pendentes. |
| G14D-02 | **P1** | **MITIGADO SINTÉTICO** | Tabela process_registry registra vínculo process_key→process_id/órgão/município/número e rejeita divergências mesmo com outro assunto. | Conferência do identificador real na Prefeitura e dados autorizados pendentes. |
| G14D-03 | **P1** | **MITIGADO PARA DEDUPE EXATA** | Fingerprint usa resumo canônico mantendo ordem, negação e frequência; similitude semântica fica como sugestão. | Classificação de fato/alegação/decisão e modelos semânticos futuros pendentes. |
| G14D-04 | **P1** | **PENDENTE** | A captura G14-E permanece método invocado por teste, sem bus/adapter real para OCR, NOM, edição ou movimento. | Exige integração e contrato de evidência em gate separado. |
| G14D-05 | **P1** | **MITIGADO SINTÉTICO** | review_batch_items permite seleção/decisão por candidato, grava item receipts e confirma snapshot integral, mantendo review_batch legado. | Sem clique, identidade real ou aprovação R06. |
| G14D-06 | **P1** | **BLOQUEADO POR ESCOPO** | Contrato autenticado de lote no servidor/portal R06 não foi alterado nem acessado nesta rodada. | Responsável R06/R07 e autorização separada. |
| G14D-07 | **P1** | **BLOQUEADO POR ESCOPO** | Readback R06 real por item, source_ref/process_id/approved/approval_ref ainda não retestado ou alterado. | Homologação autenticada e alteração própria R06 se comprovado. |
| G14D-08 | **P1** | **MITIGADO NO CAMINHO NOVO** | reserve_from_event calcula fingerprint com contexto, fonte, versão, hash e síntese e valida bytes; API antiga reserve(raw fingerprint) preservada para regressão. | A nova via não comprova provedor autenticado; legado ainda permite fingerprint informado. |
| G14D-09 | **P1** | **PENDENTE** | UNKNOWN_SYNTHETIC continua fail-closed, sem reconciliador externo ou prova de efeito real. | Não automatizar retry; readback autorizado e runbook são próximos gates. |
| G14D-10 | **P2** | **MITIGADO SINTÉTICO** | Snapshot de lote cobre process_id, conteúdo mostrado, revisão do candidato, origens, eventos, marcadores de evidência, estado e versão fixa de política. | Versão de política operacional futura não implementada. |
| G14D-11 | **P2** | **PENDENTE** | Preview ainda fetchall, sem paginação e quotas reais; não foi ampliado para evitar aumento de escopo. | Limites, cursor, cobertura e retenção necessários. |
| G14D-12 | **P2** | **PENDENTE** | Operador SyntheticOwnerOnly e SQLite TemporaryDirectory continuam apenas fixtures. | Autenticação, backup e privacidade operacional dependem de outro gate. |

**Conclusão de cobertura:** dos 9 P1 anteriores, **4 com mitigação em comportamento sintético**, **1 com mitigação restrita ao novo caminho sintético e legado mantido**, **4 pendentes/bloqueados por integrações externas**; G14D-03 tem deduplicação exata mitigada, **classificação semântica real pendente**. Esta classificação não equivale a 9/9 gaps resolvidos. Entre os 3 P2, **1 mitigado sinteticamente** e **2 pendentes**.

## 3. Diff técnico / invariantes preservadas

| Arquivo | Alteração | Evidência |
|---|---|---|
| `gaia_document_mcp/process_learning.py` | `_canonical_summary` preserva palavras na ordem original, negações e frequência. Similaridade léxica continua apenas busca, não verdade. | [Código pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/8387ceeda417e48014846311eb312a89b793bbad/gaia_document_mcp/process_learning.py) |
| `gaia_document_mcp/g14c_disposable.py` | `process_registry` para vínculo oficial imutável; revisão de candidato e histórico de transição; `evidence_markers_json` não aceita operation_id sozinho como evidência; snapshot canônico de lote; `review_batch_items` permite escolhas por item; `reserve_from_event` gera fingerprint observado no laboratório. | [Código pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/8387ceeda417e48014846311eb312a89b793bbad/gaia_document_mcp/g14c_disposable.py) |
| `tests/test_g14e_safety.py` | 32 testes negativos/positivos adicionais com dados DEMO. | [Testes pinados](https://github.com/tight-knit-net/gaia-rag-mini/blob/8387ceeda417e48014846311eb312a89b793bbad/tests/test_g14e_safety.py) |
| `.github/workflows/gaia-document-mcp-isolated-ci.yml` | Inclusão de compileall, trigger e execução da suíte G14-E; jobs de publicação não habilitados. | [Workflow pinado](https://github.com/tight-knit-net/gaia-rag-mini/blob/8387ceeda417e48014846311eb312a89b793bbad/.github/workflows/gaia-document-mcp-isolated-ci.yml) |

### Complementação de evidências — contrato preciso

Quando um lote retorna `needs_more_evidence`, os candidatos permanecem `MORE_EVIDENCE_NEEDED_SYNTHETIC`. **Nova origem, versão ou digest de evidência** identificável reabre a candidatura `PENDING_HUMAN_REVIEW`, gera `candidate_revision + 1`, cria histórico transacional e invalida o `batch_id` anterior. **Nova tentativa de operação isolada** (alterar `operation_id`) não é evidência; rejeita `NEW_EVIDENCE_REQUIRED`. Reabertura nunca aprova documento nem grava memória.

**Limite:** o marcador é calculado com campos fornecidos por `DocumentEvent` de laboratório, não é prova autenticada de fonte remota. Em sistema real, exigir observação do documento e checagem de bytes/revisão na fronteira confiável.

### Revisão agrupada — contrato sintético

`review_batch` antigo mantém semântica de lote integral. Novo `review_batch_items` aceita `{candidate_id: decision}` para subconjunto controlado, de modo que itens não selecionados permanecem pendentes. A decisão pode ser apenas `prepare_proposals` ou `needs_more_evidence`. A snapshot antes da revisão cobre **todos** candidatos pendentes daquele processo, inclusive conteúdo, processo, revisão e marcadores de origem/evidência; qualquer alteração invalida o batch_id. Recibos por candidato preservam decisão e estado. **prepare_proposals ≠ document_approved ≠ memory_approved**.

## 4. Evidências de CI, regressão e testes negativos

**GitHub Actions na SHA de código `8387ceeda417e48014846311eb312a89b793bbad`:** [run 44435007578](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435007578) `success`; logs confirmam **49 contratos v2 + 13 OCR/NOM + 39 correlação + 39 G14-B + 46 G14-C + 32 G14-E = 218/218 testes sintéticos aprovados**. [CI herdada R05/R07](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435016347) **FALHOU** no mesmo SHA nos jobs de pacote S7 e SBOM S8; o risco de cadeia de suprimentos permanece fora do escopo G14-E. Não interpretar a CI própria verde como GO para a branch inteira. Não somar linhas de teste ao conjunto de provas de um runtime real.

**Histórico de falha e correção:** a primeira execução após o commit `a68a3b3e...` falhou em **1/31 novos testes**, porque uma fixture usou o marcador proibido `demo:` em minúsculas. O teste foi corrigido preservando a exigência literal `DEMO:` no commit `8c340de8...`, sem afrouxar o isolamento. A revisão final detectou que um simples `operation_id` novo reabria uma candidatura sem evidência material; o commit `8387ceeda417e48014846311eb312a89b793bbad` introduziu marcador independente da tentativa e mais uma negativa, resultando em **32/32** novos testes aprovados.

### Cobertura resumida dos novos casos (32 executados)

| Caso agrupado | Contexto / negativa | Resultado esperado |
|---|---|---|
| E-01 | Processo de mesma numeração/órgão mas process_id distinto e assunto diferente | PROCESS_ID_COLLISION |
| E-02 | Processo registrado na seed recebe outro ID interno | PROCESS_ID_COLLISION |
| E-03 | Mesmo número em outro órgão | Identidade diferente sem ACL por cliente |
| E-04 | Requerimentos com mesmas palavras em ordem distinta | IDs de candidatos distintos |
| E-05 | Negação que altera conclusão administrativa | IDs de candidatos distintos |
| E-06 | Diferença apenas de caixa e espaços | Dedup exata sem duplicar candidato |
| E-07 | Requerimentos semelhantes de processos diferentes | Origens separadas e consulta transversal possível |
| E-08 | needs_more_evidence e nova fonte | Reabre PENDING com candidate_revision++ e histórico |
| E-09 | needs_more_evidence sem nova evidência | NEW_EVIDENCE_REQUIRED |
| E-10 | Novo operation_id sem mudança de evidência | NEW_EVIDENCE_REQUIRED |
| E-11 | Nova versão da fonte sintética | Nova revisão de evidência candidata |
| E-12 | Alteração do resumo após preview | BATCH_STALE_OR_PROCESS_MISMATCH |
| E-13 | Decisão preparada e nova origem | REVIEWED_CANDIDATE_CANNOT_CHANGE |
| E-14 | Seleção de 1 item em lote de 2 | Outro permanece pendente |
| E-15 | Decisão mista prepare_proposals/needs_more_evidence | Recibo por item e memória não aprovada |
| E-16 | Membro de outro processo no lote | BATCH_STALE_OR_PROCESS_MISMATCH |
| E-17 | Lote antigo após novo candidato/evidência | Rejeita prévia obsoleta |
| E-18 | Ação approve_qdrant solicitada ao lote | INVALID_REVIEW_DECISION |
| E-19 | Mesmo idempotency_key com resumo distinto | IDEMPOTENCY_CONFLICT |
| E-20 | Mesmo pedido com outro operation_id | Mesmo run sintético; replay |
| E-21 | Bytes diferentes do hash declarado | SOURCE_HASH_MISMATCH |
| E-22 | Reserva sem vínculo registrado | PROCESS_BINDING_NOT_REGISTERED |
| E-23 | Tentativa de reserva por outro operador sintético | OWNER_REQUIRED |
| E-24 | Após reopen, histórico de novas evidências | Readback preserva sequência sintética |
| E-25 | Revisão por lote e recuperação de recibo | Recibo detalhado, sem Qdrant |

A tabela é uma síntese temática de **25 cenários** dos **32 métodos executados**, não 25 testes adicionais. Consultar os logs/arquivo de teste para contagem exata.

## 5. Gates, dependências, limites e risco residual

| Gate | Resultado comprovado |
|---|---|
| E0 — HEAD/PR/base/permissão e CI anterior | **PASSOU** antes de cada escrita de branch |
| E1 — Revisões, contexto oficial e dedupe exata | **PASSOU** no laboratório sintético |
| E2 — Decisão por item e lotes obsoletos | **PASSOU** no laboratório sintético |
| E3 — Fingerprint calculado / idempotência | **PASSOU** na nova via sintética; reserva antiga continua por compatibilidade |
| E4 — CI no SHA técnico | **PASSOU: 218/218**, documentação e código sem produção |
| E5 — CI e readback no SHA final documental | **PENDENTE** após commit deste relatório; CI herdada do SHA técnico **FALHOU** |
| E6 — Cloudflare/portal humano/Back-end R06/Qdrant | **NO-GO / fora de escopo** |

**Riscos que permanecem bloqueantes:** event capture ainda não ligado ao processamento real do OCR/NOM; token de proprietário e origem dos dados não autenticados no laboratório; proposta em lote ainda não existe no portal R06 real; readback e linhagem Qdrant não ensaiados; UNKNOWN ainda exige reconciliação externa; paginação e retenção de lotes pendentes. **Nenhum dos 218 testes comprova esses comportamentos.**

**Segurança da prova:** `TemporaryDirectory` não é backup de produção; marcador DEMO não desidentifica dados por si; caso real exige LGPD, regras de minimização, evidências da origem, idempotência durável, audit trail, backup/restore e aprovação específica do titular. Aprovação documental e aprovação institucional da memória são eventos distintos. A coleta automática não exige clique por documento; a promoção de memória aprovada mantém revisão humana agrupada autenticada a ser implementada em gate autorizado.

## 6. Divergência de CI herdada — evidência negativa obrigatória

**Mesmo commit técnico `8387ceeda417e48014846311eb312a89b793bbad`:** Document MCP [run 44435007578](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435007578) **PASSOU**, com 218/218 testes sintéticos; workflow herdado [run 44435016347](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435016347) **FALHOU**. Dois jobs com falha:

- `R07 S7 pinned package and runtime attestation`, job `135261581509`: `dependency_install_version_locked=false`, `hash_locked_wheels=false`, resumo `pass=false`. Não confundir com defeito comprovado no módulo Document MCP; requer reconciliação de lock/pacote pelo responsável da baseline R07.
- `R07 S8 CycloneDX SBOM and public Python advisory audit`, job `135261581637`: `ValueError: SBOM_DRIFT_FROM_LOCK`. A concordância entre o SBOM e o requirements.lock não foi provada nesse runner.

**Análise de escopo:** diff G14-D `4f28b4b...` → G14-E `8387ceed...` alterou somente `g14c_disposable.py`, `process_learning.py`, `test_g14e_safety.py` e **CI própria Document MCP**. Nenhum Dockerfile, lock, SBOM ou fonte R06/R07 foi editado neste gate. Isso isola a natureza documental da divergência, mas **não substitui diagnóstico do owner do workflow herdado**.

**Decisão de fornecimento:** **NO-GO de integração/empacotamento global enquanto a CI herdada falhar**. Nenhum reparo em arquivos da R07 sem autorização específica; registrar pendência para o orquestrador, preservando o ramo G14-E e as evidências.

## 7. Rollback e próximo gate

**Rollback desta entrega:** reverter **apenas os commits G14-E desta branch** após reconferência de HEAD, preservando os commits anteriores da PR #7 e todo estado de R06/R07/legado. Nenhum restore de produção, backup Qdrant ou movimentação de documento é necessário para reverter o laboratório descartável.

**Próximo gate recomendado (G14-F, NÃO EXECUTADO):** revisão independente dos novos contratos e testes P1 remanescentes, especificar paginador/limites de lotes e adapter de eventos sintéticos; preparar matriz de interoperabilidade R06/R07 com `proposal_id`, `document_approval_ref`, `prior_point_id`, `kind`, `evidence_status` e readback itemizado. Qualquer alteração de R06/R07, serviço real, host autenticado, Qdrant ou integração/merge requer autorização separada.
