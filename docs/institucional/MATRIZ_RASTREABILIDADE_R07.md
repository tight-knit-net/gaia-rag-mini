# R07 — Matriz de evolução, requisitos e evidências
**Data-base:** 2026-11-18 | **Escopo:** homologação executiva inicial, documentação e testes sintéticos.

## I. Cadeia documental examinada
| Documento primário | Local canônico | Decisão/necessidade aplicada à R07 | Situação no GitHub |
|---|---|---|---|
| Relatório de avaliação do conector R06 (18/11) | https://docs.google.com/document/d/1xGoQTfQj9Hai_5uPOXHKUV9bHj0q8nG6LggF2JKIS10/edit | Busca exata e fonte funcionam; mistura de engenharia/simulações; histórico sem vigência; gravação real não testada | Sintetizado no projeto executivo e na política R07; relatório completo permanece no Drive |
| Caderno executivo Office Knowledge (18/11) | https://docs.google.com/document/d/1t6NydW_QqSOzfhWQAj67QQh2rWkSRBEUmuy5BPEbudk/edit | Cliente ≠ processo ≠ documento; fato ≠ alegação; minuta ≠ protocolo ≠ deferimento; documentação original é fonte | SKILL e referência 10; contratos de entrada |
| Relatório executivo de implementação R07 (18/11) | https://docs.google.com/document/d/1DpOyjf-9X5tML8pZ05M-3mBMt2_-KVc2ckGcmd4Xhu0/edit | Escopo original de 15 arquivos, PR #5, 49 testes, dependência R06 e Issue #6 | Atualizado por este inventário/parecer de homologação; arquivo histórico inalterado |
| Topologia da Central Office Knowledge | https://docs.google.com/document/d/16WP8XlBRn7zMBowoCGnij0lzR7iPs8xrR3QtY9bUgko/edit | Localização oficial de relatórios e políticas, fonte externa ao GitHub | Referenciada; não se duplicou o acervo documental no repo |
| Política de memória R04 derivada da pesquisa | skills/gaia-rag-processos-administrativos/governanca/POLITICA_MEMORIA.md | Seleção, minimização, dois níveis de aprovação e preservação de histórico | Complemento VII R07; política histórica preservada |
| Contrato de memória unificada R06 | docs/projeto-executivo/R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md | Proprietário transversal autenticado; process_id é seletor, não trava por cliente | Preservado em app/server.py; nenhuma ACL reintroduzida |
| ADR de congelamento da publicação | docs/projeto-executivo/ADR-0002-FREEZE-PUBLICACAO.md | GHCR e Linode bloqueados sem autorização e validação | Mantido; CI existente verifica job if:false |

**Nota de custódia:** documentos originais do Drive não foram copiados integralmente para esta branch; os artefatos de **arquitetura, critérios, matriz e código** estão versionados aqui. Não afirmar que arquivo físico no Drive é repositório Git ou que política em ambos foi automaticamente promulgada.

## II. Requisitos R07 versus provas
| ID | Requisito institucional | Artefato GitHub | Evidência comprovada | Situação |
|---|---|---|---|---|
| R07-RF01 | Comparar novo aprendizado a memórias aprovadas de processo exato | src/gaia_rag_r05/institutional_memory.py; app/server.py | 14 testes R07; CI validate | Verificado sinteticamente |
| R07-RF02 | Identificar candidata nova, duplicata, relação e revisão | institutional_memory.py; tests/test_institutional_memory.py | Testes de igualdade, mesma fonte e mesmo título | Verificado sinteticamente; sem juízo jurídico automático |
| R07-RF03 | Não consultar histórico de outro processo no fluxo exato | app/server.py e ScopedReads herdado | Teste negativo de escopo; regressões R05/R06 | Verificado sinteticamente |
| R07-RF04 | Preservar aprovação documental + clique humano R06 | review.py, app/server.py; SKILL.md | Código R06 não alterado pela PR; regressões R06 | Preservado no diff; não homologado com dados reais |
| R07-RF05 | Rastrear origem documental e limites de OCR/PDF | CONTRATOS_ENTRADA_DOCUMENTAL_R07.md; referência 10 | Contrato editorial escrito | Planejado, não integrado |
| R07-RF06 | Não elevar simulação/alegação a fato | tests/test_institutional_memory.py; referência 10 | Testes sintéticos positivos/negativos | Verificado na prévia |
| R07-RF07 | Preservar memória anterior em revisão | institutional_memory.py; referência 10 | Testes old_points_unchanged | Prévia verificada; supersessão efetiva fora do escopo |
| R07-RF08 | Identificar versão vigente sem ocultar história | Issue #6 e plano de acoplamento | Backlog e critérios de aceite | Pendente R07.1 |
| R07-RF09 | Integração futura com OCR/catalogação/NOM/PDF | CONTRATOS_ENTRADA_DOCUMENTAL_R07.md; PLANO_ACOPLAMENTO_BRANCHES_R07.md | Interfaces propostas; branches identificadas | Planejado |
| R07-RF10 | Carregamento de skill pelo host | SKILL.md; referências 07 e 10 | Arquivos existentes; catálogo previsto no runtime | Ativação automática não comprovada |
| R07-RF11 | Não publicar/implantar ao congelar branch | workflows GHCR e Linode herdados; PR #5 draft | CI verifica if:false, sem merge | Verificado para workflows da PR |
| R07-RF12 | Topologia e ausência de duplicidade | TOPOLOGIA.md, README.md, REDMI.md, REDME.md | Diff PR e inventário conferidos | Verificado na branch |
| R07-RF13 | Garantir imutabilidade técnica da branch | settings/ruleset GitHub | R07 protected:false; rulesets indisponíveis neste repositório privado/plano | NÃO implementado — congelamento administrativo somente |
| R07-RF14 | Homologação real end-to-end do novo tool MCP | plano R07, futuros gates | CI unitária R07; sem E2E do tool publicado com documentos reais | Pendente, bloqueia produção |

## III. Regras de precedência documental
1. R05 é histórico útil de implantação; sua política anterior de ACL por cliente foi **superada expressamente** pelo contrato R06 de proprietário transversal. Não apagar a R05 nem usar seus trechos conflitantes como decisão atual.
2. R07 é evolução isolada sobre a R06, não sobre a main; não se assume que sua nova ferramenta está implantada no conector da conversa.
3. Documentos do Drive são acervo institucional e registro de decisões editoriais; GitHub guarda a especificação executiva e o código. A existência de relatório não aprova uma memória no Qdrant.
4. A R07 aceita comparar **informação nova**, mas não executa a mudança de **vigência**. A Issue #6 descreve a continuação condicionada a autorização, revisão e testes.
5. Não confundir aprovação da PR/documentação com aprovação de documento do cliente, nem com clique humano na memória RAG.

## IV. Provas de CI e reprodutibilidade
- Execução aprovada anterior à homologação: https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44341418870
- Invariantes: validação da skill, regressões estáticas e 49 testes unitários de backend, incluindo 14 R07; suíte sintética R06; smoke de imagem em ambiente efêmero; jobs de publicação/deploy congelados.
- Reexecutar no **HEAD final do parecer**. Uma execução verde em SHA anterior não garante validação das edições posteriores.
- O marco final de SHA e a confirmação de CI devem ser registrados na PR #5 após o último commit, sem alteração da main.

## V. Responsabilidade institucional
Esta matriz constitui **parecer técnico-executivo assistido**, não certificação externa, aprovação jurídica ou aceite de produção. A decisão de merge, publicação, entrada em produção e política efetiva de supersessão permanece separada.
