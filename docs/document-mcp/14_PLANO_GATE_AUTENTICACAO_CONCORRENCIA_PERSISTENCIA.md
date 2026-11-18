# GAIA Document MCP — plano do próximo gate P0/P1: autenticação, concorrência e persistência

**Versão:** 1.0.0 — PLANO PARA APROVAÇÃO, não implementação.  
**Data/hora de emissão aferida:** 2026-11-18T20:28:11-03:00; fuso `America/Sao_Paulo`; origem do relógio: ferramenta de horário local do ChatGPT. A data do commit GitHub, se publicado, é uma segunda evidência e não é confundida com a aferição.  
**Área exclusiva de escrita:** `tight-knit-net/gaia-rag-mini` → `feat/gaia-document-mcp-isolado`; PR [#7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7), **Draft**, base `feat/r07-office-knowledge-assimilation`.  
**Baseline viva inspecionada:** `b68e2c928ebf8a7b0fc482d1b5d67b061cf3c2a0`. **Nenhum código e nenhum schema existentes serão editados neste gate de planejamento.**  
**Projeto de origem:** GDL-BC01/D1, GitLab `gaia_workspace1/gaia-doclab`, baseline documental ref SHA `2493f659866e16bd6499c9122e488d54d612a81d`; referência lida em relatórios 11 e 12.  
**Fontes normativas externas verificadas:** [MCP 2026-07-28 — autorização](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [MCP — considerações de segurança](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations), [PostgreSQL — isolamento transacional](https://www.postgresql.org/docs/current/transaction-iso.html).  
**Conectores:** catálogo e leitura da skill disponíveis em `Gaia_Rag___knowledge` (identificação de metodologia, não estado operacional); `GAIA_RAG` legado consultado para contexto aprovado, sem substituir GitHub. Fonte de verdade do estado do código: conector GitHub.  
**Classificação:** documento técnico interno, sem dados confidenciais ou documentos integrais de clientes.

## 1. Escopo, risco central e decisão recomendada

**Recomendação:** planejar um **gate de contratos de fronteira confiável em ambiente inteiramente sintético**, sem levantar novo servidor MCP, banco, OAuth, Cloudflare Access, serviço OCR, iLoveAPI/Groq ou storage. Só depois de receber aprovação específica para desenvolvimento desse gate, elaborar um adaptador backend isolado dentro da mesma branch. O primeiro incremento deverá ser reutilizável e mínimo; evitar replicar a infraestrutura grande do DocLab.

**Objetivo funcional futuro:** uma requisição documental poderá gerar somente uma prévia se o ator e seu escopo tiverem sido autenticados por um serviço confiável, a versão atual do arquivo/revisão tiver sido observada e confirmada, e a chave de idempotência tiver comportamento transacional comprovado. Nem uma prévia validada nem um recibo salvo aprova conteúdo documental ou autoriza Qdrant.

**Riscos bloqueantes:** confiança equivocada em `allowed_scope` de requisição; confusão entre `client_id=NNN`, `tenant` OCR e autorização; `ObservedRevision` fornecido por cliente em vez de readback autenticado; colisão entre `event_key` e `idempotency_key`; sucesso falso após timeout de provider; aprovação humana simulada por HMAC. Por esses motivos, este documento é **GO apenas para revisão do planejamento; NO-GO para operação**.

## 2. Inventário AS-IS (somente leitura)

| Artefato | Contrato existente | Lacuna relevante |
|---|---|---|
| [correlation.py](../..//gaia_document_mcp/correlation.py) | LogicalDocument, RevisionSnapshot, ObservedRevision, CorrelationPreview, SyntheticIdempotencyLedger | `allowed_scope` e observações são dados sintéticos; ledger é dicionário RAM |
| [contracts.py](../../gaia_document_mcp/contracts.py) | DocumentSource, DocumentEvent, evidence SHA e fingerprint de evento | `source_version` não é ETag observado por backend; hash recebido exige bytes verificados |
| [trust.py](../../gaia_document_mcp/trust.py) | ReviewProofVerifier apenas **verifica** HMAC | Sem servidor emissor, identidade, ACL, registro documental e revogação |
| [pipeline.py](../../gaia_document_mcp/pipeline.py) | memory_preview sem escrita Qdrant; recibos em RAM | Não há R07 real, workflow R06, DB ou aprovação de memória |
| [settings.py](../../gaia_document_mcp/settings.py) | flags fail-closed, direct_qdrant_write false | Feature flag não equivale a autorização por ator/recurso |
| [test_correlation_gate.py](../../tests/test_correlation_gate.py) | 39 testes sintéticos em CI do HEAD anterior | Sem auth E2E, concorrência real e recuperação pós-crash |
| [matriz 11](11_MATRIZ_REAPROVEITAMENTO_GDL_BC01_MCP_V2.md) / [mapa 12](12_MAPA_CONTRATOS_SCHEMAS_TESTES_GDL_BC01.md) | 32 requisitos BC01 e 13 negativos históricos mapeados | Planejamento não incorpora automaticamente GDL-DS nem o banco do DocLab |

**Referências de requisitos:** `GDL-RQ-003` jobs/checkpoint; `GDL-RQ-009` origem; `GDL-RQ-012` rastreabilidade; `GDL-RQ-020` autoridade por revisão; `GDL-RQ-022` concorrência; `GDL-RQ-025` idempotência SQL/artefato; `GDL-RQ-026` isolamento; `GDL-RQ-028` evidências; `GDL-RQ-029` versões. A GDL-BC01 D1 é fonte documental, não homologação operacional.

## 3. Matriz de requisitos propostos

| ID | Prioridade | Requisito mínimo proposto | Evidência para aceitar |
|---|---|---|---|
| AUTH-01 | P0 | Identidade de ator autenticada por autoridade confiável, com subject, issuer, audience/resource, validade temporal e escopos; rejeição fail-closed | Negativas token ausente/expirado/falso/issuer-audience incorretos |
| AUTH-02 | P0 | Autorizar **por documento e processo**, não por `NNN` ou `tenant`; preservar leitura transversal legitimada do proprietário autenticado sobre memórias **aprovadas** como domínio distinto | Negativas cross-client, cross-process e permissão insuficiente |
| AUTH-03 | P0 | Validar no servidor credencial para o recurso MCP, sem token passthrough a OCR, Drive ou Groq; segredos nunca no GitHub/logs | Testes de audience, isolamento de credenciais e disclosure desabilitado |
| AUTH-04 | P0 | Diferenciar permissões de preview, criação de derivado, publicação, assinatura e preparação de memória; exigir decisão explícita por efeito | Matriz de ações e negações para cada capacidade; execução real permanece proibida |
| REV-01 | P0 | Identidade estável `document_id` e `revision_id` distinta de `event_key`; readback de versão/ETag na fronteira confiável | Contratos e rejeição de revisão obsoleta |
| CONC-01 | P0 | Atualização condicionada a versão observada (`If-Match` onde suportado, ou CAS em banco). Conflito 409 sem sobrescrita | Dois operadores concorrentes, apenas um avanço; original preservado |
| CONC-02 | P1 | Reconciliar timeout, falha, resultado desconhecido, duplicação de webhook e retries; nunca confirmar write por HTTP 200 isolado | Recibo, hash, estado remoto real e testes de falha |
| PERS-01 | P0 | Chave de idempotência por `(namespace/scope, request_key)` com fingerprint imutável; `operation_id` e `event_key` não substituem o identificador da requisição | Mesmo pedido → replay; mesmo key/payload diferente → 409 |
| PERS-02 | P1 | Persistir recibo mínimo, estado de job, transições e tentativas em transação com restrição de unicidade e readback | Crash/restart/retry e concorrência sem dupla publicação |
| PERS-03 | P1 | Quarentena de payload sensível; não armazenar OCR integral, credenciais, PDF, token ou dado de cliente no registro de memória | Inspeção de logs/serialização e retenção mínima por finalidade |
| PERS-04 | P1 | Definir política de retenção/TTL, trilha de auditoria, backup/restore e rollback **antes da produção** | Restore com hash e contagem verificados em ambiente isolado, mediante autorização posterior |
| GOV-01 | P0 | Aprovação documental R06 e aprovação específica de memória R06 continuam eventos independentes; somente R07 compara candidatos aprovados | Negativas sem clique humano, fonte incompleta, mock OCR e conflito |
| GOV-02 | P0 | Manter `main`, R05/R06/R07, GitLab DocLab, NOM/OCR irmãos, Qdrant e provedores como leitura ou fora do escopo | Diff do commit futuro limitado ao ramo próprio; nenhum deploy |

**Nota de arquitetura:** usar mecanismo de identidade já homologado **se e quando existir e for autorizado**, não instalar outro provedor. Não decidir hoje por Cloudflare Access, Auth0 ou um banco novo apenas pela conveniência de desenvolvimento. Para a persistência, avaliar reaproveitar **apenas mediante inventário e autorização** um PostgreSQL existente com namespace/schema separados; o planejamento não concede acesso à instância.

## 4. Contratos de interface futuros (não são endpoints implementados)

- `VerifiedPrincipal`: `subject`, `issuer`, `resource/audience`, `grants`, `verified_at`, `auth_context_id`; construído **somente pelo middleware confiável**, jamais por JSON do usuário/LLM/OCR. Não transportar bearer token dentro de DocumentEvent.
- `AuthorizedDocumentScope`: `document_id`, `client_scope`, `process_id`, `actions`, `policy_version`; derivado de ACL e identidade reais, sem inferência de NNN.
- `ObservedSourceRevision`: `document_revision_id`, `source_ref`, `source_version/etag`, `source_sha256`, `observed_at`; resposta verificada da fonte autorizada, distinta de `ObservedRevision` sintética.
- `IdempotentRequest`: `scope`, `idempotency_key`, `request_fingerprint`, `requested_effect`, `operation_id`, `expected_revision`; chave por escopo e sem enviar documento bruto.
- `DurableReceipt`: `run_id`, `attempt_id`, `state`, `committed_at`, `source_version_after`, `readback_proof_ref`, `external_effect`, `document_approval_ref`; usar `PENDING/COMMITTED/UNKNOWN/FAILED` como estados distintos. O estado `UNKNOWN` nunca é sucesso automático.
- `MemoryProposal`: somente prévia/síntese mínima, `approved=false` até revisão R06 autenticada e clique humano; sem operação direta Qdrant nesta branch.

**Ciclo proposto:** autorização servidor → leitura do documento e versão atuais → validação SHA → reserva transacional da idempotency_key → processamento em sandbox → recibo/intent → confirmação do efeito se autorizado → readback e reconciliação → resposta. Em falha do provedor, persistir `UNKNOWN`/pendente de reconciliação (quando durabilidade existir); nunca disparar efeito não idempotente automaticamente no retry.

## 5. Plano de 23 testes sintéticos FUTUROS (0 executados neste gate)

**Dados:** IDs e clientes `DEMO_001`, `DEMO_002`, credenciais efêmeras fictícias, PDF mínimo artificial, snapshots em memória ou DB descartável ainda não autorizado. Nenhum arquivo real, OCR bruto de clientes, endpoint remoto ou credencial ativa. Os testes abaixo são **propostas**, não testes presentes na CI.

| Caso | Cenário sintético | Resultado esperado |
|---|---|---|
| AUT-01 | Nenhum token | UNAUTHENTICATED (401); nenhuma consulta de documento |
| AUT-02 | Token expirado ou assinatura inválida | UNAUTHENTICATED (401); sem fallback para NNN |
| AUT-03 | Token de issuer/audience/resource diferente | UNAUTHENTICATED (401); não aceitar token passthrough |
| AUT-04 | Sujeito autenticado sem escopo de leitura do documento | FORBIDDEN_CLIENT_SCOPE (403); não revelar metadados de outro cliente |
| AUT-05 | NNN do arquivo coincide, mas client_scope autenticado não coincide | FORBIDDEN_CLIENT_SCOPE (403), mesmo com SHA correto |
| AUT-06 | OCR tenant coincide, mas process_id não autorizado | CASE_BINDING_MISMATCH ou FORBIDDEN (403) |
| AUT-07 | Escopo autenticado e recurso permitidos em fixture | PREVIEW_ONLY; sem aprovação documental ou de memória |
| CON-01 | If-Match/expected_revision diferente da versão atual | REVISION_CONFLICT (409); original inalterado |
| CON-02 | Dois requests concorrentes para uma mesma revisão | Apenas um avanço da revisão; outro 409; sem overwrite |
| CON-03 | Duas revisões independentes de documentos diferentes | Sem colisão nem bloqueio transversal indevido |
| CON-04 | Mesma requisição repetida após mudança do event_revision | Mesmo request_fingerprint; não duplicar operação |
| CON-05 | Leitura da versão remota falha/time-out | FALHA_FECHADA, não supor versão/etag válida |
| CON-06 | Atualização remota falha após reserva local | RECONCILIATION_PENDING; sem afirmar sucesso |
| PST-01 | Mesma idempotency_key e mesmo payload no mesmo escopo | Mesmo run_id e recibo, marcado replay |
| PST-02 | Mesma idempotency_key com payload diferente no mesmo escopo | IDEMPOTENCY_CONFLICT (409); nenhuma mutação |
| PST-03 | Mesma chave em scopes distintos | Isolamento por chave composta (scope,key); sem mistura |
| PST-04 | Queda antes do commit da transação local | Rollback íntegro; nenhum recibo persistido de sucesso |
| PST-05 | Queda depois do commit e antes da resposta | Readback encontra recibo único, retry não duplica |
| PST-06 | Retomada de outbox/retry por trabalhador concorrente | At-most-once publication intent por operação; reconciliação explícita |
| PST-07 | TTL expirado ou requisição de exclusão de dados | Aplicar retenção aprovada e preservar auditoria mínima autorizada |
| PST-08 | Falha de restore ou hash incompatível no backup | NO-GO operacional; manter legado íntegro |
| REV-01 | HMAC válido sem aprovação documental registrada | Apenas prévia; não elevar a memória |
| REV-02 | Proposta R07 aprovada documentalmente mas sem clique humano R06 | MEMORIA_PENDENTE; Qdrant inalterado |

**Distribuição planejada verificável:** autenticação/escopo **7**, concorrência **6**, persistência **8**, revisão/memória **2** = **23 casos**. Não somar aos 101 testes atuais como se já tivessem passado.

**Regressão obrigatória futura:** os 49 testes do contrato, 13 do híbrido e 39 do P0/P1 anterior devem permanecer verdes **no novo SHA**; CI herdada R05/R07 separadamente. Não criar fake auth service que alegue E2E; fixture de token pode testar rejeição de claims sintéticas, não homologação OAuth.

## 6. Sequência de gates e dependências

| Gate futuro | Trabalho a autorizar | Aceite objetivo | Estado |
|---|---|---|---|
| G14-A — especificação | Revisão humana deste plano, escolha de trust boundary e tabela de permissões | Titular aprova escopo e critérios | PENDENTE |
| G14-B — testes sintéticos puramente locais | Criar mocks de principal, ACL, versionamento, transação e falhas **somente no ramo isolado** | Todos os 23 testes planejados com log de CI por SHA; invariantes antigos intactos | NÃO EXECUTADO |
| G14-C — simulação concorrente descartável | Testar CAS e unicidade com armazenamento efêmero/sem rede, se aprovado | Exatamente um commit por revisão; readback único; 409 e rollback comprovados | NÃO EXECUTADO |
| G14-D — revisão independente | Auditar schemas, código, dependências, LGPD, segredo, cobertura e negativos | Evidências e parecer versionados; corrigir somente na mesma branch | NÃO EXECUTADO |
| G14-E — integração autenticada real | Conectar identity provider, fonte documental e armazenamento reais | **Nova autorização expressa** com ambiente, identidade, namespace, rollback e operador definidos | BLOQUEADO |
| G14-F — integração R07/R06 / merge/deploy | Dependências da R07 atualizadas, portal humano, backup, migração e readback | Gate de orquestrador e titular distintos; sem implicação de GO pelos testes de unidade | BLOQUEADO |

**Condição para o próximo pedido:** autorizar separadamente a **etapa G14-B**, detalhando se deseja **somente fixtures em RAM** (recomendado primeiro) ou também teste com SQLite/PostgreSQL descartável em CI. Nenhuma ação de G14-C/E/F decorre automaticamente do aceite de G14-B. A decisão sobre persistência real permanece posterior.

## 7. Riscos, proteção, rollback e rastreabilidade

| Nível | Risco | Prevenção / gate |
|---|---|---|
| CRÍTICO | Tratar `allowed_scope` de payload como ACL comprovada | VerifiedPrincipal e decisão de autorização server-side |
| CRÍTICO | Aceitar token para outro recurso ou repassar credencial | Validação issuer/audience/resource, cofre de segredos e não-passthrough |
| ALTO | Sobrescrita concorrente/versão obsoleta | Compare-and-swap, 409, preservação imutável do original |
| ALTO | Retry duplicado após timeout de provedor | Idempotência durável + estado UNKNOWN + outbox + reconciliação |
| ALTO | Misturar memória aprovada com documento/fixture | R07 comparação apenas de aprovado, R06 revisão e clique humano separados |
| ALTO | Persistir payloads OCR/documentos ou tokens nos recibos | Metadados mínimos, hashes, logs sanitizados e política de retenção |
| MÉDIO | Dependência tecnológica desnecessária do DocLab antigo | Fachada fina; nada de Studio/SeaweedFS/DocuSeal obrigatório |
| ALTO | Migrar R07 ou alterar legado por CI verde | NO-GO para merge, deploy, Qdrant ou corte sem autorização |

**Plano de rollback para possível implementação posterior:** manter a branch/commit atual como ponto de retorno; testes futuros isolados sem alteração de registros reais; se houver falha, reverter apenas arquivos próprios da branch e preservar R06/R07, originais e sistemas existentes. Para produção, criar runbook específico com snapshot, restore, reconciliação e titular aprovador antes de qualquer mutação.

**Evidências atuais:** PR #7 no HEAD `b68e2c928ebf8a7b0fc482d1b5d67b061cf3c2a0`; [CI Document MCP](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44419855854) e [CI herdada R05/R07](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44419855275) foram verificadas como `success` **antes** desta atualização apenas documental. Isso não prova autenticação nem persistência. A CI documental do commit de publicação, caso disparada, só prova ausência de regressão sintética.

## 8. Registro de autorização

**Esta missão autoriza:** consultar artefatos já acessíveis e criar/atualizar **somente Markdown** na branch Document MCP, indexar e fazer readback.  
**Esta missão NÃO autoriza:** implementar e rodar novos testes, criar servidor, configurar OAuth/Cloudflare/DB, alterar CI ou código, conectar OCR/NOM reais, acessar dados de clientes, modificar Google Drive, GitLab, Linear, branches externas, Qdrant, fazer deploy, publicar, merge ou corte do legado.  
**Próxima autorização específica necessária:** G14-B — implementação e execução de testes sintéticos locais com critérios desta matriz; e, separadamente, G14-C se exigir concorrência em um banco efêmero.

**Conclusão:** plano P0/P1 pronto para apreciação; **G14-A = PENDENTE DE APROVAÇÃO HUMANA**; demais gates não iniciados.
