# 07 — Contrato GAIA RAG disponível em 17/11/2026 (AS-IS)

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
