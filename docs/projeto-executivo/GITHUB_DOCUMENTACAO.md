# Como está organizada a documentação do projeto no GitHub
O repositório privado mantém arquivos de projeto em `docs/projeto-executivo/` e skill versionada em `skills/gaia-rag-processos-administrativos/`. Essa estrutura permite histórico de commits, revisão técnica rastreável, CI estático e rastreabilidade no mesmo PR. Não depende de habilitar a GitHub Wiki nativa, nem de duplicar documentos.

**Porta de entrada:** [Projeto Executivo R05](PROJETO_EXECUTIVO_R05.md). [Índice e estado](README.md).

## Política
- Esta branch não contém autorização de merge para `main`, nem de publicar imagem ou implantar container.
- Código novo aguarda autorização explícita de escopo. CodeRabbit foi retirado; a revisão técnica enxuta está registrada sem bot.
- R04 e R03.1 são fontes históricas preservadas no Drive.
- Arquivos de infraestrutura aqui são propostas para revisão e estão em modo bloqueado.

## Estrutura por finalidade
`ARQUITETURA.md` + `ADR-0001-DISTRIBUICAO-SKILL.md` + `ADR-0002-FREEZE-PUBLICACAO.md`: decisões.
`BACKLOG_IMPLEMENTACAO_R05.md`: tarefas futuras, ainda proibidas.
`PLANO_DE_TESTES_R05.md`: ensaios e evidências.
`MATRIZ_GATES.md`: critérios objetivos de passagem.
`PROTOCOLO_REVISAO_R05.md`: revisão simples sem bot; `AUDITORIA_TECNICA_ENXUTA_R05_2026-11-17.md`: achados e decisões.
`STATUS_CICD_LINODE.md`: o que de fato está preparado no GitHub e no host.
`RELATORIO_DE_EXECUCAO_R05.md`: registro histórico da etapa inicial.
