# 06 — Processo administrativo: condução por fase

## Na abertura

Verificar identidade do processo, órgão, matéria, competência, partes, jurisdição e documentos. Usar `memory_process_start` no início do processo; recuperar registros aprovados, se existirem. Apresentar fatos, alegações e lacunas separadamente.

## Instrução

Mapear documentos existentes, exigências formais, provas, fundamentos oficiais, prazos e termo inicial **somente quando verificados**, atos executados e pendências com responsável quando documentado. Não inventar número de protocolo, despacho ou parecer.

## Produção e revisão de peça

Organizar identificação, fatos comprovados, fundamentos pertinentes, análise, anexos, pedidos e fecho adequados ao tipo de peça. Comprovar fonte/competência/vigência dos fundamentos. Revisar coerência entre pedido e provas. Uma peça aprovada não é deferimento oficial.

## Exigências e decisões

Extrair emissor, data, ato, conteúdo exigido, fundamento, ciência, prazo, consequências e providências com referência. Separar decisão final de exigência ou despacho de expediente. Identificar vias de recurso apenas com base na legislação/ato aplicável.

## Fechamento

Após aprovação da peça/processo, revisar se há fatos novos que mereçam memória. Não salvar automaticamente. Usar protocolo de `03-producao-e-proposta.md`; o clique de aprovação da memória continua externo e humano.

## Reutilização entre processos

Somente a **metodologia** ou entendimento bem delimitado é candidato a ser reaproveitado. Comparar jurisdição, data, objeto, base normativa, fatos e órgão antes de aplicar. Para similaridade, `memory_similar_cases` funciona como pista contextual, não jurisprudência ou documento oficial.

## Resultado mínimo

`PROCESSO`, `OBJETO`, `FASE`, `FATOS CONFIRMADOS`, `FONTE/REVISÃO`, `ATOS`, `EXIGÊNCIAS`, `PENDÊNCIAS`, `RISCOS`, `PRÓXIMO PASSO`, `LACUNAS`.


## Subfluxos especializados de processo administrativo (R04)

| Fase | Insumos mínimos | Produto verificável | Falha impeditiva |
|---|---|---|---|
| Triagem | objeto, cliente/ID, órgão, localidade | mapa de contexto/pendências | identidade ambígua |
| Pesquisa normativa | ente, competência, ato/tema, data | base legal com artigo, fonte e condição | norma não confirmada |
| Instrução documental | exigência, autos, provas e anexo | inventário/provas e lacunas | documento essencial ausente |
| Peça inicial/requerimento | fato, documentos, fundamento e pedido | minuta identificada, com anexos | pedido sem fato/prova |
| Atendimento à exigência | despacho original, ciência, prazo real | resposta e checklist de cumprimento | prazo/termo inicial inventado |
| Defesa/recurso | ato impugnado, data, cabimento, prova | peça de impugnação com pedidos coerentes | cabimento sem verificação |
| Decisão/encerramento | decisão oficial, dispositivo, termo | resumo de resultado e próximos atos | inferir deferimento a partir de minuta |

### Roteiro de redação (adaptar ao tipo de peça)

**Identificação e competência** → **síntese objetiva da pretensão** → **fatos documentados com referência** → **contexto normativo competente, atual e verificável** → **análise de adequação dos fatos ao dispositivo** → **pedidos numerados e proporcionais** → **rol de anexos** → **fecho**. Em revisão, confrontar pedido, evidência, competência e prazo.

### Casos sintéticos separados

- `DEMO-MESAS-017` (ocupação de passeio): verificar regulamento municipal do município fictício, fluxo de autorização, croqui quando exigido e acessibilidade se aplicável; **não afirmar que todo município exige croqui**.
- `DEMO-CONV-017` (minimercado): verificar objeto efetivo, horário, zoneamento, regulamentação municipal e condições do empreendimento; não transportar fundamentos de ocupação do passeio para horário de funcionamento.
- `DEMO-MESAS-018` (mesas e cadeiras de outro titular): tema semelhante ao primeiro, mas processo, documentos e eventos são distintos.

### Conclusões controladas

`PRONTO_PARA_MINUTA`: dados suficientes para **rascunho**, não para protocolo. `PRONTO_PARA_PROTOCOLO`: checklist e validação humana externos completos (skill não protocola). `EXIGE_VERIFICACAO_OFICIAL`: norma/prazo/ato não confirmado. `PROCESSO_SEM_MEMORIA`: busca vazia, não ausência de processo. Após aprovação da peça, seguir `03-producao-e-proposta.md` somente se houver intenção legítima de capturar memória.
