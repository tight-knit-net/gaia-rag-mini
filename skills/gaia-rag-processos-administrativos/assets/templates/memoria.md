# Modelo de proposta de memória (R04) — apenas editorial

**Condição:** usar somente depois que documento ou processo já tenha aprovação comprovada. Preencher e apresentar antes de `memory_prepare_after_approval`; não enviar todos estes campos como payload Qdrant.

- Modo: `PRODUCAO`; `process_id` **real**: `[ID CONFIRMADO]`; assunto e jurisdição: `[TEMA/ENTE/UF]`.
- Tipo: `[caso | fundamento | procedimento | modelo | precedente | aprendizado | pendencia]`.
- Evento/título: `[uma unidade atômica]`; data do evento: `[comprovada ou não informada]`.
- Fonte: `[source_ref real, com tipo e data]`; comprovantes adicionais: `[links ou IDs autorizados]`.
- Estado da evidência: `[alegada | documentada | confirmada]`; estado administrativo: `[minuta | protocolo | exigência | decisão]`.
- Síntese: `[o que aconteceu, por que importa, o que NÃO está comprovado]`.
- Diferença em relação à memória anterior: `[nova | complemento | correção proposta | duplicata sem salvar]`.
- Limitações e necessidade de revalidação: `[jurisdição, vigência, alcance, fonte]`.
- Aprovação da peça/processo: `[evidência verificável, data e autoria]`; aprovação da memória: **PENDENTE NO PORTAL**.

## Exemplo totalmente fictício, sem fonte oficial nem persistência

`process_id=DEMO-MESAS-017`; título: “Minuta de requerimento sobre passeio aprovada internamente”; resumo: “No processo fictício DEMO-MESAS-017, a minuta de autorização de mesas e cadeiras foi revisada e aprovada internamente. Não há prova de protocolo, exigência ou deferimento pela Administração. Referência documental DEMO/PEC-017, sintética.” **Não executar `memory_prepare_after_approval` nesse exemplo**; a aprovação citada é apenas fixture didática.

## Resultado esperado da ferramenta quando houver uso real

Exibir `proposal_id` e `review_url` **somente se retornados**. Caso contrário, reportar `PROPOSTA_NAO_CONFIRMADA`. Após clique humano, confirmar persistência por MCP, não por inferência.
