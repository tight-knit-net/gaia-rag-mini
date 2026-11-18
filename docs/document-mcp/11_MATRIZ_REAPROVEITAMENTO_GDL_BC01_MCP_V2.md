# GAIA Document MCP v2 — matriz detalhada de reaproveitamento da GDL-BC01/D1

**Versão:** 0.1.0 — proposta documental, sem implantação.  
**Emissão — instante aferido:** 2026-11-18T20:06:53-03:00, fuso America/Sao_Paulo, origem: ferramenta de horário local do ChatGPT. O commit no GitHub fornece o horário separado da publicação.  
**Escopo de escrita:** somente branch GitHub feat/gaia-document-mcp-isolado, PR #7 Draft.  
**Fontes apenas leitura:** GitLab gaia_workspace1/gaia-doclab (ID 88873934, ref docs/doclab-file-search-20261113, SHA 2493f659866e16bd6499c9122e488d54d612a81d); Linear P-GOG-7; nossa branch antes do registro SHA f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8.  
**Trabalho executado:** inspeção da arquitetura BC01/41–47, schema BC01/50, fixtures 51/52, D1/56–60, matriz BC01/45, Linear e contratos atuais do MCP. **Nenhum código copiado, corrigido ou executado nesta tarefa.**

## 1. Decisão recomendada

**Adotar os princípios úteis da GDL-BC01 sem transplantar sua implementação proposta.** GDL-DS 1.0.0-rc1 descreve conteúdo editável, layouts e autoridade de cada revisão. O gaia.document-event.v2 descreve operações, hashes e recibos de processamento; não é o mesmo agregado. A integração correta é por IDs, versões e evidências explícitas, sem fusão de schemas.

A aprovação do titular em 13/11/2026 (GDL-DEC-BC01-D1-2026-11-13) tornou a BC01 **fonte de referência documental**. NÃO aprovou código, runtime, editor, storage, esquema como API de produção ou operações em VM. Documentos históricos 40/53 continuam com texto CANDIDATA, cuja interpretação foi atualizada pelo aditivo 56. No GitLab, main observada = 442be74cd1f620a37f4fa1180254ac517bcdb25e, somente README.md e .gitlab-ci.yml; o acervo está na branch de pesquisa separada.

A classificação proposta dos **32 requisitos reais** de BC01/45 é: **8 ADOTAR como diretriz, 10 ADAPTAR por interface, 14 ADIAR no MVP**. ADOTAR não significa implementado nem testado. ADIAR não retira os bloqueios de segurança antes da produção.

## 2. Matriz de 32 requisitos — fonte BC01/45

| ID BC01 | Requisito resumido | Estado/equivalência no MCP v2 | Disposição proposta | Gate | Critério de próximo teste |
|---|---|---|---|---|---|
| GDL-RQ-001 | Sem dependência SaaS obrigatória | OCR local e ferramentas externas opcionais | **ADOTAR** | P0 | Modo local sem iLoveAPI e Groq |
| GDL-RQ-002 | Editor visual avançado | Não existe Studio/renderer no MCP | **ADIAR** | P3 | Fora do MVP |
| GDL-RQ-003 | FastAPI PostgreSQL PgQueuer e checkpoint | REST OCR existe em módulo irmão e recibos MCP em RAM | **ADAPTAR** | P1 | Definir correlação de jobs sem duplicar infraestrutura |
| GDL-RQ-004 | QA visual PDFium/OpenCV | Sem inspeção geométrica | **ADIAR** | P3 | Exigir testes antes de edição/render |
| GDL-RQ-005 | ODT preferencial para texto | Não há editor ou importador ODT | **ADAPTAR** | P2 | Fonte editável por revisão quando existir fluxo de edição |
| GDL-RQ-006 | PDF final e PDF/A condicional | MCP só lê PDF e emite prévia | **ADIAR** | P3 | Sem alegação PDF/A sem veraPDF do hash final |
| GDL-RQ-007 | Importar DOC DOCX ODT Google Docs | SourceProvider genérico mas Hybrid só aceita PDF Drive | **ADAPTAR** | P2 | Preservar original e relatório de perdas |
| GDL-RQ-008 | OCR e revisão humana | Hybrid bloqueia mock e confere SHA | **ADOTAR** | P0 | Teste real DEMO Tesseract e campos revisados |
| GDL-RQ-009 | Originais imutáveis e versionados | source_ref e SHA sem store durável | **ADOTAR** | P0 | Verificar bytes e revisão antes/depois |
| GDL-RQ-010 | Backup externo PG e objetos | RAM sem restore | **ADIAR** | P3 | Gate de produção com restore medido |
| GDL-RQ-011 | VM Akamai 8 GiB distinta | Sem implantação | **ADIAR** | P3 | Não provisionar nesta fase |
| GDL-RQ-012 | GitLab Wiki Linear EC2 por SHA | PR #7 CI no GitHub e Linear fonte externa | **ADOTAR** | P0 | Rastrear SHA e evidências sem mexer nos outros sistemas |
| GDL-RQ-013 | Nenhum deploy no estágio documental | Somente CI de testes | **ADOTAR** | P0 | Manter workflow de deploy bloqueado |
| GDL-RQ-014 | JSON Schema versionado | Event e Receipt v2 distintos sem validador semântico | **ADAPTAR** | P1 | Validação runtime e contrato por agregado |
| GDL-RQ-015 | IDs de nós e objetos únicos por revisão | Há event_key mas não árvore GDL-DS | **ADIAR** | P3 | Não confundir IDs de documentos e de eventos |
| GDL-RQ-016 | Validação page_ref | MCP não modela páginas/objetos | **ADIAR** | P3 | Só quando existir Studio ou overlay |
| GDL-RQ-017 | Geometria de objetos e assinaturas | Sem editor geométrico | **ADIAR** | P3 | Gate de render/assinatura |
| GDL-RQ-018 | Asset existe e tem escopo | Reference e SHA sem ACL de assets | **ADAPTAR** | P2 | ObjectRef mediado e scope real |
| GDL-RQ-019 | Overlay preserva original PDF | Overlay não existe | **ADIAR** | P3 | Fora do MVP |
| GDL-RQ-020 | Uma fonte editável por revisão | source_provider difere de source_kind | **ADOTAR** | P1 | Diretriz para edição futura e testes de revisão |
| GDL-RQ-021 | Relatório de perdas em conversão | derived_sha256 sem interop_report | **ADAPTAR** | P2 | Perda relevante bloqueia autopromoção |
| GDL-RQ-022 | If-Match e 409 em revisão concorrente | source_version é declarativo | **ADAPTAR** | P1 | Verificação de versão no backend e 409 |
| GDL-RQ-023 | Catálogo fontes e timbrados | Não existe renderer | **ADIAR** | P3 | Licença e embedding antes de uso profissional |
| GDL-RQ-024 | PDF/A verificado por veraPDF | Sem validação PDF/A | **ADIAR** | P3 | Não usar HTTP 200 como conformidade |
| GDL-RQ-025 | SQL/S3 idempotente e reconciliação | event_key mas recibos só em RAM | **ADAPTAR** | P1 | Request key por scope e transação/outbox |
| GDL-RQ-026 | ACL entre clientes e aprovação humana | NNN tenant e HMAC não são autorização | **ADOTAR** | P0 | Negativas cross-client e aprovação R06 separada |
| GDL-RQ-027 | Não reescrever PDF assinado silenciosamente | Sem assinatura ou mutação | **ADIAR** | P3 | Gate de assinatura |
| GDL-RQ-028 | Rastreabilidade requisito decisão contrato teste | Docs e testes sintéticos têm IDs | **ADOTAR** | P0 | Referenciar SHA caso e fonte sem confundir aprovação |
| GDL-RQ-029 | Compatibilidade de schemas e revisões | v1 preservado e v2 criado sem negociação | **ADAPTAR** | P1 | Mapa de versões e leitura retrocompatível |
| GDL-RQ-030 | Google Docs autenticado e export auditável | SourceRef Drive sem export efetiva | **ADAPTAR** | P2 | ID versão nativa e SHA de export separados |
| GDL-RQ-031 | Retenção RPO RTO antes da produção | RAM sem TTL | **ADIAR** | P3 | Gate obrigatório antes de dados reais |
| GDL-RQ-032 | SBOM licenças e benchmark 8GiB | Sem serviços novos | **ADIAR** | P3 | Executar apenas em ambiente autorizado |

## 3. Contratos e riscos de compatibilidade

| Conceito | Contrato GDL-BC01 | MCP v2 observado | Risco de confusão | Proposta |
|---|---|---|---|---|
| Identidade lógica | document_id | DocumentSource.file_id / source_ref | Mesmo arquivo pode servir mais de um documento, e vice-versa | DocumentIdentity separado de SourceAsset |
| Revisão documental | revision_id e parent_revision_id | DocumentEvent.event_revision e source_version | Número de evento não identifica conteúdo editado | document_revision_id explícito em ponte futura |
| Escopo de autorização | client_scope | client_id NNN e tenant OCR | Número NNN e tenant não provam ACL | Resolver scope por identidade autenticada e recurso |
| Fonte editável única | authority.source_kind = odt ou gdl_ds | source_provider = drive/dropbox/local/generated/notion | Localização do arquivo não é autoridade de edição | source_kind somente em DocumentRevision futuro, não no evento |
| Referência binária | objectRef com bucket/key/version_id/sha256/size_bytes | source_ref texto + sha256_original | Origem S3, Drive nativo e export são tipos diferentes | Referências tipadas e versão confirmada pelo provedor |
| Integridade | SHA sobre bytes do original, versões e render_build | sha256_original, derived_sha256, matches_original | Hash recebido não é hash verificado | Conferir bytes no backend e vincular revisão real |
| Estado do conteúdo | interop_state native/review_required/verified + status da revisão | event.status completed/review_required/blocked/failed | completed pode significar OCR feito, não documento aprovado | Estados separados por domínio |
| Operação e retry | workflow_runs, stage_attempts, idempotency_keys, publication_intents | operation_id, event_key, receipts em RAM | event_key varia com evidência/estado; não é chave de requisição | request_id, idempotency_key e run_id separados |
| Autoridade humana | ator e revisão aprovados, template não revogado | ReviewProofVerifier HMAC sem emissor autenticado | HMAC prova só posse de chave | Registro documental servidor + portal R06 e clique independente |
| Teste de schema | JSON Schema BC01/50 com validação semântica adicional | Event/Receipt JSON Schema 2020-12; teste estrutural superficial | Passar schema não valida ACL, objeto e revisão | Validadores runtime + testes de semântica e negativos |
| RAG | BC01 não confere aprovação Qdrant | preview de candidata, R07/R06 ainda não conectados | Aprendizado automático não é memória salva | R07 compara somente aprovado, R06 exige revisão humana |
| Google Docs | documento nativo + export e recibo próprios | source_provider=drive, hash opcional | Hash do ODT exportado não é hash do documento nativo | ID/revisão da origem e SHA do export separados |

### Regras de não-regressão

- Nunca copiar GDL-DS no schema v2 de eventos para resolver problemas de revisão; isso introduziria geometria, assets, modos flow/free/overlay sem motor correspondente.
- Não tornar SeaweedFS, PgQueuer, Typst, Gotenberg, PDFium, Fabric.js, DocuSeal ou banco adicional dependências do MVP OCR→NOM.
- Preservar Tesseract local operacional sem Groq/iLoveAPI. Uso de SaaS externo somente opt-in e com política de dados, custo e autorização próprios.
- Não deduzir client_scope do nome NNN nem do tenant OCR; não enviar conteúdo OCR de clientes ao Groq automaticamente.
- Não misturar RAG de memórias aprovadas com arquivos ou documentos-fonte, nem gerar aprovação por HMAC recebido.
- Não acessar Google Drive via GAIA MCP v.100. Nesta conta as ações Google Drive usam exclusivamente o conector nativo e cada escrita precisa de autorização.
- Sem merge, rebase, deploy, alterações no Linear, GitLab, EC2, produção ou Qdrant neste gate.

## 4. Camadas e prioridades de execução futura

**P0 — invariantes MVP:** origem e SHA confirmados, cliente/processo real, sem mock, NOM PREVIEW_ONLY, evento sem escrita, dados de teste sintéticos, isolamento de cliente e gates humanos.  
**P1 — modelos e provas:** documento lógico/revisão distinguíveis, versionamento real, idempotência transacional, compatibilidade de schemas e atestação autenticada.  
**P2 — capacidade expandida:** conversão com relatório de perda, importação de office, Google Docs mediado e assets.  
**P3 — adiado:** editor visual e layout avançado, PDF/A, assinaturas, fontes, VM dedicada, backup/restore operacional e benchmarks. *Backup/retention e controle de versão são gates de produção mesmo quando a implementação geral está adiada.*

## 5. Matriz de gates e resultados

| Gate | Evidência exigida | Situação |
|---|---|---|
| A0 — matriz documental | Exatamente 32 IDs, decisão D1, SHA de fonte, códigos de caso | **PROCESSADO nesta proposta**, readback do commit pendente |
| A1 — adequação das classes v2 | Regras semânticas adicionais e regressões próprias com fixtures artificiais | **PENDENTE**; nenhum código alterado |
| A2 — acoplamento OCR/NOM | Teste com motor real autorizado, PDF sintético, SHA e prévia read-only | **PENDENTE** |
| A3 — conversões e QA | Artefatos e perdas revisados, schema e semântica | **PENDENTE**; fora do MVP imediato |
| A4 — identidade e persistência | Testes cross-client, controle de tokens, revisão, concurrency 409 e readback | **PENDENTE** |
| A5 — R07/R06 | Consulta aprovada, proposta, revisão humana e readback Qdrant | **BLOQUEADO** até gate autorizado |
| A6 — integração final | Reconciliar a R07 mais recente, gates das branches irmãs, revisão do orquestrador | **NO-GO**, PR #7 segue Draft |

**Evidências de teste existentes e não reproduzidas aqui:** BC01/60 contém 13/13 negativos offline, duas fixtures e 15 entradas do manifesto verificado. Nossa última rodada de CI técnica anterior à matriz aprovou 49 casos de contrato + 13 do híbrido = 62 testes sintéticos, mas não se executou OCR real, validação de app GDL-DS, API de terceiros ou TestLab nesta tarefa. Esses conjuntos não devem ser somados como cobertura de um mesmo produto.

## 6. Governança Linear e riscos externos

Linear P-GOG-7 é o projeto documental DocLab, enquanto GOG-169 é gate do orquestrador para **última** integração da PR #7. GOG-58 e GOG-59 estavam em Backlog na consulta; GOG-61 e GOG-89 em progresso. O parecer GDL-VAL-001 documenta **NO-GO E2E** do piloto, incluindo webhook HTTP 401 observado historicamente. Não tratar esses registros como situação instantânea de serviço: nenhum endpoint foi testado.

Não publicar documentação BC01 na Wiki, não importar arquivos ZIP ou decisões do DocLab para outros repositórios e não escrever no Linear. Documentar somente as propostas na nossa branch; homologação e mudança de arquitetura dependem de decisão específica do titular.

## 7. Fontes imutáveis para readback

- [BC01/45 — requisitos 001–032](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/45_MATRIZ_RASTREABILIDADE_REQUISITOS_BC01.csv); [BC01/41 — precedência](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/41_DECISOES_PRECEDENCIA_E_GLOSSARIO_BC01.md); [BC01/42 — arquitetura](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/42_DESCRICAO_ARQUITETURAL_RECONCILIADA_BC01.md).
- [BC01/43 — autoridade ODT/GDL](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/43_CONTRATO_ODT_GDL_FONTE_E_REVISOES_BC01.md); [BC01/44 — validação semântica/API](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/44_SCHEMA_SEMANTICA_TESTES_E_API_BC01.md); [BC01/47 — riscos/gates](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/47_RISCOS_PENDENCIAS_PORTOES_BC01.md).
- [BC01/50 — schema 1.0.0-rc1 Draft](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/50_GDL_DOCUMENT_SCHEMA_BC01_DRAFT.json); [BC01/51 — fixture fictícia](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/51_GDL_DOCUMENTO_FICTICIO_BC01.json); [BC01/52 — negativos](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/52_GDL_CASOS_NEGATIVOS_BC01.json).
- [D1/56 — aprovação documental](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/04_APROVACAO_D1/56_TERMO_DE_APROVACAO_D1_GDL_BC01.md); [D1/58 — leitura correta](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/04_APROVACAO_D1/58_LEIA_PRIMEIRO_BASELINE_REFERENCIA_APROVADA_BC01.md); [D1/60 — recheck offline](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/04_APROVACAO_D1/60_EVIDENCIAS_RECHECK_D1.json).
- [MCP — contratos v2](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/gaia_document_mcp/contracts.py); [MCP — preview](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/gaia_document_mcp/pipeline.py); [MCP — híbrido OCR/NOM](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/gaia_document_mcp/hybrid.py); [MCP — prova HMAC](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/gaia_document_mcp/trust.py).
- [Projeto Linear DocLab](https://linear.app/gogetterhub/project/gaia-doclab-7e72b9011554), [GDL-VAL-001 NO-GO E2E](https://linear.app/gogetterhub/document/gdl-val-001-auditoria-do-acervo-topologia-e-integracao-grc-no-go-e2e-8a1345a92108), [GOG-169 gate final](https://linear.app/gogetterhub/issue/GOG-169/orqg-int-gate-documental-da-ultima-integracao-gaia-document-mcp).

**Risco principal:** transplante acrítico de arquitetura de produção DocLab para o MVP Document MCP. **Rollback desta entrega:** reverter apenas o commit documental da nossa branch, sem migrar dados. **Próxima autorização necessária:** se o titular aprovar a matriz, especificar e testar o contrato de correlação documental no mesmo ramo.
