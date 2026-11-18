# R06 — Migração do domínio de memória: estado verificável

**Data:** 2026-11-18
**Solicitação:** `memory.tight-knit.net/mcp` deve apontar para R06 na Linode, preservando serviço antigo DigitalOcean em `legacy-rag.tight-knit.net/mcp`.

## Executado no Cloudflare

1. Application `GAIA Memory Qdrant (independente)` (ID `660c27d1-2596-4a48-965d-fa17dcb4e890`) mantém `mcp`, OAuth + Dynamic Client Registration e uma única política `GAIA Memory Owner Only`. `destinations`: `memory.tight-knit.net` e `legacy-rag.tight-knit.net`. Audience preservada.
2. Tunnel DO `bcd5026a-0b75-42e3-9d35-0dacfac89b3c`: ingress de ambos os endereços para `http://gaia-qdrant-memory-candidate:8000`, ambos com `originRequest.access.required=true`.
3. DNS `legacy-rag.tight-knit.net`: CNAME proxied para tunnel DO (registro ID `6d9450eb762349303707c1876c81a0b0`).
4. `https://legacy-rag.tight-knit.net/mcp` responde 401 sem token (autorização obrigatória); metadados `/.well-known/oauth-protected-resource/mcp` e `/.well-known/oauth-authorization-server` respondem 200.
5. Tunnel remoto R06 Linode criado (ID `e1cad7db-b06e-4adf-8c46-f972bd18db50`, nome `gaia-rag-r06-linode-20261118`), ingress preparado para `memory.tight-knit.net` → `http://gaia-rag-mini-r06-preview:8000`, com JWT Cloudflare Access obrigatório. **Ainda INATIVO: sem conector cloudflared nesse host.**
6. DNS principal `memory.tight-knit.net` continua apontando para tunnel DO. **Não ocorreu corte do serviço principal.**

## Bloqueio antes do corte

A R06 no servidor Linode `127.0.0.1:18082` está saudável. **Após a preparação adicional de identidade**, `jwt_configured=true`, `owners_configured=true`, `qdrant_configured=false` e `writes_enabled=false`. O arquivo de proprietários é mantido em volume somente leitura no container, e `CF_ACCESS_AUD`/issuer foram configurados sem expor tokens. O código revisado da R06 suporta `QDRANT_API_KEY_FILE` para uso posterior de segredo montado; o CI dessa alteração foi aprovado. A integração com Qdrant Cloud e o conector cloudflared da Linode ainda exigem provisionamento seguro de credenciais. **Uma tentativa de transferência automatizada de segredos foi bloqueada pelo ambiente; não contornar.** Arquivos temporários de certificação dessa tentativa foram eliminados. O endereço principal permanece no serviço funcional anterior até o provisionamento feito por canal autorizado.

A coleção Qdrant Cloud `chatgpt_memoria_aprovada` contém **1 ponto registrado** na consulta de 18/11/2026 (não apagar ou declarar vazia). O contrato de consulta Qdrant R06 por texto e o `scroll` de memória aprovada responderam 200 à consulta sem escrita feita a partir do serviço anterior.

## Próximos passos

1. Provisionar **por canal operacional autorizado, sem colar credenciais no chat**, a URL e o token Qdrant na Linode, autenticação Cloudflare Access e lista de proprietários. Utilizar `QDRANT_API_KEY_FILE` no código atualizado para permitir bind mount de segredo, sem variável em `docker inspect`.
2. Validar autenticação e leitura com o Qdrant real em R06 antes de apontar o endereço público. Escrita e revisão continuam desligadas até aprovação documental e armazenamento durável.
3. Provisionar credencial cloudflared da nova tunnel Linode por canal autorizado; confirmar status `healthy` e testes protegidos de origem.
4. Mudar SOMENTE o CNAME `memory.tight-knit.net` para `e1cad7db-b06e-4adf-8c46-f972bd18db50.cfargotunnel.com`, quando pronto; validar HTTPS/OAuth/MCP e leitura real; em erro restaurar DNS anterior.
5. Após validação, retirar o hostname principal do tunnel DO, deixando somente `legacy-rag.tight-knit.net`; atualizar `MEMORY_PUBLIC_URL` da instância legada se necessário para links de revisão.

**Estado final em 18/11/2026:** endereço legado criado/protegido e tunnel Linode configurado, mas o **cutover principal NÃO foi executado** para evitar indisponibilidade.
