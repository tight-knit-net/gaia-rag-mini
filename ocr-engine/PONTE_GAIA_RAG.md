# Ponte de integração isolada: GAIA OCR Engine → GAIA RAG Mini

Escopo: branch `feat/ocr-documental-isolado` do repositório `tight-knit-net/gaia-rag-mini`.
Origem versionada: `will-iaguzeski/gaia-drive15-nomenclatura-lab`, worktree EC2 `/home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-ocr-isolated`, commit local `c96b4731a1af783d52b5addcc8adcdfcdfd032b3`. Exportação do subdiretório `ocr-engine/`, sem segredos, base de dados ou arquivos reais.

## Limites desta transferência
Transferência de código e evidências sintéticas, **não** incorporação ao runtime R06, não publicação GHCR, não alteração de pipeline, não deploy, não merge. O Dockerfile na raiz do GAIA RAG e as regras do MCP/Qdrant não são modificados. Respeitar ADR-0002 e as revisões CODEOWNERS. Não ligar dois caminhos simultâneos de gravação de memória.

## Contrato previsto
O OCR opera como serviço independente: FastAPI (recepção/consulta/exportação) + PostgreSQL temporário + MCP streamable HTTP com `ocr_process`, `ocr_document` e `ocr_search`.
Provedores `mock`, `tesseract` (OCR real local) e `iloveapi` (adaptador sem homologação autenticada). A saída destina-se à catalogação e à nomenclatura através de contratos explícitos. Não transformar automaticamente documentos brutos em memórias persistidas: GAIA RAG exige proposta, revisão humana, aprovação e readback.

## Evidências
O teste sintético Tesseract em container Linode reconheceu 6/6 campos e passou 8/8 testes REST/SQL/exportação; 5/5 checagens MCP. Teste do adaptador iLoveAPI só com HTTP fictício. Evidências ficam em `evidence/` e scripts em `tests/`. Nenhum documento de cliente foi usado.

## Operação segura
O módulo se constrói separadamente:
```bash
cd ocr-engine
docker build -t gaia-ocr-sandbox .
```
A execução do `compose.yaml` demanda configuração local protegida e avaliação de rede/permissões; nunca acoplar esse Compose automaticamente ao deploy do RAG Mini. Não commitar `.env`, `PG_PASSWORD`, `GAIA_OCR_TOKEN` ou `ILOVEAPI_SECRET`.

## Gates
G0 inventário e compatibilidade; G1 repetição E2E sintético; G2 iLoveAPI sintética autenticada; G3 isolamento/autorização, retenção, criptografia e LGPD; G4 integração read-only com organizador/nomenclatura e RAG; G5 piloto de cliente após aprovação específica; G6 promoção e rollback. O estado desta branch não comprova nenhum gate de produção.
