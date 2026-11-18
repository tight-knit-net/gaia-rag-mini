# GAIA Drive 15 — importação isolada para análise Codex

**Status:** fotografia técnica para auditoria, não serviço integrado ao RAG.
**Origem privada:** `will-iaguzeski/gaia-drive15-nomenclatura-lab`.
**Commit fonte:** `70fb5ed09b7f883ded7497f1e84b8ffca1b8b1a1`.
**Data da captura:** 18/11/2026.
**Destino da branch:** `feat/catalogacao-triagem-isolada`.
**Total transferido:** 88/88 arquivos rastreados de `main` (incluindo ZIP sintético binário e HTML legado completo).
**Pasta importada:** `docs/laboratorios/gaia-drive15-nomenclatura/`.

## Escopo e estrutura

- `drive1/`: inventário, validação do escopo por IDs, boletins SHA256, fluxo de regras, catálogo federado NOM-001..060.
- `nomenclature/`: módulo puro JS de prévia de nomenclatura, 56 regras do snapshot base.
- `pilot/`: validação por hash, ponte OCR REST, boletins, Postgres tmpfs de teste e rotinas de descarte.
- `synthetic/`: 17 arquivos sintéticos e evidências de 7 prévias / 10 bloqueios; NNN 027 fictício.
- `evidence/`: logs dos 64/74/86 testes, relatórios e verificações sintéticas.
- `legacy/`: snapshot **histórico e não executável em produção** do Apps Script original.
- `docs/`, `README.md`, `SHA256SUMS`, `.gitignore`: documentação e manifestos históricos do repositório fonte.

## Regras de isolamento

Os arquivos foram armazenados dentro de `docs/`, caminho excluído pelo
`.dockerignore` do GAIA RAG Mini. **Não foram modificados** `main`,
`Dockerfile`, `.github/workflows`, `CODEOWNERS`, `app/`, `src/`
ou as regras de memória Qdrant.

Não foram enviados documentos reais, tokens, segredos ou arquivos de configuração
não rastreados. **Não executar** as rotinas originais Apps Script que alterem
documentos do Drive 1; manter somente leitura até gate explícito.

## Integração futura

O OCR independente está na branch `feat/ocr-documental-isolado` deste
repositório. No último teste, `pilot/ocr_bridge.js` compreendia
`mock`/`iloveapi`, enquanto canary de OCR local reportava `tesseract`;
reconciliar o contrato antes da união de componentes.

O GAIA RAG memoriza **resumos aprovados por revisão humana**, não PDFs,
metadados privados completos ou OCR bruto automaticamente.
Processo de memória aprovado: `GAIA-DRIVE1-OCR-NOM-PILOTO-20261118`.
Point Qdrant: `55c40019-814b-5cf7-97d2-f74f86cce929`.

**Instrução para Codex:** auditar código, proveniência, branch, testes e gates;
sugerir integração com RAG, mas não executar deploy, merge nem movimento de
documento de cliente sem autorização adicional.
