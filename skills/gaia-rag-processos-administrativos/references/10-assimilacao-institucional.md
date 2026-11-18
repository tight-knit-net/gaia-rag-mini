# 10 — Assimilação de conhecimento e evolução da memória institucional (R07)

**Escopo:** fluxo documental e administrativo do GAIA OFFICE. Esta referência complementa a skill R06; não altera a política de acesso do proprietário nem autoriza escrita direta no Qdrant.

## Quando ativar

Ao terminar uma análise de PDF, extração OCR, inventário, catalogação, renomeação proposta, minuta, contrato, procuração, requerimento, exigência, despacho, recurso ou revisão de processo, examinar **se houve conhecimento institucional durável**. Ler este módulo quando o usuário disser “guarde isso”, “aprenda”, “atualize a memória”, “essa informação substitui a anterior” ou pedir retomada/organização do conhecimento.

**Não significa que toda leitura deve virar memória.** A maioria dos arquivos deve ficar no repositório documental, indexada por IDs e proveniência, sem cópia integral na memória. A skill não fica automaticamente ativa em todos os chats; carregar explicitamente pelo host quando disponível.

## Ciclo de assimilação com julgamento humano

1. **Coletar:** recuperar a fonte original canônica e registrar IDs, tipo, data, cliente/processo, objeto, autor da informação, local, hash quando comprovado; marcar `OCR_NAO_VALIDADO` quando a leitura depender de OCR ainda não revisado.
2. **Separar:** distinguir o documento original, fato corroborado, alegação, hipótese, interpretação, orientação geral, norma vigente verificada, pendência e decisão administrativa formal.
3. **Classificar:** `registro_caso`, `procedimento`, `modelo`, `norma`, `precedente`, `licao_aprendida`, `decisao_interna`, `pendencia` ou `simulacao`. A classificação R07 é **editorial**; não presumir campo Qdrant nem mudança automática de permissões.
4. **Comparar:** usar `memory_process_start`, `memory_search`, `memory_find_by_source` e, na R07 atualizada, `memory_assimilation_preview` com `process_id` exato e `source_ref`. Consultar fontes existentes antes de propor duplicata ou atualização. Pesquisa transversal serve para analogias; nunca misturar fatos de clientes.
5. **Diferenciar:** afirmar “nova candidata”, “duplicata”, “revisão candidata” ou “relação a verificar”. Quando a informação mais precisa contrariar a antiga, documentar **ANTES / DEPOIS / nova evidência / limite / fonte / data / ID da anterior**. A prévia não resolve contradição por pontuação de busca ou data isolada.
6. **Propor:** somente com **documento/processo previamente aprovado** no registro de aprovação documental controlado pelo servidor. Chamar `memory_prepare_after_approval` com os campos exigidos pela R06, sem campos novos inventados; a proposta não grava a memória.
7. **Aprovar:** apresentar a URL de revisão devolvida pelo MCP; o proprietário autenticado deve conferir e clicar no botão verdadeiro. Somente `readback` pode confirmar a nova memória.
8. **Retomar:** em trabalhos posteriores, distinguir o registro do estado atual das versões históricas. A R07 **não revoga nem rebaixa pontos antigos**: até existir mecanismo homologado de supersessão, alertar que resumos históricos ainda poderão aparecer na busca.

## Contrato de prévia R07 — somente após disponibilização da branch

```text
memory_assimilation_preview(
  process_id, title, summary, source_ref,
  kind="registro_caso",
  evidence_status="documentada",
  prior_point_id="", namespace="chatgpt"
)
```

Saída: disposição editorial, IDs de potenciais duplicatas/revisões no **mesmo processo**, cobertura do histórico, bloqueios, requisito de aprovação documental, requisito de clique humano, `persisted=false`, `old_points_unchanged=true`. A consulta pode cobrir no máximo 300 memórias por chamada e informa cobertura parcial quando houver mais. Não confundir a prévia do conector em branch com disponibilidade na MCP já publicada.

## Tratamento de OCR, catalogação e edição de PDF

- **OCR:** conservar ID do original, arquivo/página, método, idioma quando conhecido, status da transcrição e revisão humana; nunca transformar texto OCR não conferido em fato confirmado.
- **Catalogação:** fornecer tipologia, assunto, cliente, processo, papel documental, confiança e dúvidas; decisões sobre nomes/destinos dependem da política documental própria, e a memória não renomeia arquivos.
- **Edição, união, divisão e formatação:** cada derivado mantém relação com o original, ordem de páginas, transformação executada, hash/identificador se verificado, responsável e versão; a memória guarda síntese dos resultados aprovados, não PDFs inteiros.
- **Conflito entre fontes:** evidência mais forte ou mais nova não apaga silenciosamente o registro anterior; preservar o histórico e preparar correção revisável.

## Critérios de bloqueio e governança

Nunca promover exemplos sintéticos a precedentes reais; não gravar dados pessoais excessivos, segredos, autos completos, suposto deferimento, norma sem checagem de vigência ou hipótese como fato. A liberação da memória exige documento aprovado e revisão humana. Leitura e proposta não equivalem a aprovação, execução documental, deploy ou publicação do conector.

**Fonte canônica:** Drive/processo, não Qdrant. **Controle:** `governanca/POLITICA_MEMORIA.md`. **Plano de evolução:** `docs/institucional/ARQUITETURA_MEMORIA_E_ASSIMILACAO_R07.md` (raiz do repositório).