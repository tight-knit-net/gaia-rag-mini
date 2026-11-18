# CI / Linode — situação objetiva R05
**Referência:** 17/11/2026

- CodeRabbit: arquivo de configuração removido, assim como a dependência no CI/CODEOWNERS. O usuário informou ter desinstalado o aplicativo; a revogação em sua conta não é inspecionável por este conector.
- CI estática: validação de skill, regressões documentais, YAML, shell e ZIP temporário no runner, sem upload da skill.
- GHCR: sem gatilho de push automático; job com if: false.
- Linode staging: workflow remoto GHCR/Actions continua com `if: false`. Contudo, mediante solicitação direta posterior do proprietário em 17/11/2026, foi instalada manualmente imagem local de staging **somente leitura** e isolada: `gaia-rag-mini-staging` (`127.0.0.1:18081`), estado Docker healthy, health HTTP 200 e acesso MCP anônimo 401. Sem autenticação/grants/Qdrant; não é homologação operacional. Diagnóstico: `RELATORIO_STAGING_INSTALACAO_2026-11-17.md`.
- Origem e separação: DigitalOcean, Cloudflare e Qdrant não foram modificados; agora há execução local isolada na Linode sem credenciais nem acesso aos dados reais.
- DigitalOcean, Cloudflare, Qdrant e portal: nenhum serviço alterado nesta revisão.

Pendente antes de uso real: ACL efetiva, proposta e clique humano, dependência e ativação da skill no host, testes negativos A/B, falha/rollback. Não solicitar segredos apenas para auditar documentos.

Publicação, merge, deploy e modificação da MCP de produção continuam sujeitos a autorização explícita.
