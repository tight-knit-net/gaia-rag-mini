# G14-H — Revisão independente de evidência, replay, paginação SQLite e contrato OCR R02

**Versão:** 1.0.0 — execução de testes e relatório de auditoria de laboratório; NÃO é homologação operacional.  
**Disparo aferido:** `2026-11-18T23:44:11-03:00`, fuso `America/Sao_Paulo`, relógio local do ChatGPT.  
**Emissão aferida:** `2026-11-18T23:51:30-03:00`, fuso `America/Sao_Paulo`, mesma origem de relógio. A publicação posterior tem instante próprio, registrado pelo GitHub.  
**Último gate G14-G:** commit `c9c5bab32756659dce688497b389029230da19d7` em `2026-11-19T02:28:25Z`, equivalente a **18/11/2026 às 23:28:25 BRT** (metadados GitHub).  
**Repositório:** `tight-knit-net/gaia-rag-mini`; somente branch `feat/gaia-document-mcp-isolado`; [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7), **Draft**, base `feat/r07-office-knowledge-assimilation` @ `6aa55823082842bbe4799773a8acfc2e4eebdea1`.  
**HEAD inicial:** `c9c5bab32756659dce688497b389029230da19d7`. **HEAD técnico corrigido:** `b7b3216ef5de43bd0677bf64153a07cc39b6c27f` (`2026-11-19T02:50:41Z` = 18/11 às 23:50:41 BRT).  
**Fonte:** relatório [20 — G14-G](20_G14G_REPLAY_EVIDENCIA_PAGINACAO_SINTETICA.md); código e CI da PR #7 no GitHub; **repasse OCR R02 fornecido pelo titular nesta conversa**, classificação *proposta de correção, não implementada*, 18 ensaios planejados. O arquivo OCR R02 externo não foi aberto, e a branch `feat/ocr-documental-isolado` não foi consultada nem alterada.  
**Permissões/limites:** autorizado apenas desenvolvimento sintético na PR #7. Não ler/escrever GitLab, Linear, Google Drive, Cloudflare, Qdrant, R06/R07, outros serviços ou outras branches; não mergear, publicar, migrar ou instalar sistemas. Nenhum OCR, provedor, API, LLM, documento de cliente ou banco real envolvido.

## 1. Parecer executivo

**GO para a revisão e os ensaios sintéticos do G14-H; NO-GO para integração operacional.** O código prepara um **contrato de metadados** para futura ingestão OCR; não altera nem executa o motor OCR, não alega 100% de transcrição e não certifica documento.

**Testes do commit técnico corrigido:** [run 44447239231](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447239231) `success` com **320/320 (100%)**: 287 anteriores + **33 G14-H** (8 de paginação e 25 do contrato OCR R02). [CI PR do mesmo SHA 44447244949](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447244949) também `success`. Nenhum teste de OCR de produção, REST/MCP autenticado ou E2E foi executado aqui.

**CI herdada R05/R07:** [run 44447244970](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447244970) constava `in_progress` na última leitura anterior à publicação; **não declarar PASSOU** até status conclusivo. O baseline G14-G [44444581065](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444581065) falhou em S9, bloqueio de cadeia de suprimentos de responsabilidade da R07. A nossa branch não alterou lock, SBOM nem scripts S7/S8/S9.

## 2. Auditoria independente G14-G: achados e correção restrita

| ID | Criticidade/estado | Evidência | Decisão |
|---|---|---|---|
| H-01 | **P1 — MITIGADO SINTÉTICO** | `verify_disposable_page_sequence` validava contagem, cursor e geração; `confirm_current_coverage` antes não comparava com o banco os valores de cada item apresentado. O número da geração sozinho não detecta mutação do objeto da página no cliente. | G14-H agora lê novamente, **no mesmo snapshot transacional SQLite**, cada fatia limitada e confronta o payload exato. Mudança em `summary_digest`, `process_id`, `source_count` ou `memory_approved` dispara `PAGE_CONTENT_MISMATCH`. |
| H-02 | **P2 — MITIGADO SINTÉTICO** | Campo `limit` de páginas fornecidas ao verificador podia causar erro de tipo ou ser aceito sem verificação numérica. | Rejeita tipo/intervalo inválido com `PAGE_COVERAGE_INCOMPLETE`. |
| H-03 | **P1 — MITIGADO SINTÉTICO** | Ao consultar processo por `process_key`, o método não confrontava obrigatoriamente `process_id` da referência com o vínculo canônico. | `page_pending`/readback agora verificam `process_registry`, rejeitando alias de ID com mesmo número oficial. **Isso é controle de integridade contextual, não ACL por cliente.** |
| H-04 | **P1 — PENDENTE** | `observe_demo_source` autentica somente bytes fictícios e campos fornecidos no próprio teste. Não é attestation do OCR, do documento da Prefeitura ou do operador real. | Exigir evidência assinada/observada por fronteira confiável em gate posterior autorizado. Não usar `provider_origin_authenticated=false` como aprovação. |
| H-05 | **P1 — PENDENTE** | Os metadados OCR R02 ainda não entram em `capture_observed_demo` via adapter E2E; não há qualidade real por página nem backpressure/lease transacional do motor. | Mapear contrato OCR R02 e manter testes em fixtures; integração fica para coordenação entre responsáveis e autorização futura. |
| H-06 | **P1 — PENDENTE** | A revisão de lote R06 ainda não dispõe de gesto autenticado comprovado neste projeto; readback Qdrant real e tratamento de `UNKNOWN` não foram homologados. | Candidatos automáticos continuam provisórios; `Salvar memória` real e recibo por item necessitam gate próprio. |
| H-07 | **P2 — PENDENTE** | Cursor SQLite utiliza OFFSET e digest local; SQL é apenas laboratório, sem paginação Qdrant, TTL ou token de servidor para produção. | Reavaliar com persistência/identidade/limites reais antes de produção. |

**Risco semântico:** `process_key` traz órgão, jurisdição e número oficial; requerimentos semelhantes de processos distintos são **analogias**, não identidade documental. O operador é único; `client_id` e `process_id` não representam autorização por cliente.

## 3. Contrato sintético de evento OCR R02 — sem editar a branch OCR

Arquivo novo `gaia_document_mcp/g14h_ocr_r02_contract.py`: função pura `preview_ocr_r02_contract`, que trabalha **somente com metadados inventados**. Invariantes:
- `process_id`, `process_key`, `document_id`, `source_ref`, versão e SHA-256 de origem; geração de fingerprint contextual. Formato DEMO é proteção de bancada, **não sanitização LGPD real**.
- Para PDF, número de páginas, blocos ordenados e contíguos (até 8 páginas por bloco **neste teste**), classificação por página `NATIVE/OCR_READABLE/LOW_CONFIDENCE/EMPTY/GRAPHIC/TECHNICAL/INVALID`, confiança, contagem de tentativas e hash de texto **sem conteúdo bruto**.
- Estado da tarefa `job_state` separado de `document_quality`: tarefa `COMPLETED` pode resultar em documento `NEEDS_DOCUMENT_REVIEW`. PDF completo com páginas faltantes é recusado; um trabalho parcial não vira sucesso global.
- Para DWG, KML, SHP e GeoJSON, somente **roteamento declarado de metadados**, sem OCR indevido nem parser real. ServiceExceptionReport invalida exportação; KML com codificação divergente pede cópia UTF-8 derivada; SHP sem DBF permanece incompleto; GeoJSON não recebe certificação cadastral.
- Exceções técnicas em códigos fechados, não texto de logs/segredos. O executor de fila, lease, fornecedor real, OCR Tesseract, rotação, conversão, CAD, KML, SHP e GeoJSON são **responsabilidades futuras do motor OCR**.
- `eligible_for_verified_document_evidence=false`, `requires_source_authentication=true`, `memory_approved=false`, `qdrant_written=false`, `actual_ocr_performed=false`.

**Atenção:** campos `confidence`, qualidade, hash por página e exceções são **declarados por fixture**, não certificados por fornecedor. O envelope não contém assinatura, evidência de origem autenticada, medição real nem leitura do documento.

## 4. Matriz de integração com os 18 ensaios do repasse OCR R02

**Legenda:** `COBERTO_SINTETICO` = só metadados/contrato reproduzidos por testes locais G14-H; `PARCIAL` = validação de parte da regra, sem componente operacional; `PENDENTE_OCR` = responsabilidade da branch OCR, não testado aqui. **Esta matriz não afirma execução dos T01–T18 originais na branch OCR.**

| Teste R02 | Correspondência na PR #7 / G14-H | Estado |
|---|---|---|
| T01 PDF 1 página | Validação de página e SHA em fixture | COBERTO_SINTETICO |
| T02 PDF 10 páginas | Blocos 8+2 e contagem | COBERTO_SINTETICO |
| T03 PDF 17 páginas | Blocos 8+8+1, cobertura exata | COBERTO_SINTETICO |
| T04 limites | Limite sintético de 64 páginas e até 8 por bloco; limite de bytes/provedor não validado | PARCIAL |
| T05 nativo + OCR | Estados de qualidade mistos e consulta documental | COBERTO_SINTETICO |
| T06 páginas insuficientes | Completed 3/10 bloqueado; partial rotulado incompleto | COBERTO_SINTETICO |
| T07 branco/gráfico | Metadata de página `EMPTY` testada; reconhecimento de gráficos não executado | PARCIAL |
| T08 rotação/inclinação e retry | Tentativas limitadas e exceções estruturadas; sem imagem corrigida | PARCIAL |
| T09 KML ServiceExceptionReport | Roteador metadata `INVALID_EXPORT_NO_OCR` | COBERTO_SINTETICO |
| T10 KML CP1252 | Metadata pede derivado UTF-8; nenhuma conversão de bytes | PARCIAL |
| T11 SHP sem DBF | Metadata `INCOMPLETE_SHAPESET`; não abre arquivo SHP | PARCIAL |
| T12 DWG | Metadata `CAD_ANALYZER_REQUIRED`; sem analisador CAD | PARCIAL |
| T13 concorrência de workers | Conflitos CAS já exercitados em SQLite G14-C; claim de OCR não exercitado | PENDENTE_OCR |
| T14 crash/lease | Rollback sintético G14-C, **não** lease/reclaim de fila OCR | PENDENTE_OCR |
| T15 replay idempotente | Idempotência contextual G14-G; tarefa real OCR não demonstrada | PARCIAL |
| T16 tenant indevido | Fixture de proprietário único, não prova JWT/política de escopo REST/MCP OCR | PENDENTE_OCR |
| T17 falha de provedor | Exceção sintética em código fechado; nenhum provedor real ou segredos | PARCIAL |
| T18 exportação/readback | Comparação SHA e readback SQLite sintético; não exporta documentos, nem rollback de provedor | PARCIAL |

**Ponto de integração recomendado:** OCR produz evento observado e versionado; Document MCP valida processo+fonte, preserva originais e decide candidato de aprendizagem provisória; R07 consulta/propõe memórias com linhagem; R06 mantém aprovação humana autenticada e botão **Salvar memória** com readback. Nenhum componente atua em produção por causa do presente contrato.

## 5. Testes executados, histórico da falha e rechecagem

| Suíte | Aprovados | Total | Percentual |
|---|---:|---:|---:|
| Contratos Document MCP v2 | 49 | 49 | 100% |
| OCR/NOM híbrido anterior | 13 | 13 | 100% |
| Correlação P0/P1 | 39 | 39 | 100% |
| Contexto G14-B | 39 | 39 | 100% |
| SQLite G14-C | 46 | 46 | 100% |
| Negativos G14-E | 32 | 32 | 100% |
| Contratos G14-F | 32 | 32 | 100% |
| Replay/paginação G14-G | 37 | 37 | 100% |
| **Revisão G14-H — 8 SQLite + 25 OCR** | **33** | **33** | **100%** |
| **Total CI específica do commit técnico** | **320** | **320** | **100%** |

**Falha controlada da primeira rodada:** [run 44447123368](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447123368), commit `292382c19fa02686568639bcf0d2f150fb09c9a4`: os 287 testes anteriores e 25 novos OCR passaram; 8 testes G14-H de paginação falharam em `setUp` por `INVALID_CLIENT_ID` — fixture `DEMO_CLIENT_001` incompatível com contrato v2. Corrigido **somente o identificador sintético da fixture** para `009` em commit `b7b3216ef5de43bd0677bf64153a07cc39b6c27f`, preservando schemas e regra de validação v2. [Run 44447239231](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447239231): **320/320 PASSOU**, logs GitHub `Ran 33 tests / OK`, sem skip ou erro.

**Arquivos de código no diff G14-G → G14-H:** `gaia_document_mcp/g14g_isolated.py`, `gaia_document_mcp/g14h_ocr_r02_contract.py`, `tests/test_g14h_audit.py` e `.github/workflows/gaia-document-mcp-isolated-ci.yml`. Quatro arquivos técnicos, **duas commits** (primeira suíte + ajuste da fixture). Código v2 em `contracts.py` não alterado.

## 6. Gates, rollback e próxima etapa

| Gate | Aceite | Estado ao emitir |
|---|---|---|
| H0 | Confirmação de PR/HEAD/base/CI anterior | PASSOU |
| H1 | Auditoria independente de evidência/replay/paginação | PASSOU como revisão; 7 observações |
| H2 | Correção sintética da integridade de paginação | PASSOU; oito negativos/positivos |
| H3 | Contrato OCR R02 de metadados sem OCR real | PASSOU; 25 testes |
| H4 | Regressões completas, 320/320, v2 preservado | PASSOU |
| H5 | Relatório MD, índice e readback no HEAD final | PENDENTE até publicação |
| H6 | CI herdada da R07 / cadeia de suprimentos | PENDENTE no commit técnico; baseline falhou em S9 |
| H7 | Homologação E2E com OCR e R06/R07/Qdrant | NO-GO e fora de escopo |

**Percentuais:** **100% dos testes sintéticos executados (320/320)**. Os gates H0–H4 representam **5/8 = 62,5%** dos oito critérios nesta fotografia, com H5 ainda não publicado, H6 pendente e H7 bloqueado. O percentual global de prontidão operacional **não tem denominador homologado** e não deve ser inferido dos testes.

**Riscos:** integridade de fonte só DEMO; origem real sem autenticação; qualidade OCR por página não medida; paginação OFFSET sem TTL ou cursor assinado; provider e fila OCR não integrados; retentativa/lease reais não homologados; aprovação humana em lote R06 e readback Qdrant não demonstrados; S9 herdado com bloqueios. Proibir uso de cliente D009 como fixture, incluindo dados disfarçados como DEMO.

**Rollback:** reverter somente commits G14-H na `feat/gaia-document-mcp-isolado` após reconferir HEAD. Banco temporário descartado em cada teste; R06/R07, OCR, Google Drive, Cloudflare, GitLab, Linear, Qdrant, produção e memória não têm mudanças para reverter.

**Próximo gate recomendado: G14-I, sem execução automática.** Auditoria dos envelopes OCR R02 e de proveniência verificada em um TestLab sintético de eventos com fila mock; exercitar deduplicação de job/lease sem provedor externo; preparar contrato de consumo Document MCP e revisão humana agregada para homologação futura. Manter limite de branch e autorização separada para qualquer E2E real/serviço.

**Evidências pinadas:** [módulo OCR contratual](https://github.com/tight-knit-net/gaia-rag-mini/blob/b7b3216ef5de43bd0677bf64153a07cc39b6c27f/gaia_document_mcp/g14h_ocr_r02_contract.py), [readback paginado](https://github.com/tight-knit-net/gaia-rag-mini/blob/b7b3216ef5de43bd0677bf64153a07cc39b6c27f/gaia_document_mcp/g14g_isolated.py), [33 testes](https://github.com/tight-knit-net/gaia-rag-mini/blob/b7b3216ef5de43bd0677bf64153a07cc39b6c27f/tests/test_g14h_audit.py), [CI própria](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447239231), [PR #7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7).
