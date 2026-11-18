# GAIA Document MCP v2 — Gate P0/P1 de correlação documental sintética

**Versão:** 0.1.0 / somente proposta e testes sintéticos.
**Emissão/aferição:** 2026-11-18T20:19:07-03:00, timezone America/Sao_Paulo. Fonte verificável do relógio: ferramenta de horário local do ChatGPT. A hora oficial do commit é a do GitHub, não uma previsão de execução.
**Área de escrita:** exclusivamente tight-knit-net/gaia-rag-mini, branch feat/gaia-document-mcp-isolado, PR #7 Draft.
**Fontes imutáveis:** docs/document-mcp/11_MATRIZ_REAPROVEITAMENTO_GDL_BC01_MCP_V2.md e 12_MAPA_CONTRATOS_SCHEMAS_TESTES_GDL_BC01.md. GDL-BC01/D1 GitLab gaia_workspace1/gaia-doclab ref 2493f659866e16bd6499c9122e488d54d612a81d, base documental; GitLab e Linear NÃO acessados ou alterados neste gate.
**Baseline do código observada:** a242cf250edd33dc69c7b573e3541d19eb68ec9e. Não aplicar rebase nem merges na R07.

## 1. Escopo, riscos e critério de saída

Objetivo: testar a **distinção** entre document_id, document_revision_id, event_key e file_id; bloquear vínculos cruzados por cliente/processo, origem ou versão; simular uma chave de idempotência por escopo que retorne conflito quando o payload muda.

Este gate **não cria servidor MCP**, endpoint, autenticação, mecanismo transacional nem migração de documentos. O módulo novo deve ser importável independentemente, não modificar DocumentSource, DocumentEvent, hybrid.py, trust.py ou os schemas v2 que já existem.

**Risco central:** verificação de escopo e versão em fixtures Python pode parecer autorização de produção. O campo allowed_scope e ObservedRevision **são valores simulados pelo teste**, não são uma resposta autenticada do backend. Uma saída válida serve apenas como prévia e não autoriza MOVE, RENAME, upload, emissão de assinatura ou Qdrant. Recebimento de um HMAC de revisão também não substitui a aprovação documental R06 nem o clique específico para memória.

## 2. Arquitetura aditiva ensaiada

| Objeto novo | Responsabilidade | Ausência deliberada |
|---|---|---|
| LogicalDocument | ID lógico estável, client_scope, NNN e process_id | Não tem arquivo físico nem token OAuth |
| RevisionSnapshot | ID da revisão, pai, origem, version/hash, source_kind opcional e interop_state | Não modela editor ProseMirror, objectRef S3 ou aprovação |
| ObservedRevision | Simulação dos valores atuais do backend para detectar divergências | Não é consulta real a banco/API nem teste de If-Match |
| CorrelationPreview | Validação fail-closed de IDs, escopos, origem, versão, bytes/hash e vínculo de processo | Não persiste nem executa nenhuma ferramenta |
| SyntheticIdempotencyLedger | Simula mesma chave+mesmo payload; mesmo escopo+payload diferente falha | Usa RAM, não equivale a chave idempotente transacional |

**Semântica dos IDs:** document_id identifica o documento lógico; revision_id identifica conteúdo/linhagem; event_revision identifica evolução do evento v2; source_ref identifica origem do arquivo físico. Campos com nomes parecidos nunca são aliases.

**Associação com GDL-BC01:** GDL-RQ-009, -014, -020, -022, -025, -026 e -029. A referência GDL-DS 1.0.0-rc1 é **DRAFT** e não é transportada para o código. source_kind null representa original externo ainda não editável; odt e gdl_ds apenas descrevem o tipo de autoridade editável futuro, sem habilitar edição.

**Semântica da idempotência:** request_fingerprint incorpora identificadores de documento/revisão, escopo, fonte e ação planejada. Deliberadamente **não** equivale ao event_key, que inclui resultado, evidência, status e operação_id. Um retry idêntico pode ter outro operation_id, mantendo o mesmo request_fingerprint. A simulação é descartável e o synthetic_run_id não é ID de job real.

## 3. Testes de regressão P0/P1 — plano de aceitação

Arquivo adicional tests/test_correlation_gate.py, com casos negativos e positivos sintéticos, sem rede ou dados reais. Cobertura por dimensões:

| Dimensão | Critério |
|---|---|
| Identidade | documento lógico não se confunde com file_id ou event_revision; documentos diferentes geram request_fingerprints distintos |
| Escopo e vínculo | negar se expected_scope, scope da revisão, scope observado, NNN ou process_id divergem |
| Concorrência | revisão ou source_version diferente produz REVISION_CONFLICT, sem alterar qualquer arquivo |
| Integridade | SHA do evento, revisão e bytes verificados; alteração de PDF demo falha |
| Origem editável | source_kind desconhecido falha; importado não é automaticamente verified; revisão pai não pode ser a própria revisão |
| Idempotência | mesma chave/mesmo payload reproduz run sintético; mesmo escopo/chave e payload alterado falha; escopos diferentes isolados |
| Segurança | erro de scope forjado, flags de efeito falso/verdadeiro, ausência de divulgação do conteúdo e ausência de aprovação real |

**Teste executável do gate:** python -m unittest discover -s tests -p test_correlation_gate.py -v, pela CI própria. Os 49 testes de contrato e os 13 de ponte OCR/NOM permanecem registrados e devem continuar passando no SHA final.

A verificação herdada R05/R07 pode produzir falhas independentes e deve ser relatada separadamente, sem corrigir outras branches nesta tarefa.

## 4. Estados e critérios para fechar esta etapa

- G0 – PREPARAÇÃO: conferir head/PR e preservar contratos: verificável por compare antes/depois.
- G1 – TESTE SINTÉTICO: nova suíte passa **na CI do commit**, zero efeito remoto e sem fixture com dados de cliente.
- G2 – REGRESSÃO: 49 + 13 testes anteriores permanecem verdes e CI herdada identificada separadamente.
- G3 – PROVA DE ISOLAMENTO: diff contra baseline modifica apenas correlation.py, test_correlation_gate.py, workflow CI próprio e documentos MD/índice.
- G4 – HOMOLOGAÇÃO EXTERNA: **BLOQUEADA**, exige autenticação real, observação remota verificável, readback, storage transacional e autorização do titular.

**Não computar progresso N/total de gates além destes critérios.** O resultado só pode ser rotulado PASSOU quando houver links de Actions e readback no HEAD publicado. Nenhuma etapa posterior está autorizada automaticamente por CI verde.

## 5. Pendências e próximo gate de decisão

1. Autoridade real de client_scope: identidade/JWT + ACL de documento verificada pelo backend.
2. Observação real de source_version: If-Match/409 no provider autorizado e prova do último revision_id.
3. Idempotência durável: chaves por escopo em banco com serialização/transaction, concorrência, rollback e readback.
4. Integração OCR/NOM real: teste com dados DEMO e motor autorizado, sem serviço externo ou clientes.
5. R07/R06: comparação de registros aprovados + revisão documental + clique explícito de memória, sem escrita direta em Qdrant.
6. R07 avançou desde a criação da nossa branch: reconciliar em gate de integração posterior, não neste.

**Decisão recomendada:** GO apenas para registrar código/testes sintéticos e documentação na branch isolada. **NO-GO** para servidor real, uso de dados de clientes, iLoveAPI/Groq, GitLab/Linear/Drive, merge ou deploy.

**Rollback:** reverter unicamente o commit desse gate, preservando as alterações antigas do Document MCP e todas as branches externas.
