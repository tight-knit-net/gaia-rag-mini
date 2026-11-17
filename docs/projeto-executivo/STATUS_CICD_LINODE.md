# Status CI/CD e Linode — observações e limitações
**Data-base:** 17/11/2026. **Regra vigente:** somente documentação, validação e revisão; código, build, publicação e implantação não autorizados.

## Infra já preparada em fase anterior (sem novas alterações agora)
- Linode `nestground-ai` em Akamai `akamai-william`, Ubuntu 24.04.5, 4vCPU/8GB; Docker 29.9.2 e Docker Compose 5.6.1.
- SSH de administração existente; usuário `gaia-rag-deploy` criado com comando forçado. Teste local de `probe` e rejeição de comando não permitido passaram.
- Diretório `/opt/gaia-rag-mini`, Docker Compose de staging e segredo runtime vazio. Nenhum container GAIA RAG foi iniciado. Quatro containers NestGround foram preservados.
- RAM e disco são snapshots, não demonstração de capacidade garantida.

## PR documental — configurações versionadas para REVISÃO, não operação
- `r05-skill-static.yml`: validação documental, empacotamento privado na Action; evidências de 23 testes estáticos, sem host.
- `.coderabbit.yaml`: instruções de revisão de arquitetura, CI, dados e segurança. O vínculo do CodeRabbit foi informado pelo proprietário; reviews no PR ainda precisam ser observados.
- `rag-ghcr-image.yml`: **sem push automático, com job `if: false`**. Não pode publicar no GHCR mesmo com merge acidental, sem futura alteração revisada.
- `rag-linode-staging.yml`: **job `if: false`**. Não pode executar preflight/deploy, sem futura alteração revisada.
- `LINODE_DEPLOY_KEY`: NÃO criar nem configurar agora; nenhum segredo é necessário à revisão documental.

## Antes de usar os pipelines futuramente
Concluir e revisar o projeto executivo, obter autorização separada para iniciar código, validar origem DO, comprovar CodeRabbit, executar CI de código; somente então propor habilitar GHCR ou Linode por novo PR e autorização específica. Preservar Cloudflare Access, Tunnel, Qdrant e o portal humano.

## Gaps ainda reais
Código completo de produção e testes não migrados ao GitHub; CodeRabbit ainda sem parecer registrado para este PR; ausência de execução de GHCR/private pull; ausência de SSH GitHub runner → Linode; ausência de sandbox equivalente e de teste do portal; nenhuma homologação operacional.

**Não executar ou solicitar ações manuais ao usuário nesta fase.**
