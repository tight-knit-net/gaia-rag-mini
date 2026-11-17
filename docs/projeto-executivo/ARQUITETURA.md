# Arquitetura R05 — estado observado x alvo

## Diagrama lógico
Host consumidor -> Cloudflare Access -> Tunnel Cloudflare -> container Python/Uvicorn na DigitalOcean -> Qdrant Cloud existente.

Alvo controlado: mesmo Access, mesmo hostname e mesmas políticas; substituir unicamente a origem do container por instância Linode homologada. Enquanto em teste, manter origem atual e usar rota de teste protegida. Nunca habilitar dois caminhos concorrentes de persistência real.

## Componentes invariantes
- Coleção Qdrant: chatgpt_memoria_aprovada; esquema vetorial histórico 384D/Cosine, sem reindexação.
- Aprovação humana pelo portal Access (apresentação de proposta não equivale à aprovação, e aprovação não equivale à gravação).
- Ferramentas atuais: memory_process_start, memory_list_process, memory_search, memory_get, memory_find_by_source, memory_similar_cases, memory_prepare_after_approval.
- Seletor process_id deve corresponder a identidade autorizada no backend; namespace chatgpt é insuficiente.
- Skill é instrução de fluxo e NÃO mecanismo de acesso; documentos ou memórias recuperados não podem conceder ferramentas.

## Distribuição
A MCP Python atual não foi demonstrada como agente Cloudflare Think. Se usar Skills over MCP, implementar capabilities de skills/list, skills/get e resources/read na camada atual ou numa ponte mínima sem enfraquecer Access. A ativação depende de negociação e de suporte efetivo do host. Alternativa: plugin ChatGPT com skill e dependência MCP verificada.

## Risco principal
A mudança de infraestrutura sem teste de ACL por cliente e sem readback de aprovação humana pode aparentar sucesso de healthcheck e ainda falhar na segurança. Bloquear cutover até testes G06–G10.

Documentos originais e matriz R04 continuam no Google Drive; este repositório é canônico apenas para a nova proposta R05.
