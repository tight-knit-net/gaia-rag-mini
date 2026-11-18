# GAIA RAG Mini R05 — diagnóstico e instalação em staging

**Data local:** 17/11/2026 (America/Sao_Paulo)  
**Alvo:** Linode/Akamai `nestground-ai`, alias SSH `tigh_knit`  
**Modo:** staging isolado, somente leitura; sem cutover da DigitalOcean

## Evidência observada

- SSH para `nestground-ai` funciona pelo alias configurado; quatro contêineres NestGround preexistentes preservados.
- O erro `HTTP 503 / RECEIPT_CAPACITY` veio do transporte de comandos do GAIA MCP100, não do SSH da Linode. O código do executor em `/app/src/pocket_mcp/runtime.py` define `max_receipts=64`, armazena recibos somente durante a vida do processo e nega novas operações identificadas ao atingir a capacidade. O diagnóstico sem `operation_id` conseguiu executar comandos. **A saturação da camada de recibos não foi corrigida de forma permanente; não reiniciar o serviço nem descartar recibos sem reconciliação das operações existentes.**
- O servidor `nestground-ai` tinha cerca de 138 GB livres, 5,4 GiB de RAM disponível e Docker operacional. Não havia GAIA RAG Mini instalado.
- Criada a imagem local `gaia-rag-mini:staging-77e487efef29` a partir do runtime versionado no PR #3.
- O primeiro Docker Compose usou automaticamente a subnet `172.17.0.0/16`. A tabela de roteamento 65743 do Cloudflare WARP interceptava destinos `172.17.0.2`, causando timeout de `127.0.0.1:18081` apesar do healthcheck interno saudável.
- Corrigido **somente o Compose de staging** para usar a subnet dedicada `172.19.41.0/24`. Verificado que `172.19.41.2` tem rota pela ponte local.
- `docker compose up -d --pull never --no-build --wait` retornou sucesso; `gaia-rag-mini-staging` está `running healthy`.
- GET `http://127.0.0.1:18081/healthz`: **HTTP 200**.
- POST `http://127.0.0.1:18081/mcp` sem JWT: **HTTP 401**, resposta `ACCESS_DENIED`.
- OpenWebUI existente em `127.0.0.1:3000`: **HTTP 200**. Quatro contêineres NestGround originais permaneceram ativos.
- Porta publicada apenas no loopback `127.0.0.1:18081`. Nenhum roteamento público ou Cloudflare Tunnel foi modificado.

## Limites deliberados desta implantação

O health retornou `jwt_configured=false`, `grants_configured=false`, `qdrant_configured=false` e `writes_enabled=false`. Isso significa **imagem executável instalada e HTTP operacional**, porém a MCP R05 **ainda não está autenticada, conectada a dados nem homologada para uso com clientes**. Nenhum token, dado real, payload ou segredo foi transferido.

Cloudflare, coleção Qdrant e MCP antiga na DigitalOcean não foram alterados. Workflows de publicação e deploy GHCR/Linode seguem desativados. Não houve merge do PR #1 ou #3.

## Pendências rastreáveis

1. Corrigir a saturação de recibos no executor SSH do GAIA MCP100 por manutenção com reconciliação do estado anterior, sem apagar evidências de operações em andamento.
2. Integrar JWT verificado, grants por sujeito/tenant/processo e compatibilidade dos dados com `tenant_id`, mantendo negação padrão.
3. Validar o host real de MCP e a origem confiável de autorização antes de liberar consultas de cliente ou migração.
4. Em mudança distinta, testar portal humano, readback, rollback e eventual cutover, sem inferir autorização do sucesso do healthcheck.
