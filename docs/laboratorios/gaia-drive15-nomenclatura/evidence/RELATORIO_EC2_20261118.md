# Relatório — laboratório de nomenclatura Drive 15 (2026-11-18)

Origem: Google Apps Script `15 - Gaia Operacional e Clientes`, scriptId `1NsnZjFPLV7b2IXooU5bd--bIkliftHDOxOaUa06eYwKEte4kxR14hy0w`.
Destino: repositório privado `will-iaguzeski/gaia-drive15-nomenclatura-lab`.
EC2: alias `gaia-m7i`; cópia em `/home/ubuntu/gaia-test-lab-homologacao/gaia-drive15-nomenclatura-20261118`.
Container efêmero baseado em `gaia-t4-runtime:1.0.2-gate-sealed-191328ca`, rede desabilitada, diretório do projeto montado somente para leitura, sem acesso ao Drive.

## Evidências
- `source_integrity.log`: SHA-256 dos 31 arquivos originais validado na EC2.
- `legacy_syntax.log`: 29 de 29 arquivos JavaScript com sintaxe válida.
- `node_tests.tap.log`: 13 testes unitários aprovados; 0 falhas.
- `rule_matrix.json`: 56 regras geram nome em cenário sintético com seleção explícita e variáveis preenchidas.
- `recognition_matrix.json`: 19 regras automáticas examinadas; 17 reconhecidas isoladamente, 2 ambíguas.

## Diagnóstico
1. Motor original aceita data de calendário inexistente (31-02-2026); adaptador isolado rejeita.
2. Motor original não bloqueia separadores de caminhos em variáveis livres; adaptador isolado rejeita nomes inseguros.
3. 37 das 56 regras exigem confirmação manual ou fluxo de sugestão, não reconhecimento automático.
4. As regras NOM-041 (PDF assinado) e NOM-042 (DOCX editável) têm as mesmas âncoras; reconhecimento isolado devolve `AMBIGUIDADE_DE_REGRA`. Precisam de sinal confiável de extensão/assinatura para escolher entre elas.

## Escopo dos testes
Os campos de origem foram **sintéticos**. Passar na suíte não demonstra OCR, leitura de PDFs reais, extração de todos os dados nem integração com o Drive. A função isolada só **propõe um nome**: não escreve, move ou renomeia arquivo algum. Não foram alterados DNS, deploy do Apps Script ou dados de produção.
