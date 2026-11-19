# ADR-0002 — Congelamento obrigatório de publicação e implantação
**Status:** DECISÃO VIGENTE PARA ESTA REVISÃO; efetivada na branch documental, sem merge.

## Contexto
O proprietário determinou que esta fase sirva exclusivamente para concluir, organizar, validar e submeter o projeto executivo à revisão. Não autorizou início do desenvolvimento de runtime, publicação de pacotes ou imagens, deploy na Linode, merge ou mudança da MCP.

## Decisão
1. `.github/workflows/rag-ghcr-image.yml` não possui trigger `push` e mantém seu job `if: false`.
2. `.github/workflows/rag-linode-staging.yml` mantém `if: false`, independentemente do `workflow_dispatch`.
3. `.github/workflows/r05-skill-static.yml` valida temporariamente o conteúdo ZIP **somente no runner**, sem `actions/upload-artifact` e sem release; o CI verifica expressamente que os dois jobs de publicação/implantação permanecem desabilitados.
4. Todo o conteúdo R05 permanece em PR para revisão, sem integrar automaticamente a `main`.
5. Scripts e Compose são artefatos de design sob revisão, não sistemas autorizados a executar.
6. Não usar secrets, chaves, tokens, ferramentas de autofix/revisão automática, operações Cloudflare ou Docker nesta fase.
7. Nenhuma autorização para iniciar código é inferida do aceite documental; cada gate tem decisão própria.

## Justificativa
O pipeline de imagem anterior permitia publicação GHCR em push para `main` quando existisse Dockerfile. Isso era incompatível com a restrição expressa de não publicar. A mudança proposta impede qualquer publicação ou deploy por esses workflows, mesmo que sejam incluídos na `main` por engano, até nova revisão com autorização.

## Critério futuro para alterar esta decisão
É necessária solicitação explícita do proprietário, além de:
- DG-01..DG-06 concluídos (para código);
- Código/testes e revisão de segurança aprovados (para build);
- Homologação em sandbox com ACL/portal e rollback, com novos gates e aprovação específica (para staging);
- Plano de mudança e autorização separada (para produção).

Nenhuma dessas condições é atendida apenas pela emissão de um parecer técnico; os demais gates e autorizações permanecem obrigatórios.
