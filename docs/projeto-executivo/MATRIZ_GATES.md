# GAIA RAG R05 — checkpoints mínimos
**Data:** 17/11/2026. Projeto pequeno: pontos de controle proporcionais, sem dependência de CodeRabbit nem de auditor externo.

| ID | Decisão ou evidência | Estado |
|---|---|---|
| DG-01 | Escopo, arquitetura atual/alvo e requisitos documentados | CONCLUÍDO documentalmente |
| DG-02 | Backlog, riscos, rollback e testes planejados | CONCLUÍDO documentalmente |
| DG-03 | Autoauditoria técnica rastreável e correções documentais | CONCLUÍDO como revisão assistida; não é revisão externa |
| DG-04 | Proprietário define e autoriza escopo de implementação | PENDENTE para novo código |
| DG-05 | GHCR/Linode desabilitados e branch sem merge | CONFIRMADO na branch; CI do HEAD a verificar |
| DG-06 | Autorização expressa para novo código operacional | NÃO CONCEDIDA nesta revisão |

## Provas antes de colocar em uso real
| ID | Teste | Situação |
|---|---|---|
| G01 | Skill/YAML/JSON e regressão estática | Automatizado, revalidar no HEAD |
| G02 | ACL backend por cliente/processo, UUID/fonte/similaridade | NÃO EXECUTADO |
| G03 | Proposta não grava; só clique humano autenticado grava com readback | NÃO EXECUTADO |
| G04 | Contrato MCP e ativação real da skill no host | NÃO EXECUTADO |
| G05 | Falhas, timeouts e rollback | NÃO EXECUTADO |
| G06 | GHCR, permissão de publicação e staging isolado antes de habilitar | NÃO EXECUTADO |

Achados BR-01 (ACL) permanecem prioritários e bloqueiam uso multi-cliente sem prova de backend. BR-02 (Skills over MCP) e BR-03 (plugin) são alternativas condicionadas à plataforma, não exigem implementar as duas. BR-04 (GHCR/Linode) é requisito apenas quando houver autorização para publicar/implantar.

Autoauditoria documental pronta; nenhum código operacional, merge, build ou deploy está automaticamente autorizado.
