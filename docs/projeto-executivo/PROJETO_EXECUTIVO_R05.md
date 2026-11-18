# GAIA RAG Mini — Projeto Executivo R05
**Revisão:** 2026-11-17 | **Estado documental:** REVISADO NA AUTOAUDITORIA ENXUTA | **Escopo de código:** A DEFINIR PELO RESPONSÁVEL | **Código novo:** NÃO AUTORIZADO | **Publicação/deploy:** BLOQUEADOS.

> Este documento é a especificação executiva para futura implementação. O fato de sua redação estar concluída **não** autoriza início de desenvolvimento, merge, publicação de imagem, implantação ou migração. A liberação do desenvolvimento dependerá de revisão técnica documentada, conclusão dos gates de projeto e aprovação expressa.

## 1. Objetivo e resultado esperado
Integrar a skill única GAIA RAG de processos administrativos (derivada de R04, identificada como R05) com a MCP GAIA RAG existente; preparar a futura execução do container em Linode/Akamai, preservando a Cloudflare como borda de acesso, o Qdrant Cloud existente e a aprovação humana antes de persistir memória. O repositório `tight-knit-net/gaia-rag-mini` é o local futuro de código versionado e da documentação executiva desta evolução.

O resultado funcional depende de duas capacidades independentes:
- **A — Recuperação:** recuperar somente memórias autorizadas do processo exato, rastreáveis a fontes, data, status e jurisdição.
- **B — Produção:** propor sínteses atômicas e deduplicadas somente após aprovação documental; persistir exclusivamente após autenticação e clique humano explícito no portal Access.

A disponibilidade da skill na MCP **não** garante carregamento automático em ChatGPT; esta etapa requer comprovação no host.

## 2. Decisões de arquitetura e invariantes
| Item | Decisão para a R05 | Tipo |
|---|---|---|
| Fonte de verdade da skill | `skills/gaia-rag-processos-administrativos/` neste repositório; R04/R03.1 preservadas no Drive | DECISÃO |
| MCP | Evoluir a MCP Python/Uvicorn existente, ou adaptador Cloudflare mínimo e reversível; não assumir Cloudflare Think | DECISÃO |
| Distribuição | Validar Skills over MCP e, se host não suportar, plugin ChatGPT com dependência MCP; não duplicar fontes | DECISÃO CONDICIONADA |
| Origem de produção | DigitalOcean continua ativa até aprovação explícita de mudança | DECISÃO |
| Destino candidato | `nestground-ai`, Akamai `akamai-william`, Miami, 8GB/4 vCPU; seleção final condicionada a benchmark e isolamento | HIPÓTESE DE CAPACIDADE |
| Cloudflare | Manter hostname, Access, Tunnel e política atual; nenhuma alteração nesta fase | INVARIANTE |
| Qdrant | Manter coleção `chatgpt_memoria_aprovada`, vetores/índices/dados reais, sem reindexação | INVARIANTE |
| Gravação | Preparação é proposta; portal protegido + clique humano é o único ponto de autorização final | INVARIANTE |
| GitHub | Revisão técnica documentada sem dependência de bot ou terceiro; CI estático; sem merge automático | DECISÃO |
| Publicação | Workflows GHCR/Linode condicionados a `if: false` nesta branch; exigem nova mudança revisada e autorização explícita | BLOQUEIO |

## 3. Arquitetura observada e arquitetura-alvo
**AS-IS observado em consultas anteriores, em 17/11/2026:**
`Host MCP -> Cloudflare Access -> memory.tight-knit.net / Tunnel gaia-qdrant-memory-independent-20261117 -> container gaia-qdrant-memory:candidate-v2 (Docker, Uvicorn porta 8000) na Droplet DO -> Qdrant Cloud.`
Existe volume Docker para `/state`, origem configurada por Docker Compose, e política Access denominada `GAIA Memory Owner Only`. O estado health/healthy não prova isolamento entre clientes, aprovação humana efetiva nem instalação da skill.

**TO-BE conceitual (NÃO implantado):**
`Host autorizado -> Cloudflare Access existente -> Tunnel existente -> container GAIA RAG versionado na Linode -> Qdrant Cloud existente`.
Plano de controle: `GitHub PR + revisão + CI estático -> (APÓS NOVA AUTORIZAÇÃO) build GHCR por digest -> (APÓS HOMOLOGAÇÃO) staging protegido -> cutover controlado`.
Plano da skill: `arquivos R05 versionados -> [Skills over MCP ou plugin, conforme host] -> seleção/carregamento sob demanda no ChatGPT`.

**Não ampliar superfície:** não iniciar Worker, agente Think, coleção alternativa, nova indexação, DNS ou túnel sem necessidade e justificativa assinada.

## 4. Requisitos funcionais (contratos de aceite futuro)
| ID | Requisito obrigatório | Evidência para o aceite |
|---|---|---|
| RF-01 | Identificar `process_id` exato antes de consultar memória | Log sintético com process_id e identidade |
| RF-02 | Usar `memory_process_start`, `memory_list_process`, `memory_search` conforme contexto, sem mistura de processos | Casos A/A e A/B negativos |
| RF-03 | `memory_get`, `memory_find_by_source`, `memory_similar_cases` jamais expor cliente não autorizado | Verificação de ACL no servidor para cada método, incluindo escopo indireto |
| RF-04 | Apresentar proveniência, versão, data, status jurídico e jurisdição sem inventar fonte ou ato | Respostas comparadas a fixtures e fonte primária |
| RF-05 | Após documento efetivamente aprovado, produzir candidatos mínimos, atômicos e deduplicados | Ensaio de propostas sintéticas com origem e idempotência |
| RF-06 | `memory_prepare_after_approval` apenas cria proposta; persistência depende do portal, identidade e clique humano | Testes antes/depois + readback independente |
| RF-07 | Publicar recursos versionados da skill no host suportado, com carregamento progressivo real | Trace de list/get/resources-read ou plugin efetivo |
| RF-08 | Falha de ferramenta, Access, rede ou identidade produz negativa explícita e não gravação | Testes de falha e ausência de efeito colateral |
| RF-09 | Preservar R04/R03.1 e bibliografia sem substituição dos originais | Matriz de hash e links de proveniência |
| RF-10 | Separar aprovação de peça, proposta, aprovação no portal, persistência, protocolo e decisão da administração | Estados independentes documentados e testados |

## 5. Requisitos não funcionais e controles
- **RNF-01 Segurança:** negar por padrão quando não houver identidade autorizada no backend; a skill e `namespace=chatgpt` não substituem ACL por tenant/processo.
- **RNF-02 Privacidade:** sem dados reais de clientes em CI, teste, logs ou artefatos; fixtures `DEMO-*`; segredos fora de GitHub e de PRs.
- **RNF-03 Integridade:** Qdrant Cloud atual permanece sem migração de dados, alteração de embeddings, schema, índices e coleção.
- **RNF-04 Auditoria:** cada teste do host registra data UTC, commit, digest, ator, identidade sintética, operação, resultado e evidência sanitizada.
- **RNF-05 Disponibilidade:** estabelecer SLO de latência, erros, memória e disco com medições em staging; **nenhum número SLO foi homologado**.
- **RNF-06 Capacidade:** a `nestground-ai` possui cargas NestGround em execução; container futuro terá quota inicial documentada de 1 vCPU/1GiB em ambiente isolado, sujeita a benchmark; não extrapolar capacidade do snapshot.
- **RNF-07 Reversibilidade:** manter origem DO operacional; rollback exige prova independente, não declaração em runbook.
- **RNF-08 Supply chain:** versões fixadas, proveniência de imagem, checksum/SBOM e scanner antes de qualquer build autorizada.
- **RNF-09 Controle de mudanças:** PR rastreável, revisão técnica documentada, aprovação humana de execução e bloqueio de publicação.
- **RNF-10 Segregação:** todo tipo de busca, inclusive similaridade/UUID/fonte, deve negar exposição cruzada por cliente, não somente por instrução no prompt.

## 6. Segurança lógica e dados
**Fluxo A — BUSCA:** (1) confirmar identidade/autorização no backend; (2) vincular usuário ao processo exato; (3) executar consulta no escopo permitido; (4) conferir `process_id`, origem, vigência e classificação dos resultados; (5) responder apenas fatos suportados. Em resultado vazio, registrar ausência de hit, não inexistência jurídica.

**Fluxo B — PRODUÇÃO:** (1) provar aprovação documental identificável; (2) coletar fatos aprovados e fonte oficial; (3) sintetizar memória mínima, com deduplicação por processo/fonte/versão; (4) produzir proposta sem escrita; (5) apresentar em portal Access; (6) obter clique humano autenticado; (7) persistir; (8) verificar readback e trilha de auditoria. Qualquer falha impede transição ao próximo estado.

**Ameaças que precisam de teste real:** acesso cruzado por UUID, bypass via fonte, similaridade sem tenant, replay de proposta, ausência de identidade Access, segredos em logs, tentativa de prompt injection em memória recuperada, propostas expiradas, concorrência e gravação duplicada.

## 7. Estado do ambiente e caminho de desenvolvimento
A pasta Linode `/opt/gaia-rag-mini` e usuário de deploy restrito foram preparados anteriormente, **sem iniciar o container GAIA RAG**. O SSH foi validado localmente; ligação GitHub Actions → Linode **não foi demonstrada**. Há quatro containers NestGround preservados. Não há aprovação para publicar imagem ou habilitar `RAG_STAGING_APPROVED=1`.

Os arquivos de CI/CD estão na branch documental para revisão de segurança. O workflow de build e o de implantação estão explicitamente inabilitados por `if: false`; não devem ser habilitados nem incorporados ao ciclo de entrega sem nova decisão documentada.

**Ordem de trabalho:**
1. **D0 — Projeto executivo:** este documento + backlog + matriz de riscos + plano de testes e rollback; revisar e obter aceite técnico.
2. **D1 — Autorização para codificar:** após D0 aprovado, mapear fonte operacional da DO e planejar commits limitados à aplicação e testes.
3. **D2 — Validação do código:** pytest/CI, análise de dependências, revisão técnica rastreável, checagens de segurança, pacote reproduzível; sem deploy.
4. **D3 — Homologação isolada:** somente mediante autorização específica, testar host, Access, ACL, portal humano, rollback e capacidade sintética.
5. **D4 — Publicação de produção:** autorização separada e plano de mudança; nenhuma decisão automática de cutover.

## 8. Gates executivos para iniciar a escrita de código
O código novo **não pode começar** enquanto faltar qualquer item obrigatório:
- **DG-01** Documentação executiva completa, sem contradição entre AS-IS e TO-BE.
- **DG-02** Inventário de requisitos, backlog, critérios de aceite, riscos e rollback aprovado.
- **DG-03** Autoauditoria documental rastreável registrada, sem exigência de revisão externa; riscos operacionais mantidos no backlog.
- **DG-04** Definições de escopo, pontos canônicos, interfaces e plano de testes aprovados por responsável autorizado.
- **DG-05** Confirmação do freeze de publicação e implantação, com segregação do PR e `main`.
- **DG-06** Autorização explícita para iniciar desenvolvimento (não inclui autorização de deploy).

**Estado desta entrega:** DG-01/DG-02 documentados e DG-03 revisado na auditoria enxuta; DG-04/DG-06 dependem da decisão do proprietário sobre o próximo escopo. Este pacote **não é homologação operacional**.

## 9. Evidências e rastreabilidade
- Skill R04 e relatório no Drive: https://drive.google.com/drive/folders/1UVHd6Vz0FaI7QLVcZCNbVOyy5b6WcQ2-
- R03.1 preservada: https://drive.google.com/drive/folders/15X-POHeZGrzQlY8ZeJYxgrW0eJYvZmMf
- Pesquisas originais: https://drive.google.com/drive/folders/1i-R53N5Brq6k4et5IPscBqKPKKkPm1HR
- Relatório histórico R04: https://drive.google.com/file/d/18pjdLj_uBN-zqPC45QoqCx9m3dQ7TWEI/view
- Inventário próprio: `ARQUITETURA.md`, `RELATORIO_DE_EXECUCAO_R05.md`, `STATUS_CICD_LINODE.md`.
- Decisão de skill: `ADR-0001-DISTRIBUICAO-SKILL.md`.
- Requisitos em desenvolvimento: `BACKLOG_IMPLEMENTACAO_R05.md`; revisões: `PROTOCOLO_REVISAO_R05.md`.
- Gate de homologação operacional: `MATRIZ_GATES.md`. O sucesso dos 23 testes estáticos históricos não autoriza RF/RNF operacionais.
- Fontes normativas técnicas: https://developers.cloudflare.com/agents/skills/ ; https://skills.extensions.modelcontextprotocol.io/specification/beta/skills ; https://developers.openai.com/plugins/build/skills .

## 10. Declaração de encerramento documental
O conteúdo executivo acima especifica o objetivo, o ambiente conhecido, o alvo, os requisitos, a arquitetura, os controles, a sequência de trabalho, os testes a realizar e as condições de aceite. **Revisão documental enxuta registrada; controles de runtime ainda não validados**. O registro de auditoria fica em `AUDITORIA_TECNICA_ENXUTA_R05_2026-11-17.md`; achados futuros exigem avaliação conforme sua evidência. Nenhuma ação de escrita do runtime ou publicação fica implícita.

## 6.1 Achados da revisão técnica e bloqueadores ainda não resolvidos
A revisão detectou a antiga instrução em `SKILL.md` de verificar `process_id` **após** a recuperação por `memory_get`/`memory_find_by_source`. **A orientação da skill R05 foi corrigida nesta branch** para não chamar esses métodos com dados multi-cliente sem comprovação de autorização no backend. **BR-01 (CRÍTICO para uso real):** ainda comprovar ACL server-side por identidade, `tenant_id` e `process_id` para todas as ferramentas; até lá, não usar essas rotas sem escopo seguro comprovado.

**BR-02 (ALTO):** verificar negociação da extensão beta Skills over MCP (capabilities `server/discover`, `skills/list`, `skills/get`, `resources/read` e `resources/directory/read` apenas quando anunciado); confirmar revisão-base e manifestos de recursos. O host ainda não demonstrou consumir a extensão. Conferir ADR-0001 revisada.

**BR-03 (ALTO):** `agents/openai.yaml` não traz dependência MCP real e não existe plugin validado. Qualquer pacote futuro deve declarar dependência efetiva e testar autorização/conexão; não inventar URL nem marcar como instalado.

**BR-04 (ALTO):** os pipelines GHCR/Linode estão congelados na branch; os scripts de deployment, chave de acesso, pull do registro privado, isolamento e rollback ainda não passaram auditoria end-to-end. O sucesso da CI estática não elimina o risco.

Esses achados são **revisão documental assistida**, não homologação do runtime nem auditoria externa certificada. O Fireflies foi consultado para atas e decisões relativas ao GAIA RAG, mas não retornou reuniões acessíveis. Sem novas evidências, preservar as decisões já documentadas e não supor aceite de reuniões.

**Decisão executiva resultante:** documentação estruturada e revisada, porém **APROVAÇÃO PARA DESENVOLVER = NÃO CONCEDIDA** e **APROVAÇÃO PARA PUBLICAR = NÃO CONCEDIDA**. O fechamento de BR-01 a BR-04 exige evidências específicas e aceite do responsável, sem alteração de Qdrant/Cloudflare/produção por inferência.

