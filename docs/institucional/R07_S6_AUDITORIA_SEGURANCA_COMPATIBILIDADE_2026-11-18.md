# GAIA RAG & Knowledge — Gate S6 | Auditoria de segurança e compatibilidade

**Versão:** 1.0.0
**Data/hora aferidas de emissão:** 18/11/2026, 20:46:47, fuso America/Sao_Paulo (UTC-03:00).
**Origem verificável do relógio:** serviço de hora local ChatGPT, resposta `2026-11-18T20:46:47-03:00`.
**Escopo:** auditoria e correções exclusivamente na R07, utilizando CI e dados sintéticos. Sem merge/deploy/Cloudflare/DNS/Qdrant real/produção/legado/migração.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Branch-alvo de escrita:** `feat/r07-office-knowledge-assimilation` — PR #5, draft e aberta.
**Base de comparação (somente leitura):** `feat/r06-lifecycle-skill-staging`, SHA `14cca2e325b8919506c9a95b917e02ae6bf293c7` — PR #4.
**HEAD do código S6 que passou na CI:** `652ff9274417ba636ea8557ba11a0ad215231c45`.
**Evidência de CI:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44423451558
**Data-base da comparação inicial:** HEAD R07 `4a61c72eefd7ef6599fa5af59d921f6fea78810a`, 39 arquivos distintos na PR, comparação GitHub à época: 80 commits à frente, zero atrás da base.

## 1. Parecer executivo

**GO técnico condicionado** para continuar a revisão da candidata **isolada em CI**. Não há falha S6 P1 sem correção de código detectada nesta rodada, e todas as regressões sintéticas passaram no HEAD acima. **NO-GO para operação real, publicação, migração de memórias e desligamento do legado**, que exigem gates independentes com autenticação e recuperação real.

Não considerar hash SHA-256 do arquivo como certificado de origem ou permissão. Não considerar a execução de uma skill no host homologada por testes de consumo emulado. A própria MCP R06 publicada ainda informa `human_review_enabled=false`; não houve ativação de gravação nesta etapa.

## 2. Achados da revisão de contratos e segurança

| ID | Severidade | Achado | Correção R07 / Estado |
| --- | --- | --- | --- |
| S6-01 | P1 | Os métodos `gaia_skill_catalog`, `gaia_skill_read`, `gaia_skill_read_chunk` e três recursos MCP autenticavam JWT, mas não exigiam a identidade do proprietário cadastrada no registro do servidor. Um usuário autenticado não proprietário poderia ler conteúdo da skill. | **CORRIGIDO:** `_require('chatgpt','all-processes')` em cada leitor/recurso. Testes negativos MCP confirmados. Não alterada a política transversal de memórias do proprietário. |
| S6-02 | P1/P2 | Leitura de arquivo allowlisted verificava só `target.is_symlink()`, sem validar o caminho intermediário; catálogo/arquivo/chunk usavam leituras separadas para conteúdo/hash. | **CORRIGIDO:** `_safe_installed_skill_bytes` bloqueia symlinks em todos os segmentos, restringe arquivos declarados e usa um mesmo snapshot de bytes por resposta. Teste MCP com pasta symlinked negado. |
| S6-03 | P2 | Context manager SQLite não fecha fisicamente a conexão ao sair de `with conn`; risco de descritores/WAL/locks residuais. | **CORRIGIDO:** `contextlib.closing` preserva o commit/rollback transacional em `review.py` e fecha conexões de consultas de auditoria em `lifecycle_read.py`. |
| S6-04 | P1 | A base SQLite da R06 pode ter `CHECK(status IN ('pending','approving','approved'))`, incompatível com o novo descarte R07. `CREATE TABLE IF NOT EXISTS` não migra o esquema. | **BLOQUEIO SEGURO IMPLEMENTADO:** descarte verifica `sqlite_master` e retorna `DISCARD_SCHEMA_MIGRATION_REQUIRED`, sem atualizar status. A migração transacional da base real está **PENDENTE de backup e autorização**. |
| S6-05 | P2 | Descarte da proposta pendente não checava novamente expiração no POST (apenas o token CSRF). | **CORRIGIDO:** impede descarte após `expires_at` e mantém proposta intacta. |
| S6-06 | P2 operacional | Conteúdo carregado como skill pode conter instruções hostis; o hash atual identifica consistência dos arquivos empacotados, não autoridade de uma instrução vinda de documento externo. | **CONTROLE CONFIRMADO:** roteador aceita somente sete missões fixas e caminhos instalados, não executa instruções, retorna `effects=none` e exige carregamento explícito. **PENDENTE:** validar comportamento do host ChatGPT real; não alegar imunidade da LLM a prompt injection. |
| S6-07 | P2 operacional | `user_confirmed_proposal=true` vem do chamador e não é prova criptográfica de consentimento; ainda pode preparar proposta SQLite, nunca gravar diretamente no Qdrant. | **RISCO CONHECIDO / CONTIDO:** processo de documento aprovado, review_url e clique CSRF humano separados. Não permitir que conteúdo recuperado sirva de autorização para preparar propostas. Gate operacional deve verificar origem de intenção. |
| S6-08 | P1 de continuidade, fora de S6 | Históricos de propostas legadas, estados pendentes, backup e dados Qdrant ainda não estão reconciliados. | **PENDENTE / NO-GO de migração.** Não transformar proposta pendente em memória aprovada. |

## 3. Matriz de testes e resultados — evidência GitHub Actions

| Dimensão | Ambiente real/sintético | Resultado |
| --- | --- | --- |
| CI global do HEAD de código | 8 jobs GitHub Actions no run `44423451558` | **PASSOU 8/8** |
| Regressão unitária geral | `validate`: testes unitários de projeto | **PASSOU 99 testes** |
| Contratos estáticos Skill R05 | `validate`: regressões da skill | **PASSOU 23 testes** |
| Segurança S6 SQLite/autorização | job `r07_s6_security` | **PASSOU 5/5**, incluídos no universo dos 99 unitários |
| MCP + Qdrant descartável + browser sintético | job `r06_lifecycle_synthetic` | **PASSOU 67 verificações**, incluindo negativas novas S6 |
| Negativa não proprietário para catálogo/leitura/chunks/recurso | MCP sintético | **PASSOU 4/4 negativas** |
| Symlink intermediário do pacote de skill | MCP sintético | **PASSOU 1/1 negativa** |
| Roteador Skilldrum | job `r07_skill_router_synthetic` | **PASSOU 14/14** |
| Host consumidor explícito | job `r07_host_contract_synthetic` | **PASSOU 9/9** |
| Docker e Qdrant demonstrativo | `staging_image_smoke` | **PASSOU** |
| Runtime R07 sem rede ou credenciais | `r07_operational_isolated` | **PASSOU** |
| Política de aceite candidata, autenticação e bloqueios | job `r07_candidate_acceptance` | **PASSOU**, inclusive nova checagem AST da presença de owner guard em todos os recursos/leitores |
| Cloudflare Access/JWT de produção, host ChatGPT real | Não acionado | **PENDENTE** |
| Estado e integridade de Qdrant/ledger reais | Não acionado | **PENDENTE** |

**Nota de contagem:** as 5 provas S6 estão incluídas nos 99 unitários, e as 5 negativas MCP S6 estão incluídas nas 67 verificações E2E. Não somar esses subconjuntos como casos adicionais independentes.

## 4. Compatibilidade R06 versus R07

**Compatibilidade preservada:** nomes das ferramentas R06 de consulta e preparação, autorização por identidade do proprietário (não por cliente), retorno de memória aprovada com processo exato, confirmação documental antes de proposta, botão `Salvar memória — Aprovar e gravar` e readback Qdrant após clique humano. R07 adicionou ferramentas e metadados; não modificou endpoints R06 ou main.

**Mudanças deliberadas R07:** novos métodos de roteamento, consulta de eventos, exportação, estatísticas, estado de descarte e parâmetros de paginação; exigência explícita da lista de proprietários para leitura de skills; fechamento de conexões SQLite. Migração de CHECK no ledger R06 é separada e **não foi executada**.

**Limitações de fonte:** RAG legado foi consultado apenas em memórias aprovadas para contexto e não é evidência do runtime; o conector Gaia_Rag___knowledge informou `host_must_explicitly_load` no catálogo, e sua chamada `gaia_skill_read` respondeu `{}` no adaptador atual. GitHub/CI e código de commit fornecem as evidências deste gate. Nenhuma operação de escrita de memória foi solicitada.

## 5. Mudanças executadas nesta R07

- `app/server.py`: autorização do proprietário em todos os leitores e resources de skill; leitura allowlisted por caminho sem symlinks; conteúdo e hash do mesmo snapshot.
- `src/gaia_rag_r05/review.py`: conexões SQL explicitamente fechadas, proteção de descarte expirado e gate de compatibilidade SQLite.
- `src/gaia_rag_r05/lifecycle_read.py`: fecho de conexões SQLite de consultas somente leitura.
- `tests/r06_live_review_e2e.py`: negativas MCP para não proprietário, resource e symlink de pasta.
- `tests/test_r07_s6_security.py`: casos sintéticos para CSRF, descarte idempotente, expiração, owner allowlist e esquema R06 incompatível.
- `.github/workflows/r05-skill-static.yml`: job S6 obrigatório anterior ao aceite.
- `scripts/r07_candidate_acceptance.py`: checagem AST de owner guard em cada leitor/recurso, segurança de caminhos e bloqueio legado.

## 6. Privacidade, ambiente e rollback

Sem GroqCloud, sem dados reais de clientes, sem SSH/TestLab, sem Cloudflare real, sem deploy de containers persistentes, sem backup ou migração de pontos e sem mudanças em R06, main ou legado. GitHub Actions usa runners temporários, JWT/Qdrant de demonstração. A saída de logs de S6 contém apenas IDs sintéticos.

Se alguma regressão aparecer, realizar revisão e reversão **somente na branch R07** com reconferência de HEAD; não efetuar merge, restauração de banco real ou promoção de imagens por esta autorização.

## 7. Próximo gate proposto — S7 (NÃO EXECUTADO)

**Nome:** S7 — prontidão de empacotamento operacional e plano de homologação autenticada da candidata, sem publicação.

**Escopo interno autorizado para solicitação posterior:** inspecionar Dockerfile, dependências, manifests CI, política de segredo, limites de rede, idempotência, persistência de ledger/snapshot e composição de rollback; produzir runbook testável de implantação portátil, checagens do host e requisitos de Cloudflare Access/botão humano. Executar somente testes sintéticos de restauração e configuração em GitHub Actions, com dados DEMO. Corrigir apenas a R07 caso haja gaps comprovados.

**Critérios S7:** pacote reproduzível no CI, nenhum segredo ou dado real em logs, revisão humana preservada, rollback sintético verificável e lista objetiva de provas que dependem de host final real. Se não existir destino autorizado, registrar PENDENTE sem inventar homologação operacional.

**Fora do S7:** merge, deploy, DNS, Cloudflare, escrita Qdrant real, migração/backup de produção e desativação legado. **O botão da resposta final solicita somente o S7**; não é aprovação de operações externas.

**Parecer S6:** **GO técnico para preparação da candidata em CI; NO-GO operacional para publicação/migração/corte**.
