# GAIA Drive 1 — fluxo de triagem, topologia e lotes

Data: 18/11/2026. Estado: LAB ISOLADO; Drive 1 somente leitura; nenhum executor habilitado.

Este módulo desenvolve o fluxo sem modificar o Apps Script original, sem chave Google e sem utilizar arquivos reais de clientes nos testes.

## Âncoras verificadas em leitura

Shared Drive 1-CLIENTES: 0ALBFaLnE8ZPHUk9PVA (único drive aceito).
000_README: 1qcZTumNI0IkICDyEvGprSAMeH398x4Ig
Triagem: 1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-
Topologia temporária: 1obPrd8IpvOvlFSgx5tGa1lQtt7x6SwEb
OCR temporário: 14lBYiStqthQsEWtNzbCpZSeRXGZxR8K_
Quarentena: 1l0VI0NW8CDRkPbTtmC0CczyzDpXGp6bo
Governança: 1AckKZsRCyZflTYVmZ_HvSl5-VFZQHuHX
Rastreabilidade permanente: 1HUYGCWM3xhBIuv1vX_rNaZwjC0H3V57y

As três pastas técnicas internas à Triagem são fixas, não são lotes entrantes.

## Fluxo obrigatório

1. OPERADOR deposita o lote na Triagem. Identificar o escopo exato de pastas/arquivos.
2. INVENTÁRIO: varrer recursivamente páginas de metadados só do lote, por IDs, pais, versão, MIME e nomes. Incompletude bloqueia o lote; modifiedTime não é data de emissão.
3. TOPOLOGIA: criar boletim inicial cobrindo todos os itens e suas cadeias de pais (fileId e parentId). Na revisão seguinte, novo boletim com hash anterior, nunca sobrescrevendo o anterior.
4. SANITIZAÇÃO/CLASSIFICAÇÃO: leitura e OCR por outro componente autorizado, separar documentos de terceiros, identificar cliente, pessoa, empresa, imóvel, processo e vínculo com evidências.
5. NOMENCLATURA: regras NOM, variáveis comprovadas, prefixo NNN oficial, calendário válido, extensão correta e ausência de colisão. Nomes são apenas propostas. Inconclusivos ficam pendentes e os demais prosseguem.
6. TOPOLOGIA MODULAR: regras MOD-001..020 para entidades e destinos, não inferir titular só por endereço. Raiz rasa por entidade; processos podem ter subpastas por órgão/assunto/protocolo.
7. CADASTRO: conferir índice oficial e manifesto ativo. Mesmo existindo cadastro, AGUARDAR liberação específica antes de mover.
8. PACOTE EM LOTE: exigir todos os file IDs e revisões estáveis, boletim registrado, destino inspecionado, ausência de colisões e autorização específica. O código gera plano, não MOVE.
9. CONCILIAÇÃO FUTURA: readback após executor homologado e boletim append-only na Rastreabilidade permanente, sem apagar históricos.

## Contratos da fonte

Root README: 1c_5G0aVSI6BJXG6Nkc2FgEEkaRDAQCPk
Guia rápido: 169JeP_WdcUsQTB2CDt0P3Sjgq8qhToXG
Política declarativa: 1Uh0pm8zmGnbzChLXZFxaRn_IAWxIwITA
Regras MOD: 1cmjvUdiwlFgn4dpaQCelnKVHkdUgRU7_
Índice NOM 60 regras: 1GEsfv0j87tSZRrqf2YKgyBgXJkUazZeG
Contrato NOM: 16H8LODVHVLXM9flf1bhO7mWGVUZXbE7A

O catálogo federado com 60 regras é DERIVADO e não uma release. O script antigo tinha 56 regras. As quatro adicionais, NOM-057 a NOM-060, não foram automaticamente ativadas. Regras com overlays/ressalvas exigem revalidação da fonte.

## API sem rede e sem alteração

inventory.js: inventoryFromReadOnlyPages obtém inventário completo a partir de páginas já lidas por conector autorizado.
workflow.js: proposeItem, markCollisions e prepareBatch; status PREVIEW, BLOCKED e READY_FOR_SPECIFIC_OPERATOR_APPROVAL, mas nunca aplicação.
bulletin.js: makeInitialBulletin, nextBulletin e bulletinAsJson; boletins sequenciais SHA256, com efeito NOT_EXECUTED.
catalog60.js: validateCatalog, gateRule, consulta de regras documentais sem homologar runtime.

Testar com Node: node --test nomenclature/tests/*.test.js drive1/tests/*.test.js

## Limites e persistência

Drive 1 permanece READ ONLY neste ciclo. O destino futuro dos boletins é a pasta Topologia; os testes atuais geram arquivos somente na EC2/GitHub, não dentro do Drive 1. A gravação real de boletins e a movimentação em lote exigem autorização específica, executor e reconciliação. Não há OCR nem integração automática com o Organizador no código atual.

Não carregar documentos reais, nomes de clientes, credenciais, arquivos pessoais ou manifestos operacionais neste repositório.
