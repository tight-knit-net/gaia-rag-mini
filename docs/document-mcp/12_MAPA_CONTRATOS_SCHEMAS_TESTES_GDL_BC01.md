# Mapa técnico de contratos, schemas e testes — GDL-BC01 → MCP v2

**Versão:** 0.1.0 (apêndice da matriz 11).  
**Instante aferido de emissão:** 2026-11-18T20:06:53-03:00 America/Sao_Paulo (relógio local do ChatGPT); momento do commit é separado.  
**Baseline:** GitLab 88873934 commit 2493f659866e16bd6499c9122e488d54d612a81d, D1 aprovada apenas como referência. MCP antes do registro: f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8, PR #7 Draft.  
**Objetivo:** declarar equivalências e *não equivalências* para impedir implementação ambígua. Sem código, cópia de schema ou teste executado nesta entrega.

## 1. Identidade dos schemas — NÃO mapear por nome parecido

| Critério | BC01/50 GDL-DS | MCP v2 |
|---|---|---|
| Propósito | Documento editável com árvores, geometria, layout, assets e autoridade por revisão | Evento operacional e recibo de processamento sem efeito externo |
| ID de versão | schema_version = 1.0.0-rc1 e $id em domínio .invalid (DRAFT) | schema = gaia.document-event.v2 e gaia.document-receipt.v2 |
| Campos requeridos | 13: schema_version, document_id, client_scope, revision_id, mode, page_profile, flow_tree, free_layers, assets, constraints, provenance, pages, authority | Evento tem 16 obrigatórios; recibo 19 |
| Chave de integridade | provenance.origin_sha256 e objectRef.sha256 | document_sha256, derived_sha256, event_key, evidence_sha256, summary_sha256 |
| Domínio de operação | editor, modelos, importação, exportação e render | OCR, pdf_transform, catalog, nomenclature, document_create, signature, workspace |
| Referência | objectRef bucket/key/version_id/sha256/size_bytes | source_ref texto e provider; origem Drive ainda sem revisionId validado |
| Estado | authority.interop_state native/review_required/verified | status do evento completed/review_required/blocked/failed |
| Forma | JSON Schema Draft 2020-12 com allOf/if-then | JSON Schema Draft 2020-12 para envelope e recibo; sem esquema integral de entrada Python |
| Verificação | 2 fixtures e 13 negativos offline no recheck D1 | 49 testes de contrato e 13 híbridos aprovados anteriormente, sintéticos |
| Integração | Não há runtime GDL aprovado | Não há servidor MCP remoto, nem conexão direta R07/R06 |

O evento não pode receber mode=overlay, flow_tree ou free_layers apenas para "compatibilidade". Um sistema futuro que edite documento define **DocumentRevision** e **ArtifactRef** tipados separados do **DocumentEvent**.

## 2. Mapeamento de campos e decisões de design

| Fonte GDL / origem | Destino ou lacuna MCP | Política de mapeamento |
|---|---|---|
| document_id | file_id / source_ref **não equivalente** | Criar identidade documental lógica independente do arquivo físico |
| revision_id | event_revision **não equivalente** | Introduzir document_revision_id apenas quando houver revisão |
| parent_revision_id | ausente | Manter linhagem de revisões de documentos no servidor autorizado, não no resumo do LLM |
| client_scope | client_id NNN e tenant OCR **não equivalentes** | Permissão por sujeito/recurso real, nunca por prefixo |
| provenance.origin_sha256 | sha256_original | Hash dos bytes reais e origem tipada |
| created_by_actor_id | ausente em evento v2 | Sujeito autenticado e logs sanitizados no backend, não alegação OCR |
| authority.source_kind | source_provider **não equivalente** | source_kind = odt/gdl_ds para edição, source_provider = local/drive/etc para proveniência |
| authority.source_ref | DocumentSource.source_ref **semântica distinta** | Adaptador distingue ObjectRef S3 de referência de arquivo SaaS |
| authority.interop_state | event.status **não equivalente** | Status de revisão/conversão separado do resultado OCR |
| authority.conversion_report_ref | ausente | Nova referência e resumo de perdas quando houver conversão |
| objectRef.version_id | source_version (string declarativa) | Revalidar revisionId/etag/versão da API na fronteira confiável |
| assets[].* | nenhum | Adiar até editar/converter arquivos com assets; proteção ACL |
| page_profile/pages/free_layers | nenhum | Não transportar; fora do OCR→NOM |
| template_revision_id | nenhum | Template versionado e aprovado é gate futuro |
| run_id/stage_run_id | operation_id no evento | Distinção explícita de requisição, job e tentativa |
| idempotency_keys(scope,key) | fingerprint event_key | Chave de requisição separada do fingerprint do evento revisável |
| document_approval_ref R06 | ausente da BC01 e da etapa híbrida | Documento aprovado no registro R06 antes de preparar memória |
| R07 memory candidate | não faz parte do GDL-DS | Só síntese curta, fonte, processo, revisão e comparação com aprovado |

**Caso específico Google Docs:** nativo não fornece "hash do arquivo original" como um PDF binário. Guardar ID/revisão/metadados Google e SHA do artefato exportado separadamente. Não prometer original nativo SHA por inferência de ETag.

## 3. Negativos da baseline BC01/52: destino e não-cobertura

O arquivo BC01/60 declara 13/13 resultados negativos esperados em teste **offline**. Isso não significa que estes mesmos 13 casos já passem no Document MCP v2. A correspondência é:

| Caso BC01 | Teste original | Destino proposto | Limite atual |
|---|---|---|---|
| NEG-01 | page_ref inexistente | DEFERIDO-STUDIO | A estrutura MCP não modela camadas |
| NEG-02 | layer ID duplicado | DEFERIDO-STUDIO | Testar quando Studio entrar |
| NEG-03 | assinatura fora da página | DEFERIDO-STUDIO | QA geométrico quando houver render |
| NEG-04 | objeto ID duplicado | DEFERIDO-STUDIO | Não confundir event_key com object_id |
| NEG-05 | assinatura abaixo da altura mínima | DEFERIDO-STUDIO | Perfil de assinatura futuro |
| NEG-06 | asset_id inexistente | ADAPTAR-P2 | Referência tipada e acesso autorizado quando houver asset |
| NEG-07 | ODT como origem sem source_ref | ADAPTAR-P2 | Exigir source_ref na revisão editável futura |
| NEG-08 | overlay sem PDF original | DEFERIDO-STUDIO | Overlay fora do MVP |
| NEG-09 | página inconsistente com A4 | DEFERIDO-STUDIO | QA de páginas futuro |
| NEG-10 | page_id duplicado | DEFERIDO-STUDIO | Schema GDL não equivalente ao event v2 |
| NEG-11 | nó ProseMirror duplicado | DEFERIDO-STUDIO | Sem UI/editor nesta fase |
| NEG-12 | document_id obrigatório ausente | ADAPTAR-P1 | Identidade lógica futura separada de file_id |
| NEG-13 | modo de edição desconhecido | DEFERIDO-STUDIO | Sem modos flow/free/overlay no MVP |

## 4. Testes negativos novos recomendados para a nossa fachada

| ID proposto | Entrada sintética | Resultado esperado |
|---|---|---|
| GDL-MCP-NEG-01 | Mesmo file_id mas document_id diferente | Não colidir identidades de documento |
| GDL-MCP-NEG-02 | Mesmo documento, event_revision diferente e revision_id invariável | Recibos distinguíveis, documento não reescrito |
| GDL-MCP-NEG-03 | client_id 009, client_scope autenticado de outro cliente | FORBIDDEN_CLIENT_SCOPE sem OCR/NOM/LLM |
| GDL-MCP-NEG-04 | tenant OCR = test, mas identidade não corresponde ao processo | Negado até mapeamento server-side |
| GDL-MCP-NEG-05 | SHA correto, source_version remota obsoleta | REVISION_CONFLICT e nenhum efeito |
| GDL-MCP-NEG-06 | Mesma Idempotency-Key, payload distinto | 409 IDEMPOTENCY_CONFLICT |
| GDL-MCP-NEG-07 | OCR interno marcado mock com campos aparentemente completos | Não gerar candidatura institucional |
| GDL-MCP-NEG-08 | Nome NOM válido sem regra vigente ou sem comprovação do cliente | PREVIEW pendente, nunca MOVE/RENAME |
| GDL-MCP-NEG-09 | Texto PDF contém instrução para compartilhar documento | Tratado como dado, não comando de ferramenta |
| GDL-MCP-NEG-10 | HMAC correto sem aprovação documental R06 | Não persistir Qdrant |
| GDL-MCP-NEG-11 | Groq/iLoveAPI desligadas, pedido de chamada externa | Provider disabled, sem upload |
| GDL-MCP-NEG-12 | OCR completo, registro R07 detecta duplicata/conflito | Propor revisão, sem supersessão automática |
| GDL-MCP-NEG-13 | Origem Google Docs nativo, hash de export tratado como original | Erro de proveniência, exigir duas identidades distintas |

Os IDs acima são **casos planejados**, não testes implementados.

## 5. Segurança: estado atual, evidência e bloqueador

| Risco | BC01 especifica | MCP atual | Gate |
|---|---|---|---|
| Isolamento de cliente | client_scope e autorização no backend | NNN e tenant OCR, sem ACL autenticada real | BLOQUEADO para dados de cliente |
| Autenticidade da fonte | versão/hash em ObjectRef | SHA informado e comparação local opcional | Backend precisa observar bytes |
| Revisão humana | ator/revisão e estado no registro | flags não confiáveis + HMAC verificador sem emissor | Emissor autenticado e revisão R06 pendentes |
| Evidência de OCR | qualidade, coordenadas, revisão | texto e digest, sem QA por página | OCR DEMO real pendente |
| LLM externa | proteção de dados e origem | Groq opcional inativa | Privacidade/licença/autorização pendentes |
| Conversão/assinatura | relatório de perdas, zonas protegidas | não existe editor/assinatura | Fora do MVP |
| Concorrência | If-Match, 409 | source_version sem verificação remota | Backend transacional pendente |
| Persistência/recuperação | Postgres/PgQueuer/SeaweedFS/backup coerente | recibos em RAM | Produção bloqueada |
| RAG | não trata memória persistente Qdrant | captura preview sem Qdrant write | R07/R06 precisam de aprovação separada |
| Governança | SHA, decisão, evidência, Linear e Wiki | PR #7 somente branch isolada | Sem escritas externas/merge |

**Metodologia do parecer:** rastreabilidade sobre código/documentos declarados, não ensaio operacional. Evidências oficiais provêm do GitLab e Linear, sem revalidar VM, SSH, webhooks ou APIs dos provedores. Google Drive não foi consultado nem alterado.

## 6. Decisão e próxima mudança permitida

**GO documental** para manter estas propostas na PR #7; **NO-GO técnico** para copiar GDL-DS, alterar contratos de produção, rodar infraestrutura, usar documentos reais, salvar memória ou publicar. Se o titular autorizar nova etapa, preparar uma alteração limitada a contratos de correlação e testes sintéticos na PR #7, preservando schema v2 e históricos.

**Rollback da presente documentação:** reverter somente os novos arquivos Markdown/índice da nossa branch. Nenhum estado operacional foi modificado.

Fontes: [GDL/50 schema](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/50_GDL_DOCUMENT_SCHEMA_BC01_DRAFT.json); [GDL/52 negativos](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/03_BASELINE_BC01/52_GDL_CASOS_NEGATIVOS_BC01.json); [GDL/60 evidência D1](https://gitlab.com/gaia_workspace1/gaia-doclab/-/blob/2493f659866e16bd6499c9122e488d54d612a81d/doclab-file-search/04_APROVACAO_D1/60_EVIDENCIAS_RECHECK_D1.json); [MCP v2 event schema](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/schemas/gaia.document-event.v2.schema.json); [MCP v2 receipt schema](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/schemas/gaia.document-receipt.v2.schema.json); [MCP testes](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/tests/test_document_mcp.py); [MCP híbrido](https://github.com/tight-knit-net/gaia-rag-mini/blob/f95164d6ae4f75e823111b4bcfee1fbde5a3bbc8/tests/test_hybrid_mcp.py).
