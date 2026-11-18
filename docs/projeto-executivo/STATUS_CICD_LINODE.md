# CI / Linode — situação objetiva R05
**Referência:** 17/11/2026

- CodeRabbit: arquivo de configuração removido, assim como a dependência no CI/CODEOWNERS. O usuário informou ter desinstalado o aplicativo; a revogação em sua conta não é inspecionável por este conector.
- CI estática: validação de skill, regressões documentais, YAML, shell e ZIP temporário no runner, sem upload da skill.
- GHCR: sem gatilho de push automático; job com if: false.
- Linode staging: job com if: false; nenhuma implantação autorizada.
- Histórico anterior: host nestground-ai com Docker/Compose e pasta /opt/gaia-rag-mini preparada, sem inicialização de RAG nesta etapa. Não houve inspeção operacional recente.
- DigitalOcean, Cloudflare, Qdrant e portal: nenhum serviço alterado nesta revisão.

Pendente antes de uso real: ACL efetiva, proposta e clique humano, dependência e ativação da skill no host, testes negativos A/B, falha/rollback. Não solicitar segredos apenas para auditar documentos.

Publicação, merge, deploy e modificação da MCP de produção continuam sujeitos a autorização explícita.
