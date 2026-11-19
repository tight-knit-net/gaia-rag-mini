# GAIA Document MCP — contratos v2 (fase 0.1)

**Estado:** kernel de contratos e testes sintéticos; sem servidor MCP ou adaptadores conectados.

## Componentes
- `contracts.py`: evento e fonte documentais, origem Drive/Dropbox/local/gerado/Notion, cliente e processo opcionais na triagem, checagem antecipada de `source_ref`, identificação `operation_id`/`event_revision` e digest de evidências.
- `trust.py`: verifica atestação HMAC do serviço confiável futuro; **não emite** assinaturas ou aprovações. O emissor autenticado deve comprovar identidade, revisão e dados originais.
- `pipeline.py`: recibos transitórios em RAM sem texto OCR integral, candidatura editorial bloqueada sem atestação, vínculo de processo, hash e revisão. Não comunica com Qdrant.
- `schemas/gaia.document-event.v2.schema.json` e `schemas/gaia.document-receipt.v2.schema.json`: evento e recibo em contratos distintos. O arquivo `v1` permanece histórico.
- `settings.py`: gates conservadores; flags de ambiente não são autenticação nem autorização por arquivo.

## Teste sintético
`python -m unittest discover -s tests -p test_document_mcp.py -v`

## Não implementado
Servidor MCP, emissão autenticada de atestação, armazenamento transacional, OCR Stirling, DocuSeal, Groq, Google Workspace, OCR→NOM, consulta R07, aprovação R06. Nenhum documento de cliente pode ser usado nesta fase.

A assinatura HMAC por si só não comprova a qualidade do conteúdo ou autorização humana. A proposta R07 é um passo independente da aprovação documental R06 e do clique de memória.

Relatório: `docs/document-mcp/08_SANEAMENTO_CONTRATOS_V2.md`.
