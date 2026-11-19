# G14-D — Auditoria de contratos e plano autenticado de revisão agrupada / Salvar memória R06-R07

**Versão documental:** 1.0.0 — parecer técnico, sem alterações de código.  
**Emissão aferida:** 2026-11-18T21:55:13-03:00; fuso `America/Sao_Paulo`; fonte: ferramenta de hora local do ChatGPT. O commit de publicação possuirá timestamp GitHub separado.  
**Repositório e branch de escrita:** `tight-knit-net/gaia-rag-mini`, `feat/gaia-document-mcp-isolado`, [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7) **Draft**, sem merge.  
**HEAD de auditoria:** `4e18c016e4ad144edd866751bb6c0fc07e8513d3`, prévia G14-C (relatório 16); [CI Document MCP 44425144782](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44425144782) **success** e [CI herdada R05/R07 44425144989](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44425144989) **success** nesse HEAD.  
**Fonte R06/R07 — somente leitura:** snapshot do ramo R07 `d40fa0d68f1636f68ac76a32db4a8b354ebf60d3`, em particular `src/gaia_rag_r05/review.py`, `src/gaia_rag_r05/institutional_memory.py`, `docs/projeto-executivo/R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md`, documentos S6/S7 e runbook. A documentação histórica R06/R07 **não comprova** o runtime autenticado atual.  
**Conectores:** catálogo Gaia_Rag___knowledge consultado para metodologia (skill listada, `skill_read` retornou vazio, sem confirmação de carregamento pelo host); GAIA_RAG legado consultado somente para contexto **aprovado histórico** do processo `GAIA-RAG-R06-ARQUITETURA-2026`; GitHub nativo é a fonte da PR/CI/código. Nenhum GitLab, Linear, Google Drive, Cloudflare, Qdrant, TestLab, banco real ou fornecedor acessado.  
**Trabalho autorizado/executado:** revisão estática de contratos, controles e testes históricos e elaboração deste documento; nenhuma execução adicional de testes, escrita de memória, alteração de schema/código/CI, migração ou publicação. 

## 1. Escopo, critérios de saída e parecer executivo

Este G14-D é uma **revisão independente e exclusivamente documental** de: (a) persistência descartável e estados; (b) concorrência e idempotência; (c) contexto dos processos administrativos com proprietário único; (d) revisão humana agrupada; (e) contrato futuro do botão **Salvar memória** e readback R06/R07.

**Parecer:** **GO DOCUMENTAL** para encerrar auditoria e priorizar correções futuras **somente na branch isolada**. **NO-GO TÉCNICO para integrar lote no R06, escrever Qdrant, usar documentos reais, publicar MCP, rebase/merge ou migrar.** A CI verde de 186/186 testes é evidência de regressão sintética, não elimina os gaps abaixo.

Respeitar o contexto do usuário: há **um único operador**, não clientes acessando o sistema. `client_id` é contexto/proveniência, `process_key` diferencia órgãos e números de processos administrativos, não ACL. O proprietário autenticado deve recuperar memórias aprovadas transversalmente, distinguindo fato do processo atual de analogias oriundas de outros processos. **Aprender automaticamente = capturar, classificar, comparar, recuperar e propor** sem clique para cada documento; **memória institucional aprovada = aprovação documental independente + revisão humana R06 autenticada + escrita Qdrant e readback**.

## 2. Estado AS-IS e evidências que PASSARAM

| Componente | Evidência observada no GitHub | Resultado/limite |
|---|---|---|
| SQLite descartável | `g14c_disposable.py`: `TemporaryDirectory`, `BEGIN IMMEDIATE`, CAS em `process_heads`, chave única `(process_key, request_key)`, recibos | **PASSOU na CI sintética**; sem SQL/efeito em produção |
| Concorrência | Dois requests concorrentes, replay, 409 e rollback pré-commit | **PASSOU na CI sintética**; sem CAS de ETag de fonte documental real |
| Aprendizagem provisória | `capture`, `working_context`, dedupe por `process_key`/tema, `preview_batches` | **PASSOU na CI sintética**; ligação com o fluxo OCR/NOM real **não demonstrada** |
| Revisão agrupada | `review_batch(prepare_proposals/needs_more_evidence)`, `batch_readback`, rejeição de membros errados | **PASSOU na CI sintética**; não é aprovação R06 |
| R06 documental e memória | `review.prepare`, `review_view`, `review.approve` com registro documental e CSRF | **Implementação de referência existente**, mas não integrada a lotes e não homologada aqui |
| R07 | `institutional_memory.preview`: duplicata, revisão, cobertura parcial e linagens sem escrita | Contrato consultado **somente em código**, não E2E real |
| Release/produção | PR #7 Draft; workflow de publicação congelado na CI anterior | Sem merge, deploy, Qdrant real ou operação externa |

**Medição de testes:** 49 contratos + 13 híbrido + 39 correlação + 39 aprendizagem + 46 G14-C = **186/186 aprovados no commit-base**, conforme run 44425144782. **0 testes novos executados no G14-D.** O conjunto de 15 casos abaixo é **planejamento**, não execução.

## 3. Matriz de achados com prioridade e evidência por linha

| ID | Prioridade | Achado comprovado por inspeção de código | Correção ou investigação recomendada | Evidência imutável |
|---|---|---|---|---|
| G14D-01 — **Complementação bloqueada** | **P1** | Após needs_more_evidence, status MORE_EVIDENCE_NEEDED_SYNTHETIC torna capture incapaz de aceitar novo material para o mesmo candidato (função aceita somente PENDING_HUMAN_REVIEW). | Desenhar revisão/rodada versionada com reabertura explícita, trilha antes/depois e novos hashes; nunca promover automaticamente. | [g14c_disposable.py L282–290](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L282-L290); [g14c_disposable.py L360–385](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L360-L385) |
| G14D-02 — **Dupla identidade sob mesma process_key** | **P1** | process_heads registra apenas process_key/revision; candidates possui process_id em cada linha, mas só compara IDs quando a deduplicação encontra mesmo topic_digest. Dois tópicos distintos podem mapear à mesma chave oficial e IDs internos incompatíveis. | Tabela de vínculo imutável process_key↔process_id, órgão/jurisdição/numeração; rejeitar associação contraditória em qualquer tópico. | [g14c_disposable.py L20–45](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L20-L45); [g14c_disposable.py L270–287](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L270-L287) |
| G14D-03 — **Falsa equivalência de conteúdos** | **P1** | Deduplicação utiliza SHA-256 da ordenação de tokens como conjunto: descarta ordem e frequência e não examina sujeito, ato, decisão ou status da evidência. Frases com mesmos termos mas relações distintas podem colapsar. | Usar fingerprint exato para idempotência + comparação semântica assistida apenas para sugestão; separar fato, alegação e decisão e manter todos os eventos/evidências. | [g14c_disposable.py L266–280](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L266-L280); [process_learning.py L29–41](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/process_learning.py#L29-L41) |
| G14D-04 — **Captura não integrada aos eventos reais** | **P1** | Método capture aceita event.status completed/review_required, sem exigir source_verified/document_sha256 observado; tests G14-C alimentam DocumentEvent sintético manualmente. Não existe roteamento operacional OCR/NOM/edição/move comprovado nesta branch. | Criar adaptador de eventos autenticados, outbox/reprocessamento e validação de proveniência, qualidade e aprovação documental, evitando promoção de texto bruto. | [g14c_disposable.py L251–268](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L251-L268); [test_g14c_disposable.py L29–42](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/tests/test_g14c_disposable.py#L29-L42) |
| G14D-05 — **Revisão em lote é integral e simulação** | **P1** | review_batch exige TODOS os candidatos pendentes de um processo, não permite aceitar/rejeitar subconjuntos ou diferenciar itens, e prepare_proposals não cria propostas R06 nem prova clique humano. | Projetar seleção explícita por item, revisão por lote versionada, recusa/complemento individual e comprovante servidor por proposta, sem dar permissão de escrita à LLM. | [g14c_disposable.py L352–393](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L352-L393) |
| G14D-06 — **Contrato de lote autenticado ausente na R06 consultada** | **P1** | review.py prepara, apresenta e aprova proposta individual; não fornece nessa interface um endpoint/fluxo de aprovação de múltiplos proposal_ids em um único ato auditado. | Definir contrato de lote com consentimento explícito para a lista de IDs/versões e submissão R06 serializada/idempotente; envolver orquestrador R06/R07 em implementação futura autorizada. | [review.py L109–147](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/src/gaia_rag_r05/review.py#L109-L147); [review.py L196–258](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/src/gaia_rag_r05/review.py#L196-L258) |
| G14D-07 — **Readback R06 precisa de cobertura documental explícita** | **P1** | O readback consultado confirma found, document_sha256, text, index_method e index_keywords; no bloco de comparação não estão explicitamente verificados namespace/process_id/source_ref/document_approval_ref/approved/approved_by do ponto. | Exigir validação de toda a ligação por item, ID estável, estado approved, namespace, processo, origem, SHA, autoria, timestamp e auditoria; corrigir somente pelo responsável R06/R07 em gate futuro. | [review.py L229–255](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/src/gaia_rag_r05/review.py#L229-L255) |
| G14D-08 — **Idempotência depende de fingerprint fornecido** | **P1** | SyntheticRequest aceita request_fingerprint externo; reserve o persiste/compara, mas não recalcula hash de ação, versão, fonte e payload a partir de dados autenticados. CAS apenas atualiza string process_heads no SQLite descartável. | Calcular fingerprint na fronteira backend a partir do envelope assinado/observado; separar idempotência de evento e revisão física com CAS/ETag do provedor. | [owner_concurrency.py L27–38](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/owner_concurrency.py#L27-L38); [g14c_disposable.py L127–204](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L127-L204) |
| G14D-09 — **Estado UNKNOWN sem reconciliação comprovada** | **P1** | mark_unknown altera estado; commit_revision bloqueia UNKNOWN e não existe reconciliador com prova remota de efeito. Correto falhar fechado, mas falta procedimento operacional de recuperação. | Projetar triagem de resultados desconhecidos usando readback e point_id/idempotency key determinísticos; evitar retry cego; rollback auditado. | [g14c_disposable.py L169–220](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L169-L220) |
| G14D-10 — **Snapshot do lote cobre só parte do conteúdo** | **P2** | _candidate_snapshot inclui candidate_id e JSON de origens/eventos, mas não summary, process_id, revisão, estado documental ou versão das políticas. Mudança fora desse trio pode deixar batch_id inalterado. | Fixar digest canônico de todo o payload exibido/decidido e policy_version; confirmar snapshot no clique autenticado. | [g14c_disposable.py L55–64](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L55-L64); [g14c_disposable.py L328–366](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L328-L366) |
| G14D-11 — **Consulta de lote sem paginação/cotas** | **P2** | preview_batches executa fetchall de todos os pendentes; working_context também não limita volume. Não há cursor, quota de anexos, TTL de candidaturas ou controle de cardinalidade do lote. | Adicionar limites, paginação/cursor estável, cobertura explícita, retenção e tamanho máximo por lote e por processo. | [g14c_disposable.py L309–352](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L309-L352) |
| G14D-12 — **Evidência real de identidade/durabilidade ausente por desenho** | **P2** | SyntheticOwnerOnly compara string de fixture; TemporaryDirectory e reabertura SQLite testam consistência local, não acesso Cloudflare, retenção criptografada, restore/backup de produção ou revisão humana R06. Prefixos FILE_DEMO/DEMO não desidentificam dados. | Manter NO-GO para documentos/clientes reais; validar autenticação do operador único, backups, retenção, LGPD, readback e fluxo R06 em gate operacional próprio. | [g14c_disposable.py L66–107](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L66-L107); [g14c_disposable.py L251–270](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L251-L270) |

**Contagem rastreável:** 12 achados, dos quais **9 P1** e **3 P2**. Trata-se de inspeção estática; as hipóteses de corrupção semântica e operações reais demandam os testes específicos planejados, sem tratar o cenário hipotético como incidente ocorrido.

## 4. Contrato TO-BE: aprendizagem híbrida e revisão agrupada

### 4.1 Domínios e estados separados

1. **Evento documental:** `event_id`, `document_id`, `source_ref`, `process_id`, `process_key`, `document_revision_id`, `source_sha256`, `evidence_status`, `kind`, `operation`, `origin_verified` e `observed_at`. Nunca transformar texto OCR ou instruções de documento em autorização de ferramenta.
2. **Candidato provisório:** `candidate_id`, `candidate_revision`, `source_refs`, `evidence_refs`, `origin_kind`, `summary` minimizada, `process_key`, `process_id`, `status=PENDING_REVIEW`. Captura automática e idempotente, com unicidade contextual, sem ponto Qdrant.
3. **Prévia de assimilação R07:** comparação com registros `approved=true` de processo exato e pesquisa transversal controlada; `kind`, `evidence_status`, `prior_point_id`, `source_ref`, cobertura da paginação, duplicata, possível revisão/supersessão e rótulo `ANALOGY_ONLY` para outros processos. O resultado **não aprova nem grava**.
4. **Aprovação do documento:** consultar registro documental confiável por `source_ref`/SHA/revisão/status; `document_approval_ref` obrigatório para cada proposta elegível. Aprovação documental e aprovação da memória são independentes.
5. **Proposta R06:** invocar `memory_prepare_after_approval(process_id,title,summary,source_ref,document_approval_ref,document_sha256,...)` **apenas** quando o gate documental for verdadeiro; R06 cria `proposal_id` e `review_url`, estado `pending`; nenhuma gravação Qdrant.
6. **Revisão agrupada:** pedido de lote com `batch_id`, `batch_revision`, `process_key`, lista fechada `(candidate_id,candidate_revision,proposal_id,source_ref,document_approval_ref,document_sha256)`, `policy_version`, `digest` canônico, validade e intenção por item `APPROVE/DECLINE/REQUEST_MORE_EVIDENCE`. R06 deve **validar tudo novamente no servidor** e oferecer preview transparente das decisões.
7. **Clique humano autenticado:** portal protegido com JWT Cloudflare Access válido do operador, origem e CSRF, texto claro **Salvar memória — Aprovar e gravar**; um gesto explícito pode autorizar o subconjunto selecionado **exatamente como exibido e versionado**. Nenhum MCP, LLM, nó OCR ou token cliente pode disparar esse efeito sozinho.
8. **Persistência e readback:** para cada item, usar point_id determinístico, sequência `pending → approving → approved` somente após PUT e readback; se falhar, `approving/UNKNOWN` com reconciliação (sem sucesso falso). Não copiar automaticamente o status de um item para o lote. Relatório de lote só `SUCCEEDED` quando TODOS itens selecionados têm readback e audit event; se parcial, `PARTIAL_RECONCILIATION_REQUIRED`, cada item mantendo seu estado.
9. **Recuperação futura:** apenas memórias aprovadas `approved=true`, identidade do proprietário validada, `namespace` e contexto de processo preservados; analogias identificadas; contexto pendente pode apoiar trabalho no **mesmo processo** sem ser verdade institucional.

### 4.2 Contrato mínimo proposto para a futura fronteira de lote — NÃO implementado

`BatchReviewIntent` imutável: `batch_id`, `batch_revision`, `process_key`, `actor_subject` (validado pelo backend), `items[]` com `proposal_id` e decisão, `content_digest`, `expiry`, `nonce`, `policy_version`. Não carregar bearer token, OCR bruto, PDF ou segredos no objeto. A comparação de digest deve cobrir os dados efetivamente exibidos e a versão do documento.

`BatchReviewReceipt` auditável: `batch_id`, `actor_subject`, `human_click_at`, `verified_origin`, `items[]` com `proposal_id`, `point_id`, `state`, `source_ref`, `document_sha256`, `document_approval_ref`, `readback_result`, `audit_ref`; `partial_failures`; `requires_reconciliation`. Um recibo de aprovação parcial **não** é comprovante de aprovação coletiva.

**Contrato existente R06 verificado:** `review.prepare` é por proposta, com revisão de registro documental e `review_url`; `review.approve` é browser-mediated, valida CSRF, altera ledger para `approving`, escreve ponto e faz `read_point` antes de marcar `approved`. Não foi encontrada interface de lote nesse módulo. Não instalar nem modificar isso nesta tarefa; encaminhar contrato para o responsável técnico R06/R07.

### 4.3 Compatibilidade e precauções

- G14-C **não** deve serializar candidatos pendentes como memória aprovada nem substituir o ledger R06. A captura automática é reusável; o ato humano não precisa ocorrer a cada documento, mas deve autorizar cada memória selecionada e seus hashes.
- O R07 possui função de previsão editorial com `prior_point_id`, `kind`, `evidence_status` e cobertura de paginação; o G14-C ainda não envia esses campos. Mapear contrato explicitamente sem copiar código da R07.
- O `process_key` inclui agência, jurisdição e número oficial, mas a R06 usa `process_id` exato. Manter mapa autenticado e inequívoco, sem converter números municipais em aliases de permissão.
- A R06 documenta `approved=true` e `namespace` em consultas do proprietário, sem filtro por cliente. Isso **não** autoriza usar boolean `approved` de fixture como prova real do banco.
- Conforme R07 S6/S7, `human_review_enabled=false` foi observado historicamente em preview da R06 e o destino operacional não foi homologado; **estado atual do serviço NÃO verificado**. O botão de produção permanece NO-GO até teste autenticado e readback.
- Antes de qualquer corte/integração, revisar divergência de branches, backup íntegro de SQLite/Qdrant, estado `pending/approving/approved`, comparação de fontes/IDs e rollback. Não reaproveitar URL/credencial de ambiente antigo.

## 5. Plano de testes NEGATIVOS e critérios do próximo gate — NÃO executados

| ID | Ensaio planejado com DEMO | Evidência esperada |
|---|---|---|
| D-T01 | Pedido de mais evidências → novo evento → nova versão → lote reapresentado | Mantém linhagem e permite nova decisão sem aprovar automaticamente |
| D-T02 | Mesmo process_key/órgão/número, outros process_id e tópicos diferentes | Bloqueia ligação contraditória sem impor ACL por processo |
| D-T03 | Frases com mesmo saco de palavras e decisões administrativas distintas | Não são mescladas como mesmo fato |
| D-T04 | Evento não verificado de OCR ou MOVE/RENAME simulado | Captura no máximo provisório, sem candidatura institucional elegível |
| D-T05 | Revisão agrupada com dois aprováveis e um que necessita complemento | Decisão por candidato com único gesto humano explicitamente conferido |
| D-T06 | Após prévia de lote, altera summary, documento, origem ou nova evidência | STALENESS/409 e novo snapshot requerido |
| D-T07 | Dois cliques concorrentes no mesmo batch_id/mesma revisão | Não gera duas aprovações nem dois pontos; recibo por item idempotente |
| D-T08 | Um item do lote falha após outros aprovados | Resultado parcial explícito, sem marcar lote inteiro como aprovado; reconciliação segura |
| D-T09 | Backend R06 recebe aprovação com token expirado/CSRF diferente | Nenhum novo ponto Qdrant, evento auditado e negativa |
| D-T10 | Readback omite namespace/process_id/source_ref/approved/doc_approval_ref | Item permanece indeterminado, não APPROVED |
| D-T11 | Mesmo idempotency_key com payload ou documento alterado | Conflito e nenhum reprocessamento irreversível |
| D-T12 | Candidatos pendentes, paginação parcial, múltiplos processos | Cobertura explícita, limites e analogias rotuladas, sem mistura |
| D-T13 | Memória já aprovada de outro processo com conteúdo similar | Recuperação transversal com rótulo ANALOGY_ONLY e proveniência |
| D-T14 | Processo administrativo municipal com numeração 000123/2026 vs 00123/2026 | Zeros preservados; não colapsar IDs nem inferir identidade |
| D-T15 | Backup corrompido ou restore mais antigo com proposta APPROVING | NO-GO e preservação do ledger anterior; não duplicar escrita |

**Matriz de aceite próximo gate:** corrigir em branch isolada os **P1** que cabem no Document MCP; adicionar testes determinísticos separados por dimensão com contagem por job/commit; rever integridade, paginação e status P2. Envolvimento do R06/R07 para novos contratos/botão exige **autorização explícita distinta** e não permite escrita neste ramo em outros projetos.

## 6. Gates, GO/NO-GO, dependências e rollback

| Gate | Evidência / decisão G14-D |
|---|---|
| D0 — HEAD/PR/base/CI anterior | **PASSOU:** PR #7 Draft, base conhecida, GitHub CI success no commit-base |
| D1 — Auditoria G14-C | **PASSOU como inspeção:** 12 achados classificados e linkados por código; **NO-GO para operação** |
| D2 — Contratos R06/R07 | **ANALISADO:** desenho da aprovação por proposta, documento, CSRF e readback; lote autenticado **PENDENTE** |
| D3 — Plano dos testes | **DOCUMENTADO:** 15 cenários sintéticos propostos, **0 executados neste gate** |
| D4 — Documentação isolada | **PENDENTE de commit/readback** no instante desta redação |
| D5 — Correção de código e CI novos | **NÃO EXECUTADO**; escopo desta auditoria é somente leitura+MD |
| D6 — Identidade real, botão, Qdrant e migração | **NO-GO**; ambientes/credenciais/autorizações externas fora do escopo |

**Riscos mais importantes:** falsos vínculos de processos municipais, deduplicação não semântica, complementação de evidências interrompida, lote com escolhas implícitas, estado de escrita ambíguo e readback incompleto. **Não declarar automaticamente 186 testes = homologação operacional.**

**Rollback documental:** reverter somente o commit desta auditoria (dois arquivos MD: relatório 17 e índice), se necessário, após reconfirmar HEAD. Nenhum dado de negócio, fila real, workflow de produção, Qdrant, Drive, DNS, Cloudflare, TestLab, R06, R07 ou `main` deve ser afetado.

**Próximo gate recomendado:** **G14-E — saneamento de P1 com novos testes exclusivamente sintéticos** no ramo Document MCP. Escopo obrigatório: transições de revisão, vínculos oficiais, fingerprint semântico/qualidade de origem, interface de lote versionada e paginação. **NÃO executar integração real R06/R07, Cloudflare ou Qdrant nesse gate**; primeiro critérios e autorização específica do titular.

## 7. Fontes e evidências

- [Relatório G14-C](16_GATE_G14C_TRANSACOES_APRENDIZAGEM_REVISAO_AGRUPADA.md) e [índice do Document MCP](README.md).
- [GitHub Actions Document MCP (186/186 sintéticos)](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44425144782); [CI R05/R07 no commit-base](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44425144989).
- [g14c_disposable.py L20–404](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/g14c_disposable.py#L20-L404); [process_learning.py L44–221](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/process_learning.py#L44-L221); [owner_concurrency.py L25–147](https://github.com/tight-knit-net/gaia-rag-mini/blob/4e18c016e4ad144edd866751bb6c0fc07e8513d3/gaia_document_mcp/owner_concurrency.py#L25-L147).
- [review.py L109–255](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/src/gaia_rag_r05/review.py#L109-L255); [institutional_memory.py L54–163](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/src/gaia_rag_r05/institutional_memory.py#L54-L163); [R07_S6_AUDITORIA_SEGURANCA_COMPATIBILIDADE_2026-11-18.md L14–58](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/docs/institucional/R07_S6_AUDITORIA_SEGURANCA_COMPATIBILIDADE_2026-11-18.md#L14-L58); [R07_S7_RELATORIO_PRONTIDAO_EMPACOTAMENTO_2026-11-18.md L14–35](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/docs/institucional/R07_S7_RELATORIO_PRONTIDAO_EMPACOTAMENTO_2026-11-18.md#L14-L35).
- [Decisão R06: memória unificada com operador autenticado](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/docs/projeto-executivo/R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md); [runbook R07 autenticado](https://github.com/tight-knit-net/gaia-rag-mini/blob/d40fa0d68f1636f68ac76a32db4a8b354ebf60d3/docs/institucional/RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md).

## 8. Checkpoint de fechamento documental — aditivo v1.0.1

**Aferição:** 2026-11-18T21:59:06-03:00, `America/Sao_Paulo`, origem: relógio local da ferramenta de tempo do ChatGPT.  
**Publicação da versão inicial do documento:** commit `05ed5c6523f62c04c45e3ccfac1c2bfc6cc292a3`, GitHub `2026-11-19T00:58:01Z` (18/11/2026 às 21:58:01, BRT). O SHA do commit que acrescenta este checkpoint será referência independente.

**D0 — HEAD/PR:** [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7) conferida `Draft`, sem merge, base `feat/r07-office-knowledge-assimilation`, head `05ed5c6523f62c04c45e3ccfac1c2bfc6cc292a3` antes do aditivo. **PASSOU**.

**D1 — auditoria:** 12 achados (9 P1, 3 P2), com linhas/links por fonte e classificação documental; inspeção estática, nenhum cenário adversarial novo executado. **PASSOU COMO AUDITORIA**, com **NO-GO OPERACIONAL** até saneamento.

**D2 — revisão R06/R07:** conferidos `review.prepare`, `review.approve` e readback por proposta, além de `institutional_memory.preview`; **não existe prova de endpoint/portal de revisão agrupada autenticada** neste gate. **PENDENTE DE CONTRATO E GATE DO RESPONSÁVEL R06/R07**.

**D3 — plano:** 15 casos novos propostos (D-T01–D-T15), **0/15 executados**, sem somar casos planejados à CI anterior. **DOCUMENTADO**.

**D4 — isolamento documental:** readback da versão inicial confirmou relatório novo com 12 achados e 15 testes e índice atualizado; comparação com `4e18c016e4ad144edd866751bb6c0fc07e8513d3` identificou **somente 2 arquivos MD** alterados. **PASSOU**.

**CI no commit documental inicial:** [GAIA Document MCP run 44433235301](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44433235301) **success**; logs: 49 + 13 + 39 + 39 + 46 = **186/186 testes sintéticos anteriores**. [CI herdada R05/R07 run 44433235295](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44433235295) **success** no mesmo SHA. Não houve novo teste de integração com provedores reais.

**D5:** nenhuma implementação/correção no G14-D. **NÃO EXECUTADO, POR ESCOPO**.

**D6:** Cloudflare Access real, aprovação agrupada efetiva, Qdrant, migração e botão no host real **NÃO TESTADOS**. **NO-GO**.

**Parecer de encerramento:** **GO para relatório G14-D e planejamento do G14-E de saneamento P1**, exclusivamente no ramo documental. **NO-GO para ativação, integração R06/R07, merge/deploy ou gravação Qdrant.**

**Rollback:** reverter somente a documentação G14-D no ramo autorizado após checagem de HEAD; os componentes de execução e os registros externos permanecem intocados.
