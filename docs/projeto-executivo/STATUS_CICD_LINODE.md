# CI / Linode — situação objetiva R05
**Referência:** 17/11/2026

- CodeRabbit: arquivo de configuração removido, assim como a dependência no CI/CODEOWNERS. O usuário informou ter desinstalado o aplicativo; a revogação em sua conta não é inspecionável por este conector.
- CI: validação de skill, 35 testes unitários de backend, regressões documentais, YAML, shell e ZIP temporário no runner, sem upload da skill. O job de imagem constrói Docker localmente, testa 200/401 e executa **7 testes com Qdrant real descartável e dados DEMO**; a CI não acessa Qdrant de produção.
- GHCR: sem gatilho de push automático; job com if: false.
- Linode staging: workflow remoto GHCR/Actions continua com `if: false`. Contudo, mediante solicitação direta posterior do proprietário em 17/11/2026, foi instalada manualmente imagem local de staging **somente leitura** e isolada: `gaia-rag-mini-staging` (`127.0.0.1:18081`), estado Docker healthy, health HTTP 200 e acesso MCP anônimo 401. Após sanitização: gate `RAG_STAGING_APPROVED=0` efetivo no contêiner; sem autenticação/grants/Qdrant de produção. O Qdrant sintético de teste foi removido após 7 casos aprovados. Não é homologação operacional. Diagnóstico: `RELATORIO_STAGING_INSTALACAO_2026-11-17.md`.
- Origem e separação: DigitalOcean, Cloudflare e Qdrant não foram modificados; agora há execução local isolada na Linode sem credenciais nem acesso aos dados reais.
- DigitalOcean, Cloudflare, Qdrant e portal: nenhum serviço alterado nesta revisão.

Pendente antes de uso real: JWT real e concessões por cliente/processo, metadados `tenant_id` dos registros históricos, proposta com clique humano, instalação de skill no host, integração com Qdrant Cloud real e rollback de produção. Testes A/B sintéticos foram executados; não são prova de isolamento dos dados históricos. Não solicitar segredos apenas para auditar documentos.

Publicação, merge, deploy e modificação da MCP de produção continuam sujeitos a autorização explícita.
