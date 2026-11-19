# Contratos e segurança — interfaces a integrar

Versão inicial `gaia.document-event.v1`. Implementação **local sem efeitos externos**: `gaia_document_mcp/contracts.py`, `pipeline.py` e `schemas/gaia.document-event.v1.schema.json`.

## 1. Envelope de proveniência
Campos mínimos versionados:
- `drive_id`, `file_id`, `client_id` NNN, `process_id` exato.
- `source_version`: observação/versionamento declarado e conferido; **`OBS_...` NÃO é ETag/revision do Drive**. Em ação futura, revalidar a versão original imediatamente antes do efeito.
- `sha256_original`: digest comprovado do binário original; `derived_sha256` para o derivado.
- `source_ref`: referência canônica lógica `drive:{drive_id}:{file_id}`, validável no registro documental R06, sem informação pessoal no identificador.
- `operation`, `provider`, `status`, `evidence[source_file_id,locator,reviewer_verified]`.
- `fields_verified`, `client_verified`, `ocr_reviewed`, `external_llm_used`.
- `rule_id` e `proposed_filename` só para NOM; sempre `NNN_` no nome proposto.
- `event_key` determinístico por operação + versão/proveniência para deduplicar evento. Aprovação continua operação separada.

O contrato vigente de R06 exige para a proposta `process_id`, `title`, `summary`, `source_ref`, `document_approval_ref` e `document_sha256`; o registro de aprovação controlado pelo servidor deve conferir exatamente a versão do documento. Nunca forjar `document_approval_ref` a partir de um OCR ou simples status.

## 2. Integração das branches irmãs
**OCR atual** `feat/ocr-documental-isolado`: `ocr-engine/api.py` REST e `ocr-engine/mcp_server.py`; ponte `pilot/ocr_bridge.js` recebe PDF por HTTP interno, compara `sha256` e retorna candidato. Bug observado: ponte aceita apenas `mock`/`iloveapi`, mas engine aceita `tesseract`. Deve receber também saída de Stirling, com método, páginas, hash e indicação de revisão. Não misturar `OCR_PROVIDER=mock` com real.

**Nomenclatura** `feat/catalogacao-triagem-isolada`: `drive1/workflow.js` e `nomenclature/` fazem preview, rechecagem de regra, comprovação de vínculo do cliente e topologia. O `ocr_batch.js` atual gera revisão, não reintroduz automaticamente `DOCUMENT_VERIFIED_FIELDS` e não reexecuta as regras após revisão. Criar adaptador explícito, sem copiar pastas inteiras de laboratório para produção.

**R07** `feat/r07-office-knowledge-assimilation`: `memory_assimilation_preview` compara processo/fonte/duplicata/revisão; não grava nem revoga memórias.

**R06**: `memory_prepare_after_approval` apenas propõe; a gravação exige registro documental aprovado, portal autenticado, CSRF, clique humano e readback. O plugin ativo pode ter política diferente da branch ainda não integrada: consultar `memory_status` antes de alegar prontidão.

## 3. Interface pública futura e política de efeitos
Classificar ferramentas em READ, PREVIEW, DERIVED_FILE, EXTERNAL_WRITE, EXTERNAL_DISCLOSURE, APPROVAL_WORKFLOW. A camada do MCP expõe somente recursos que o usuário e a identidade atual puderem acessar; ferramentas de escrita exigem confirmação específica, objeto, esperado antes/depois, autorização, idempotency key, readback, rollback possível e recibo.

Acessos a arquivos com nome de cliente nunca equivalem a aprovação de identidade. Isolamento por entidade/documento, limites de volume, MIME e tamanho, antifraude, validação de PDF e PDFs maliciosos, sem invocação de shell arbitrário via LLM, sandbox de renderização e desativação de macros.

## 4. Proteções de LLM e dados
- Groq desabilitada por padrão; não enviar PDF, OCR bruto ou identificador pessoal antes de avaliação de dados, contrato, política de retenção e autorização da operação.
- Tratar conteúdo OCR, texto em PDF e comentários de documentos como **dados não confiáveis**, não como instruções para alterar permissões ou ignorar políticas. Contramedidas de prompt injection entre fonte e ferramenta.
- Extrair campos estruturados com evidência por página; nunca preencher uma assinatura ou autorização com nome não comprovado.
- Não registrar corpo completo de OCR em logs/eventos, URLs assinadas ou exceções. Logs com segregação, política de retenção e controles de acesso.
- Não misturar fatos de clientes; o acesso global de proprietário da R06 não autoriza transposição automática de fatos.

## 5. Retenção, corrupção, falhas e reconciliação
Cópias de trabalho têm TTL, hash e estado, com limpeza de arquivos e SQL tratados separadamente. Retentativas só com chave idempotente, especialmente DocuSeal e Drive. Webhooks: validar assinatura/origem e buscar situação real na API antes de afirmar "concluído". Guardar recibos de efeito só após readback. A `KnowledgeCapture` inicial usa **dicionário em memória somente para testes**; não alegar auditoria durável.

