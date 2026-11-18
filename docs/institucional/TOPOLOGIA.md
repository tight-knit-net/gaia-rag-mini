# TOPOLOGIA — OFFICE KNOWLEDGE R07
Revisão: 2026-11-18 | Branch: feat/r07-office-knowledge-assimilation | Base: feat/r06-lifecycle-skill-staging

## Índice físico da pasta docs/institucional
| Arquivo | Finalidade | Estado |
|---|---|---|
| README.md | Entrada e leitura orientada | criado na R07 |
| REDMI.md | Protocolo de gravação, prevenção de colisões e indexação | criado na R07 |
| REDME.md | Guia de utilização editorial | criado na R07 |
| TOPOLOGIA.md | Índice autorreferente | criado na R07 |
| ARQUITETURA_MEMORIA_E_ASSIMILACAO_R07.md | Ciclo institucional, decisões e limites | proposta arquitetural R07 |
| PROJETO_EXECUTIVO_R07.md | Projeto consolidado, escopo, interfaces e critérios de aceite | projeto executivo R07 |
| MATRIZ_RASTREABILIDADE_R07.md | Vínculo a relatórios do Drive e matriz de requisitos/evidências | governança R07 |
| PLANO_ACOPLAMENTO_BRANCHES_R07.md | Cadeia de PRs, divergência OCR/NOM e integração futura | plano técnico-executivo R07 |
| TERMO_HOMOLOGACAO_INICIAL_R07.md | Parecer condicional e regra de congelamento administrativo | homologação executiva inicial |
| CONTRATOS_ENTRADA_DOCUMENTAL_R07.md | Interfaces futuras OCR, PDF, NOM e catalogação | contrato proposto, NÃO implementado |
| PLANO_VALIDACAO_R07.md | Testes e gates de merge e deploy | plano de execução |

## Arquivos existentes alterados nesta branch
| Caminho | Finalidade | Estado |
|---|---|---|
| app/server.py | Nova ferramenta memory_assimilation_preview autenticada, sem escrita, e allowlist da nova referência | implementado na R07, não implantado |
| skills/gaia-rag-processos-administrativos/SKILL.md | Inclusão de gatilhos de assimilação e uso da prévia | atualizado na R07 |
| skills/gaia-rag-processos-administrativos/governanca/POLITICA_MEMORIA.md | Complemento editorial R07 | atualizado na R07 |
| skills/gaia-rag-processos-administrativos/references/07-contratos-mcp-atual.md | Declaração do novo contrato R07 em branch | atualizado na R07 |
| skills/gaia-rag-processos-administrativos/tests/test_regressao_r05.py | Atualização das expectativas da skill: 10 módulos e versão R07 | atualizado na R07; regressão preservada |

## Arquivos novos fora desta pasta
| Caminho | Finalidade | Estado |
|---|---|---|
| src/gaia_rag_r05/institutional_memory.py | Comparação determinística sem mutação | implementação R07 |
| tests/test_institutional_memory.py | 14 testes sintéticos de assimilação | testes offline |
| skills/gaia-rag-processos-administrativos/references/10-assimilacao-institucional.md | Protocolo de uso documental, OCR, PDF e memórias | nova referência da skill |

## Rastreabilidade e contratos de publicação
- Origem: código e skill reais inspecionados na branch R06, PR #4 draft; nenhum arquivo da main foi sobrescrito.
- Outras branches isoladas verificadas no mesmo repositório: feat/ocr-documental-isolado e feat/catalogacao-triagem-isolada; nenhuma foi editada pela R07.
- A branch R07 é stack dependente da R06, com PR draft separada a ser revisada **contra a R06**.
- Não se migrou, reprovou, apagou, editou ou gravou memória da base real; nenhum PDF de cliente foi incorporado.
- Qualquer novo arquivo exige atualização deste mapa antes da finalização do mesmo lote.
- Esta topologia não substitui o índice dos documentos institucionais no Google Drive 16, que é outro acervo.

## Revisão de completude da documentação executiva — 18/11/2026
- Inventário inicial da R07: 15 arquivos alterados/criados em relação à R06, antes dos quatro artefatos adicionais de homologação.
- Quatro artefatos incorporados: projeto executivo, matriz de rastreabilidade, plano de acoplamento e termo de homologação. O diff deve conter agora 19 caminhos exclusivos da R07 (validar no HEAD final).
- Relatórios-fonte consultados: avaliação sistemática R06 (Google Doc 1xGoQTfQj9Hai_5uPOXHKUV9bHj0q8nG6LggF2JKIS10), executivo de implementação R07 (1DpOyjf-9X5tML8pZ05M-3mBMt2_-KVc2ckGcmd4Xhu0) e caderno institucional (1t6NydW_QqSOzfhWQAj67QQh2rWkSRBEUmuy5BPEbudk). Originais permanecem no Drive; decisões, escopo e lastro agora indexados em MATRIZ_RASTREABILIDADE_R07.md.
- Cadeia verificada: PR #1 -> #3 -> #4 -> #5; nenhum merge para main.
- Congelamento administrativo somente por baseline SHA e PR draft; main e R07 estavam sem proteção técnica de branch (protected=false).
- Status de CI do SHA final e aceitação condicional deverão constar em comentário de controle da PR #5; qualquer commit posterior invalida o marco até revalidação.
