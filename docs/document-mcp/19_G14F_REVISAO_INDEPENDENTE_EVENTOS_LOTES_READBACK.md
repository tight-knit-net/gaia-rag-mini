# G14-F — revisão independente: G14-E, P1 remanescentes, lock/SBOM e contratos sintéticos

**Versão:** 1.0.0 — relatório de auditoria técnica e ensaio de contratos; **não é homologação operacional**.  
**Instante de emissão aferido:** 2026-11-18T22:30:53-03:00, fuso `America/Sao_Paulo`; origem do relógio: ferramenta de tempo local do ChatGPT. Metadados de commits e execuções GitHub são fontes independentes de data de publicação.  
**Escopo exclusivo de escrita:** `tight-knit-net/gaia-rag-mini` → `feat/gaia-document-mcp-isolado`, [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7) Draft. Sem merge/rebase/deploy.  
**Baseline de abertura:** `95c6a60a18a0c4e78a29bbc97a27394e296124a9`, base PR R07 `6aa55823082842bbe4799773a8acfc2e4eebdea1`.  
**Commit de contratos e testes:** `100f13a00b4e6cf5d1812e29212190a614f50576`.  
**Fontes e conectores:** GitHub (HEAD, PR, diff e logs Actions), catálogo de skill `Gaia_Rag___knowledge` (metodologia listada, porém leitura de SKILL.md retornou conteúdo vazio; host não comprovou carregamento), GAIA_RAG legado (memória histórica aprovada, processo `GAIA-RAG-R06-ARQUITETURA-2026`, **não estado vivo**), relatório 18. Nenhum acesso a GitLab, Linear, Google Drive, Cloudflare, serviço real R06/R07, Qdrant ou TestLab. A comparação de commits de **base** foi somente leitura.  
**Dados e ambiente dos testes:** somente fixtures fictícias em GitHub Actions, sem bancos operacionais, LLM externo, clientes ou gravação real.

## 1. Escopo, critérios e parecer

**Objetivo:** conferir G14-E de forma independente e preparar interfaces sintéticas para eventos documentais, paginação verificável de prévias de lote, readback itemizado de R06 e decisão segura diante de estados de efeito desconhecido. Nenhum dos novos helpers conecta ao servidor OCR, à Prefeitura, ao portal R06 ou à base Qdrant.

**Recomendação:** **GO para contratos sintéticos de G14-F; NO-GO para integração real** enquanto os P1 de fronteira confiável, aprovação em lote, readback e reconciliação externa permanecerem. O sistema tem **um operador autenticado** no destino; `process_key` identifica contexto, órgão, município e número oficial do processo, não permissão por cliente. A recuperação transversal do operador sobre memórias aprovadas deve distinguir casos análogos de fatos próprios do processo atual.

## 2. Diagnóstico causal da oscilação de lock/SBOM — com SHA do merge virtual

| Observação | Execução com falha | Execução com sucesso |
|---|---|---|
| Workflow herdado | [44435016347](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435016347) `failure` | [44435537188](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435537188) `success` |
| Evento | `pull_request`, checkout de `refs/pull/7/merge` | `pull_request`, checkout de `refs/pull/7/merge` |
| Head da PR | `8387ceeda417e48014846311eb312a89b793bbad` | `95c6a60a18a0c4e78a29bbc97a27394e296124a9` |
| SHA do merge efetivamente executado | `436b911f88de9e99f4ec49287e1263b869145d10` | `4e4bd5ef76c398ea5ee932d14e5509cdafd99af2` |
| Base R07 do merge | `05ff8b10a1ff2a645a755af765eec3b1372b4507` | `55d6e0642bec215bf3b0dff110854fbded4e035c` |
| S7 atestação pacote | `dependency_install_version_locked=false`; `hash_locked_wheels=false` | Build com `pip install --require-hashes` aprovado |
| S8 validação SBOM | `ValueError: SBOM_DRIFT_FROM_LOCK` | SBOM/revalidação e auditoria aprovaram |
| Hash do requirements.lock reportado | `bb2aacbc1249159b1625222731a443e86b73e65fca32b056d6c4f4188efe3903` | **O mesmo SHA-256** |

**Comparação somente leitura das duas bases** (05ff8b10 → 55d6e064): **4 commits / 4 arquivos**, precisamente `docs/institucional/R07_SBOM_PYTHON_LOCK_S8.cdx.json` (modificado), `scripts/r07_s7_package_preflight.py` (modificado), `scripts/r07_s9_os_audit.py` (adicionado) e `tests/test_r07_s9_os_audit.py` (adicionado). Nenhuma alteração em `requirements.lock` apareceu nessa comparação.

**Conclusão causal sustentada:** a diferença de resultados é explicada pelo **código e SBOM diferentes do merge virtual por avanço da base R07**, não por alteração feita na nossa branch ao lock. Não concluir que os scripts herdados são estáveis sob toda base futura; o workflow `pull_request` deve documentar explicitamente `head_sha`, `base_sha`, `merge_sha`, blob hash do lock, SBOM e script antes do aceite. **Não modificar nem tentar corrigir a R07 neste projeto.**

## 3. Matriz de auditoria independente

| ID | Prioridade | Estado | Evidência / interpretação | Próxima providência |
|---|---|---|---|---|
| **F-01** | P1 | PENDENTE DE INTEGRAÇÃO | G14D-04: nenhum adaptador provado para publicação real de eventos OCR/NOM/edição/movimentação; o novo event_contract_preview valida apenas fixture observada, sem ingest nem outbox. | [capture](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L341-L465); [protótipo F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py) |
| **F-02** | P1 | BLOQUEADO POR ESCOPO | G14D-06: review_batch_items é simulação local com decisões prepare_proposals/needs_more_evidence; portal humano R06 não foi integrado nem alterado. | [lotes](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L505-L590) |
| **F-03** | P1 | BLOQUEADO POR ESCOPO | G14D-07: não existe readback Qdrant autenticado para cada proposal_id/point_id/approved/source_ref neste ramo; verificação F de recibo fictício não é prova externa. | [contrato simulado](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py) |
| **F-04** | P1 | PENDENTE DE OPERAÇÃO | G14D-09: UNKNOWN_SYNTHETIC permanece sem reconciliador de provedor; novo contrato apenas prescreve READBACK_AND_RECONCILE e proíbe retry automático. | [G14C](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L277-L317); [F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py) |
| **F-05** | P1 | ACHADO NOVO | O caminho reserve_from_event não incorpora expected_revision no fingerprint; reserve reencontra chave existente e compara apenas fingerprint, retornando replay mesmo quando expected_revision mudou. A regra de versão só é verificada para requisição nova. | [reserva e replay](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L186-L211); [fingerprint](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L218-L253) |
| **F-06** | P1 | RISCO NÃO HOMOLOGADO | O marcador de nova evidência e a flag de review provêm de DocumentEvent fornecido pelo chamador do laboratório; não há emissão autenticada do dado observado. Mudança de declaração de revisão pode ser confundida com mudança probatória real. | [marcador](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L94-L105); [captura](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L341-L425) |
| **F-07** | P2 | CONTRATO SINTÉTICO PRONTO | G14D-11: novo paginador realiza snapshot, limite, cursor por offset e prova de cobertura sobre coleção já carregada; porém o SQLite G14C ainda usa fetchall e não controla quota/TTL do armazenamento. | [paginador F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py); [G14C](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/g14c_disposable.py#L472-L505) |
| **F-08** | P2 | LIMITAÇÃO EXPLÍCITA | O recibo sintético compara os campos esperados e aprovação declarada; não verifica assinatura/CSRF/JWT, origem do registro ou autoridade do serviço que forneceu observed. | [readback F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py) |
| **F-09** | P2 | PENDENTE | Operador único em fixture String, não Cloudflare Access; o process_id é contexto administrativo e jamais ACL por cliente. Sem prova real de auth, retenção ou backup. | [SyntheticOwnerOnly](https://github.com/tight-knit-net/gaia-rag-mini/blob/95c6a60a18a0c4e78a29bbc97a27394e296124a9/gaia_document_mcp/process_learning.py#L95-L107) |
| **F-10** | P2 | EXPLICADO POR BASE MÓVEL | Falha S7/S8 na CI PR usou merge de base 05ff8b10; sucesso usou 55d6e064. Diferença de quatro arquivos no ramo-base, com SBOM e script S7 atualizados; mesmo requirements.lock SHA reportado. | [run falho](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435016347); [run aprovado](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44435537188) |

**Total auditado:** 10 pontos de atenção: **6 P1** e **4 P2**, sendo quatro P1 de integração já conhecidos (G14D-04/06/07/09) e dois P1 adicionais de consistência/autenticidade dos metadados. A classificação é técnica e preventiva, **não afirma incidente operacional ou manipulação real**. Permanecem também as restrições de migração, backup e homologação R07/R06.

## 4. Contratos preparados, sem integração externa

| Artefato | Contrato mínimo | O que NÃO comprova |
|---|---|---|
| `SyntheticSourceObservation` + `event_contract_preview` | Confronta `process_id`, `process_key`, `source_ref`, `source_version`, SHA do original e bytes fictícios antes da prévia de assimilação OCR/NOM; rejeita OCR mock/falha; saída sem corpo de documento nem comando de memória | Observação é **fixture**; sem autenticação de fonte ou consumidor real, sem consumo de eventos e sem captura automática operacional |
| `synthetic_batch_page` + `verify_synthetic_coverage` | Limite de 1–25, offset, digest canônico, contagem, ordenação e cobertura de todas as páginas de um snapshot sintético, rejeitando páginas duplicadas, incompletas ou obsoletas | Ainda não pagina SQL por cursor e não prova cobertura R06/Qdrant |
| `synthetic_readback_contract` | Compara `point_id`, `namespace`, `process_id`, `source_ref`, `document_sha256`, `document_approval_ref`, `proposal_id`, `approved_by`, `approval_event_ref`, e exige `approved=true` declarado na fixture | Não verifica JWT/CSRF/click ou ponto Qdrant real; retorno contém `real_qdrant_readback=false` |
| `synthetic_unknown_decision` | Em `UNKNOWN_SYNTHETIC`, somente `READBACK_AND_RECONCILE` sem retry; outros estados não permitem efeito externo automático | Não resolve conflito remoto nem executa rollback real |

**Fontes executáveis de teste:** [módulo G14-F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/gaia_document_mcp/g14f_contracts.py), [32 testes G14-F](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/tests/test_g14f_contracts.py), [workflow CI da branch](https://github.com/tight-knit-net/gaia-rag-mini/blob/100f13a00b4e6cf5d1812e29212190a614f50576/.github/workflows/gaia-document-mcp-isolated-ci.yml).

**Gate de revisão humana futura (não implementado):** pacote de `BatchReviewIntent` versionado com `batch_id`, `batch_revision`, digest do conteúdo exibido, propostas e decisões individuais; aprovação documental deve estar verificada; portal autenticado pelo operador valida identidade e CSRF, clique explícito sobre subconjunto, leitura de volta **por proposta/ponto**, e recibo `SUCCEEDED/PARTIAL_RECONCILIATION_REQUIRED` por item. Nenhum candidato é promovido apenas por similaridade ou por leitura OCR. O fluxo manual Salvar memória permanece preservado.

## 5. Evidência de teste e limites

**CI do commit técnico `100f13a00b4e6cf5d1812e29212190a614f50576`:** [run 44437266092](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44437266092) `success`. Logs: 49 contratos v2 + 13 híbrido OCR/NOM + 39 correlação + 39 G14-B + 46 G14-C + 32 G14-E + **32 G14-F** = **250/250 testes sintéticos PASSOU**.

**Não houve** E2E autenticado, dados de cliente, portal R06, instalação de outra skill no host, migração de Qdrant, execução contra OCR/NOM externo, SQL de produção ou deploy. É **errado** chamar os 32 testes novos de testes reais de R06 ou do storage.

A CI herdada da base R07 pode avaliar um merge virtual distinto do código HEAD deste documento; seus resultados devem sempre ser reportados com a base/merge efetivos.

## 6. Gates e decisão

| Gate | Evidência | Status |
|---|---|---|
| F0 — branch, PR, base, CI anterior | GitHub preflight `95c6a60a18a0c4e78a29bbc97a27394e296124a9` e PR #7 Draft; dois workflows `success` | **PASSOU** |
| F1 — revisão independente dos achados G14-E | Matriz de 6 P1 e 4 P2 com fontes estáticas | **PASSOU como auditoria** |
| F2 — lock/SBOM e comparação merge virtual | Dois runs, SHAs de merge/base e quatro arquivos divergentes | **PASSOU como diagnóstico de provenance**, sem mudança R07 |
| F3 — contratos de eventos/lotes/readback | Helpers novos **sem efeitos externos**, 32 testes | **PASSOU em CI sintética** |
| F4 — regressão v2 e núcleo Document MCP | 250/250 no commit técnico | **PASSOU** |
| F5 — commit documental / readback / CI no HEAD final | Verificar depois da publicação | **PENDENTE neste texto inicial** |
| F6 — E2E autenticado, R06, Qdrant, deploy, migração | Fora do escopo e sem gate humano | **NO-GO** |

**Parecer G14-F:** **GO para fechar a auditoria sintética e preparar o próximo contrato; NO-GO operacional.** Não deduzir aprovação humana da prévia, do flag `approved` em fixture, de testes verdes ou de um recibo SQLite.

## 7. Próximo gate, dependências e rollback

**Recomendação G14-G — especificação/correções adicionais de concorrência e fonte, somente na nossa branch:** atacar primeiro F-05 com teste negativo que vincule `expected_revision` ao fingerprint de reserva/replay; F-06 com origem/evidência atestada, não somente campos controlados pela fixture; adicionar paginação persistente e limites em SQLite descartável, sem conectar R06. **Só então** propor ao titular separadamente contrato do operador humano autenticado e de lotes R06/R07, sem modificar R06/R07 por iniciativa da PR #7.

**Gate de integração R06/R07 futuro, exigindo autorização distinta:** preservar `approved=true`, namespace, `process_id`, linhagem, dedupe, revisão humana por lote e readback com `source_ref`, `document_sha256`, `document_approval_ref`, autor e timestamp verificados; backups de Qdrant e rollback comprovados; legado preservado. Não autorizar merge/deploy/corte por CI verde.

**Rollback do G14-F:** reverter apenas módulo `g14f_contracts.py`, `test_g14f_contracts.py`, mudanças na CI própria, relatório 19 e índice, mediante checagem de HEAD e sem tocar em R06/R07. Nenhum restore externo necessário, porque nenhum dado operacional foi escrito.

**Publicação documental:** `docs/document-mcp/19_G14F_REVISAO_INDEPENDENTE_EVENTOS_LOTES_READBACK.md`. Fonte canônica de estado após publicação: commit GitHub + readback da PR, não este texto sozinho.
