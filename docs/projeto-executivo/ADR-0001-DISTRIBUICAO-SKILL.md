# ADR-0001: distribuição canônica da GAIA RAG Skill R05
**Status:** proposta; arquitetura final depende de host e ACL.

## Decisão
- Uma única fonte de verdade versionada: `skills/gaia-rag-processos-administrativos/`.
- Caminho A: disponibilizar via Skills over MCP com `skills/list`, `skills/get` e `resources/read` `skill://...` na MCP atual ou adaptador Cloudflare mínimo. A identidade Cloudflare Access precisa continuar validada, e a autorização real de ferramentas deve permanecer no backend.
- Caminho B: plugin ChatGPT associado à MCP GAIA RAG e à mesma skill versionada. Empacotar e testar caso o host não negocie a extensão.
- São estratégias complementares, não duas cópias editáveis de fontes canônicas.

## Limites
A MCP atualmente observada é Python/Uvicorn, não um agente Cloudflare Think comprovado. APIs `skills.workspace`, `skills.r2`, `skills.code`, `activate_skill` e `read_skill_resource` não serão inseridas sem comprovar que a stack suporta esse runtime. A Cloudflare passar a servir as próprias skills por MCP em outubro/2026 não significa que esta GAIA RAG já o faça.

## Portões
A extensão deve ser anunciada, negociada, listar a R05, buscar seus recursos e apresentar prova de carregamento sob demanda no host consumidor. Se o host não a suportar, documentar negativa e usar plugin testado. Nunca prometer auto-injeção.

Referências técnicas:
https://developers.cloudflare.com/agents/skills/
https://developers.cloudflare.com/agents/skills/execution/
https://skills.extensions.modelcontextprotocol.io/specification/beta/skills
https://developers.openai.com/plugins/build/skills
https://developers.openai.com/plugins/build/plugins
https://developers.openai.com/plugins/deploy/connect-chatgpt
