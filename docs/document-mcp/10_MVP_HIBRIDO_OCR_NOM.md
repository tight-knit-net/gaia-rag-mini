# GAIA Document MCP — redução estratégica e MVP híbrido OCR/NOM

**Versão:** 0.3 — plano e adaptador inicial.  
**Data/hora aferida:** 2026-11-18T19:52:15-03:00, America/Sao_Paulo, relógio local do ChatGPT.  
**Escopo de escrita:** somente `feat/gaia-document-mcp-isolado`; PR #7 draft.  
**Fontes técnicas:** GitHub das branches OCR e NOM apenas leitura; documentação oficial da iLoveAPI e da Groq; memória legada apenas contexto histórico, não estado operacional.

## 1. Decisão: trocar a arquitetura grande por uma fachada mínima

**Objetivo da fase MVP:** atender `ChatGPT → GAIA Document MCP → OCR existente → nomenclatura existente → recibo de prévia`, sem recriar o motor e sem duplicar o catálogo NOM. A integração RAG é um evento futuro condicionado à R07/R06 e aprovação documental independente.

O Stirling-PDF, DocuSeal, Dropbox, Notion, MongoDB e edição avançada de Docs/Sheets saem do caminho crítico da primeira versão. Mantêm-se como backlog opcional. iLoveAPI serve inicialmente como capacidade de processamento PDF externo sob autorização, sem substituir o Tesseract local que já tem E2E sintético. Groq (com Q) é classificador/extrator opcional, jamais autoridade de nome ou aprovação. Não utilizar o termo "Frankenstein" para justificar cópias cegas, duplicação de dados ou contorno de controles.

## 2. Evidência existente (somente leitura)

| Fonte | Contrato/estado verificado | Reaproveitamento |
|---|---|---|
| `feat/ocr-documental-isolado` | `ocr-engine/api.py`: GET `/v1/documents/{id}?tenant=...` com Bearer; PostgreSQL, campo `sha256`, `status=processed`, `provider`, `text`; MCP `ocr_process`, `ocr_document`, `ocr_search` | **Usar REST privado** e manter MCP legado em loopback, não expor diretamente |
| Ponte OCR piloto | `ocr_bridge.js` só reconhece `mock`/`iloveapi`, embora OCR engine tenha `tesseract` | Nova fachada aceita `tesseract` e bloqueia `mock` como prova |
| `feat/catalogacao-triagem-isolada` | `nomenclature/index.js` expõe `suggestDocumentName` puro; sem efeito Drive; exige regra e variáveis | Chamá-lo via Node no próprio ambiente, sem copiar/reescrever regras; manter versão/snapshot controlados |
| NOM `drive1/workflow.js` | Exige vínculos, prova de cliente, topologia e autorização; saída somente preview | Manter gates de MOVE/RENAME fora deste MCP MVP |
| GAIA R07/R06 | Prévia institucional R07, fluxo humano R06; sem gravação direta legítima | Reutilizar depois; NÃO salvar OCR bruto, simulações ou campos autoextraídos como memória |

O E2E anterior de OCR e NOM é histórico dos laboratórios. O código desta branch **não afirma** esses serviços ativos nem homologação de ponta a ponta com eles.

## 3. Arquivo de integração desta etapa

`gaia_document_mcp/hybrid.py` define:
- `InternalOcrReader`: **somente GET** em `http://127.0.0.1:<porta>/` com Bearer por backend; valida ID, tenant, status e limite de resposta. Não liga portas externas, não cria documentos e não executa OCR novo.
- `LegacyOcrRecord`: valida a resposta REST, distinguindo `mock`, `tesseract` e `iloveapi`; `tenant=test` do laboratório é aceito.
- `ExistingNomPreview`: recebe caminho `index.js` da instalação controlada do NOM; executa Node sem shell, JSON via stdin e `timeout=5`. Só aceita resultado `PREVIEW_ONLY` com `write_performed=false`. O código NOM **não foi copiado** de outra branch.
- `HybridOcrNom`: exige PDF original em bytes, SHA verificado, tenant correspondente, processo vinculado e OCR não-mock antes de gerar prévia NOM. Resultado não faz MOVE/RENAME/DELETE, não compartilha arquivo, não prepara assinatura e não grava Qdrant.

**Limitação relevante:** a prévia NOM só pode ser produzida quando um operador traz `rule_id` e variáveis revisadas. Esses valores ainda não estão autenticados pelo backend; portanto a prévia permanece marcada `REQUIRES_APPROVAL`, não é execução nem memória aprovada.

## 4. Configuração e passo técnico para operação isolada (ainda não executado)

No ambiente autorizado, o integrador deverá entregar o caminho do `nomenclature/index.js` do snapshot NOM aprovado; instalar Node local; configurar somente no secret manager o Bearer do OCR REST privado; fixar host loopback; verificar que os bytes do PDF correspondem ao SHA informado; atribuir `operation_id` único. Não reutilizar chave de produção no teste. **Para conectar à instância OCR de outra branch/servidor, pedir autorização adicional antes de qualquer acesso operacional.**

É necessário ainda servidor MCP de autenticação própria para conectar o ChatGPT. A fachada nesta etapa é uma biblioteca Python importável e testável, não um servidor MCP remoto publicado.

## 5. iLoveAPI e Groq — mínimo viável e política de custo

### iLovePDF / iLoveAPI
Documentação oficial: https://www.iloveapi.com/docs/api-reference e https://www.iloveapi.com/docs/pdf-guides/common . O ciclo REST é `start → upload → process → download`. iLoveAPI anuncia 2.500 créditos mensais grátis, sujeitos ao plano/uso: https://www.iloveapi.com/pricing . A ferramenta não está configurada nem invocada. Consumir créditos e transmitir bytes a terceiro só após política LGPD/fornecedor, orçamento e autorização.

O serviço OCR existente **já tem provider iloveapi no código**, mas não tem homologação autenticada de provedor externo. Para PDF genérico (merge/split/convert/edit), um adaptador adicional será necessário. Ele não é condição para o primeiro teste OCR→NOM.

### Groq (com Q)
Documentação oficial: https://console.groq.com/docs/structured-outputs e https://console.groq.com/docs/tool-use/local-tool-calling . Pode sugerir classificação, campos e evidências estruturadas. Deve produzir JSON candidato que **não pode preencher automaticamente variáveis `verified_fields`** nem alterar regras NOM. A transmissão de conteúdo de cliente permanece desligada por padrão; modelo, custo e retenção devem ser aprovados.

## 6. Gates de aceitação

- **H0 — adaptador/contratos:** CI unitária sintética no commit final (incluindo testes OCR, tenant, mock, SHA, NOM e ausência de writes). Só isso pode ser considerado homologação de código.
- **H1 — NOM real read-only:** executar a biblioteca contra `index.js` real homologado, com cópia de regra versionada, fixture sintética e sem Drive; comparar nome e versão. **PENDENTE**.
- **H2 — OCR real read-only:** usar arquivo sintético e instância OCR autorizada em loopback; verificar id, tenant, status, hash e 6 campos; sem clientes. **PENDENTE**.
- **H3 — pipeline combinado:** E2E OCR Tesseract→NOM real com campos revisados, falhas e readback. **PENDENTE**.
- **H4 — iLoveAPI e Groq:** aprovação de custos, retenção/segurança e credenciais; teste sintético externo antes de clientes. **PENDENTE**.
- **H5 — MCP autenticado/RAG:** servidor autenticado, OCR→NOM→R07 preview, R06 portal humano, readback e rollback. **PENDENTE**.
- **H6 — publicação/merge:** dependente de autorização explícita do titular e reconciliação da R07 que avançou. **BLOQUEADO**.

## 7. Riscos e próxima decisão

**Preferência:** priorizar OCR local + NOM e não instalar Stirling/DocuSeal neste MVP. Isso reduz dependências e custo. Não assumir que o "80% funcionando" informado pelo titular equivale a auditoria de 80% de requisitos: faltam validações reais do acoplamento.

A PR #7 mantém base R07 histórica. A R07 avançou e precisa de reconciliação semântica **somente após autorização**, antes de merge; não trazer mudanças de outras branches por `cherry-pick` indiscriminado.

**Estado da entrega deste documento:** projeto MVP e código de fachada implementados na nossa branch; integração operacional e serviços externos NÃO executados.