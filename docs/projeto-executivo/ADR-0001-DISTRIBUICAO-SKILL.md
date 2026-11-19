# ADR-0001 — Distribuição da skill GAIA RAG R05 (revisão técnica)
**Status:** DECISÃO CONDICIONADA — distribuição futura, sem instalação ou deploy nesta fase.

## Fonte canônica e alternativas
A skill única tem fonte versionada em `skills/gaia-rag-processos-administrativos/`. A R04 e R03.1 permanecem intactas no Drive.

**Alternativa A — Extensão Skills over MCP (beta):**
1. Confirmar protocolo-base compatível (revisão `2026-07-28` ou posterior) e suporte do host consumidor.
2. O servidor deve anunciar `io.modelcontextprotocol/skills` em capabilities de `server/discover`, juntamente com `resources`.
3. A extensão define `skills/list` e `skills/get` como obrigatórios. O conteúdo dos arquivos é lido por `resources/read` do MCP-base; **não é método novo da extensão**.
4. `resources/directory/read` é opcional e só deve ser exposto/anunciado quando implementado (`directoryRead: true`). O manifesto de arquivos/digests e a resolução `skill://` exigem validação.
5. Provar no host, com traces reais, descoberta, seleção, recuperação de recursos e uso progressivo. A presença da capacidade ou do ZIP não implica ativação automática.

**Alternativa B — Plugin ChatGPT com a mesma skill:**
- O empacotamento para o plugin depende de `plugin.json` conforme schema aplicável, da pasta `skills/`, e dos mapeamentos/dependências de MCP efetivos; `mcp.json` pode ser necessário conforme distribuição.
- O `agents/openai.yaml` atual descreve interface/política, mas **não declara dependência MCP verificável**. Não inventar URL, ID de servidor ou OAuth. Determinar contrato e vinculação reais antes de empacotar.
- A autorização permanece no servidor MCP, não nas instruções da skill.

## Segurança
A skill é conteúdo executável como instrução ao agente, não um limite de segurança. Identidade Cloudflare Access, `tenant_id`, `process_id`, filtros de Qdrant e autorização por método devem ser validados no backend ANTES de qualquer dado ser retornado ao host. O método `memory_get` por UUID, `memory_find_by_source` e `memory_similar_cases` precisam de verificação específica, porque a filtragem na resposta do modelo não impede vazamento de dados.

## Critério de escolha
Decidir após inspeção read-only da MCP e ensaio do host em ambiente aprovado. Se não houver suporte à extensão beta, registrar limitação e testar plugin empacotado. Se nenhum canal carregar a skill, preservar documentação sem anunciar funcionamento. Não assumir agente Cloudflare Think: a origem observada é Docker/Python/Uvicorn.

## Fontes oficiais
- https://skills.extensions.modelcontextprotocol.io/specification/beta/skills
- https://developers.openai.com/plugins/build/skills
- https://developers.openai.com/plugins/build/plugins
- https://developers.cloudflare.com/agents/skills/execution/

**A implantação depende de autorização futura e não é objeto desta ADR.**
