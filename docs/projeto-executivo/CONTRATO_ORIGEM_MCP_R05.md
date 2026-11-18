# R05 — contrato da MCP observado na origem e implementação offline

**Data:** 17/11/2026. **Origem inspecionada somente para leitura:** container `gaia-qdrant-memory-gaia-qdrant-memory-candidate-1` no host DigitalOcean `mcp-100-do`. Arquivos observados dentro do container: `/app/server.py`, `/app/workflow.py`, `/app/qdrant_memory.py`, `/app/requirements.txt`. **Nenhum segredo, token, dado de cliente ou proposta foi copiado para o GitHub.** Não foram executadas chamadas de escrita ou de consulta ao Qdrant.

## Contrato observado

O servidor existente usa FastMCP, Uvicorn e Cloudflare Access. O middleware valida o JWT do Access e confere o e-mail contra aprovadores permitidos, mas isso não constitui controle de autorização **por cliente e processo**. A gravação ocorre apenas via proposta, portal HTML protegido, POST com verificação de CSRF e recibo assinado; esse mecanismo foi preservado, não foi alterado.

| Ferramenta observada | Limite observado no código |
|---|---|
| `memory_process_start(process_id, description, namespace)` | Consulta processo e casos semelhantes; similaridade é buscada dentro do namespace, sem grant explícito por cliente |
| `memory_search(query, namespace, process_id, limit)` | `process_id` é opcional |
| `memory_list_process(process_id, namespace, limit, offset)` | Filtra processo, mas não confere grant por identidade |
| `memory_get(point_id, namespace)` | Busca UUID e confere namespace/aprovação depois, sem tenant |
| `memory_find_by_source(source_ref, namespace, limit)` | Filtra namespace e fonte, sem processo |
| `memory_similar_cases(description, process_id, namespace, limit)` | Busca global no namespace e exclui o processo atual somente na resposta |
| `memory_prepare_after_approval(...)` | Cria proposta pendente, não grava ponto diretamente |
| `/review/{proposal_id}` + POST `/approve` | Página de aprovação humana vinculada ao JWT Cloudflare Access |

O payload observado da gravação atual inclui `process_id`, mas **não exige `tenant_id`**. A fonte de autorização por e-mail/cliente/processo **não foi identificada**. Portanto, é incorreto declarar o isolamento operacional resolvido.

## Código novo desta etapa

- `src/gaia_rag_r05/authz.py`: contrato `Principal`, `Scope`, `Authorizer`. Exige grants que vêm de registro confiável; compara `issuer` e `audience`; sem grant exato, nega.
- `src/gaia_rag_r05/scoped_reads.py`: adaptador Qdrant **somente leitura**. Busca e listagem exigem filtros de `namespace`, `approved`, `tenant_id`, `process_id`. Filtra `source_ref` adicionalmente; UUID usa scroll filtrado por `has_id` e ACL **antes da recuperação** e revalida o payload antes de devolvê-lo ao host; limita similares a processos previamente autorizados e exige autorização do processo de origem.
- `tests/test_scoped_reads.py`: 35 testes `unittest` totalmente sintéticos com negação cross-tenant, UUID com ACL na consulta, listagem por processo, capability forjada, fonte, similares, grants ausentes, `issuer/audience` divergentes e falhas backend.

**Atenção:** o mecanismo em memória de emissão de capabilities impede passagem direta de um `AuthorizedScope` criado manualmente, mas não valida assinatura JWT nem resiste a código Python malicioso no mesmo processo. O adaptador rejeita registros históricos que não tenham `tenant_id` confiável, por desenho. Não o conectar ao runtime real sem definir o mapeamento de clientes e a fonte dos grants. A classe `Principal` somente deve ser construída pelo backend **após** verificação criptográfica de JWT; nunca por dados fornecidos no payload de ferramenta MCP.

## Próxima integração autorizável (sem alterar Qdrant por suposição)

1. Definir registro canônico de `sujeito Cloudflare Access → cliente → processos`, com revogação e provas de origem.
2. Verificar como mapear pontos antigos a clientes sem inferir `tenant_id` do nome de documento. Qualquer ajuste de payload/índice da coleção real é decisão separada.
3. Integrar adaptador ao FastMCP com identidade verificada por requisição, sem cache compartilhado indevido; não confiar em `process_id` declarado pelo LLM.
4. Executar testes de integração com Qdrant falso e identidades A/B fictícias antes de qualquer teste em staging.
5. Manter workflow GHCR e Linode bloqueados, sem alteração do serviço DigitalOcean existente.

**Fontes técnicas:** [Filtros Qdrant](https://qdrant.tech/documentation/search/filtering/) · [Validação de JWT Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).

**Estado:** código e testes na branch isolada; sem merge, imagem, deploy, gravação, novo container ou mudança em produção.
