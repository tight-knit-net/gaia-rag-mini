# Backlog de implementação R05 — ESPECIFICAÇÃO, NÃO EXECUÇÃO
**Estado:** pronto para revisão técnica, tarefas de código bloqueadas até DG-01..DG-06. `RF-*` e `RNF-*` referem-se ao projeto executivo.

## Etapa A — descoberta técnica da origem (read-only até autorização)
| ID | Dependência | Entrega verificável | Gate |
|---|---|---|---|
| BK-01 | Acesso autorizado à DO | inventário sanitizado de `server.py`, `workflow.py`, `qdrant_memory.py`, Dockerfile, Compose, requisitos, estado `/state` | DG-04 / OG-G03 |
| BK-02 | BK-01 | contrato real e esquema de argumentos da MCP (incluindo ferramentas disponíveis e ausentes) | DG-04 / OG-G03 |
| BK-03 | BK-01 | mapa de identidades e autorização backend sem expor credenciais, segredo ou dados reais | DG-04 / OG-G07 |
| BK-04 | BK-01 | mapa do portal, proposta, TTL, idempotência e auditoria antes/depois do clique | DG-04 / OG-G08/G09 |

## Etapa B — desenvolvimento futuro (NÃO AUTORIZADO)
| ID | Dependência | Entrega verificável | Requisito |
|---|---|---|---|
| BK-05 | BK-01–04 + DG-06 | estrutura do runtime no GitHub com testes reproduzíveis, sem segredos, origem documentada | RF-09, RNF-08 |
| BK-06 | BK-03 + DG-06 | autorização por usuário/tenant/processo no backend para busca semântica, UUID, fonte e similaridade | RF-01/02/03, RNF-01/10 |
| BK-07 | BK-04 + DG-06 | fluxo de proposta idempotente, sem escrita antes do portal, readback auditável | RF-05/06/10 |
| BK-08 | DG-06 | skill R05 versionada e recursos sob demanda com controle de paths/hashes | RF-07/09 |
| BK-09 | BK-08 | adaptador mínimo para `skills/list`, `skills/get`, `resources/read` se host negociar extensão; ou plugin compatível | RF-07 |
| BK-10 | BK-05–09 | suite de regressão real com fixtures sintéticas A/B, falhas e evidências, sem gravar dados reais | RF-01..10 |
| BK-11 | BK-05 + DG-06 | SBOM, secrets scan, SAST, fixação de dependências/imagem; não habilitar GHCR push | RNF-02/08 |
| BK-12 | BK-05–11 | documentação das interfaces, ADRs, runbooks e notas de compatibilidade, revisadas | RNF-07/09 |

## Etapa C — homologação futura (autorização nova e independente)
| ID | Dependência | Entrega verificável |
|---|---|---|
| BK-13 | BK-05–12 aprovados | ambiente isolado Linode, sem escrita Qdrant real, acesso privado e controle de recursos |
| BK-14 | BK-13 | teste do host ChatGPT/Work de seleção e carregamento real de skill |
| BK-15 | BK-13 | negativos multi-tenant por UUID/fonte/similaridade + proposta sem persistência |
| BK-16 | BK-15 | portal humano sintético/isolado e readback com trilhas de auditoria |
| BK-17 | BK-13–16 | relatório de performance/capacidade, rollback ensaiado e riscos residuais |
| BK-18 | BK-17 | decisão de corte de produção com autorização explícita; não executar automaticamente |

## Definição de pronto para cada item de código
A entrega de código deve ter contrato rastreado a RF/RNF, teste unitário/integração com fixtures não reais, resultado CI, revisão técnica independente, análise de segurança e atualização de documentação. Alterações de Qdrant, Cloudflare Access, DNS e coleção são fora de escopo sem ADR separada e autorização.

## Dependências externas que NÃO podem ser presumidas
- CodeRabbit retirado do projeto por decisão do proprietário; a revisão técnica independente continua obrigatória, sem dependência de bot.
- Host aceita Skills over MCP: não demonstrado.
- Embedding model e ACL multi-tenant: ainda não inspecionados.
- Projeto GitHub e fonte operacional: repositório começou sem runtime completo; portar código requer comparação e aprovação.
- Capacidade da Linode: snapshot não é benchmark.

## Itens adicionais identificados na revisão
| ID | Dependência | Entrega objetiva, somente em fase autorizada |
|---|---|---|
| BK-19 | BK-03 e aprovação DG-06 | Ajustar orientação da skill que hoje prevê validação pós-consulta; nunca usar retorno de dados como substituto da autorização de backend |
| BK-20 | BK-02, BK-08 e host aprovado | Negociação da extensão beta Skills com `server/discover`, `skills/list`, `skills/get`, `resources/read` e hashes de recursos |
| BK-21 | BK-20 sem suporte de host | Empacotamento alternativo com `plugin.json` e dependência MCP real, sem endpoint inventado |
| BK-22 | BK-03, BK-11 | Verificação independente de supply chain, actions de terceiros, fluxo de token de GHCR e capacidade de rollback, preservando freeze |

