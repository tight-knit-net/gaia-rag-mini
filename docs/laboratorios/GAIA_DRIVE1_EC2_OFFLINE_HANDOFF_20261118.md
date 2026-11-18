# GAIA — Transporte por arquivos, Drive 1 → EC2 — piloto isolado v1

**Status**: componente de laboratório; não é conector automático, nem deploy, nem integração com `main`, Akamai, MCP de produção, Qdrant ou GAIA RAG Mini operacional. Em 18/11/2026, testes **sintéticos** locais passaram. Sem ensaio real de transporte Drive→EC2 feito por esta entrega.

## Pastas e autoridade

- **Ponto A** (recebimento oficial): Drive compartilhado `1-CLIENTES`, ID `0ALBFaLnE8ZPHUk9PVA`; `000_README/000_TRIAGEM_E_SANITIZAÇÃO_DE_ARQUIVOS`, ID `1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-`.
- Código histórico de leitura e nomenclatura: branch `feat/catalogacao-triagem-isolada`, snapshot `docs/laboratorios/gaia-drive15-nomenclatura/`.
- Motor OCR independente: `feat/ocr-documental-isolado`, `ocr-engine/`. O piloto **não precisa** iniciar sua REST/MCP; usa Tesseract e Poppler locais para OCR de pixels.
- **Ponto B** (recebimento de cópias no EC2): `/home/ubuntu/gaia-test-lab-homologacao/pilots/<RUN_ID>/raw/`. Entrada temporária após SCP: `/home/ubuntu/gaia-test-lab-homologacao/transport_inbox/<RUN_ID>/`. Os dois diretórios são **privados**, nunca publicados pelo servidor web.
- Saída local: `pilots/<RUN_ID>/reports/ocr_local_<LABEL>/*.txt` e `resultado.json`; prévia NOM/boletins produzidos por `pilot/run.js` quando houver manifesto completo. Destino permanente de relatórios exige entrega/validação posterior específica, sem MOVE automático.

## Limite incontornável, sem API

Este projeto **não baixa do Google Drive sozinho**. Um operador autorizado ou uma IA com ferramenta de leitura autorizada deve copiar os arquivos elegíveis da Triagem para ambiente seguro. Sem qualquer API, sincronização ou ferramenta de Drive, o transporte **começa com download autenticado pelo operador e SCP por SSH**; SSH transporta bytes, não expõe API do GAIA. Não há watch/sincronização da pasta. Mesmo recebendo `package.json`, o código só verifica consistência da evidência fornecida; ele não comprova que a captura é genuína ou está atualizada. Conferir IDs, pais, arquivo, manifesto e revisão novamente no provedor antes de ações de escrita.

**Jamais commitar** PDFs reais, conteúdo OCR bruto, manifestos individuais com dados pessoais, pacotes, nomes pessoais, credenciais, tokens, ZIPs de clientes ou logs de transferência no GitHub. GitHub só contém fonte/testes sintéticos. Arquivos reais ficam dentro do EC2 privado e do Drive autorizado.

## Operação (um lote explícito)

1. Registrar o lote e **selecionar IDs exatos** dos arquivos reais presentes na Triagem, com cliente comprovado no índice e manifesto. Coletar metadados atuais do provedor, caminho de pastas, MIME, nome e fingerprint, além de aprovação específica de leitura/transporte do lote. É necessário comprovar origem na Triagem (direta ou por subpastas inventariadas).
2. Baixar **cópias** por interface autenticada, sem alterar originais. Conferir SHA-256 local. Renomear **apenas as cópias de transporte** para `<GoogleFileID>.pdf` ou `<GoogleFileID>.docx`, sem mexer no nome do documento no Drive. Montar um `package.json` privado no schema `gaia.drive1.offline-handoff.v1`: `driveId`, `clientId`, `triageFolderId`, `runId`, `approval` (operação `READ_ONLY_OCR_NOM_PREVIEW`, `ref`, `fileIds` exatos), `files` (`fileId`, `sourceParentId`, `sourceName`, `mimeType`, `localName`, `sha256`, `bytes`) e `pilotManifest` completo em modo `READ_ONLY` (`schema=gaia.drive1.pilot.v1`, páginas completas da Triagem e pastas do escopo, `scopeIds`, `clientProof`, `metadataById`, `destinationSnapshot`). **Não inventar ou preencher `verified=true` por hipótese.**
3. Copiar por SCP, via chave e alias SSH operacionais aprovados, `package.json` e os arquivos para a área temporária privada do EC2. A autenticação SSH, pasta de entrega e logs devem ser configurados pela operação; este pacote não cria chaves nem conectividade.
4. No checkout **isolado** da branch `feat/catalogacao-triagem-isolada`:

   ```bash
   node docs/laboratorios/gaia-drive15-nomenclatura/pilot/offline_handoff.js receive \
      /home/ubuntu/gaia-test-lab-homologacao/transport_inbox/<RUN_ID>/package.json \
      /home/ubuntu/gaia-test-lab-homologacao/transport_inbox/<RUN_ID> \
      /home/ubuntu/gaia-test-lab-homologacao/pilots
   node docs/laboratorios/gaia-drive15-nomenclatura/pilot/offline_handoff.js verify \
      <RUN_ID> /home/ubuntu/gaia-test-lab-homologacao/pilots
   python3 docs/laboratorios/gaia-drive15-nomenclatura/pilot/offline_ocr.py \
      /home/ubuntu/gaia-test-lab-homologacao/pilots/<RUN_ID> --label rodada01
   ```

5. O leitor offline usa `pdfinfo`, `pdftotext`, `pdftoppm`, `tesseract -l por+eng`, ou texto nativo de DOCX. Por padrão aceita **até 10 páginas por PDF**, máximo absoluto 30 apenas se `--max-pages` for aumentado conscientemente pelo operador. Limite de arquivo: 15 MiB. Uma página com poucos caracteres é marcada `LOW_TEXT_REVIEW`, **não aprovada**.
6. Depois do OCR, validar conteúdo, identidade, tipo documental e regras NOM na fonte normativa. Para prévias com manifesto completo, `pilot/run.js` continua bloqueando ações reais; a ponte não dispara RENAME/MOVE. O gate de nomenclatura pré-MOVE é outra etapa, somente no futuro executor autorizado. Nomes e bytes originais do Drive são preservados.
7. Exportar somente relatórios **minimizados e aprovados** para pasta de testes no Drive, com verificação de leitura posterior. Descartar raw e derivados no EC2 somente após retenção e comprovação de relatório; `pilot/purge.js` exige relatório salvo, porém o SQL e snapshots externos precisam de limpeza própria. Não alegar apagamento físico seguro apenas com unlink.

## Testes e checkpoints

- `node --test docs/laboratorios/gaia-drive15-nomenclatura/pilot/test_offline_handoff.js` — 20 casos sintéticos verificados.
- `python3 -m unittest -v docs/laboratorios/gaia-drive15-nomenclatura/pilot/test_offline_ocr.py` — 7 casos incluindo OCR efetivo de PDF sintético em pixels; para esse fixture de teste o pacote `PyMuPDF` é opcional, OCR runtime usa Poppler/Tesseract.
- Não foram testados: primeira transferência autenticada de arquivo real, ACL efetiva no EC2, runner de classificação com documento real, readback de relatório no Drive, rollback, seleção real NOM e gate de MOVE em produção.
- Falhar fechado se houver divergência de cliente, origem, revisão, assinatura, SHA, duplicação, destino, captura incompleta ou ausência de autorização. Não levar adiante documento real em `mock`, `iloveapi` ou infraestrutura pública.

**Próximo gate**: copiar **um** PDF autorizado e de baixo risco da Triagem para o inbox privado do EC2 por transporte SSH, validar SHA-256 dos dois lados, executar OCR local e revisar relatório. Só depois ampliar para lote. A branch `main`, Akamai e MCP continuam sem alterações.
