# GAIA — lote sintético de nomenclatura (18/11/2026)

**Resultado homologado somente em laboratório EC2, sem OCR e sem escrita no Drive 1.**

## O que foi criado

- [Pacote ZIP com os documentos, metadados e evidências](GAIA_LOTE_SINTETICO_027_E2E_20261118.zip).
- 17 documentos inteiramente fictícios: **15 PDFs e 2 DOCX**.
- 16 arquivos com metadados estruturados `.meta.json`; 1 sem metadados para testar bloqueio.
- PDFs contêm `/Subject` no dicionário nativo; DOCX contêm `dc:subject` no arquivo de propriedades. O código lê o `/Subject` dos PDFs, verifica a assinatura binária dos DOCX e usa o sidecar JSON para identificação e variáveis. **Não faz OCR, nem valida o conteúdo jurídico.**
- Os 17 arquivos originais são preservados. O executor de laboratório renomeou **7 cópias locais**, verificando SHA-256.
- Resultados: **7 PREVIEW / 10 BLOCKED intencionais**, sem divergência das expectativas.

## Tipos testados com metadados

DANFSe, comprovante CNPJ, certidão de IPTU, alteração JUCESC, auto CBMSC/e-SCI, DARE, requerimento PMF (PDF assinado e DOCX editável) e CNH como regra pendente de revisão. Os dois requerimentos são distinguidos pelo campo de assinatura e MIME; apenas se o campo estiver explícito.

Bloqueios simulados: colisão entre IDs distintos, NOM-033 com ressalva, emissão ausente, conteúdo de terceiro, data impossível, tipo desconhecido, DOCX incompatível, metadados ausentes e cliente divergente.

**Atributos inventados no JSON são evidência artificial, não prova de documento real.** Os IDs `synthetic_...` não correspondem a objetos no Drive. NNN `027` é um código fictício.

## Como reproduzir na EC2 (sem rede e sem Drive)

Gerar o pacote com Python padrão:

```bash
python3 synthetic/generate_fixtures.py /tmp/gaia-fixtures
```

Executar testes Node com as fixtures geradas:

```bash
GAIA_SYNTHETIC_FIXTURES=/tmp/gaia-fixtures node --test nomenclature/tests/*.test.js drive1/tests/*.test.js synthetic/tests/e2e.test.js
```

Executar fluxo completo, com cópias locais renomeadas:

```bash
node synthetic/run_e2e.js /tmp/gaia-fixtures /tmp/gaia-resultado
```

Os comandos acima são exemplos offline. Na EC2, a execução registrada ocorreu em container sem rede, com repositório e fixtures montados em somente leitura; somente a pasta de resultados foi gravável.

## Arquivos dentro do ZIP

- `lote_original/`: PDFs, DOCX, metadados `.meta.json`, `manifest.json` e hashes.
- `resultado_E2E/catalogo_documentos.json`: identificação, domínio, regras e estados por item.
- `resultado_E2E/inventario_topologico.json`: pais, IDs, MIME e versões.
- `resultado_E2E/boletim_001.json` e `boletim_002.json`: topologia inicial e incremental, SHA-256 encadeado.
- `resultado_E2E/arquivos_renomeados_LOCAL/`: 7 cópias com nome final.
- `resultado_E2E/plano_lote_BLOQUEADO.json`: exige cadastro, boletim persistido e resolução das pendências.
- `resultado_E2E/RELATORIO_FINAL.md`: tabela de resultados.
- `logs/`: suíte de 64 testes e execução.

## Limites

São oito tipos documentais tratados no mapeador sintético, **não as 60 regras homologadas**. O motor legado continua com 56 regras; o catálogo Drive 1 com 60 é referência não publicada para execução. O sistema não lê imagens ou texto PDF, não comprova identidade, propriedade, assinatura, dados cadastrais nem destino do cliente real.

Não houve push/deploy do Apps Script nem MOVE/RENAME/DELETE no Drive 1. A gravação dos boletins na pasta Topologia do Drive 1 ainda não foi executada. O plano de lote real permanece bloqueado.
