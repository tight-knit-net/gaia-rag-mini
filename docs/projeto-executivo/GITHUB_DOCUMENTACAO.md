# GitHub Wiki x documentação versionada

O GitHub oferece uma Wiki própria, versionada em repositório separado `<repo>.wiki.git`, cujo acesso e automação diferem do repositório de código. Para esta R05, a documentação foi colocada em `docs/projeto-executivo/` no mesmo repositório, de forma auditável por pull request, reviews e CI. É equivalente funcional à pasta executiva solicitada, mas NÃO é a GitHub Wiki nativa.

Opcional futuramente: habilitar a Wiki nativa nas configurações do GitHub e publicar apenas um índice com links para os documentos canônicos desta pasta, evitando duplicação de conteúdo.

Navegação:
- README.md — projeto e escopo
- ARQUITETURA.md — estado AS-IS e TO-BE
- MIGRACAO_AKAMAI.md — execução, rollback e comparação de hosts
- ADR-0001-DISTRIBUICAO-SKILL.md — canais MCP/plugin
- SEGURANCA_E_ISOLAMENTO.md — contratos de autorização
- MATRIZ_GATES.md — requisitos e homologação
- RELATORIO_DIAGNOSTICO_2026-11-17.md — observações e lacunas
