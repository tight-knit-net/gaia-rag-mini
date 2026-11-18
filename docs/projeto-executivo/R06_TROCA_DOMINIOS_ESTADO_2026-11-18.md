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


---

## Revalidação operacional independente — 18/11/2026 (pré-corte, MCP 100 + Cloudflare + GitHub)

**Conclusão: NO-GO para o corte de DNS.** O estado observado permanece de migração preparada e NÃO concluída. Esta atualização é somente documentação; nenhuma alteração de DNS, Access, Qdrant, serviço legado, R05 ou ZITADEL foi feita nesta etapa. Não realizar merge por causa deste relatório.

### Servidores e contêineres

- **Linode**, alias SSH `tigh_knit`, host `nestground-ai`: `gaia-rag-mini-r06-preview` executa `gaia-rag-mini:r06-owner-auth-ready` e respondeu **200** em `http://127.0.0.1:18082/healthz`. Corpo retornado: `jwt_configured=true`, `owners_configured=true`, `qdrant_configured=false`, `writes_enabled=false`, `approval_registry_configured=false`. O origin `http://gaia-rag-mini-r06-preview:8000/healthz` respondeu **200** a partir da rede Docker `gaia-rag-r06-preview-net`, comprovando a resolução do nome e a comunicação Docker interna.
- O contêiner R06 roda como **UID:GID 10001:10001** e contém suporte a `QDRANT_API_KEY_FILE`, modelo `intfloat/multilingual-e5-small` e coleção `chatgpt_memoria_aprovada`. O arquivo de chave previsto em `/opt/gaia-rag-mini/secrets/r06-service/qdrant_api_key` **não existe**. Uma chave futura precisa ser fornecida por canal autorizado, com permissões de leitura para UID/GID do serviço e montagem *read-only*, sem impressão no terminal, argumentos sensíveis, respostas ou logs. As credenciais existentes no serviço antigo NÃO foram transferidas.
- A R05 independente `gaia-rag-mini-staging` respondeu **200** em `127.0.0.1:18081/healthz` e não foi alterada.
- **DigitalOcean**, alias `mcp-100-do`: contêiner antigo `gaia-qdrant-memory-gaia-qdrant-memory-candidate-1` e túnel `gaia-qdrant-memory-tunnel` estão em execução, o primeiro **healthy**. Só foram conferidos os **nomes** das variáveis Qdrant; seus valores não foram expostos.

### Coleção Qdrant existente — testes somente leitura executados a partir da DigitalOcean

- `GET /collections/chatgpt_memoria_aprovada` → **200**. Vetores de **384 dimensões**, distância **Cosine**.
- `POST .../points/count` com `exact=true` → **200**, **1 ponto**. `POST .../points/scroll` → **200**.
- O único ponto tem `approved=true`, `namespace=chatgpt`, `process_id` presente e **nenhum `tenant_id`**. A contagem com filtro `namespace=chatgpt AND approved=true` retornou **1**.
- `POST .../points/query` por texto, modelo `intfloat/multilingual-e5-small` → **200**, **1 ponto encontrado**.
- Nenhum ponto foi apagado, criado, recriado ou modificado. Esses resultados comprovam o formato histórico e a leitura no **serviço anterior**, NÃO uma consulta autenticada a partir da R06.
- Com apenas um registro real, **não é possível homologar por dados reais dois clientes distintos**. A compatibilidade de leitura transversal está implementada no código da branch e foi coberta por testes sintéticos, mas a validação ao vivo da identidade e da R06 permanece pendente.

### DNS, Tunnel, OAuth e Access — estados verificados na API Cloudflare

- Zona `tight-knit.net` `e97de8d11151b5e73bee4dbf62519a44`; CNAME principal `memory.tight-knit.net`, ID `102e5d08fc4159d1d12e9f0a2f43e0bf`, permanece **proxied** para **`bcd5026a-0b75-42e3-9d35-0dacfac89b3c.cfargotunnel.com`**. Este é o valor exato de **rollback**, caso haja corte futuro.
- CNAME legado `legacy-rag.tight-knit.net`, ID `6d9450eb762349303707c1876c81a0b0`, permanece no mesmo destino antigo. Preservar.
- Túnel antigo `bcd5026a-0b75-42e3-9d35-0dacfac89b3c`: **healthy**, 4 conexões. Ingress atual contém `memory` e `legacy-rag`, ambos para `http://gaia-qdrant-memory-candidate:8000`, Access obrigatório.
- Túnel novo `e1cad7db-b06e-4adf-8c46-f972bd18db50`: **inactive**, 0 conexões. Ingress preparado `memory.tight-knit.net` → `http://gaia-rag-mini-r06-preview:8000`, Access obrigatório. Existe imagem `cloudflare/cloudflared:2026.8.3` na Linode, mas não há conector R06 em execução; a credencial do túnel não foi provisionada. Não copiar token para chat ou argumentos/logs; utilizar secret management autorizado e `--token-file` ou equivalente.
- Aplicação Cloudflare Access `660c27d1-2596-4a48-965d-fa17dcb4e890`, tipo MCP, preservada com os dois destinos, política única `GAIA Memory Owner Only`. A política permite exatamente as duas identidades de proprietário previstas; nenhuma regra everyone/bypass, e `office@govhubsuite.com` não foi incluída.
- Ambos os endereços públicos existentes: `GET /mcp` sem autenticação → **401**; `/.well-known/oauth-protected-resource/mcp` → **200**; `/.well-known/oauth-authorization-server` → **200**, com `authorization_endpoint`, `token_endpoint` e `registration_endpoint` presentes. O origin privado R06 também respondeu **401** ao `tools/list` sem JWT.
- Estes testes **não** comprovam login OAuth real do proprietário nem `tools/list` autenticado da R06, pois a R06 ainda não foi exposta e não recebeu Qdrant.

### Pendências bloqueantes, sem contorno de políticas

1. Acesso à console **Qdrant Cloud** pelo navegador apresentou login/seleção de conta Google; nenhuma conta foi escolhida automaticamente. Criar credencial **própria, de preferência somente leitura e restrita à coleção**, por operador autenticado ou API de gerenciamento legitimamente autorizada; entregar por secret manager aprovado, nunca usar o segredo da DigitalOcean.
2. Provisionar na Linode `QDRANT_URL` e `QDRANT_API_KEY_FILE` (arquivo legível ao UID 10001), sem habilitar escrita. Validar `healthz`, coleção, contagem 1 e `memory_search_all`/ferramentas com JWT real de proprietário, incluindo registro histórico sem tenant.
3. Provisionar o token do túnel Linode por meio autorizado, **fora do chat/logs/argumentos de processo**; conectar `cloudflared` à rede `gaia-rag-r06-preview-net` e verificar `healthy` com conexões ativas antes de modificar o DNS.
4. Homologar OAuth/DCR e `tools/list`/consultas pelo **hostname R06** com a identidade proprietária; confirmar 401 anônimo e negação a não proprietário.
5. **Somente se todos os critérios passarem**, alterar exclusivamente o CNAME principal para `e1cad7db-b06e-4adf-8c46-f972bd18db50.cfargotunnel.com`, testar HTTPS/OAuth/MCP/consulta real, e só então retirar `memory.tight-knit.net` do ingress antigo, preservando `legacy-rag`. Reverter para o destino antigo acima se qualquer critério falhar.
6. Registro documental de aprovação, portal humano autenticado, banco persistente de revisão e segurança de gravação **ainda não homologados**. `writes_enabled=false` deve permanecer.

**Evidência de código:** branch `feat/r06-lifecycle-skill-staging`, PR #4 **draft**; HEAD auditado antes deste adendo `6571f260df8a806215baa3240da7b3203fec2d86`. Documento de arquitetura `R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md` e teste sintético `tests/r06_live_review_e2e.py`. Este adendo documenta auditoria de produção, sem alegar homologação completa.

---

## R06 — Auditoria do reparo do túnel na Linode (18/11/2026, 09:39–09:41 UTC)

**Resultado observado: TÚNEL R06 AINDA BLOQUEADO.** Não foi instalado conector sem o token, pois não existe canal aprovado disponível para entregar o segredo diretamente Cloudflare → host. Os valores *inactive / 0 conexões* referem-se à auditoria Cloudflare anterior e NÃO foram revalidados pela API autenticada nesta execução.

### Auditoria na Linode pelo Gaia MCP v.100

- Acesso SSH: alias **tigh_knit**, hostname **nestground-ai**, usuário **gaia-admin**, sudo não interativo habilitado; Docker Server **29.9.2**.
- R06: **gaia-rag-mini-r06-preview**, imagem **gaia-rag-mini:r06-owner-auth-ready**, Docker status **running / healthy**, restart **unless-stopped**; rede **gaia-rag-r06-preview-net**. Porta da R06 publicada exclusivamente em **127.0.0.1:18082 → 8000/tcp**.
- Testes diretos: **HTTP 200** em http://127.0.0.1:18082/healthz; **HTTP 200** em http://gaia-rag-mini-r06-preview:8000/healthz de dentro da rede Docker, com service **gaia-rag-mini-r06**. Resposta confirma jwt_configured=true, owners_configured=true, qdrant_configured=false, writes_enabled=false, approval_registry_configured=false.
- **HTTP 401** em GET /mcp local sem token: autorização obrigatória preservada.
- **Nenhum contêiner cloudflared** R06, ativo ou parado; nome pretendido **gaia-rag-r06-cloudflared** inexistente. Imagem **cloudflare/cloudflared:2026.8.3** já está presente; versão e suporte CLI a **tunnel run --token-file** confirmados. Imagem executa com UID:GID **65532:65532**.
- **Arquivo de token NÃO EXISTE** em /opt/gaia-rag-mini/secrets/r06-service/cloudflare_tunnel_token. Diretórios de segredo têm acesso restritivo; ajustar leitura apenas para UID/GID do cloudflared quando o segredo for provisionado por operador.
- Teste de conectividade HTTPS para api.cloudflare.com chegou ao servidor (HTTP 400 sem credenciais, TLS validado), mas **não** valida autenticação Cloudflare nem estado do túnel.
- R05 **gaia-rag-mini-staging** permaneceu **running / healthy**. Outros contêineres R06 de rollback não foram modificados.
- A única alteração incidental no host foi o download da imagem auxiliar **curlimages/curl:latest** para validar a rede com contêiner efêmero --rm. Nenhum serviço persistente foi alterado.

### Preservação externa, verificada sem escrita

- DigitalOcean (SSH alias **mcp-100-do**): serviço **gaia-qdrant-memory-gaia-qdrant-memory-candidate-1 running / healthy** e contêiner antigo **gaia-qdrant-memory-tunnel running**. A porta 127.0.0.1:8000 no host DO não estava disponível; o estado saudável foi verificado no Docker.
- https://memory.tight-knit.net/mcp → **HTTP 401** sem autenticação.
- https://legacy-rag.tight-knit.net/mcp → **HTTP 401** sem autenticação.
- **Nenhuma solicitação de alteração de DNS, ingress, Access, ZITADEL, Qdrant, R05, R06 ou serviço antigo foi realizada.** CNAME exato dos dois hostnames, status do novo túnel e conexões históricas não puderam ser revalidados nesta execução por ausência de integração autenticada com API Cloudflare; consulta DNS pública em hostname proxied não fornece diretamente o CNAME do túnel.

### Causa e bloqueio seguro

**Causa técnica identificada:** ausência do processo cloudflared R06 e do respectivo token no destino previsto. O origin R06 já funciona na rede Docker. **Bloqueio:** não foi disponibilizada ferramenta de entrega de segredo direta Cloudflare → host sem revelação do token à IA/chat, e o arquivo não existe. Não consultar endpoint de token que o exponha ao modelo; não copiar segredo DO; não passar por argumentos CLI, metadata Docker, GitHub ou logs.

**Ação exigida do operador autenticado:** provisionar por canal aprovado, diretamente na Linode, a credencial do túnel existente **e1cad7db-b06e-4adf-8c46-f972bd18db50** no arquivo protegido **/opt/gaia-rag-mini/secrets/r06-service/cloudflare_tunnel_token**, evitando qualquer ferramenta que devolva segredo no resultado visível à IA. Validar dono/permissões e leitura restrita ao processo **UID 65532**. Não publicar token nem seu hash.

**Próxima execução após provisionamento:** confirmar somente metadados do arquivo (não conteúdo); implantar conector **gaia-rag-r06-cloudflared** na rede **gaia-rag-r06-preview-net**, com bind mount read-only, --token-file, restart unless-stopped e sem porta pública; revalidar origin 200 e MCP 401; Cloudflare API autenticada precisa comprovar *healthy* e conexões ativas, ingress e Access preservados; confirmar CNAME principal e legado, túnel DO healthy, teste de restart/recovery; registrar novas evidências. DNS NÃO deve ser cortado nesta fase; PR #4 NÃO deve ser mesclado.

### Critérios de aceite nesta execução

- [x] Origin R06 e DNS interno Docker: HTTP 200.
- [x] R05/DO em execução e URLs protegidas com HTTP 401.
- [x] Imagem cloudflared e suporte a token-file verificados.
- [ ] Token provisionado em canal seguro, fora da IA.
- [ ] Conector R06 instalado e persistente.
- [ ] Cloudflare API autenticada retorna status healthy + conexões ativas.
- [ ] DNS/ingress/Access conferidos via API Cloudflare nesta execução.
- [ ] Teste restrito de reinicialização do conector.

**Declaração: TÚNEL R06 AINDA BLOQUEADO**; nenhum corte DNS nem alteração do ambiente legado.

---

## Preparação operacional adicional: conector R06 automatizado, aguardando segredo (18/11/2026 09:49 UTC)

**Resultado:** stage de infraestrutura executado na Linode via Gaia MCP v.100, com verificação read-only posterior. O túnel **não foi ativado** porque falta token do túnel Cloudflare por canal seguro; o Cloudflare Tunnel ainda **não está atestado healthy**. Não alterar DNS nem PR #4.

### Mudanças efetivamente realizadas em nestground-ai

1. **Novo Compose válido**, em **/opt/gaia-rag-mini/r06-preview/cloudflared.compose.yaml** (root:root, modo 0644), validado com docker compose config --quiet. Define exclusivamente o serviço cloudflared-r06, contêiner **gaia-rag-r06-cloudflared**, imagem local **cloudflare/cloudflared:2026.8.3**, rede Docker externa **gaia-rag-r06-preview-net**, restart **unless-stopped**. Não publica portas, não usa network host nem Docker socket. Executa tunnel --no-autoupdate run --token-file /run/secrets/cloudflare_tunnel_token, montado como **read-only** a partir de **/opt/gaia-rag-mini/secrets/r06-service/cloudflare_tunnel_token**. Bind mount usa create_host_path=false (não gera diretório fictício na falta de token). Imagem executa com UID:GID 65532:65532.
2. **Novo serviço systemd** em **/etc/systemd/system/gaia-rag-r06-cloudflared.service**, unit de inicialização one-shot docker compose up -d --no-deps cloudflared-r06, Requires/After docker.service, ConditionFileNotEmpty no caminho do token. Não inicia enquanto o arquivo de credencial não existir.
3. **Novo monitor systemd.path** em **/etc/systemd/system/gaia-rag-r06-cloudflared.path**, habilitado com systemctl enable --now. Observa PathExists do token e dispara o serviço apenas depois do provisionamento. Evidência: **LoadState=loaded, ActiveState=active, SubState=waiting, UnitFileState=enabled**. O serviço continua **inactive/dead** (normal enquanto token ausente).
4. Units e arquivos configurados sem credenciais em texto ou em variável de ambiente Docker; arquivos de configuração e units no modo root:root 0644. Nenhuma credencial foi emitida, solicitada a APIs sem canal protegido, exposta ao modelo ou armazenada em GitHub.

### Verificação após configuração

- Token esperado **ausente**; contêiner gaia-rag-r06-cloudflared **ainda inexistente** (intencional: não criar contêiner que reinicia em erro sem autenticação).
- **R06** segue healthy; health body: service=gaia-rag-mini-r06, jwt_configured=true, owners_configured=true, qdrant_configured=false, writes_enabled=false. **R05** permanece running/healthy.
- **DigitalOcean**: serviço gaia-qdrant-memory-gaia-qdrant-memory-candidate-1 em execução/healthy e contêiner gaia-qdrant-memory-tunnel em execução.
- **HTTP 401** anônimo em https://memory.tight-knit.net/mcp e https://legacy-rag.tight-knit.net/mcp. Nenhuma alteração de DNS/Access/ingress, serviço DO, ZITADEL, Qdrant, demais contêineres ou PR. Destino CNAME exato e estado API Cloudflare continuam sem revalidação autenticada nesta execução.
- Tentativa de identificação de conector Cloudflare nativo nesta sessão: indisponível. Também não há autenticação Cloudflare preexistente utilizável no ambiente SSH da Linode ou no Pocket MCP100 (apenas nomes de variáveis testados, sem exibir valores), nem token no arquivo designado. A ferramenta Browser não dispõe de acesso ao contexto de navegador autenticado nesta sessão.

### Única pendência para ativar o conector preparado

O operador autenticado deve **provisionar diretamente** no host, por canal seguro aprovado e sem colocar conteúdo em chat, logs, CLI ou GitHub, o token do túnel remoto existente **e1cad7db-b06e-4adf-8c46-f972bd18db50**, no caminho **/opt/gaia-rag-mini/secrets/r06-service/cloudflare_tunnel_token**, **atomicamente** e com leitura restrita ao UID 65532 do cloudflared. Ao aparecer um arquivo válido, o monitor systemd.path está configurado para iniciar o serviço Docker Compose automaticamente.

**Após isso, o fato de um contêiner subir não equivale à homologação:** confirmar Cloudflare API status healthy, conexões ativas e estáveis, origin interno HTTP 200, Access ingress e audience preservados, retry/boot, status legado healthy e ambos CNAMEs sem alteração. Sem corte do domínio de produção e sem merge PR #4.

**Declaração operacional nesta execução: TÚNEL R06 AINDA BLOQUEADO — conector preparado/autoacionável, mas não iniciado por ausência de credencial de túnel.**
