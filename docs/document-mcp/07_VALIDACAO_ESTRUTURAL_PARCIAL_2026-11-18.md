# GAIA Document MCP — validação estrutural parcial v1

**18/11/2026 | Escopo estrito:** somente `feat/gaia-document-mcp-isolado`; leitura superficial da `main` para comparação. **Não houve acesso/mudança de servidores, serviços externos, Qdrant ou branches alheias durante esta auditoria.**

**Baseline analisada:** `e45ed4a69fd9eae98c5703baf0b890e9a1784b85`.
**PR de isolamento:** https://github.com/tight-knit-net/gaia-rag-mini/pull/7 — draft, base `feat/r07-office-knowledge-assimilation`.

## A. Resultado
**APROVADA COM RESSALVAS para arquitetura de fase 0 e continuação somente dentro desta branch.**
**NÃO APROVADA** para publicar MCP, conectar contas ou aceitar documentos reais; **NÃO HOMOLOGADA** para integração operacional com R07/R06, Stirling-PDF, DocuSeal, Groq, Google Workspace ou Qdrant.

A topologia dos novos arquivos está organizada e não altera `app/server.py`, `src/gaia_rag_r05` nem workflows preexistentes do RAG. O pacote independente não tem servidor MCP registrado ou adaptadores externos executáveis. Ele expõe apenas dataclasses, manifesto de capacidades, prévia de memória sem persistência e configurações demonstrativas.

**Evidência GitHub**: a comparação da branch com R07 observou 2 commits à frente, 0 atrás e 16 arquivos **adicionados**, nenhum arquivo existente alterado. A PR #7 permanece em draft e mergeable_state=clean no momento da inspeção; branch protected=false.

**CI auditada no SHA**:
- `GAIA Document MCP - isolated contract CI`: 21/21 testes de `unittest`, compilação e checagem textual de congelamento dos workflows: sucesso em https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44349609576
- Validação estática herdada R05: sucesso em https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44349609744
- Estes testes são sintéticos e **não** exercitam operações de rede, runtime MCP real, payload completo de PDF, OCR, credenciais, assinatura ou Google Drive.
- Um workflow anterior falhou por uma checagem de sintaxe YAML; erro foi corrigido na mesma branch, confirmado por CI verde atual. Não transferir aceite para outro SHA.

## B. Auditoria por componente

| Componente da branch | Parecer | Evidência e limite |
|---|---|---|
| `gaia_document_mcp/contracts.py` | PARCIAL | Validação de tipagem/proveniência inicial e prefixo de cliente; não comprova hash nem identidade do revisor |
| `pipeline.py` | PARCIAL | Recibos idempotentes apenas em RAM; prévia institucional bloqueada para condições básicas, sem comparação R07 |
| `settings.py` | PARCIAL | Recursos perigosos desligados por padrão; flags de ambiente não constituem autenticação/autorização |
| `schemas/gaia.document-event.v1.schema.json` | PARCIAL | Representa o **recibo produzido por `capture()`**, não o `DocumentEvent` de entrada nem a candidata R07 |
| `tests/test_document_mcp.py` | OK fase 0 | 21 casos sintéticos aprovados, sem cobertura dos casos contratuais abaixo |
| `docs/document-mcp/` | OK estrutural | Projeto, fontes, contratos, topologia, gates e parecer separados e rastreáveis |
| CI exclusiva | OK limitada | Teste sem segredos ou deploy; guardião de freeze textual não substitui análise semântica dos jobs |
| Serviços Stirling/DocuSeal/Groq/Drive | NÃO IMPLEMENTADOS | Sem conexões, servidor MCP ou certificados operacionais; só catálogo de futuras ferramentas |

## C. Lacunas verificadas no código (prioridade antes do primeiro adaptador real)

**P1 — identidade do evento e deduplicação insuficientes.** `DocumentEvent.fingerprint()` não incorpora `drive_id`, `client_id`, o digest do conjunto de evidências, estado da revisão ou um ID separado de execução/tentativa. Dois eventos com o mesmo `file_id`/processo/hash/operação/provedor/status mas avaliações distintas podem gerar o mesmo `event_key`. Manter `operation_id` e `review_revision` separados da chave de idempotência de uma única tentativa; garantir isolamento por origem, execução e política de retentativas antes de usar armazenamento durável.

**P1 — evidência/identidade autoafirmada.** `source_verified`, `fields_verified`, `client_verified`, `ocr_reviewed` e `reviewer_verified` são apenas booleanos passados pelo chamador. O módulo não confere ator, assinatura de recibo, registro de aprovação, correspondência real dos bytes com SHA256 ou autenticidade da origem. Nunca autorizar movimento, assinatura, compartilhamento ou memória por estes flags; exigir verificação server-side.

**P1 — entrada excessivamente atrelada a Google Drive e vínculo já estabelecido.** `DocumentSource` exige `drive_id`, `file_id`, `client_id` NNN e `process_id` para **todas** as operações. Não representa bem documentos criados do zero, cópias temporárias, fontes Dropbox/Notion, documentos ainda sem cliente ou triagem sem processo. Separar objeto documental, proveniência por provedor e vínculo administrativo posterior, com bloqueio de promoção até haver identificação confirmada.

**P1 — falta implementação real de ferramentas e autorização.** `TOOL_CATALOG` é manifesto declarativo, não registro MCP. `GateSettings.may_execute()` é função de configuração, não política por usuário/arquivo/ação. Não conecta nenhum vendor nem consulta R07/R06. A futura camada precisa aplicar identidade, escopo, confirmação, recibos e readback por operação.

**P2 — `source_ref` tem validação tardia.** Cada ID do Drive é aceito até 150 caracteres, mas a referência concatenada `drive:{drive_id}:{file_id}` é limitada a 200 caracteres somente quando a propriedade é acessada. Entradas aceitas na construção podem falhar depois; validar a referência final no construtor e adicionar caso negativo.

**P2 — processamento e revisão documental incompletos.** Falta MIME, páginas e idioma OCR, qualidade, ID do original/derivado, ordem das páginas, tipo de transformação, hash validado de fato e status de revisão atestada. `derived_sha256` pode existir no objeto, mas não aparece no recibo. São necessários para rastreabilidade forte de PDF/editoração.

**P2 — OCR mock e candidatura editorial.** `memory_preview()` não bloqueia explicitamente `provider=mock` para OCR se o chamador marcar manualmente todos os booleanos como verdadeiros. Nenhuma decisão automática de confiabilidade pode vir do próprio modelo ou do texto do PDF.

**P2 — regras de nome insuficientes no contrato base.** O prefixo `NNN_` é imposto para nome proposto, mas os caracteres e formatos proibidos são menos restritivos que as regras canônicas NOM. Reutilizar o motor NOM real; não criar segunda regra de nomenclatura independente.

**P2 — modelo de eventos e schema.** O JSON Schema `v1` descreve `capture()` (com `persisted=false`) e não o `DocumentEvent` integral. Diferenciar nomes e versões de contratos de entrada, recibo, OCR, derivado e candidato de memória; criar validação schema↔runtime.

**P2 — guarda de CI.** A verificação de `if: false` é textual e pode ser satisfeita por comentários/trechos não aplicáveis. Para um futuro controle de publicação, interpretar YAML efetivo e testar os jobs/actions permitidos, permissões e eventos.

**P2 — privacidade e progresso operacional.** A saída de `memory_preview` inclui `summary` quando elegível, sem rotina de minimização de dados pessoais; `KnowledgeCapture` guarda eventos em dicionário efêmero e não tem TTL, auditoria persistente ou controle de concorrência. Não anunciar captura de conhecimento durável até existir store transacional, idempotência e retenção definida.

**P3 — higiene de documentação.** A referência antiga `https://docs.stirlingpdf.com/Configuration/Operations/OCR/` redireciona para `https://docs.stirlingpdf.com/Server/Operations/OCR-Languages/`. Atualizar a origem canônica em revisão editorial posterior; verificar versões exatas da API depois de fixar o fornecedor.

## D. Verificação cruzada com documentação oficial

**Stirling-PDF**: https://docs.stirlingpdf.com/Server/Install/Docker/ confirma imagem `latest` com Tesseract, OCRmyPDF e LibreOffice; `latest-ultra-lite` não tem OCR. API REST https://docs.stirlingpdf.com/Developers/API/ documenta `X-API-KEY`, Swagger local e limite/allowance para chamadas API conforme plano; não prometer ilimitado. Uso exige imagem versionada e teste local com PDFs de laboratório.

**DocuSeal**: https://www.docuseal.com/docs/api confirma templates, submissions e documentos; https://www.docuseal.com/faq/which-endpoints-are-available-only-with-the-pro-plan lista endpoints exclusivos Pro/Developer Sandbox. https://www.docuseal.com/resources/use-webhooks define assinatura HMAC SHA-256 no `X-Docuseal-Signature`, timestamp e corpo bruto, importante para a futura verificação de eventos.

**GroqCloud**: https://console.groq.com/docs/tool-use/remote-mcp confirma suporte MCP remoto em beta; https://console.groq.com/docs/your-data esclarece retenção: inference não é retida por padrão, mas logs de confiabilidade/abuso e recursos persistentes podem reter dados; ZDR é configurável. Necessário avaliar destino de dados e uso com documentos de cliente.

**MCP**: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization e https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations exigem cuidados OAuth de transporte HTTP, validação de audience, proteção de tokens, princípio de menor privilégio e rejeição de token passthrough. A branch ainda não contém esse servidor de recursos autenticado.

**Google Drive**: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update e https://developers.google.com/workspace/drive/api/guides/manage-revisions respaldam o plano de controle por ID/versão e readback. A versão observada `OBS_` no laboratório não é uma garantia de ETag oficial. Nenhuma operação Google foi executada nesta auditoria.

## E. Leitura superficial da main — sem alteração

Consulta da `main`: SHA `11c0eb593890dc7ff2a26b2d5eda8fb33828522b`, apenas `README.md` na árvore observada.

Comparação read-only `main...feat/gaia-document-mcp-isolado`: ramo descendente, 230 commits à frente, zero atrás (histórico herdado de R05/R06/R07 incluído), não prova que todas as etapas intermediárias tenham sido aprovadas para merge. A comparação relevante para esta entrega é **R07...Document MCP: 2 commits, 16 arquivos adicionados**. A PR #7 aponta a R07, não `main`. A `main` não contém runtime documental com o qual testar integração direta; compatibilidade inicial é apenas **de intenção/contrato e Git**, não de operação. Qualquer deploy existente fora do GitHub não foi inspecionado.

## F. Decisão e próximo gate

**Aprovado:** organização da branch, separação arquitetural, documentação de responsabilidades, gates e testes sintéticos de fase 0.

**Condicionado:** antes de programar adaptadores e usar dados reais, corrigir P1, acrescentar testes negativos de eventos/proveniência, definir identidade e armazenamento, separar modo de captura do modo de aprovação, fixar versões e contratos.

**Bloqueado:** merge à `main`, deploy, integração com Akamai/EC2/Drive fora da branch, ferramentas externas e qualquer gravação de memória.

**Nota de governança:** este relatório é uma validação parcial interna. Não é homologação externa, de produção, legal ou de cliente. Todas as mudanças futuras permanecem limitadas à branch isolada até autorização explícita.
