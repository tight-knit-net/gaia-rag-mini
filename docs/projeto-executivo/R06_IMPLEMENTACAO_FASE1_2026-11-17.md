# R06 — implementação inicial, testes e gates remanescentes
**Data local:** 17/11/2026 (America/Sao_Paulo) · **Ambiente:** Linode `nestground-ai` · **PR:** #4 (draft)

## O que foi de fato entregue

1. **Contrato MCP R06**: `memory_process_start`, `memory_prepare_after_approval`, `memory_proposal_preview`, `memory_pending_reviews` integrados à aplicação, somando **13 ferramentas**. As operações de leitura continuam com controle servidor-side por identidade verificada, namespace, tenant e processo.
2. **Aprovação documental prévia**: a proposta só é criada se uma referência de aprovação e SHA-256 do documento forem encontrados no registro de documentos aprovados **controlado pelo servidor**. Alegação textual na chamada MCP não aprova documento.
3. **Gravação com aprovação humana**: fila SQLite de propostas, chave idempotente por tenant/processo/fonte/versão e conteúdo, URL de revisão configurada, página HTML protegida pela autenticação Access da aplicação, validação de Origem e CSRF no POST, gravação Qdrant somente após POST, UUID determinístico e readback independente. Retry após erro de escrita/readback **não é automático**: mantém estado `approving` para conciliação de operação ambígua.
4. **Skill incluída na imagem R06**: pasta Agent Skills versionada + **13 arquivos allowlisted** acessíveis por `gaia_skill_catalog` e `gaia_skill_read`; **3 recursos MCP** `skill://...` para leitura progressiva. O contrato na skill foi atualizado sem substituir documentação R04/R03.1.
5. **CI real**: job isolado roda Qdrant v1.15.5 descartável e teste MCP/TestClient com JWT RS256 assinado localmente (JWKS simulado), proposta, browser POST simulado, gravação e readback, controle cruzado de clientes e deduplicação. O job de staging também testa health 200 e JWT ausente 401.

## Evidências da prova em laboratório

- **22 assertivas iniciais aprovadas** diretamente na Linode, com Qdrant real isolado e memória sintética. `0 pontos` antes do clique simulado; `1 ponto` após, `1 ponto` após repetição; autorização de outro cliente negada e readback pelo MCP funcionando.
- Os testes posteriores na CI também validam `resources/list`, `resources/read` e `memory_process_start`, somando **25 verificações** no roteiro atualizado.
- **Nenhum segredo, dado real, tenant real ou ponto da coleção produtiva foi utilizado**. O Qdrant de laboratório foi destruído, juntamente com rede e imagem temporárias.
- O preview **não** realizou escrita, pois os controles estão desativados por padrão.

## Inventário na Linode

| Ambiente | Contêiner | Porta | Estado |
|---|---|---|---|
| R05 staging original | `gaia-rag-mini-staging` | `127.0.0.1:18081` | `healthy`, não alterado |
| R06 preview paralelo | `gaia-rag-mini-r06-preview` | `127.0.0.1:18082` | `healthy`, somente loopback |
| NestGround | 4 serviços anteriores | originais | `running` |

A prévia R06 opera sem JWT/grants/Qdrant reais e com `GAIA_RAG_ENABLE_REVIEW=0`, `RAG_STAGING_APPROVED=0`. `GET /healthz` 200 e MCP sem JWT 401; `read_only=true`, UID 10001, `cap_drop ALL`, limites 1 GiB/1 CPU. A rede `172.19.45.0/24` evita o conflito com o Cloudflare WARP.

## Bloqueios de homologação antes de ligar escrita de clientes

| ID | Gate necessário | Situação |
|---|---|---|
| R06-G01 | Identificar aplicação Access real, issuer e audience; ensaiar JWT real, revogação de usuário e política por cliente/processo | **PENDENTE**. O laboratório usa JWT assinado com JWKS simulado |
| R06-G02 | Definir origem autoritativa dos grants; montar arquivo read-only operado pela instituição; validar revogação | **PENDENTE**. Não inferir cliente por process_id nem pela coleção histórica |
| R06-G03 | Alimentar registro de aprovação documental a partir de fonte verificável; vincular hash da peça e aprovação com identidade real | **PENDENTE**. Testado apenas com registro fictício |
| R06-G04 | Provar gravação/embedding de 384D, filtro `tenant_id` e índices no Qdrant Cloud ou sandbox equivalente; reconciliar registro legado sem `tenant_id` | **PENDENTE**. Nenhum dado histórico alterado |
| R06-G05 | Portal HTTPS real com Cloudflare, clique humano efetivo, ledger SQLite persistente/bkp, concorrência, erro de readback, reconciliação de `approving` | **PENDENTE**. Apenas browser POST simulado |
| R06-G06 | Conectar host ChatGPT/Work e demonstrar ativação da skill; não confundir recursos MCP com instalação no catálogo | **PENDENTE**. Lista/leitura de recursos MCP passou |
| R06-G07 | SAST/SBOM, versões pinadas, auditoria de segurança, teste carga, rollback, aprovação de deploy/cutover | **PENDENTE**. Workflows GHCR/Linode seguem desligados |

## Ordem de continuidade

1. R06-G01–03: identificar e versionar contrato confiável de identidade/grants/aprovação documental em staging; nenhuma permissão por conjectura.
2. R06-G04–05: montar armazenamento durável com backup e ambiente privado homologado, executar escrita de prova e readback com isolamento e rollback.
3. R06-G06: instalar e ensaiar a skill no host consumidor real, observando seleção e leitura progressiva.
4. R06-G07: revisão de segurança, publicação controlada e eventual migração mediante autorização e evidências independentes.

**Limite:** a conclusão da CI e o estado healthy não autorizam produção nem modificam DigitalOcean, Cloudflare, Qdrant Cloud, DNS, Tunnel, usuários, segredos ou clientes. O PR continua draft, sem merge. O defeito `RECEIPT_CAPACITY` no executor compartilhado GAIA MCP100 permanece um item upstream independente.
