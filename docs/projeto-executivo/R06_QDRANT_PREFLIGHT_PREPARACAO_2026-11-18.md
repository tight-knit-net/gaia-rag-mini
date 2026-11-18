# GAIA RAG Mini R06 — Pré-implantação de leitura Qdrant e validação OAuth/JWT

**Data da revalidação:** 18/11/2026  
**Status:** **NO-GO para transferência de DNS**; R06 saudável, Cloudflare Tunnel saudável, mas **credencial própria Qdrant e homologação JWT real do proprietário pendentes**.  
**Escopo:** apenas leitura da coleção existente; escrita e registro documental não ativados. Nenhum merge.

## 1. Evidências operacionais efetivamente obtidas

- Linode `nestground-ai`, GAIA MCP v.100 alias `tigh_knit`: `gaia-rag-mini-r06-preview` executa `gaia-rag-mini:r06-owner-auth-ready`, `GET http://127.0.0.1:18082/healthz` responde HTTP 200 com `jwt_configured=true`, `owners_configured=true`, `qdrant_configured=false`, `writes_enabled=false`, `approval_registry_configured=false`.
- Túnel Linode `e1cad7db-b06e-4adf-8c46-f972bd18db50` reportado pela API Cloudflare como **healthy, 4 conexões**. Túnel antigo DigitalOcean `bcd5026a-0b75-42e3-9d35-0dacfac89b3c` também **healthy, 4 conexões**.
- `memory.tight-knit.net` e `legacy-rag.tight-knit.net` continuam com CNAME proxied apontando para `bcd5026a-0b75-42e3-9d35-0dacfac89b3c.cfargotunnel.com`. **Nenhuma alteração DNS realizada.**
- R06 origin HTTP 200 na rede Docker `gaia-rag-r06-preview-net`, resolvendo `gaia-rag-mini-r06-preview:8000`. R05 `127.0.0.1:18081/healthz` também HTTP 200.
- Ambos hostnames existentes: `/mcp` sem token retorna **401**, discovery `/.well-known/oauth-protected-resource/mcp` retorna **200**, discovery `/.well-known/oauth-authorization-server` retorna **200** com authorization/token/registration endpoints presentes.
- MCP interno `tools/list` sem token e com JWT intencionalmente inválido retornou **401**. JWKS pública do issuer `https://tight-knit.cloudflareaccess.com/cdn-cgi/access/certs` expôs 2 chaves RSA (nenhuma chave privada).
- Inspeção local do R06 confirmou correspondência **exata** entre o issuer configurado, audience `e80d673dfb652a20d7f3847faef1aa6183711641cb855bf010691d8186387c47` e duas identidades de proprietário previstas. Política Access `GAIA Memory Owner Only` inclui somente as duas identidades previstas; não inclui `office@govhubsuite.com`, nem everyone.
- **Esses testes NÃO provam login OAuth final do proprietário, JWT real aceito, `tools/list` autenticado nem leitura Qdrant pela R06.**

## 2. Qdrant Cloud existente: contagem atualizada e compatibilidade

Consulta **somente leitura** efetuada do serviço legado DigitalOcean, sem exibição ou movimentação da credencial:

- Endpoint: `https://9cc1ac99-0719-41fe-bd7e-60e9aed12815.us-central1-0.gcp.cloud.qdrant.io`.
- Coleção: `chatgpt_memoria_aprovada`; vetores **384** dimensões, distância **Cosine** (configuração anteriormente confirmada).
- `POST .../points/count` `exact=true`: HTTP **200**, **14 pontos**. A auditoria anterior registrava **1 ponto**; a contagem foi atualizada, não presumir banco vazio/1 registro.
- Contagem filtrada `namespace=chatgpt AND approved=true`: HTTP **200**, **14**.
- `scroll` `limit=100`, `with_vector=false`: HTTP **200**, 14 payloads, sem paginação restante; 14 com `approved=true`, 14 com `namespace=chatgpt`, 14 com `process_id`, **10 `process_id` distintos**, **zero com campo `tenant_id`**, 14 com `source_ref`.
- Consulta textual via `intfloat/multilingual-e5-small` com filtro aprovado/namespace: HTTP **200**, 8 hits sob limite 8.
- Nenhuma memória, coleção ou vetor foi criado, modificado, apagado ou recriado. Nenhum texto de cliente/processo foi exposto nesta evidência.
- O modelo de leitura `ScopedReads.search_all_owner` não deve impor `tenant_id` e deve respeitar `approved=true`, `namespace` e `process_id` exato nas operações por processo. A capacidade transversal entre *clientes* exige homologação real do proprietário após conexão; o conjunto histórico não possui `tenant_id`.

## 3. Artefatos não secretos preparados nesta execução — Linode

**Arquivos instalados e validados:**

1. `/usr/local/sbin/gaia-r06-provision-qdrant-key` — `root:root` modo `0700`; comando `--status` não revela dados. Exige terminal SSH/LISH interativo + `sudo`, solicita *Database API Key* por `getpass` (entrada oculta), recusa argumentos e sobrescrita, grava atomicamente em `/opt/gaia-rag-mini/secrets/r06-service/qdrant_api_key` com proprietário **UID:GID 10001:10001**, modo **0400**. Não inicia serviço.
2. `/usr/local/sbin/gaia-r06-qdrant-readonly-preflight` — `root:root` modo `0700`; somente operações **GET collection**, **POST points/count**, **POST points/query** e filtros aprovados; não exibe chave nem texto de memória; comprova 384/Cosine, contagem, namespace/approved e busca real pelo modelo. Teste negativo sem arquivo concluiu com erro informativo e sem modificação.
3. `/opt/gaia-rag-mini/r06-preview/qdrant-readonly.compose.yaml` — `root:root` modo `0644`; **candidato, não implantado**; `docker compose config --quiet` aprovado. Preserva imagem R06 existente, UID 10001, read-only rootfs, cap drop ALL, no-new-privileges, restart unless-stopped, bind RO `/opt/gaia-rag-mini/secrets/r06-service:/run/gaia`, `127.0.0.1:18082:8000`, rede Docker `gaia-rag-r06-preview-net`, tmpfs de `/state` e `/tmp`, variáveis não secretas `QDRANT_URL` e `QDRANT_API_KEY_FILE=/run/gaia/qdrant_api_key`, preservando env_file existente.
4. O arquivo `qdrant_api_key` continua **ausente**; portanto não houve reinicialização ou troca da R06. O `healthz` corretamente continua `qdrant_configured=false`.

**Não executar `docker compose up` sobre o contêiner de mesmo nome enquanto a credencial não estiver provisionada e validada, nem remover o contêiner original.** Fazer operação de troca controlada com nome/rollback explícitos, confirmar readback real e JWT de proprietário antes de promover qualquer URL.

## 4. Bloqueio e método autorizado de desbloqueio

O painel `https://cloud.qdrant.io/` exige login; ainda não há comprovação de qual conta é proprietária do cluster. Nenhum login foi escolhido ao acaso. O catálogo do GAIA MCP v.100 não apresentou operação de gerenciamento de Database API Keys do Qdrant Cloud; o conector GAIA RAG existente tem acesso ao Qdrant, mas **suas credenciais não foram extraídas nem transportadas**.

**Ação externa de autenticação necessária:**

1. Entrar em `https://cloud.qdrant.io/` na **conta que possui o cluster do endpoint indicado**. Selecionar o cluster correspondente, **API Keys**, e criar **Database API Key própria para a R06, somente leitura e limitada à coleção `chatgpt_memoria_aprovada`**, conforme suporte de RBAC granular do Qdrant Cloud. Não confundir com Cloud Management API Key. Não mostrar, colar ou enviar a chave no ChatGPT.
2. No console SSH/LISH **do `nestground-ai`**, usar `sudo /usr/local/sbin/gaia-r06-provision-qdrant-key`, colando **somente o valor da chave na entrada oculta**. Nunca colar em ferramenta ChatGPT, GitHub, logs, argumento CLI, terminal do servidor incorreto ou variável de ambiente pública.
3. Após o arquivo existir, executar `sudo /usr/local/sbin/gaia-r06-qdrant-readonly-preflight`; só prosseguir se exibir `QDRANT_R06_READ_PREFLIGHT_PASS` e contagem real. Confirmar que nenhum dado foi alterado.
4. Só então realizar *redeploy* controlado da R06 com `qdrant-readonly.compose.yaml`, mantendo a imagem original e contêiner renomeado como rollback; validar `healthz`, comunicação pelo nome na rede, `tools/list` com token Access **real do proprietário**, `memory_search_all`, `memory_list_process` para qualquer `process_id`, negação a não autorizado, OAuth/DCR pelo hostname de teste ou etapa de cutover controlado. Não liberar produção por um mero `qdrant_configured=true`.
5. Após TODOS os testes, mudar somente CNAME `memory.tight-knit.net` para `e1cad7db-b06e-4adf-8c46-f972bd18db50.cfargotunnel.com`, confirmar HTTPS/OAuth/JWT/MCP/readback público. Se falhar, restaurar CNAME para túnel DigitalOcean. Somente depois de sucesso remover hostname principal do ingress antigo, **preservando `legacy-rag.tight-knit.net`**.
6. Escrita Qdrant, registro documental, revisão humana persistente e aprovação seguem **desativados**; uma chave de leitura R06 não habilita o fluxo de gravação.

**Estado final desta execução:** infraestrutura de leitura preparada e testada sem credenciais; `TUNNEL HEALTHY`, `QDRANT R06 NOT CONFIGURED`, `JWT REAL / MCP TOOLS AUTHENTICATED NOT HOMOLOGATED`, `DNS NOT CUT OVER`. Nenhum segredo publicado; R05, DO, ZITADEL e outros serviços preservados.
