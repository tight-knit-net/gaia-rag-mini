# 02 — Recuperação de memória (somente leitura)

## Fluxo por finalidade

| Objetivo | Ferramenta atual | Regra |
|---|---|---|
| Abrir contexto de processo | `memory_process_start` | `process_id` real, início de processo |
| Listar todas as aprovadas do processo | `memory_list_process` | Paginar com `offset` quando houver |
| Responder pergunta semântica do processo | `memory_search` | Passar `process_id` para restringir; `limit` curto |
| Recuperar por documento | `memory_find_by_source` | Referência exata `source_ref` |
| Inspecionar registro específico | `memory_get` | Usar UUID real retornado, `namespace` correto |
| Ver cronologia | `memory_process_timeline` | Interpretar eventos, não inventar marcos |
| Procurar analogia | `memory_similar_cases` | Sem mistura de fatos/órgãos/prazos |
| Exportar síntese do processo | `memory_export_process` | Até 100 resumos aprovados por chamada |
| Entender cobertura | `memory_stats` | Conta propostas, não pontos Qdrant |

## Seleção

1. Identifique o processo e restrinja a consulta. Somente para buscas institucionais gerais use consulta sem `process_id`; jamais derive fatos particulares sem fonte.
2. Preferir método exato antes de analogia. Em decisões críticas, conferir referência com `memory_get` ou origem documental externa autorizada.
3. Registrar o que realmente retornou: conteúdo, status, ID, autor/fonte, data e revisão **se fornecidos**. Não inferir campos ausentes.
4. Para normas, confirmar texto legal, localidade, competência e vigência em fonte oficial atual. Uma memória antiga não atualiza a lei.
5. Antes de `memory_similar_cases`, verificar se a autorização de leitura interprocessos é demonstrável no ambiente. A ferramenta não recebe `client_id`/`tenant_id`: evitar busca ampla de casos particulares caso o escopo autorizado não esteja claramente estabelecido. Para resultados autorizados, comparar método e diferenças impeditivas; não divulgar dados pessoais de terceiros.
6. `memory_find_by_source` não recebe `process_id`, e `memory_get` recebe apenas UUID/namespace: conferir os identificadores do resultado antes de associar àquele processo. Caso falte identidade verificável, classificar como sem vinculação demonstrada, não como prova do processo.
6. Se nenhum resultado: `SEM_MEMORIA_LOCALIZADA_NO_ESCOPO_CONSULTADO`. Não alegar inexistência de processo, documento ou decisão.

## Prioridade de síntese

Retornar somente fatos relevantes ao objetivo, com `process_id` e referência da origem por afirmação material. Diferenciar:
- peça aprovada internamente;
- protocolo efetivamente realizado;
- exigência administrativa recebida;
- despacho/decisão do órgão;
- norma verificada e situação de vigência;
- hipótese, alegação ou pendência.

## Não fazer

Sem consulta, não afirmar memória encontrada; não expandir `process_id` automaticamente; não executar chamada direta ao Qdrant; não inventar score de embedding; não reclassificar status aprovado como prova.


## Plano de busca adaptativo R04

1. **Exata:** `memory_list_process(process_id, namespace)` e `memory_process_timeline(process_id)` quando o caso estiver identificado. Paginar enquanto houver `next_offset`; não assumir cobertura exaustiva só com primeira página. A linha do tempo de aprovação não é sinônimo de cronologia de decisões do órgão.
2. **Semântica restrita:** `memory_search(query, process_id, namespace, limit=5–8)`. Formular pergunta com objeto/ato, não dados pessoais; manter filtro por processo para casos concretos. Não aumentar a busca para sem filtro só porque não houve hit.
3. **Reconciliação de hit:** confrontar ID de processo, namespace, título, origem, período, estado e conteúdo. Em `memory_find_by_source`/`memory_get`, se o retorno não expuser `process_id` e não houver prova independente do vínculo, classificar `VINCULO_NAO_VERIFICADO` e não atribuir ao caso.
4. **Analogia controlada:** `memory_similar_cases` tem parâmetro de processo, mas **não** declara ACL por cliente. O usuário pedir “casos similares” não demonstra que possui acesso a outros clientes; use apenas quando o servidor demonstrar autorização adequada. Mesmo assim, extrair método anonimizado, jamais fato privado.
5. **Cobertura e falha:** `[]` → `SEM_MEMORIA_RECUPERADA_NO_ESCOPO`; timeout → `CONSULTA_INDISPONIVEL`; fontes contraditórias → `CONFLITO_DE_EVIDENCIA`; memória sem data/revisão → `VALIDACAO_PENDENTE`. Nenhum significa que o processo não existe ou está sem atividade.
6. **Norma:** não citar memória como se fosse atualização da lei. Para ato/norma municipal, consultar fonte oficial atual antes de empregar em parecer, requerimento ou recurso.

### Rubrica de relevância e risco (decisão editorial, não score do Qdrant)

- Identidade de processo e autorização: eliminatórias; sem elas o resultado não será aplicado.
- Fonte canônica encontrada: alta confiança **sobre o que o documento prova**, não sobre sua juridicidade geral.
- Revisão, data e estado: essenciais para afirmar atualidade; não inventar score, embedding, thresholds ou datas de indexação.
- Jurisdição e fatos essenciais coincidentes: úteis apenas para transferir **método**, com nova verificação; precedente local não é regra vinculante universal.

**Exemplo de saída:** “Na consulta ao processo fictício P-MC-017, nenhuma memória aprovada foi recuperada. Não é possível concluir que o protocolo inexista; conferir os autos originais.” [O01, O02, O04; Qdrant F01].
