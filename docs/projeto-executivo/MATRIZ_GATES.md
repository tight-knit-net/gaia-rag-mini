# GAIA RAG R05 — checkpoints mínimos
**Data:** 17/11/2026. Projeto pequeno: pontos de controle proporcionais, sem dependência de CodeRabbit nem de auditor externo.

| ID | Decisão ou evidência | Estado |
|---|---|---|
| DG-01 | Escopo, arquitetura atual/alvo e requisitos documentados | CONCLUÍDO documentalmente |
| DG-02 | Backlog, riscos, rollback e testes planejados | CONCLUÍDO documentalmente |
| DG-03 | Autoauditoria técnica rastreável e correções documentais | CONCLUÍDO como revisão assistida; não é revisão externa |
| DG-04 | Proprietário define e autoriza escopo de implementação | PENDENTE para novo código |
| DG-05 | GHCR/Linode pipelines de publicação desabilitados e branch sem merge | CONFIRMADO: CI do PR executa imagem/Qdrant sintético, mas GHCR e deploy automatizados seguem desabilitados |
| DG-06 | Autorização expressa para código novo | AUTORIZADO nesta etapa apenas módulo offline de ACL e testes sintéticos; integrar runtime/deploy depende de decisão separada |

## Provas antes de colocar em uso real
| ID | Teste | Situação |
|---|---|---|
| G01 | Skill/YAML/JSON e regressão estática | Automatizado, revalidar no HEAD |
| G02 | ACL backend por cliente/processo, UUID/fonte/similaridade | 35 testes unitários sintéticos + 7 testes de integração contra Qdrant REAL e descartável na Linode, repetidos em CI. **PASSOU para dados DEMO; integração com JWT/Qdrant de produção NÃO VALIDADA** |
| G03 | Proposta não grava; só clique humano autenticado grava com readback | NÃO EXECUTADO |
| G04 | Contrato MCP e ativação real da skill no host | Serviço staging HTTP 200 e solicitação MCP sem JWT 401; ativação da skill no host e JWT real NÃO EXECUTADAS |
| G05 | Falhas, timeouts e rollback | Timeout Docker/WARP reproduzido e corrigido; falha de JWT falso 401 e gate de staging desligado; rollback completo NÃO ENSAIADO |
| G06 | GHCR, permissão de publicação e staging isolado antes de habilitar | Staging local verificado em Linode, contêiner sem privilégios; publicação GHCR e deploy de produção NÃO EXECUTADOS |

Achados BR-01 (ACL) permanecem prioritários e bloqueiam uso multi-cliente sem prova de backend. BR-02 (Skills over MCP) e BR-03 (plugin) são alternativas condicionadas à plataforma, não exigem implementar as duas. BR-04 (GHCR/Linode) é requisito apenas quando houver autorização para publicar/implantar.

Autoauditoria documental concluída. A autorização inicial limitada foi ampliada por solicitação posterior do proprietário para instalar e sanitizar o **staging local e isolado na Linode** e executar testes reais com dados DEMO. O runtime staging foi instalado e testado; **merge, publicação GHCR, integração com Qdrant real de clientes, cutover de produção e alterações de Cloudflare continuam fora desta homologação**.
