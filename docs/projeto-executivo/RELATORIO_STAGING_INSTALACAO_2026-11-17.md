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

## Sanitização e testes de integração real — continuidade da mesma data local

**Escopo:** apenas o staging GAIA RAG Mini na Linode; nenhum cliente real foi incluído na carga de testes.

### Ações realizadas e comprovadas

1. O `RAG_STAGING_APPROVED` foi alterado de `1` para **`0`** no `/opt/gaia-rag-mini/secrets/runtime.env`, com modo `0600`. O contêiner foi recriado via Compose para absorver a variável: leitura do ambiente do processo confirmou **`RAG_STAGING_APPROVED=0`**.
2. O backup do Compose de antes da correção da rede ficou restrito a modo `0600` para rollback. Não foram apagados dados históricos, volumes de staging ou backups.
3. A imagem `gaia-rag-mini:staging-77e487efef29` manteve `read_only=true`, usuário não-root `10001:10001`, `cap_drop=[ALL]`, 1 GiB de limite de memória, 256 PIDs, sem modo privilegiado. Publicação continua somente em `127.0.0.1:18081`.
4. Hashes Git dos **sete arquivos de runtime** transferidos para o host foram comparados aos blobs do repositório, todos idênticos.
5. O Docker retornou `running/healthy`. Testes HTTP do próprio host: `GET /healthz => 200`, `POST /mcp` sem JWT `=> 401`, `POST /mcp` com JWT artificial inválido `=> 401`.
6. Os quatro contêineres NestGround anteriores permaneceram `running`.
7. Para testar com backend real, foi iniciado um **Qdrant v1.15.5 temporário**, em rede Docker `--internal` exclusiva, armazenamento em `tmpfs`, sem mapeamento de porta pública, com telemetria desligada. Os dados eram seis registros `DEMO` de dois tenants com itens aprovados, não aprovados e sem `tenant_id`.
8. **Sete verificações passaram** contra esse Qdrant efetivo: listagem por escopo; UUID de mesmo/outro tenant e sem tenant; fonte; consulta semântica filtrada; similares de processo autorizado; negação de autorização de outro tenant antes da consulta; negação de similaridade sem permissão para o processo corrente. **A consulta usou vetor numérico determinístico de teste, não a inferência textual hospedada no Qdrant Cloud.**
9. Terminados os testes, o Qdrant sintético, sua rede, a imagem de teste e o script temporário do host foram removidos; `tests/test_live_qdrant_synthetic.py` foi versionado no GitHub e executado novamente na CI, com resultado de sucesso em [GitHub Actions](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44221076949).
10. A CI continua sem publicar imagem nem implantar produção.

### Diagnóstico adicional, somente leitura, da fonte histórica

A coleção Qdrant Cloud `chatgpt_memoria_aprovada` associada à MCP da DigitalOcean retornou **1 registro** na inspeção. As únicas informações examinadas foram existência de metadados e o esquema de índices; o registro retornado **não possui `tenant_id`**, enquanto `namespace`, `process_id` e `approved` estão presentes. O índice `tenant_id` também não consta no esquema observado. **Nenhum payload de cliente foi copiado, modificado ou migrado**. O adaptador R05 intencionalmente nega esse registro até existir mapeamento comprovável.

### Problema do executor SSH do GAIA MCP 100 — ainda independente do staging

A implementação ativa de `ExecutionRuntime` na DigitalOcean usa `max_receipts=64` com recibos apenas em memória, sem expiração/descarte. Isso produz `RECEIPT_CAPACITY` quando novas operações identificadas chegam após saturação. O [repositório-fonte acessível](https://github.com/will-iaguzeski/GaiaAdminTools.v.100) não inclui `src/pocket_mcp/runtime.py` em `main`, embora a imagem ativa contenha esse módulo; **há divergência entre imagem implantada e fonte versionada**.

**Mitigação operacional para este staging:** diagnóstico e execução por SSH sem um novo `operation_id` explícito funcionaram, mas isso não fornece recibo durável e não deve ser considerado solução universal de idempotência. A correção permanente requer sincronizar o código do runtime com a fonte, adicionar ledger persistente ou retenção auditável com tombstones que impeçam replay, ensaiar recuperação e só depois realizar atualização controlada do executor. Não reiniciar o executor compartilhado nem descartar recibos sem reconciliação.

### Bloqueadores efetivos para operação com clientes reais

- Staging não contém `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`, `GAIA_RAG_GRANTS_FILE`, `QDRANT_URL` nem `QDRANT_API_KEY`; o health informa que JWT, grants e Qdrant não estão configurados. A falta de credenciais não foi mascarada por valores falsos.
- O Qdrant Cloud histórico não garante vínculo `tenant_id` e a fonte de autorização por cliente/processo não foi determinada. **Não inferir cliente pelo nome do documento ou pelo UUID**.
- Integração real Cloudflare Access/JWT, seleção da skill no host, teste do portal de aprovação humana, readback e rollback de cutover ainda não foram executados. O staging segue somente leitura, sem escrita Qdrant e sem corte de produção.

**Conclusão precisa:** hardening e testes reais com backend descartável = **APROVADOS**; integração de dados reais/identidade = **BLOQUEADA** por falta de metadados confiáveis, sem degradação dos serviços existentes.
