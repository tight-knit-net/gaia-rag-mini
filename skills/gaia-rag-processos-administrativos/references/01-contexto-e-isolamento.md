# 01 — Contexto, identidade e isolamento

## Entrada/triagem

Identifique a tarefa e classifique o pedido: `BUSCA`, `PRODUCAO`, `PROCESSO` ou `GOVERNANCA`. Para caso concreto, use o ID real do processo obtido do usuário, documento oficial ou ferramenta autorizada. Nunca converter nome de cliente, CPF, endereço, assunto ou número parcial em `process_id` por suposição.

Checklist de contexto: `process_id`, assunto, órgão, município/UF, objetivo, estado da peça, documentos-fonte identificados, recorte temporal, fonte oficial atual e nível de confirmação. Se faltar ID, permita pesquisa exploratória **sem confundir** os resultados com um processo identificado; não preparar salvamento de memória sem `process_id` correto.

## Isolamento

- Uma memória de **mesas e cadeiras** de um processo não deve agregar dados de outro processo de mesas e cadeiras.
- Uma memória de **minimercado/conveniência** deve permanecer independente, mesmo para o mesmo cliente.
- A unidade determinística visível da MCP é `process_id` + `namespace`. O assunto/tema é etiqueta editorial e texto útil à busca, **não filtro técnico garantido** pela MCP atual.
- No início de processo administrativo inequívoco, chamar `memory_process_start`. Ao continuar um processo existente, ler memórias daquele ID. Não usar casos semelhantes como autorização para ler dados privados de terceiros.

## Prioridade de evidências

1. Documento oficial e fonte primária de origem, com data e integridade avaliadas.
2. Ato administrativo ou peça protocolada, conforme o fato que prova.
3. Memória aprovada com vínculo à fonte, tratada como resumo indexado.
4. Relato/hipótese explicitamente sinalizado.

Não copiar IDs ou endereços pessoais para o texto indexável se uma referência menos identificadora atende à finalidade.

## Saída

Produzir um mapa conciso: processo, objeto, fatos com fontes, alegações, fase, normas a validar, pendências, riscos de mistura e próximo ato. Ausência de resultado significa cobertura insuficiente ou nenhuma memória encontrada na consulta executada.


## Procedimento expandido R04 — triagem sem contaminação

**Gate C1 — identidade:** identificar `process_id` a partir de fonte real (protocolo, dossiê interno ou saída autorizada). Rótulos como `GAIA-009` podem identificar cliente, mas **não** bastam para identificar qual dos múltiplos processos está em andamento. Na ausência de ID, registrar `PROCESSO_NAO_IDENTIFICADO`; realizar apenas pesquisa exploratória, sem enviar `process_id` fabricado.

**Gate C2 — origem dos dados:** separar `RECEBIDO_DO_USUARIO`, `DOCUMENTO_IDENTIFICADO`, `MEMORIA_APROVADA`, `FONTE_OFICIAL_VERIFICADA` e `INFERENCIA`. Um relato do usuário pode orientar a busca, mas não vira fato documental por aparecer na conversa.

**Gate C3 — recorte:** órgão, município/UF, data do ato, período de vigência, estado processual (rascunho/protocolo/exigência/decisão) e finalidade do trabalho. Um processo de mesas e cadeiras e outro de funcionamento de minimercado são objetos diferentes mesmo que o titular seja idêntico.

**Gate C4 — autorização:** não inferir que a autenticação global no plugin autoriza todo cliente. Se a ferramenta retornar registros de outro processo ao iniciar ou buscar caso semelhante, não os citar, não transportar dados e não preparar proposta baseada neles. Solicitar delimitação de escopo por canal autorizado; não há bloqueio de segurança garantido por este texto.

**Gate C5 — saída de triagem:** `CONTEXTO_SUFICIENTE`, `CONTEXTO_PARCIAL`, `SEM_ID_CONFIRMADO`, `SEM_FONTE`, `ACESSO_NAO_COMPROVADO`. Especificar o que falta, sem declarar inexistência de processo por busca vazia.

**Exemplo inteiramente sintético:** o usuário diz “cliente fictício C-017, processo de ocupação do passeio”. Há duas referências `P-MC-017` e `P-ALV-017`. Antes de consultar, verificar qual se relaciona ao passeio; não usar o número de cliente como processo, nem mesclar resultados. [Fonte conceitual: O01, O02, R03.1].
