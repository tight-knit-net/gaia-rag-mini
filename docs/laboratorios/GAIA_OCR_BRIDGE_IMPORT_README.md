# GAIA OCR Sérgio — contrato de ponte com Drive15

Branch de destino: `feat/ocr-documental-isolado`.
Origem da ponte: `will-iaguzeski/gaia-drive15-nomenclatura-lab`,
`main@70fb5ed09b7f883ded7497f1e84b8ffca1b8b1a1`.

Este pacote inclui **8 arquivos de integração**, todos sob
`docs/laboratorios/gaia-drive15-ocr-bridge/`. Ele serve para análise
Codex independente do motor OCR existente em `ocr-engine/`, que já tinha
sido importado por outra execução no commit `6fa5680`.
Aqueles 14 arquivos OCR foram conferidos byte a byte pelos hashes Git
com o worktree local `feature/ocr-iloveapi@c96b473` e não foram duplicados.

- `pilot/ocr_bridge.js`: contrato REST (na versão observada aceita mock/iloveapi,
  não tesseract).
- `pilot/ocr_batch.js`: preparação de revisão e boletim OCR.
- `pilot/run.js`: validações e relatório base somente leitura.
- `pilot/ocr_postgres_tmpfs.compose.yaml`: DB de teste efêmero,
  distinto do `ocr-engine/compose.yaml` original com pgdata persistente.
- `pilot/scripts/temp_pg.sh`: inicia e descarta o PostgreSQL temporário
  após relatório.
- `pilot/tests/`: testes sintéticos de ponta de integração.
- `pilot/INTEGRACAO_OCR_20261118.md`: relatório histórico, não status final.

Para funcionamento o bridge precisa dos módulos `drive1/` e
`nomenclature/` que estão no snapshot completo da branch
`feat/catalogacao-triagem-isolada`.

Este código sob `docs/` é **snapshot não implantado**. Não modificar runtime
R06, Qdrant, MCP existente, workflows, imagem Docker, Cloudflare, produção
ou documentos reais sem gate e aprovação separados. Provedores iLoveAPI
externos requerem consentimento e avaliação LGPD.
