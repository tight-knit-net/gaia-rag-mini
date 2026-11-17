# Parecer de revisão técnica documental — GAIA RAG Mini R05
**Data de referência:** 17/11/2026
**Autor da revisão:** ChatGPT (revisão de consistência assistida; também participou da elaboração anterior; **NÃO é revisor externo independente**).
**Escopo:** documentação e configuração versionada na branch `docs/r05-gaia-rag-homologacao`, PR #1 do repositório privado `tight-knit-net/gaia-rag-mini`.
**Resultado:** **AJUSTES SOLICITADOS**, com correções documentais aplicadas e bloqueadores para próxima etapa. DG-03 **NÃO APROVADO**.
**Limite:** nenhuma implementação nova de runtime, instalação, publicação, operação Cloudflare/Qdrant/Linode ou migração foi realizada.

## Base examinada
- [Projeto executivo](PROJETO_EXECUTIVO_R05.md), [arquitetura](ARQUITETURA.md), [ADR-0001](ADR-0001-DISTRIBUICAO-SKILL.md), [ADR-0002](ADR-0002-FREEZE-PUBLICACAO.md), [segurança](SEGURANCA_E_ISOLAMENTO.md), [backlog](BACKLOG_IMPLEMENTACAO_R05.md), [testes](PLANO_DE_TESTES_R05.md), [matriz](MATRIZ_GATES.md) e [riscos](RISCOS_DEPENDENCIAS_R05.md).
- Artefatos do próprio repositório: `skills/gaia-rag-processos-administrativos/SKILL.md`, `agents/openai.yaml`, validadores de skill, workflows e scripts de staging.
- Documentação técnica oficial consultada: MCP Skills beta (https://skills.extensions.modelcontextprotocol.io/specification/beta/skills); OpenAI skills e packaging (https://developers.openai.com/plugins/build/skills ; https://developers.openai.com/plugins/build/plugins); Qdrant multitenancy (https://qdrant.tech/documentation/manage-data/multitenancy/); Cloudflare Access JWT (https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/); GitHub Actions security (https://docs.github.com/en/actions/reference/security/secure-use).
- Fireflies explicitamente consultado: buscas por `GAIA RAG`, `GaiaRAG`, `GAIA`, `RAG`, `projeto executivo`, listagem geral e reuniões ativas. **Zero registros acessíveis.** Nenhuma decisão de reunião usada como evidência.

## Achados e tratamento
| ID | Gravidade | Evidência e avaliação | Ação / estado |
|---|---|---|---|
| BR-01 | CRÍTICA (desenho de segurança) | `SKILL.md` sugere checar `process_id` de hit depois de `memory_get`/`memory_find_by_source`. Essa checagem editorial NÃO impede retorno de dado de outra identidade ao host; não se comprovou que a MCP atual seja vulnerável, pois a ACL real não foi inspecionada end-to-end. | Explicitar negação por padrão e ACL server-side anterior à leitura/retorno para UUID, fonte, semântica e similaridade. Adicionados requisitos e testes TR-18/19; **mudança efetiva de skill/runtime PENDENTE de autorização**. |
| BR-02 | ALTA (compatibilidade) | A extensão beta é anunciada em capabilities `server/discover`; `skills/list` e `skills/get` são métodos da extensão, `resources/read` pertence ao MCP-base, e `resources/directory/read` é opcional. A versão anterior não explicitava essa diferença. | **ADR-0001 CORRIGIDA**; negociação/host ainda não testados. |
| BR-03 | ALTA (integração host) | `agents/openai.yaml` tem interface e política, mas não contém dependência real do MCP; não há manifesto de plugin completo, instalação nem prova de host. | **ADR-0001 CORRIGIDA**; empacotamento e ativação ainda bloqueados até inspecionar endpoint e suportes reais. |
| BR-04 | ALTA (infra/segredos) | GHCR e Linode estão com jobs `if: false`, mas a futura cadeia de credenciais, package permissions, rollback e segurança dos scripts não foi homologada. `if: false` é proteção temporária, não prova de readiness para deploy. | **MATRIZ e BACKLOG COMPLEMENTADOS**; publicação continua proibida. |
| BR-05 | MÉDIA (supply chain) | Actions de terceiros ainda referenciadas por tags sem pinagem de SHA; não há SBOM/SAST de runtime. | Requisito futuro de fixação/pinagem e auditoria antes de CI com segredos ou build; sem alterar código/deploy neste parecer. |
| BR-06 | MÉDIA (validação) | 23 testes são estruturais e verificam conteúdo, não fluxos reais da MCP/portal/ACL/host. | Preservada distinção; critérios TR-18..22 acrescentados, sem marcar como executados. |

## Controles avaliados documentalmente
1. Projeto R05 possui invariantes claros de preservar Qdrant Cloud, coleção, dados reais, Cloudflare Access e clique humano.
2. Branch de documentação isolada da `main`; PR de revisão, sem autorização de merge.
3. Workflows GHCR/Linode com `if: false`; CI documental sem upload persistente de pacote.
4. Busca e produção diferenciadas; porém os contratos de ACL/portal permanecem hipóteses até inspeção do backend.
5. Linode `nestground-ai` é candidata condicional e partilha host com workloads existentes; benchmark não realizado.

## Decisão para gates
- **DG-01:** documentação de escopo e requisitos consolidada e revisada; achados registrados.
- **DG-02:** backlog, riscos, testes e rollback registrados; aceite do responsável ainda pendente.
- **DG-03:** **PENDENTE**; esta autoauditoria assistida não é parecer externo independente e BR-01 não foi fechado no runtime/skill.
- **DG-04:** aceite formal do desenho e decisão de segurança ainda pendentes.
- **DG-05:** verificação estática de freeze documentada; não significa proteção de toda a conta GitHub.
- **DG-06:** autorização para desenvolver **NÃO CONCEDIDA**.
- **G02–G12 operacionais:** NÃO HOMOLOGADOS.

## Recomendação de decisão
**Revisão interna concluída com AJUSTES SOLICITADOS.** Manter o projeto em revisão; considerar a documentação pronta para avaliação final do responsável apenas depois de resolver/aceitar explicitamente cada achado de desenho. Não iniciar código, não fazer merge, não publicar imagem, não implantar container e não transferir a MCP até autorização específica.

O trabalho futuro deve começar por uma prova de isolamento server-side e contrato real da MCP, sem aceitar validação pós-retorno como proteção. A correção documental deste parecer não garante nem finge a correção operacional.
