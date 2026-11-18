# R06 — Decisão arquitetural: memória GAIA unificada, sem bloqueio por cliente

**18/11/2026 · decisão operacional explícita do proprietário do GAIA**

## Decisão

O GAIA RAG é **um acervo unificado do proprietário**, acessível em qualquer conversa/projeto do ChatGPT em que o conector MCP do GAIA esteja disponível e autenticado. Projetos do ChatGPT são apenas contexto de organização e produção. O sistema **não** restringe leitura por cliente ou por associação de cliente ao chat.

Qualquer processo cadastrado pode ser localizado e consultado pelo mesmo proprietário, mesmo se pertencer a um cliente diferente do projeto atual. O filtro `process_id` continua sendo identificação/seleção precisa do processo, **não permissão**. A semelhança temática de processos diferentes não significa que sejam o mesmo processo; nome duplicado deve ser desambiguado antes de consolidar conclusões.

## O que foi retirado do contrato R06

- Nenhum argumento `tenant_id` exigido em ferramentas de consulta, abertura, proposta ou visualização.
- Nenhum vínculo `usuário → cliente → processo` é exigido para o proprietário autenticado.
- Nenhum filtro Qdrant por `tenant_id` é aplicado em leituras com capacidade de proprietário.
- `memory_similar_cases` pode procurar casos de **qualquer cliente**; `memory_search_all` pesquisa todo o acervo aprovado (inclusive pontos antigos sem etiqueta de cliente).
- `tenant_id` pode permanecer no payload/documento para **proveniência, auditoria e classificação**, sem impacto em autorização.

## Controles que permanecem (não são travas por cliente)

- JWT Cloudflare Access assinado, emissor e audience verificados; identidade incluída em `GAIA_RAG_OWNER_SUBJECTS_FILE`, arquivo da operação. Sem proprietário autorizado, negar acesso.
- `namespace` e `approved=true` obrigatórios na leitura. `process_id` exato nas operações de processo; `memory_search_all` permite descobrir casos sem conhecer seu identificador.
- Documento previamente aprovado em registro controlado pelo servidor; proposta idempotente não grava por si só; revisão humana no portal com validação de identidade/origem/CSRF; gravação e readback antes de confirmar.
- Registros sem `tenant_id` podem ser consultados pelo proprietário quando correspondem a memória aprovada, mas não se inventa qual cliente lhes pertence.
- Nunca publicar ferramenta sem autenticação, expor Qdrant publicamente ou retirar revisão humana.

## Contrato MCP R06 revisado

| Uso | Ferramentas |
|---|---|
| Iniciar processo identificado | `memory_process_start(process_id,namespace='chatgpt')` |
| Recuperar histórico exato | `memory_list_process(process_id,...)`, `memory_search(query,process_id,...)` |
| Encontrar processo/memória em toda base | `memory_search_all(query,namespace='chatgpt')` |
| Conhecimento transversal | `memory_similar_cases(description,process_id,...)` |
| Conferir fonte ou UUID | `memory_find_by_source(source_ref,process_id,...)`, `memory_get(point_id,process_id,...)` |
| Propor memória após aprovação documental | `memory_prepare_after_approval(process_id,title,summary,source_ref,document_approval_ref,document_sha256,...)` |
| Inspecionar propostas | `memory_pending_reviews(process_id,...)`, `memory_proposal_preview(proposal_id,process_id,...)` |

## Impacto e teste

Implementação iniciada na branch `feat/r06-lifecycle-skill-staging`, PR #4 (draft). Testes de integração sintéticos via Qdrant descartável cobrem: proprietário lê processos A e B de clientes diferentes, busca global, similaridade entre clientes, UUID/fonte cruzados, registro histórico sem tenant, outro usuário não proprietário negado, revisão humana e readback.

Nenhuma modificação nos dados da DigitalOcean. O acesso real do proprietário e seu registro de identidade no Cloudflare ainda exigem homologação. Somente após CI e prévia isolada validada, eventual publicação e migração operacional.

**Critério de aceitação:** o mesmo proprietário, iniciando chat em qualquer projeto, é capaz de recuperar um processo de outro cliente pelo `process_id`, sem pedir autorização baseada no projeto/cliente e sem misturar processos diferentes.
