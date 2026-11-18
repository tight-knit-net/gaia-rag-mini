# GAIA Document MCP — G14-B: operador único, processos administrativos e aprendizagem híbrida

**Versão:** 1.0.0, implementação candidata com testes **exclusivamente sintéticos**.  
**Instante de emissão aferido:** 2026-11-18T20:40:51-03:00; fuso `America/Sao_Paulo`; origem do relógio: ferramenta de horário local ChatGPT. O commit GitHub possui timestamp independente e é referência de publicação.  
**Área única de escrita:** `tight-knit-net/gaia-rag-mini` / `feat/gaia-document-mcp-isolado`, PR #7 Draft; nenhuma mudança em R07, R06, main, GitLab DocLab, Linear, serviços, Google Drive, PostgreSQL real ou Qdrant.  
**Baseline inicial:** `646a611227a64677a4a294083c7dae860790dd1d`. O titular autorizou expressamente a etapa G14-B com ressalvas, incluindo mudança de premissa sobre clientes/processos.  
**Referências:** planos `11`, `12`, `13`, `14` deste diretório, contrato R06 de memória transversal; [R06 memória unificada sem trava por cliente](https://github.com/tight-knit-net/gaia-rag-mini/blob/feat/r06-lifecycle-skill-staging/docs/projeto-executivo/R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md). O conector `Gaia_Rag___knowledge` identificou a skill institucional, mas o host não confirmou ativação real ao ler SKILL.md. O conector `GAIA_RAG` legado retornou contexto aprovado histórico; fonte viva de código e CI: GitHub.

## 1. Correção mandatória da visão de autorização

**Um único operador autenticado utiliza o GAIA. Clientes e órgãos administrativos não acessam o sistema por conta própria.** O `client_id` existente pode representar cliente na nomenclatura/proveniência, mas **não** determina quem pode consultar memórias aprovadas nem cria ACL tenant por cliente. O número oficial do processo administrativo é identificador de **contexto**, sempre acompanhado de órgão e jurisdição quando disponíveis; não é token ou controle de permissão.

Autorização futura deve validar a **identidade do proprietário** no backend. No G14-B apenas `SyntheticOwnerOnly` compara sujeitos fornecidos por fixture; **NÃO** é OAuth, JWT, Access, token nem autenticação operacional. A consulta transversal do proprietário às memórias aprovadas permanece institucional; nenhuma barreira de permissão baseada em `process_id`, `tenant` ou `client_id` pode ser introduzida neste módulo.

## 2. Semântica processual exigida pelo titular

- `AdministrativeProcess.process_id`: identificador interno vinculado à origem e ao evento.
- `official_number`: número oficial do processo da Prefeitura/órgão, preservando zeros à esquerda e separadores. Não normalizar `000123/2026` como `123/2026`.
- `agency_code` + `jurisdiction`: diferenciam números repetidos em órgãos ou municípios distintos.
- `process_key`: concatenação determinística dos três elementos acima. **Identidade/proveniência, não permissão**.
- Um requerimento do processo A e outro muito semelhante do processo B podem ser encontrados por similaridade, mas o resultado de B recebe `ANALOGY_ONLY` e seu `process_key`, `source_ref` e `approval_ref` próprios. **Não transferir automaticamente fatos de B para A**.
- A pontuação deste protótipo é **Jaccard lexical simples**, sem embeddings nem certeza semântica; ela é apenas um filtro de teste. Antes de produção, testar desambiguação, jurisprudência e contexto administrativo; caso não haja número do órgão confiável, registrar contexto pendente, nunca inferir.

## 3. Aprendizagem híbrida: duas camadas, não uma trava de memória

**Camada A — captura automática / contexto de trabalho:** eventos `ocr`, `pdf_transform`, `catalog`, `nomenclature`, `document_create`, `workspace`, `signature` podem criar automaticamente candidatos mínimos na fila por `process_key`. Nenhum prompt repetitivo nem clique manual é necessário para **propor** candidatos a cada evento. Duplicatas semânticas são unificadas por processo, preservando origem/eventos. Fluxos bloqueados/falhos, OCR `mock` e texto sem informação não promovem conhecimento. Todos recebem `PENDING_HUMAN_REVIEW`; nesta etapa a fila é **apenas RAM sintética**, não persistente.

**Camada B — recuperação automática de conhecimento institucional aprovado:** a consulta transversal aceita registros aprovados de todos os processos e apresenta resultados do processo atual separadamente de analogias de outros processos, cada uma com provenance e rótulo explícito. Resultados pendentes só integram contexto provisório **do mesmo processo**, sem se tornarem verdade institucional. A fonte de registros aprovados é uma fixture controlada neste gate; a implementação real deverá consultar apenas registros `approved=true` autorizados na R06/R07, sem confiar em um boolean enviado por OCR, PDF ou usuário.

**Gate de promoção institucional:** captura, classificação, busca e comparação podem ser automáticas; a aprovação documental e a aprovação da memória no portal autenticado R06 continuam atos distintos. A presente autorização de G14-B **não** libera gravação real Qdrant sem revisão humana/ação explícita. Para diminuir a operação do titular, o próximo desenho poderá propor **revisão agrupada** de candidatos com botão real e readback, mas não existe nesta implementação. Candidatos pendentes não equivalem a pontos persistidos.

## 4. Concorrência e persistência: ensaio limitado, mas preservado

O `InMemoryRevisionCoordinator` simula reserva por `(process_key, idempotency_key)`, fingerprint de payload, `REVISION_CONFLICT`, disputa atômica sob Lock, retorno reexecutado e estado `UNKNOWN_SYNTHETIC` que **não** é confirmado automaticamente. Usa um dicionário RAM e `synthetic_snapshot` copiado. Nenhuma atualização de documento, transaction PostgreSQL ou durabilidade foi criada. `COMMITTED_SYNTHETIC` altera apenas o HEAD do simulador; `document_write_performed=false`, `qdrant_write_performed=false` e `durable=false` em todos os recibos.

Para produção, continuam pendentes CAS/If-Match real, unicidade/transação no banco autorizado, tratamento de timeout/outbox, restore e readback em origem. A simulação evita escolher um storage novo prematuramente.

## 5. Implementação aditiva e plano de validação

| Artefato novo | Conteúdo | Restrições |
|---|---|---|
| `gaia_document_mcp/process_learning.py` | `AdministrativeProcess`, `ApprovedKnowledgeFixture`, `SyntheticOwnerOnly`, `HybridLearningPreview` | Somente RAM, eventos sintéticos, no Qdrant; operador único |
| `gaia_document_mcp/owner_concurrency.py` | `SyntheticRequest`, `InMemoryRevisionCoordinator` | Sem banco, rede, persistência ou mutações de arquivos |
| `tests/test_owner_process_learning.py` | Positivos e negativos de processos, analogias, captura automática, owner, replay e corrida | Fixtures fictícias; nenhuma credencial real |
| `.github/workflows/gaia-document-mcp-isolated-ci.yml` | Compilação/teste adicional somente na CI própria | Não alterar workflows de release nem habilitar deploy |
| `docs/document-mcp/14, 15, README` | Aditivo de escopo e evidências versionadas | Fontes históricas preservadas |

**Gates de CI:** regressões anteriores 49 contratos v2 + 13 OCR/NOM + 39 correlação P0/P1, mais a nova suíte G14-B. Contagem real da nova suíte apenas após leitura dos logs; não contabilizar como PASS antes de CI verde. Verificar também workflow herdado R05/R07 por SHA final separadamente.

## 6. Critérios de aceite e limites de evidência

| Gate | Critério |
|---|---|
| B0 Inventário | Branch/PR/HEAD confirmados; nenhuma mutação em branches de base |
| B1 Contexto administrativo | Processos com requerimentos semelhantes, mas números diferentes, permanecem distintos; analogia rotulada |
| B2 Captura automática | Eventos geram candidatos deduplicados com processo/origem; sem exigir clique por evento |
| B3 Recuperação híbrida | Contexto provisório fica no processo; memórias aprovadas podem ser consultadas transversalmente com proveniência |
| B4 Dono único | Rejeição sintética de operador diferente; **sem atribuir autenticação real** |
| B5 Concorrência | Uma única revisão sintética avança em corrida; conflito de payload/retry e UNKNOWN não produzem sucesso falso |
| B6 Isolamento de commits | Diff limitado ao ramo Document MCP, workflows de deploy ainda bloqueados |
| B7 Operação real | **BLOQUEADO**; exige autorização própria para IDP/DB/OCR/NOM, LGPD, registros reais, Qdrant e merge |

**Riscos:** conteúdo OCR é dado não confiável (prompt injection); nenhuma instrução do documento deve gerar ferramenta; o protótipo não faz PII redaction nem embeddings; origem e revisão não são autenticadas; approved flag da fixture não é prova do conector; memória de trabalho é volátil; concatenação de número oficial é contextual e não equivale a ID judicial ou identificação de cliente.

**Rollback:** reverter somente commit(s) do G14-B na nossa branch, sem afetar R07/R06, NOM/OCR, Qdrant, GitLab, Linear, objetos ou serviço externo. Nenhum histórico BC01 foi importado.

**Status de autoria deste MD:** relatório preparado na branch; resultado real da CI, SHA final e eventuais falhas devem ser verificados por readback do GitHub antes de declarar PASS.
