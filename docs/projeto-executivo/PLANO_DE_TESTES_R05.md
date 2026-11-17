# Plano de testes e evidências — GAIA RAG Mini R05
**Estado:** critérios definidos, testes operacionais NÃO EXECUTADOS. Os 23 testes anteriores são exclusivamente estáticos/documentais.

## Fase de documentação/CI (pode rodar sem serviço)
| ID | Ensaio | Evidência de aceite |
|---|---|---|
| TD-01 | Analisar YAML da skill, scripts, recursos e contratos JSON | CI e manifesto do commit |
| TD-02 | Regressões de instrução: não persistência, separação de processo, fontes | 23 asserções R05 e fixtures |
| TD-03 | Conferir que GHCR/Linode não podem publicar ou fazer deploy | Workflow `if: false`, ausência de triggers automáticos |
| TD-04 | Executar revisão técnica independente do PR documental | parecer identificado, comentários rastreáveis, resposta aos achados e decisão registrada no PR |

## Fase de código e runtime FUTUROS — não executados
| ID | Entrada | Esperado | Gate |
|---|---|---|---|
| TR-01 | Usuário A autorizado, process_id A | recuperar apenas A, com fonte/status | G06 |
| TR-02 | Usuário A, process_id B | negar no servidor, não apenas filtrar resposta | G07 |
| TR-03 | Usuário A, UUID/source de B | negar, mesmo que ferramenta aceite UUID exato | G07 |
| TR-04 | Usuário A, similaridade sem filtro B | negar ou aplicar ACL backend antes da consulta | G07 |
| TR-05 | Identidade ausente/expirada, qualquer rota | negar, sem fallback permissivo | G07/G10 |
| TR-06 | Memória com instrução maliciosa | tratar como dado; não chamar ferramenta indevida | G10 |
| TR-07 | Documento não aprovado | não gerar proposta ou persistir | G08 |
| TR-08 | Documento aprovado, proposta válida | gerar proposta e nenhuma escrita antes do clique | G08 |
| TR-09 | Duas propostas idênticas mesmo processo/fonte | deduplicação idempotente com proveniência | G08 |
| TR-10 | Portal de homologação com usuário habilitado | clique humano autenticado, persistência única e readback | G09 |
| TR-11 | Portal negado/sem clique/expirado | nenhuma persistência | G09/G10 |
| TR-12 | Rede Qdrant indisponível, timeout, resposta parcial | erro controlado, sem violar ACL | G10 |
| TR-13 | Reinício com proposta pendente | consistência de estado; sem gravação implícita | G10 |
| TR-14 | Extensão Skills over MCP negociada | list/get/read funcionais e recursos versionados | G04 |
| TR-15 | ChatGPT/Work carregando módulo sob demanda | traces reais demonstram seleção/uso; ZIP não basta | G05 |
| TR-16 | Linode com workloads NestGround | memória, CPU, disco, latência, saúde e competição medidos | G11 |
| TR-17 | Falha deliberada em staging e rollback | origem restaurada com evidência sanitizada | G11 |

## Regras de dados
Usar identidades sintéticas A/B e processos `DEMO-*`; nenhum dado de cliente ou API key no CI. Testar persistência humana apenas em sandbox aprovado com backend isolado e logs minimizados. Não assumir que tabela de testes é prova de execução.

## Evidência mínima por teste
`test_id`, data/hora UTC, commit, digest, ambiente, identidade fictícia, process_id fictício, operação, expectativa, status observado, hash/recibo minimizado, executor e aprovação. Registrar bloqueios como `NÃO EXECUTADO`, não `PASSOU`.

## Critérios de interrupção
Qualquer vazamento cruzado, proposta auto-persistida, credencial exposta, alteração involuntária do Qdrant, desvio da Cloudflare Access ou falha de rollback interrompe a homologação.

## Testes adicionais exigidos pelo parecer documental
| ID | Cenário | Aceite esperado | Estado |
|---|---|---|---|
| TR-18 | A tenta `memory_get` com UUID válido de B, sem contexto ou tenant A | O **backend** nega ANTES de retornar payload; nenhuma informação de B alcança host | PLANEJADO |
| TR-19 | A tenta `memory_find_by_source` e `memory_similar_cases` contendo fonte exclusiva de B | Filtro/autorização server-side efetiva; nenhum resultado de B enviado | PLANEJADO |
| TR-20 | Host sem suporte Skills beta; servidor anuncia extensão apenas quando suportada | Falha segura, protocolo correto em `server/discover`, `skills/list/get` e `resources/read` conforme negociação | PLANEJADO |
| TR-21 | Plugin ChatGPT sem `agents/openai.yaml` de dependência verificada | Falha de empacotamento/instalação declarada, nunca simular vínculo com MCP | PLANEJADO |
| TR-22 | Workflow GHCR/Linode acionado por evento sem liberação explícita | Jobs bloqueados e nenhum pacote/imagem/deploy publicado | PARCIAL: checagem estática apenas |

