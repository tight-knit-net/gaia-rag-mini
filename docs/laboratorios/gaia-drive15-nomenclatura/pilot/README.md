# GAIA — piloto de documentos reais do Drive 1 (sem OCR)

Estado em 18/11/2026: ponte de leitura comprovada; teste com cliente real ainda pendente.

## Fluxo operacional

1. Operador informa cliente NNN e pasta exata do Drive 1-CLIENTES (drive ID 0ALBFaLnE8ZPHUk9PVA), idealmente dentro da Triagem, pasta 1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-.
2. ChatGPT usa CONECTOR NATIVO GOOGLE DRIVE para listagem, metadados, leitura do índice e manifesto ativo e download RAW. A transferência Drive→EC2 foi comprovada com um documento não sensível de 1.778 bytes, SHA-256 conferido.
3. EC2 privada recebe apenas cópias temporárias dentro de pilots/RUN_ID/raw, com nomes internos fileId.pdf ou fileId.docx, sem credenciais de Google.
4. Para cada item, o pilot/run.js verifica Drive ID, origem, bytes, tamanho, SHA-256, MIME, versão/fingerprint e eventual evidência documental com proveniência. Somente nomes/datas comprovados geram prévias. Metadados genéricos do Drive não são prova de data de emissão, titularidade ou assinatura.
5. O programa gera um catálogo, inventário, boletins de topologia 001 e 002, plano bloqueado e relatório BOLETIM.md. Nenhum arquivo no Drive é movido, renomeado ou excluído.
6. Após salvamento e conferência do relatório, pilot/purge.js elimina somente arquivos temporários da pasta raw sob a raiz segura. Limpeza lógica não garante sobregravação física de SSD/backups.
7. GitHub contém SOMENTE código, testes e documentação sintéticos. Não enviar PDFs ou relatórios com dados pessoais ao GitHub. Dropbox não é necessário e criaria uma cópia adicional.

## Preparação EC2 (exemplo ilustrativo; não é cliente real executado)

Diretório do código:
 /home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-nomenclatura-20261118

1) node pilot/purge.js setup piloto_009_exemplo_001 009

2) O conector nativo copia arquivos para pilots/piloto_009_exemplo_001/raw e produz manifest.json. O ID, parent, NNN, mime, hash e revisão/fingerprint devem corresponder à captura Google.

3) node pilot/run.js /CAMINHO/piloto_009_exemplo_001/manifest.json /CAMINHO/piloto_009_exemplo_001/raw /CAMINHO/piloto_009_exemplo_001/reports/resultado_001

4) Conferir o BOLETIM.md e garantir sua cópia no diretório reports principal antes de limpar (o script exige um MD no diretório reports).

5) node pilot/purge.js purge piloto_009_exemplo_001  # apenas prévia

6) node pilot/purge.js purge piloto_009_exemplo_001 --commit   # descarte local real

O descarte não prova upload externo do relatório: exigir verificação separada da persistência antes de chamar --commit.

## Contratos e limitações

pilot/snapshot.js transforma metadados do conector em uma marca OBS_ de revisão; OBS_ é fingerprint de ID/pai/nome/MIME/tamanho/modifiedTime, NÃO é versão ou ETag nativo do Google. A listagem do conector só pode ser marcada completa quando o provedor realmente esgotou o conjunto; uma página no limite de top_k é bloqueada. A real mudança de arquivo exigirá revalidação independente e executor homologado.

pilot/run.js recebe manifest JSON com schema gaia.drive1.pilot.v1, mode READ_ONLY, driveId, batchId, clientId, scopeIds, pages, copies, metadataById, clientProof e destinationSnapshot. Sem campos de identidade, tipo, assinatura e variáveis comprovados, o arquivo fica BLOQUEADO / PENDENTE: não renomear automaticamente só pelo título.

pilot/tests/pilot.test.js usa exclusivamente documentos sintéticos para simular prévias, validação SHA-256, bloqueio por evidência ausente, restrição do lote e limpeza local. Não houve leitura de PDFs reais de clientes neste ciclo.

Drive1 permanece read-only. O usuário escolhe a cliente e o escopo de documentos para um piloto individual.
