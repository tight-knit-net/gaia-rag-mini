# Topologia Git e dependências de merge

**Consulta ao GitHub: 18/11/2026**. Repositório `tight-knit-net/gaia-rag-mini`, privado. `main` SHA `11c0eb593890dc7ff2a26b2d5eda8fb33828522b`: apenas README na árvore observada. A implantação mencionada no Akamai ainda deve ser reconciliada por digest e repositório de origem; não extrapolar do `main`.

```text
main (apenas README)
 └── docs/r05-gaia-rag-homologacao       PR #1
      └── feat/r05-mcp-acl-offline       PR #3
           └── feat/r06-lifecycle-skill-staging  PR #4 (draft)
                └── feat/r07-office-knowledge-assimilation PR #5 (draft)
                     └── feat/gaia-document-mcp-isolado   NOVO / último a integrar

 feat/ocr-documental-isolado       [branch irmã, histórico divergente]
 feat/catalogacao-triagem-isolada  [branch irmã, histórico divergente]
```

- A nova branch nasce diretamente do commit R07 `6aa55823082842bbe4799773a8acfc2e4eebdea1`, sem mudar `main`, R07, OCR ou NOM.
- Arquivos iniciais novos sob `gaia_document_mcp/`, `docs/document-mcp/`, `schemas/`, `config/`, workflow isolado e testes novos; nenhum patch em `app/server.py` ou `src/gaia_rag_r05`.
- GitHub Actions do RAG para GHCR e deploy Linode permanecem congelados (`if: false`/expressão false); workflow novo só testa contratos, sem construir imagens ou conectar dados.
- A PR futura desta branch deve inicialmente mirar R07, em modo **draft**. Após integração de R05/R06/R07 e módulos OCR/NOM à `main`, reconciliar esta branch via rebase/merge revisado, atualizar contratos e **só então** abrir gate final de integração. Não fazer merge direto da cadeia incompleta.
- OCR e catálogo não entram na nova branch como código copiado antes de análise de diff e resolução de contratos. A nova pasta é um adaptador, não fork paralelo das regras NOM.
- O controle de exclusividade da branch é processual. Verificar regras de proteção, CODEOWNERS, status CI e SHA da PR sempre que houver alteração. Não afirmar que a branch é tecnicamente imutável.

## Estrutura prevista
```text
gaia_document_mcp/     núcleo independente, registro de capacidades e gates
schemas/               contratos de eventos/proveniência
config/                parâmetros exemplificativos sem segredos
docs/document-mcp/     projeto executivo, auditoria, gates e decisões
tests/                 testes isolados e sintéticos
.github/workflows/     CI apenas teste, sem deploy
```

## Ordem de encaixe
1. R05/R06/R07 via PRs e suas aprovações.
2. OCR e NOM via integração individual e E2E sintético conjunto.
3. GAIA Document MCP (último), com adaptação à assinatura efetiva da R06/R07 e aos módulos anteriores.
4. Publicação em Akamai somente por nova mudança operacional com digest, rede, ACL, métricas e rollback aprovados.

