# R07 — Gate S5: compatibilidade de carregamento MCP pelo host

**Versão:** 1.0.0
**Emissão:** 18/11/2026 20:34:21, America/Sao_Paulo.
**Fonte de relógio:** ferramenta de horário local do ChatGPT, ISO `2026-11-18T20:34:21-03:00`.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Branch de escrita:** `feat/r07-office-knowledge-assimilation`, PR #5 draft, base `feat/r06-lifecycle-skill-staging`.
**Commit funcional aprovado pela CI:** `5edc92a6f46bfff64cfa6fc172b20f12fcab2091`.
**Evidência CI:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44421753978
**Escopo:** somente host sintético e contrato MCP da R07. Sem implantação, hosts externos, dados de clientes, migração, Qdrant de produção, DNS ou chamada Groq.

## Trabalho efetivamente executado

- Atualizado o `skill_router.read_selected` para comparar novamente o SHA-256 dos bytes realmente devolvidos após a seleção; mudança de arquivo entre seleção e leitura gera `SKILL_CONTENT_DRIFT`.
- Criado `tests/test_r07_host_contract.py`: host sintético explicitamente solicita a rota, lê módulos obrigatórios/opcionais, remonta o texto e valida cada SHA, sem conceder acesso ou gravar memória.
- Adicionados testes completos de leitura de três módulos via protocolo MCP em `tests/r06_live_review_e2e.py`, conferindo SHA do conteúdo versus manifesto oficial do pacote instalado.
- Adicionado `r07_host_contract_synthetic` como job obrigatório para o aceite da candidata no GitHub Actions.
- Corrigidos dois testes **sintéticos históricos** de preflight para não inspecionarem `/home/ubuntu` em runner do GitHub: agora usam diretórios temporários fictícios. TestLab real não foi acessado.
- Registrado `docs/institucional/PROTOCOLO_DISPARO_GATES_R07.md` como convenção documental: cada gate encerrado apresenta escopo do próximo e botão de novo disparo humano. Não é armazenamento em memória ChatGPT.

## Resultados

| Dimensão | Resultado | Limitação |
| --- | --- | --- |
| 9 testes do host sintético | PASSOU 9/9 | Host simulado, não ChatGPT real |
| 3 novas verificações MCP de leitura integral | PASSOU 3/3 | Ambiente de demonstração Qdrant/JWT |
| Regressão do roteador S4 | PASSOU 14/14 | Apenas teste unitário |
| CI completa código do gate | PASSOU 7/7 jobs, run 44421753978 | Não é homologação de produção |
| Conector Knowledge atual (R06) | `gaia_skill_catalog` respondeu; `gaia_skill_read(SKILL.md)` retornou `{}` | Não prova carregamento de instruções pelo host |
| R07 carregada efetivamente no ChatGPT | PENDENTE | R07 não publicada no host |
| Botão Salvar memória real | NÃO EXECUTADO | Mantido e testado somente em laboratório |
| Migração/legado/produção | NÃO EXECUTADO | Etapa separada com autorização |

**Decisão:** PASSOU S5 na camada de contrato e consumidor sintético; PENDENTE o carregamento real pelo host. Não declarar a skill ativada no ChatGPT apenas por `tools/call` ou `resources/read`.

## Riscos e rollback

- Erro de ponte host/conector ou materialização pode retornar dados vazios mesmo com habilidade instalada; verificar no destino operacional antes de GO.
- Conteúdo de skill não é credencial/autorização; seleção, hash e contexto não podem habilitar gravação, contornar aprovação humana ou filtrar o proprietário por cliente.
- Em caso de regressão, reverter somente commits da branch R07 após revisão do diff. Nenhuma mudança em R06/main/legado/Qdrant exige rollback neste gate.

## Próximo gate sugerido, não iniciado — S6

**Auditoria de segurança e compatibilidade do diff R07:** comparar alterações R07 vs R06, conferir contratos MCP, seleção fail-closed, identidade/proprietário, proteção de processos, resistência a conteúdo não confiável, segregação de propostas, proteção do botão Salvar e regressões. Testes apenas com dados sintéticos no GitHub Actions. Produzir matriz de gaps classificados e parecer GO/NO-GO técnico; correções somente na branch R07. **Exclusões:** merge, publicação, Cloudflare, serviços externos, Qdrant real, migração e desativação do legado. Critério de aceite: CI do HEAD aprovado e ausência de falhas bloqueantes ainda não tratadas; host real permanece pendente para gate operacional separado.

**Gatilho:** botão na resposta do chat envia nova solicitação S6. O botão não é autorização de deploy/merge/migração.
