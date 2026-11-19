# Contratos para OCR, PDF e catalogação (propostos; não implementados)

## Envelope mínimo
- document_id, source_ref, process_id exato, tipo documental, nome lógico, origem e versão.
- origem do texto: nativo, OCR ou inspeção; páginas e método; conferência/limitações.
- transformação: original ou derivado, ID anterior, operação, ordem de páginas, hash quando verificado.
- classificação editorial: fato, alegação, hipótese, ato, decisão, modelo, procedimento, regra de nomenclatura.
- estado: triagem, catalogado, aprovado, protocolado, decisão comprovada; não inferir um estado pelo outro.
- intenção de memória: candidata ou não; status separado de aprovação da fonte e aprovação da memória.

## Sistemas futuros
OCR informa conteúdo e qualidade; catalogador informa tipologia e vínculo documental; NOM propõe nome/destino com ID e regra provada; editor de PDF informa split, merge, conversão, reordenação e origem. O GAIA RAG recebe somente uma síntese selecionada e uma fonte previamente aprovada. Não executa processamento, renomeação ou movimento de arquivos por causa da memória.

## Reutilização
Processos semelhantes servem como analogia metodológica. Não transportar fatos, números e dados pessoais de um cliente para outro. Verificar órgão, jurisdição, legislação atual e evidências antes de recomendar reutilização. Informação superveniente não apaga versão aprovada: preparar revisão para deliberação.

Este documento não declara ferramentas OCR/PDF instaladas nem integração completa.
