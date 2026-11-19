# Registro de decisões de arquitetura (ADRs) — R04

| ADR | Decisão | Status | Motivo/evidência |
|---|---|---|---|
| ADR-001 | Uma única skill com referências sob demanda | ADOTADA NESTE PACOTE | Objetivo do usuário e padrão Agent Skills [F01,F02] |
| ADR-002 | Não alterar Qdrant, MCP, Cloudflare | RESTRIÇÃO APROVADA PELO USUÁRIO | escopo Fase 2 |
| ADR-003 | Preservar `process_id` como unidade de caso e assunto como rótulo | ADOTADA EDITORIALMENTE | O01, O02; sem garantia de filtro técnico |
| ADR-004 | Consulta semântica restrita por processo para processos concretos | ADOTADA EDITORIALMENTE | ferramenta atual `memory_search` com `process_id?`; precisa de verificação ACL de servidor |
| ADR-005 | Distinguir aprovação documental e aprovação de memória | REGRA VIGENTE DECLARADA PELA MCP | O05 e `memory_policy`; portal humano |
| ADR-006 | Não invocar ferramentas R02 propostas como se existissem | ADOTADA | O06,O12; inventário real GAIA RAG |
| ADR-007 | Não usar resultado de UUID/source sem pós-verificação processual | ADOTADA | interfaces atuais não contêm filtro por processo |
| ADR-008 | Não usar analogias cross-client sem autorização demonstrada | ADOTADA | interface de casos similares não expõe filtro por cliente; Qdrant F04 |
| ADR-009 | Não criar coleções, campos ou embeddings por categoria | ADOTADA | arquitetura atual observada O05 é vetorial; desenho alternativo O06 não implantado |
| ADR-010 | Não prometer Skills via Qdrant/porta do conector | PENDENTE DE PROJETO FUTURO | distribuição depende do host e gateway [F01,F02] |
| ADR-011 | Preservar fonte e revisão com matriz de evidências | ADOTADA | O01/O02 e diretrizes CONARQ/AGU [F07,F10] |
| ADR-012 | Não criar manifest/plugin com URL ou ID não verificado | ADOTADA | exige implantação independente e teste de host [F02] |

**Regra de revisão:** mudança técnica futura exige novo ADR, dono, risco e teste antes de modificar o serviço. A presente tabela não autoriza nenhuma modificação.
