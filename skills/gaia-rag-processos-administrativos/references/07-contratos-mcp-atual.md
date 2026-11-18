# 07 — Contrato MCP R06 (prévia na Linode)

A fonte de verdade para este contrato é a lista `tools/list` e os recursos retornados pela imagem R06. **Não confundir com a MCP R05/legada da DigitalOcean.** O ambiente R06 ainda não utiliza credenciais, usuários ou dados reais de clientes e a skill não está homologada para ativação automática em ChatGPT/Work.

## Ferramentas expostas pela R06 — acesso unificado do proprietário

**Os projetos do ChatGPT são espaços de organização, NÃO divisões de autorização.** O usuário autenticado como proprietário do GAIA tem acesso a todos os processos, documentos aprovados e memórias aprovadas. Não existe mais `tenant_id` como parâmetro obrigatório ou permissão por cliente. `process_id` é identificador de caso; `tenant_id`, caso presente no Qdrant, é exclusivamente metadado documental. Se houver mais de um processo com o mesmo identificador canônico, identificar explicitamente a ambiguidade antes de combinar fatos.

| Ferramenta R06 | Entrada principal | Efeito |
|---|---|---|
| `memory_status`, `memory_policy` | sem parâmetros | Estado e política de proprietário autenticado |
| `memory_process_start` | process_id, namespace? | Recupera abertura e histórico exato |
| `memory_list_process` | process_id, namespace?, limit? | Memórias aprovadas deste processo, de qualquer cliente |
| `memory_search` | query, process_id, namespace?, limit? | Pesquisa dentro do processo |
| `memory_search_all` | query, namespace?, limit? | Pesquisa SEM filtro de cliente/processo na base aprovada, inclusive pontos antigos sem tenant |
| `memory_get` | point_id, process_id, namespace? | Leitura por UUID no processo informado |
| `memory_find_by_source` | source_ref, process_id, namespace?, limit? | Fontes do processo |
| `memory_similar_cases` | description, process_id, namespace?, limit? | Casos semelhantes entre TODOS os clientes, exceto processo atual |
| `memory_prepare_after_approval` | process_id, title, summary, source_ref, document_approval_ref, document_sha256, namespace? | Somente proposta, após validar documento no registro do servidor |
| `memory_proposal_preview` | proposal_id, process_id, namespace? | Inspeciona proposta do processo |
| `memory_pending_reviews` | process_id, namespace?, limit? | Lista propostas do processo |
| `gaia_skill_catalog`, `gaia_skill_read` | caminho da allowlist | Entrega conteúdo da skill sem ativação automática no ChatGPT |

**14 ferramentas MCP**; três recursos `skill://gaia-rag-processos-administrativos/...` via `resources/list` e `resources/read`. O servidor requer JWT verificado e email incluído no registro `GAIA_RAG_OWNER_SUBJECTS_FILE`. Não é acesso público ou anônimo.

A aprovação documental vem de uma fonte controlada pelo servidor. O campo `tenant_id` da proposta vem da fonte aprovada ou fica explicitamente como `unassigned`; não decide quem pode consultar. O clique humano no portal é etapa distinta da aprovação do documento e da preparação da proposta. A escrita só é confirmada após readback, sem retry automático em caso ambíguo.

## Segurança e indisponibilidade

O servidor verifica assinatura JWT CF Access e issuer/audience, consulta uma lista de proprietários controlada pelo servidor a cada chamada e exige processo exato nas operações processuais. Sem `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`, `GAIA_RAG_OWNER_SUBJECTS_FILE`, `QDRANT_URL`, `QDRANT_API_KEY`, `GAIA_RAG_APPROVED_DOCS_FILE`, URL real de revisão e chave CSRF, **o fluxo não está operante**. Não preencher esses valores com amostras DEMO no staging oficial. `GAIA_RAG_ENABLE_REVIEW` fica desligado até homologação controlada.

## Documentação histórica da MCP legada — apenas comparação

## Contrato legado observado em 17/11/2026 (DigitalOcean)

A skill **não implementa** as rotas da proposta R02 (`gaia_memoria_salvar`, `gaia_skill_catalogo`, `gaia_contexto_processo`, `gaia_documento_buscar` etc.). Elas NÃO foram observadas nesta MCP atual. Revalidar a lista quando instalar.

| Nome de ferramenta real | Finalidade | Entrada mínima |
|---|---|---|
| `memory_status` | saúde/configuração sem segredos | `{}` |
| `memory_policy` | gatilhos e autorização | `{}` |
| `memory_process_start` | início de processo, contexto exato/similares | `process_id`, `description?`, `namespace?` |
| `memory_search` | busca semântica aprovada | `query`, `process_id?`, `namespace?`, `limit?` |
| `memory_list_process` | lista paginada por processo | `process_id`, `namespace?`, `limit?`, `offset?` |
| `memory_get` | memória por UUID | `point_id`, `namespace?` |
| `memory_find_by_source` | fonte exata | `source_ref`, `namespace?`, `limit?` |
| `memory_process_timeline` | cronologia de processo | `process_id`, `namespace?` |
| `memory_similar_cases` | casos análogos | `description`, `process_id?`, `namespace?`, `limit?` |
| `memory_prepare_after_approval` | prepara revisão, NÃO persiste | `summary`, `title`, `process_id`, `namespace?`, `kind?`, `source_ref?`, `source_type?` |
| `memory_proposal_preview` | mostra proposta sem salvar | `proposal_id` |
| `memory_pending_reviews` | propostas pendentes | `namespace?`, `process_id?`, `limit?` |
| `memory_discard_proposal` | descarta proposta pendente, não ponto persistido | `proposal_id` |
| `memory_export_process` | exporta até 100 sínteses aprovadas | `process_id`, `namespace?` |
| `memory_approval_audit` | auditoria de aprovações | `namespace?`, `limit?` |
| `memory_stats` | contagem de propostas e prontidão | `namespace?` |

## Política confirmada (leitura MCP em 17/11/2026)

- `configured: true`, `approval_enforced: true`.
- coleção: `chatgpt_memoria_aprovada`.
- `namespace` padrão: `chatgpt`.
- aprovação de memória: interface HTTPS com Cloudflare Access e clique humano.
- gravação sem aprovação: bloqueada.
- proposta pendente: TTL de 14 dias.
- memória admitida: resumo revisado, referência de processo, fonte e autoria — nunca transcrição integral automática.

## Limites dos filtros de busca observáveis

- `memory_search`: `process_id` opcional, mas **obrigatório como procedimento da skill** para consulta sobre um caso concreto.
- `memory_find_by_source`: sem argumento `process_id`; verificar identidade processual no resultado antes de apresentá-lo.
- `memory_get`: filtra `namespace`, não `process_id`; validar processo/fonte após obtenção.
- `memory_similar_cases`: `process_id` opcional, sem filtro explícito por cliente; exigir autorização a leitura interprocessos e anonimização de comparações quando cabível.
- Não afirmar que o conector implementa ACL por cliente/tenant apenas por usar `namespace=chatgpt`. A implantação precisa ser inspecionada para homologação de isolamento real.

## Ausências críticas

A lista atual não inclui: criação de skills via MCP; catálogo de skills do servidor; `upsert` Qdrant arbitrário; migração de collections; payload indexes; alteração de namespace; exclusão/revogação de pontos; controle de embeddings; modificação de políticas; `gaia_memoria_salvar` direto. A skill orienta a produção do **resumo** e usa os parâmetros existentes, sem inventar parâmetros extras.

## Reconhecimento de falhas

Se serviço falhar ou não retornar ID/link/recibo, reportar estado desconhecido. Nunca afirmar salvamento ou aprovação porque a geração de proposta funcionou. Se servidor evoluir, revalidar assinaturas e revisar este documento antes de usar métodos novos.


## Protocolo de descoberta e compatibilidade R04

**Conferido contra a lista de ferramentas exposta em 17/11/2026.** Antes de executar em novo host, listar ferramentas disponíveis e comparar assinaturas. Uma ferramenta futura de R02 não vira método existente porque consta de documento. Não usar `gaia_memoria_salvar`, `gaia_documento_buscar`, `gaia_skill_obter`, `gaia_contexto_processo` na MCP atual se não foram apresentados pelo host.

### Matriz de riscos por operação

| Ferramenta | Semântica | Limitação de segurança/efeito |
|---|---|---|
| `memory_process_start` | leitura de contexto no início | retorno pode ter analogias; filtrar na apresentação |
| `memory_list_process` | leitura exata e paginada | ID de processo + namespace não certifica ACL por cliente |
| `memory_search` | leitura semântica | forçar `process_id` no procedimento, conferir hits |
| `memory_get` / `memory_find_by_source` | leitura por UUID/fonte | sem filtro de processo no contrato; checar pós-hit |
| `memory_similar_cases` | analogias | sem filtro exposto de cliente; bloquear uso sem autorização adequada |
| `memory_prepare_after_approval` | cria proposta de revisão | possui efeito em fila de propostas, mas **não grava ponto aprovado**; não chamar em testes de produção |
| `memory_discard_proposal` | descarta proposta pendente | operação mutativa; exige solicitação explícita |
| `memory_pending_reviews` / `memory_proposal_preview` | leitura de fila/preview | não revelar proposta de outro contexto |
| `memory_export_process` | exportação de resumos | limitar escopo; evitar republicação de dados privados |
| `memory_stats` | estatística | número de propostas NÃO é `points_count` Qdrant |
| `memory_approval_audit` | histórico de revisão | auditar sem expor dados pessoais de terceiros |

### Tratamento de falhas da aplicação

Se `memory_prepare_after_approval` não retornar link válido, não fabricar URL. Se retorno disser `PENDING_REVIEW`, nunca declarar `PERSISTED`. Se a leitura retornar zero, não chamar gravação ou ampliar a busca por conta própria. Em timeout de proposta, procurar propostas pendentes pelo processo antes de considerar um novo envio (sem garantia de idempotência). Caso a política/TTL tenha mudado, reconsultar `memory_policy` antes de orientar prazo.

### Verificações negativas sugeridas para homologação com sandbox

Dois principais distintos (`tenant_A` e `tenant_B`) e dois casos autorizados devem comprovar filtragem no backend. Testar omissão do filtro, UUID cruzado, `source_ref` cruzado e busca semântica/analogia, validando resposta sem divulgação. **Não executar esses testes em produção sem ambiente de prova e autorização explícita**.

## Contrato adicional R07 (branch isolada; NÃO instalado no runtime atual)

A branch `feat/r07-office-knowledge-assimilation` acrescenta, sobre a R06, **uma ferramenta de leitura**: `memory_assimilation_preview(process_id, title, summary, source_ref, kind="registro_caso", evidence_status="documentada", prior_point_id="", namespace="chatgpt")`. Saída: disposição editorial, eventuais duplicatas, revisões candidatas e relação pelo título, indicador de cobertura, necessidade de aprovação documental e humana, `persisted=false` e `old_points_unchanged=true`.

A consulta exige identidade proprietária verificada e respeita o `process_id` exato, sem bloqueio de acesso por cliente. Memória semelhante em outro processo NÃO é candidato de alteração deste caso. Quando um registro anterior não é encontrado numa listagem incompleta, a saída declara incerteza em vez de ausência definitiva. A implementação examina até três páginas de 100 memórias e verifica UUID explicitamente indicado por consulta escopada.

**R06 preservada:** `memory_prepare_after_approval`, proposta, portal de aprovação autenticada, CSRF, gravação e readback não foram substituídos. Nenhuma ferramenta aprova o conteúdo pelo ChatGPT; a R07 não contém update/revoke. Até merge, CI e deploy específicos, este contrato não pode ser presumido disponível no conector publicado.
