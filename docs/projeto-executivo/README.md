# GAIA RAG Mini — Projeto Executivo R05
**Data de referência:** 17/11/2026
**Documentação:** COMPLETA PARA REVISÃO TÉCNICA
**Revisão externa:** PENDENTE DE PARECER COMPROVADO
**Código de aplicação, build, publicação e implantação:** NÃO AUTORIZADOS

## Leia primeiro
O documento principal é **[PROJETO_EXECUTIVO_R05.md](PROJETO_EXECUTIVO_R05.md)**. Ele consolida objetivo, estado observado, arquitetura-alvo, requisitos RF/RNF, segurança, interfaces, fases, gates e termos de aceite.

## Índice executivo
| Tema | Documento |
|---|---|
| Escopo, requisitos e projeto completo | [PROJETO_EXECUTIVO_R05.md](PROJETO_EXECUTIVO_R05.md) |
| Arquitetura atual e futura | [ARQUITETURA.md](ARQUITETURA.md) |
| Migração e rollback | [MIGRACAO_AKAMAI.md](MIGRACAO_AKAMAI.md) |
| Distribuição da skill | [ADR-0001-DISTRIBUICAO-SKILL.md](ADR-0001-DISTRIBUICAO-SKILL.md) |
| Congelamento de publicação | [ADR-0002-FREEZE-PUBLICACAO.md](ADR-0002-FREEZE-PUBLICACAO.md) |
| Segurança e ACL | [SEGURANCA_E_ISOLAMENTO.md](SEGURANCA_E_ISOLAMENTO.md) |
| Riscos e dependências | [RISCOS_DEPENDENCIAS_R05.md](RISCOS_DEPENDENCIAS_R05.md) |
| Tarefas de implementação, ainda não autorizadas | [BACKLOG_IMPLEMENTACAO_R05.md](BACKLOG_IMPLEMENTACAO_R05.md) |
| Testes previstos e evidências | [PLANO_DE_TESTES_R05.md](PLANO_DE_TESTES_R05.md) |
| Gates de desenho e operação | [MATRIZ_GATES.md](MATRIZ_GATES.md) |
| Revisão técnica independente | [PROTOCOLO_REVISAO_R05.md](PROTOCOLO_REVISAO_R05.md) |
| Condição do CI e Linode | [STATUS_CICD_LINODE.md](STATUS_CICD_LINODE.md) |
| Relatório histórico de execução R05 | [RELATORIO_DE_EXECUCAO_R05.md](RELATORIO_DE_EXECUCAO_R05.md) |
| Proveniência e justificativas | [RELATORIO_DIAGNOSTICO_2026-11-17.md](RELATORIO_DIAGNOSTICO_2026-11-17.md) |

## Regra de execução
Este repositório contém proposta de infra e CI para revisão. **Não executar** GHCR, deploy Linode, troca de Cloudflare Tunnel, alteração de Access, Qdrant ou merge. O `main` fica intocado por esta revisão. O PR é um mecanismo de controle documental, não uma autorização de implantação.

### Estado real versus simulação
- Histórico R04: 23 regressões estáticas e testes de pacote, não homologação no ChatGPT.
- Instância DigitalOcean: ativa anteriormente, sem alteração nesta fase.
- Linode: preparação anterior sem container GAIA RAG iniciado; capacidade em staging exige benchmark.
- Revisão técnica: parecer independente verificável ainda é necessário para o DG-03; o CodeRabbit foi retirado da configuração do projeto a pedido do proprietário.
- Skill no host: pendente; artefato de CI não prova instalação ou carregamento.

**Fontes canônicas:** [R04 no Drive](https://drive.google.com/drive/folders/1UVHd6Vz0FaI7QLVcZCNbVOyy5b6WcQ2-) e [R03.1 preservada](https://drive.google.com/drive/folders/15X-POHeZGrzQlY8ZeJYxgrW0eJYvZmMf).

[Pull Request de revisão documental #1](https://github.com/tight-knit-net/gaia-rag-mini/pull/1)
