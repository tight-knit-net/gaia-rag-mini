# CI/CD R05 + Linode — configuração verificada
**Data-base:** 17/11/2026.
**Repositório:** tight-knit-net/gaia-rag-mini, privado. Toda preparação nesta etapa está no PR #1 em rascunho, branch docs/r05-gaia-rag-homologacao. A branch main não foi alterada nesta configuração.

## Workflow: pacote / revisão
- `.github/workflows/r05-skill-static.yml`: linter de skill, 23 testes de regressão estática, ZIP e SHA256; já homologado no CI documental (não na MCP).
- `.coderabbit.yaml`: idioma pt-BR, revisões automáticas e PRs draft, instruções de revisão por path.
- App GitHub do CodeRabbit: precisa ser habilitada/autorizada no repositório pelo titular. A presença do YAML, isoladamente, não instala o aplicativo.

## Workflow: imagem Docker
- `.github/workflows/rag-ghcr-image.yml`: publicação no GHCR a partir da main após Dockerfile e servidor Python estarem disponíveis. Usa o GITHUB_TOKEN efêmero, sem PAT persistente, e gera referência imutável do digest.
- NÃO existe código Dockerfile na main no início desta preparação; portanto não foi publicada imagem.

## Workflow: deployment manual
- `.github/workflows/rag-linode-staging.yml`: workflow_dispatch somente em main, com modo preflight ou deploy de digest SHA256. Usa SSH com known_hosts pinado e o secret LINODE_DEPLOY_KEY a ser criado por usuário.
- Conta de destino: Akamai/Linode akamai-william, host nestground-ai, SSH público 172.235.134.117.
- Usuário novo: gaia-rag-deploy. authorized_keys com restrict e forced-command; sem login interativo e sem sudo genérico. Código dos scripts de instalação/deploy está versionado em `.github/deploy/linode/`.
- O deploy script permite apenas `probe` ou `deploy sha256:<64hex> <github-actor>` e imagem `ghcr.io/tight-knit-net/gaia-rag-mini@sha256:...`. GITHUB_TOKEN é transmitido por SSH no stdin, usado em login GHCR temporário e removido após a operação.
- Compose existente em `/opt/gaia-rag-mini/staging/compose.yml`; porta `127.0.0.1:18081:8000`, nome container `gaia-rag-mini-staging`, limites 1 vCPU/1 GiB, cap_drop ALL, read-only e volume separado.
- Segredos reais NÃO foram copiados. `/opt/gaia-rag-mini/secrets/runtime.env` inicia vazio, modo 600 root; flag `RAG_STAGING_APPROVED=1` ausente bloqueia implantações.
- A validação bash, sudoers, Docker Compose e teste de `probe` do usuário restrito passaram na Linode. Comando arbitrário negado.
- Nenhuma instância RAG nova foi iniciada; os containers NestGround e a rota Cloudflare/DigitalOcean atuais foram mantidos.

## Para concluir a conexão GitHub → Linode
1. Salvar o conteúdo integral do arquivo privado LINODE_DEPLOY_KEY no secret GitHub Actions com o mesmo nome, em https://github.com/tight-knit-net/gaia-rag-mini/settings/secrets/actions .
2. Autorizar o CodeRabbit GitHub App em https://github.com/apps/coderabbitai selecionando explicitamente tight-knit-net/gaia-rag-mini.
3. Incorporar a configuração por PR após a revisão. GitHub Actions workflow_dispatch precisa existir na branch main para acionamento na UI.
4. Rodar o modo preflight do workflow; isso verifica SSH real a partir de um runner GitHub.
5. Somente após portar/revisar código e configurar GHCR, testar ambiente sintético e habilitar gate explícito RAG_STAGING_APPROVED=1, autorizar a primeira implantação de teste.
6. Manter a migração de produção, Qdrant, tunnel e política humana fora de escopo até gates de homologação operacionais.

## Pendências / não comprovado
- CodeRabbit GitHub App efetivamente instalada
- GitHub secret cadastrado; SSH externo vindo de runner GitHub
- Build de imagem real no GHCR; acesso de pull ao pacote privado
- Runtime Python portado / variáveis do ambiente de homologação
- Homologação de ACL por tenant e portal humano, rollback e migração real

## Rollback
Nenhum container foi criado, portanto não há rollback de runtime necessário. Em implantação futura, o script guarda a referência da imagem anterior e restaura o apontamento quando o comando compose up falhar; o corte Cloudflare permanece fora do pipeline.
