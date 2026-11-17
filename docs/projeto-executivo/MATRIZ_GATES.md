# Matriz R05 — gates de projeto (DG) e homologação operacional (G)
**Referência:** 17/11/2026. Status de cada gate depende de evidência real. `PRONTO PARA REVISÃO` não é `APROVADO`.

## A. Gates do projeto executivo ANTES do primeiro commit de código novo
| Gate | Critério | Situação observável |
|---|---|---|
| DG-01 | Escopo, AS-IS/TO-BE, requisitos, interfaces e decisões documentados | DOCUMENTAÇÃO CONCLUÍDA; aguardando revisão |
| DG-02 | Backlog, testes, riscos, rollback e dependências rastreáveis | DOCUMENTAÇÃO CONCLUÍDA; aguardando revisão |
| DG-03 | Parecer de revisão técnica independente verificável, com achados materiais resolvidos | PENDENTE DE REVISÃO INDEPENDENTE |
| DG-04 | Responsável pelo projeto aceita desenho, limites de segurança e decisões condicionadas | PENDENTE |
| DG-05 | Publicação/implantação bloqueadas no PR e sem merge automático | PROPOSTA CONFIGURADA na branch, validação CI pendente da revisão |
| DG-06 | Autorização EXPRESSA para começar código (distinta de autorização de publicar) | NÃO CONCEDIDA |

## B. Gates futuros do código, da MCP e do ambiente
| Gate | Critério objetivo | Situação |
|---|---|---|
| G00 | Originais R04/R03.1 preservados, branch e PR isolados | DOCUMENTADO; merge não executado |
| G01 | Parsing skill YAML/JSON/Python, recursos internos e regressão estática | APROVADO NA CI HISTÓRICA: 23 testes; revalidar no HEAD atual |
| G02 | Secrets scan, SAST, SBOM, fixação de dependências e imagem | NÃO EXECUTADO |
| G03 | Código da origem DO, digest, Compose, Cloudflare e fluxo de portal inventariados sem segredos | PARCIAL (container, imagem e Tunnel observados) |
| G04 | Skills over MCP list/get/resources/read ou plugin ChatGPT comprovados | NÃO EXECUTADO |
| G05 | Seleção e carregamento efetivo da skill no host consumidor | NÃO EXECUTADO |
| G06 | Busca exata por process_id autorizado, fontes e jurisdição | NÃO EXECUTADO |
| G07 | Isolamento A/B por ID/fonte/UUID/semântica/similaridade | NÃO EXECUTADO |
| G08 | Proposta atômica, dedup e prepare sem persistência | NÃO EXECUTADO |
| G09 | Portal humano Cloudflare Access, clique e readback em teste | NÃO EXECUTADO |
| G10 | Rede, timeout, replay, ausência de identidade e negativas | NÃO EXECUTADO |
| G11 | Benchmark Linode, implantação de teste e rollback ensaiado | NÃO EXECUTADO |
| G12 | Revisão técnica independente e CI aprovados para código do runtime | NÃO EXECUTADO |

## Critérios de liberação
- **Projeto executivo pode ser apresentado a review:** documentação DG-01/DG-02 preenchida.
- **Codificar:** somente DG-01..DG-06 aprovados, incluindo autorização expressa, após revisão real.
- **Testar em host/Linode:** nova autorização específica e ambiente isolado.
- **Publicar / implantar / migrar:** autorização expressa adicional, G02..G12 demonstrados e plano de rollback aprovado.
- **Nenhum gate de segurança ou controle humano é dispensado** por sucesso de linter ou saúde de container.

## C. Bloqueadores de desenho identificados na revisão (ainda não homologados)
| ID | Condição de aceite | Estado |
|---|---|---|
| BR-01 — CRÍTICO | Provar ACL do backend **antes** de retornar qualquer memória via UUID, fonte ou similaridade e harmonizar SKILL.md | BLOQUEADO — runtime não inspecionado para esse teste |
| BR-02 — ALTO | Contrato de Skills over MCP beta e suporte efetivo do host comprovados, sem confundir `resources/read` com novo método | PENDENTE — execução futura |
| BR-03 — ALTO | Dependência da MCP no pacote de plugin identificada e testada, sem URL presumida | PENDENTE — execução futura |
| BR-04 — ALTO | Pipeline GHCR/Linode, credenciais e rollback revisados antes de qualquer habilitação | BLOQUEADO — publicação proibida |

A revisão de consistência realizada pelo assistente que também participou da elaboração **não equivale a revisor externo independente**. DG-03 permanece PENDENTE até parecer independente; DG-04 e DG-06 dependem do proprietário. Nenhum BR é tratado como incidente real ou teste de host executado.

