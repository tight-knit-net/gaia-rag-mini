# Política editorial de memória GAIA RAG — R04
**Natureza:** proposta interna para adoção; sem alteração do backend, sem declaração de conformidade jurídica ou ISO.

## I. Escopo e responsáveis
- Titular institucional define finalidade, processo, escopo e validação documental; o usuário aprova peça/processo e decide separadamente a aprovação técnica da memória no portal.
- A IA sugere e revisa; não autentica, não exerce autoridade, não prova existência do caso.
- O conector GAIA RAG aplica suas políticas de acesso e aprovação; a skill é apenas o roteiro e **não substitui** ACL, registro de consentimento quando aplicável, base legal, guarda e controles técnicos.

## II. Entrada, tipo e condições mínimas
1. Identificador real do processo e referência da fonte; sem `process_id` verificável, não enviar proposta ao serviço.
2. Informação útil, proporcional à finalidade de continuidade ou melhoria institucional; eliminar duplicatas, segredo, excessos e transcrição integral do chat.
3. Classificação de natureza, origem, estado da evidência, jurisdição, data e validade.
4. Aprovação documental distinta de aprovação da memória; confirmar a primeira antes de preparar proposta, e exigir a segunda por clique humano no portal.
5. Sem confirmação de backend, informar `PROPOSTA`/`PENDENTE`/`ESTADO_DESCONHECIDO`, nunca `PERSISTIDA`.

## III. Reutilização
- Identificar separadamente `REGISTRO_DE_CASO`, `REFERENCIA_NORMATIVA`, `PROCEDIMENTO`, `MODELO`, `PRECEDENTE`, `LICAO_APRENDIDA` e `PENDENCIA`.
- Conhecimento de caso só pode virar método institucional após desidentificação, contexto de aplicação, evidência, verificação de norma e validação humana.
- Mesmo tema não implica mesmo processo; mesma estratégia não implica deferimento.
- Referência a norma deve indicar esfera e fonte oficial. Antes de reutilização decisiva, revalidar vigência, alteração, competência e regime especial.

## IV. Controle de versões, correção e descarte
- Documento-fonte não é substituído por síntese no Qdrant.
- Eventual correção de memória deverá preservar referência à revisão anterior e mostrar divergência antes/depois. A MCP atual não permite revogação de ponto por esta skill: registrar pendência técnica, sem mascarar correção como efetivada.
- Retenção, classificação arquivística e eliminação de documentos **não** são definidas por esta skill. Cabe à organização e regime documental aplicável determinar a política.
- Propostas pendentes seguem TTL informado pela MCP no momento de uso, não um prazo legislativo.

## V. Privacidade e segurança
- Observância de finalidade, adequação, necessidade, qualidade e segurança (Lei 13.709/2018, art. 6º). A base legal do tratamento deve ser avaliada por finalidade/operador/controlador; consentimento não é sempre a única hipótese.
- Proibir divulgação interprocessual não autorizada, segredos, chaves, credenciais, anexos pessoais excessivos e informações que possam ser recompostas em outra pessoa sem finalidade.
- Redações e exemplos da skill são sintéticos. Os documentos originais continuam sob seus controles no Drive ou órgão.

## VI. Critérios de qualidade
- `Q1` utilidade operacional; `Q2` proveniência verificável; `Q3` identidade inequívoca; `Q4` jurisdição e vigência; `Q5` aprovação nos dois níveis; `Q6` deduplicação; `Q7` minimização; `Q8` recuperabilidade com contexto e limitações.
- Falha crítica em Q2/Q3/Q5/Q7 bloqueia proposta; falha jurídica em Q4 bloqueia apresentação de norma como vigente.

## Referências primárias
LGPD: https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html ; CONARQ Resolução 50/2022: https://www.gov.br/conarq/pt-br/legislacao-arquivistica/resolucoes-do-conarq/resolucao-no-50-de-06-de-maio-de-2022 ; ISO 30401 (resumo público, não norma reproduzida): https://www.iso.org/standard/68683.html ; ANPD: https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-sobre-seguranca-da-informacao-para-agentes-de-tratamento-de-pequeno-porte

## VII. Complemento R07 — assimilação e mudança de entendimento (proposto)

1. A memória **não se autoalimenta de toda conversa, OCR ou PDF**. Ao concluir trabalho documental, a IA só sugere uma candidata durável quando houver finalidade, fonte, objeto, contexto, validade e relevância comprovados.
2. Separar armazenamento de **dossiê de processo** e **conhecimento genérico do escritório**; dados específicos não podem ser generalizados como política. Acesso transversal do proprietário permanece, mas reutilização exige minimização.
3. Distinguir três aprovações: (a) qualidade e autenticidade da fonte, (b) aprovação do documento/processo no registro formal da R06 e (c) aprovação da memória pelo titular no portal. Uma não implica as demais.
4. Classificação editorial mínima: registro de caso, procedimento, modelo, norma, precedente, lição aprendida, decisão interna, pendência e simulação. Casos fictícios não são precedentes reais; OCR não revisado não é fato.
5. Uma fonte mais precisa gera **revisão candidata** com antes/depois, identificação da memória anterior, motivo, comprovação e limites. A R07 de prévia não implementa supersessão/revogação de ponto antigo, e o conhecimento mais recente não se torna automaticamente vigente.
6. Respostas institucionais devem apresentar a base oficial, a versão/data e a incerteza, discriminando `protocolo`, `despacho` e `deferimento`.
7. A ferramenta `memory_assimilation_preview` somente compara registros aprovados do mesmo processo e não grava; propostas e clique humano seguem os contratos originais da R06. A ferramenta só estará disponível no conector após integração e implantação específicas.
