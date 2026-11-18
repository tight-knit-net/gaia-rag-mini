# GAIA RAG Mini R05 — projeto executivo
**Data:** 17/11/2026
**Situação:** documentação revisada; próxima fase depende de escopo autorizado. Runtime não homologado. CodeRabbit removido; não é requisito.

## Documentos principais
- [Projeto executivo](PROJETO_EXECUTIVO_R05.md)
- [Auditoria técnica enxuta](AUDITORIA_TECNICA_ENXUTA_R05_2026-11-17.md)
- [Skill R05 candidata](../../skills/gaia-rag-processos-administrativos/SKILL.md)
- [Checkpoints](MATRIZ_GATES.md), [testes](PLANO_DE_TESTES_R05.md), [backlog](BACKLOG_IMPLEMENTACAO_R05.md) e [riscos](RISCOS_DEPENDENCIAS_R05.md)
- [Revisão sem bot](PROTOCOLO_REVISAO_R05.md) e [congelamento de publicação](ADR-0002-FREEZE-PUBLICACAO.md)

## Referências
[Arquitetura](ARQUITETURA.md) · [Segurança](SEGURANCA_E_ISOLAMENTO.md) · [Distribuição da skill](ADR-0001-DISTRIBUICAO-SKILL.md) · [Migração/rollback](MIGRACAO_AKAMAI.md) · [CI e Linode](STATUS_CICD_LINODE.md) · [Relatório histórico](RELATORIO_DE_EXECUCAO_R05.md).

## Resumo operacional
1. Backend autoriza cliente e processo antes de retornar memória; não usar UUID/fonte/similaridade sem ACL comprovada.
2. Não gravar sem clique humano autenticado e readback.
3. Demonstrar ativação real da skill no host, com testes A/B de dados fictícios.
4. Manter a DO, Cloudflare e Qdrant atuais intactos até migração autorizada.

R04/R03.1 continuam preservadas no Drive. A autoauditoria foi feita pelo assistente e não é revisão externa independente. CI estática não equivale a homologação. Sem merge, publicação ou deploy nesta etapa.

[PR #1 para consulta e continuidade](https://github.com/tight-knit-net/gaia-rag-mini/pull/1)
