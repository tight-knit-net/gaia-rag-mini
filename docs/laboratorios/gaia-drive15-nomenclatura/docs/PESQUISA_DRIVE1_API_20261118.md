# Pesquisa documental — arquitetura Drive 1 / Google Drive API

Data da consulta: 18/11/2026. Escopo: somente leitura no Drive 1-CLIENTES; fontes públicas do Google para orientar uma implementação futura.

## Fontes públicas oficiais

1. Google Drive REST API files.list: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list
   - Listar por parentId via q, paginar nextPageToken até o fim; evitar declarar inventário completo antes do fim.
   - Em shared drives, usar corpora=drive, driveId, includeItemsFromAllDrives e supportsAllDrives conforme o escopo.
2. Shared Drive support: https://developers.google.com/workspace/drive/api/guides/enable-shareddrives
   - Validar explicitamente o Drive ID; respostas com IDs de outro Drive não pertencem ao lote.
3. Recurso files (metadados): https://developers.google.com/workspace/drive/api/reference/rest/v3/files
   - Salvar fileId, parents, name, mimeType, version, modifiedTime e md5Checksum quando disponível.
   - version não é data de emissão; md5Checksum não é prova de titularidade.
4. Changes feed: https://developers.google.com/workspace/drive/api/guides/manage-changes
   - Suporte futuro ao checkpoint incremental via changes.getStartPageToken / changes.list; revalidar metadados antes de propor lote.
5. Pastas e pais: https://developers.google.com/workspace/drive/api/guides/folder
   - Mover um arquivo futuramente usa atualização de parents com addParents/removeParents, mas NENHUMA chamada desse tipo está implementada aqui.
6. files.update: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update
   - Mudanças de name e parents devem ser separadas do mecanismo de inventário e protegidas por pacote e readback. Não há transação atômica de vários arquivos garantida pela API.

## Consequências para o modelo

- No laboratório, cada página vem de um adaptador externo somente-leitura, e é rotulada como completa ou incompleta. O motor rejeita páginas ausentes, cruzamento de Drive, pastas fora do lote e versões indefinidas.
- Um boletim preserva inventário imutável, trilha de IDs e hash de boletim anterior; cada mudança gera NOVA versão, sem alterar originais.
- Nomenclatura só propõe nome. Não confundir identificação documental, prova de cliente, assinatura, nome do arquivo, nem pasta de destino.
- MOD define domínio entidade/processo, não altera o padrão NOM. Cliente e manifesto ativo devem estar confirmados no índice.
- A etapa registro/cadastro pode existir previamente mas continua WAIT até decisão externa.
- Um lote é planejamento; executor real ainda não existe. Se no futuro ocorrer resposta ambígua ou timeout em uma operação de Drive, reconciliar antes de repetir e gerar evento UNCERTAIN em vez de afirmar sucesso.
- No atual modo READ ONLY, o boletim é produzido em memória/local; escrever esse boletim na pasta de Topologia constitui mutação do Drive e não foi feito.

## Referências internas verificadas em 18/11/2026

Root README: https://drive.google.com/file/d/1c_5G0aVSI6BJXG6Nkc2FgEEkaRDAQCPk/view
Guia do fluxo: https://drive.google.com/file/d/169JeP_WdcUsQTB2CDt0P3Sjgq8qhToXG/view
Triagem: https://drive.google.com/drive/folders/1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-
Topologia: https://drive.google.com/drive/folders/1obPrd8IpvOvlFSgx5tGa1lQtt7x6SwEb
Catálogo NOM-60: https://drive.google.com/file/d/1GEsfv0j87tSZRrqf2YKgyBgXJkUazZeG/view
Diretrizes MOD: https://drive.google.com/file/d/1cmjvUdiwlFgn4dpaQCelnKVHkdUgRU7_/view

A referência federada catalogada no repositório é somente snapshot de estudo; Drive 15 continua autoridade de nomenclatura. Não armazenar conteúdo de documentos reais no GitHub.
