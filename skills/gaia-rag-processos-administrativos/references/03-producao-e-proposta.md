# 03 — Produção de memória e encaminhamento à aprovação humana

## Gatilho obrigatório

A pessoa aprova previamente o DOCUMENTO ou PROCESSO. Só então a skill pode usar `memory_prepare_after_approval` para uma proposta, que **não grava**. A decisão de salvar a memória é nova e independente, feita no portal protegido com Cloudflare Access e clique humano. A aprovação de conversa genérica, sem peça ou processo aprovado, não basta para afirmar que o gatilho do serviço foi cumprido.

## R06: autorização documental verificável e aprovação técnica humana

A prévia R06 requer um registro servidor-controlado de documento aprovado (`source_ref`, `document_approval_ref`, `document_sha256`) vinculado a `namespace + tenant_id + process_id`. Uma alegação no prompt de que a peça foi aprovada não cria esse registro.

`memory_prepare_after_approval(namespace, tenant_id, process_id, title, summary, source_ref, document_approval_ref, document_sha256)` valida o documento e gera uma proposta idempotente, **sem escrita Qdrant**. `memory_proposal_preview` e `memory_pending_reviews` permitem visualizar somente propostas no escopo autorizado. A `review_url` vem do serviço, nunca deve ser fabricada. A aprovação técnica exige formulário humano e autenticação Access; falha, expiração ou ausência de clique não gravam. Apenas retorno de readback associado à mesma fonte e processo confirma `MEMORIA_CONFIRMADA`. O servidor pode desativar todo esse módulo com `GAIA_RAG_ENABLE_REVIEW=0`.

**Atenção:** o detalhamento abaixo sobre assinaturas opcionais `kind`/`source_type` é histórico da DigitalOcean; esses argumentos **não** estão presentes no contrato R06. O R06 não expõe uma ferramenta MCP para clicar/autorizar escrita.

## Seleção: o que merece memória

Guardar síntese enxuta de: ato confirmado, contexto necessário para continuidade, decisão interna efetivamente adotada, exigência formal, providência pendente, fundamento oficial verificado, lição decorrente de resultado real e referência do documento final. Não guardar o chat bruto, raciocínio exploratório, palpites, dados pessoais desnecessários, senhas, segredos, duplicatas ou texto integral dos autos.

## Ciclo

1. **Inventariar** o que mudou desde a última memória aprovada e quais fontes o comprovam.
2. **Classificar** categoria (caso, procedimento, fundamento, precedente, modelo, aprendizado, pendência), assunto, órgão, jurisdição, validade, grau de evidência e processo. Categorias editoriais não são novos campos de payload técnico.
3. **Deduplicar** com `memory_list_process`, `memory_search` filtrada pelo processo e, quando necessário, `memory_find_by_source`. Conferir o vínculo processual dos resultados por fonte; não incorporar retorno cujo `process_id` seja incompatível ou desconhecido. A MCP atual não permite update/revoke por comando desta skill.
4. **Redigir** uma unidade de memória por ato/decisão/estado relevante, com título curto, resumo verificável e limitações. Usar template em `../assets/templates/memoria.md`.
5. **Revisar**: nenhuma alegação promovida a fato; todos os números e datas em fontes; aprovação da peça documentada; `process_id` exato; fonte identificada; dados reduzidos.
6. **Preparar** via MCP real, preenchendo SOMENTE os argumentos suportados: `summary`, `title`, `process_id`, opcionalmente `namespace`, `kind`, `source_ref`, `source_type`. Nunca enviar um JSON de payload Qdrant como se a ferramenta o aceitasse.
7. **Entregar** o link de revisão informado pelo serviço; não produzir link fictício, simular botão ou gravar por outro meio.
8. **Verificar após a aprovação no portal**, se solicitado: consultar memória aprovada e auditoria. Se houver revisão ainda pendente, informar `AGUARDANDO_APROVACAO`.

## Semântica de status

- `CANDIDATA`: texto da skill ainda não enviado.
- `PROPOSTA_GERADA`: ferramenta retornou identificador/link; ainda NÃO persistida.
- `EM_REVISAO`: revisão humana pendente.
- `MEMORIA_CONFIRMADA`: confirmação de persistência por ferramenta autorizada após clique humano.
- `NAO_COMPROVADO`: falha/ausência de recibo; não afirmar gravação.

## Correção

Para fonte inexata ou norma desatualizada, produzir análise **ANTES/DEPOIS** e propor nova memória ligada ao processo e fonte real. **Não prometer** substituição/revogação técnica automática, porque a MCP presente não expõe métodos de update/revoke de pontos. Se a coexistência de versões representar risco, sinalizar revisão humana/operacional fora deste procedimento.

## Vida útil de proposta

`memory_policy` informa TTL de **14 dias** para propostas pendentes. Prazo de proposta não é prazo do processo administrativo.


## Gate de aprovação e revisão em duas etapas (R04)

A aprovação documental e a aprovação da memória são eventos **distintos**:

```
[Documento/processo concluído] -> [aprovação do conteúdo pelo titular]
       -> [síntese revisada e deduplicada]
       -> [memory_prepare_after_approval: apenas PROPOSTA]
       -> [link verdadeiro do portal protegido]
       -> [clique HUMANO no portal, não reproduzido pela IA]
       -> [consulta autorizada para confirmar persistência, se aplicável]
```

- Antes da aprovação do documento/processo, apenas **redigir um candidato local**, sem chamar a ferramenta de proposta. Se não está claro se houve aprovação, declarar `DOCUMENTO_NAO_APROVADO`.
- Não enviar múltiplas propostas por repetição automática/timeout: antes de retry, consultar `memory_pending_reviews` quando autorizado; idempotência de backend não está comprovada.
- Para cada candidata, identificar: fato/ato/decisão, `process_id`, fonte, autor da validação, data relevante, município/UF, diferença para memória existente, estado de comprovação e restrição. **Conservar esses itens em texto editorial**; a MCP não aceita novos campos do Qdrant.
- `source_ref` será referência existente, resolúvel e adequada. Não usar um ID pseudoidentificador inventado, URL expirada ou CPF embutido. Se inexistente, indicar lacuna e usar somente campos permitidos; não declarar proveniência verificada.
- Aprovação humana no portal é requisito técnico declarado pela MCP. A skill não clica, não acessa URL para simular aprovação nem converte confirmação verbal em aprovação técnica.
- `memory_proposal_preview` permite inspecionar proposta existente; `memory_discard_proposal` é ação distinta (muta proposta pendente). Nunca descartar sem ordem explícita.
- Uma memória já aprovada, mas incorreta, não pode ser simplesmente sobrescrita/revogada pela skill atual: redigir correção proposta + alertar que o estado anterior ainda poderá ser recuperado até intervenção técnica autorizada.

### Critérios de seleção específicos

| Candidato | Guardar? | Por quê |
|---|---|---|
| Exigência formal confirmada no despacho | Sim, como evento do processo | Continuidade, origem e prazo verificados |
| Estratégia de defesa aprovada pela equipe | Sim, como decisão interna | Não confundir com aceite pelo órgão |
| Lista genérica de artigos ainda não verificados | Não como norma consolidada | Exige fonte oficial e vigência |
| Modelo de requerimento final aprovado | Sim, referência estrutural + fonte | O documento original fica no repositório canônico |
| Conversa completa e raciocínio exploratório | Não | Excesso, duplicação, privacidade |
| Deferimento presumido por ausência de resposta | Não | Fato não demonstrado |

**Exemplo sintético:** peça de uso do passeio aprovada internamente; resumo informa “minuta interna aprovada; protocolo ainda não confirmado”, e nunca “pedido deferido”. Fonte: O01, O02, O04, O09, Lei 13.709/2018 arts. 6º e 7º.
