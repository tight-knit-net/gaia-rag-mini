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

## Complemento de topologia — gate CI R07 sem TestLab obrigatório (18/11/2026)
Os artefatos históricos do TestLab permanecem para auditoria, mas não integram mais o caminho crítico. Código e testes novos na R07:
- `scripts/r07_candidate_acceptance.py`: inspeção estática de contratos e bloqueios de produção, sem efeitos externos.
- `.github/workflows/r05-skill-static.yml`: job `r07_candidate_acceptance`, dependente dos quatro jobs de validação sintética.
- `docs/institucional/PLANO_VALIDACAO_R07.md`: contrato atualizado de aceite da candidata pelo GitHub Actions.
- `docs/institucional/R07_GATE_CI_SEM_TESTLAB_2026-11-18.md`: relatório do novo gate e das limitações, quando publicado.
- `scripts/r07_testlab_preflight.py`: ferramenta preservada apenas como código histórico; **não executar no antigo TestLab** nesta frente.
A documentação original de R07 e os relatórios G4 não devem ser reescritos retroativamente; este complemento registra a decisão posterior de não usar o antigo ambiente.

## Complemento S7 — preparação portátil, sem deploy (18/11/2026)

- `requirements.lock`: 29 versões Python fixadas conforme CI; o Dockerfile agora fixa base digest e instala do lock.
- `scripts/r07_s7_package_preflight.py`: auditoria estática de base, runtime, segredos, deploy congelado, estado SQLite e integridade das dependências.
- `tests/test_r07_s7_recovery.py`: 5 testes sintéticos de backup SQLite WAL, integridade, restauração em arquivo isolado e rollback sem sobrescrever origem.
- `tests/r06_live_review_e2e.py`: 4 provas adicionais de exportação lógica Qdrant, restauração na coleção shadow, sem perda de metadata e rollback conservando a origem; **não** equivale a snapshot nativo nem a migração real.
- `.github/workflows/r05-skill-static.yml`: jobs `r07_s7_package` e `r07_s7_sqlite_recovery`, ambos pré-requisitos do aceite R07.
- `scripts/r07_candidate_acceptance.py`: pacote S7 e testes sintéticos viraram critérios obrigatórios para CI candidate.
- `docs/institucional/RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md`: runbook de próxima homologação, exclusivamente documental.
- `docs/institucional/R07_S7_RELATORIO_PRONTIDAO_EMPACOTAMENTO_2026-11-18.md`: relatório S7 com 10/10 jobs no código, limites e decisão NO-GO operacional.

**Limitação:** os caminhos históricos de publicação e compose existentes são apenas referências congeladas, não implantação autorizada. A integração no host real, backup nativo Qdrant, wheel hashes/CVE e migração legada seguem pendentes. Nenhuma operação no TestLab antigo foi executada.

## Complemento S8 — supply chain, readback e snapshot nativo planejado (18/11/2026)

- `src/gaia_rag_r05/review.py`: replay de memória aprovada exige readback Qdrant atual, íntegro e contextualizado; não retorna `stored=true` apenas pela linha SQLite.
- `tests/test_r07_s8_review_integrity.py`: 6 testes de readback/idempotência/negação sem efeito real.
- `scripts/r07_s8_supplychain.py`: SBOM CycloneDX determinístico derivado do lock; verificação fail-closed de scanner público das 29 versões.
- `tests/test_r07_s8_supplychain.py`: 8 testes de integridade do BOM, cobertura completa do audit e falha ante vulnerabilidade conhecida.
- `docs/institucional/R07_SBOM_PYTHON_LOCK_S8.cdx.json`: CycloneDX 1.6 versionado com 29 dependências Python, não inclui pacotes do SO nem hashes das wheels.
- `src/gaia_rag_r05/native_snapshot_plan.py` e `tests/test_r07_s8_snapshot_contract.py`: 8 provas sintéticas da decisão de snapshot, destino ausente, SHA, prioridade `snapshot`, inventário e ledger independente.
- `.github/workflows/r05-skill-static.yml`: novos jobs `r07_s8_supplychain`, `r07_s8_review_and_snapshot` antes do aceite.
- `scripts/r07_candidate_acceptance.py`: valida SBOM versionado, contratos de revisão e gates S8.
- `docs/institucional/R07_S8_AUDITORIA_FINAL_SEGURANCA_SUPPLYCHAIN_2026-11-18.md`: relatório do gate, CI 12/12, gaps e próximo S9.
- `docs/institucional/RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md`: adendo de regras de restauração Qdrant, limites da auditoria pública e medidas S9.

**Situação:** S8 aprovado tecnicamente em CI; wheel hashes, CVEs dos pacotes de SO, backup nativo em Qdrant descartável e carregamento do host real ainda pendentes de gates separados. Nada foi implantado.

## S9 — Hashes de wheels e risco OS Debian (18/11/2026)

- `requirements.lock` contém 29 hashes SHA256 de wheels Linux AMD64/CPython 3.12; `Dockerfile` instala exclusivamente por hash.
- `scripts/r07_s9_wheel_lock.py` e `tests/test_r07_s9_hashlock.py`: geração/bootstrap e revalidação das wheels no GitHub Actions.
- `tests/r06_live_review_e2e.py`: oito verificações de snapshot nativo em Qdrant DEMO descartável, prioridade `snapshot`, restore em coleção nova, checksum/paridade e rollback.
- `scripts/r07_s9_os_audit.py` e `tests/test_r07_s9_os_audit.py`: inventário de 87 pacotes Debian/CycloneDX e scan Grype fail-closed.
- `.github/workflows/r05-skill-static.yml`: jobs `r07_s9_hash_bootstrap` e `r07_s9_os_scan`, dependências do aceite do candidato.
- `scripts/r07_candidate_acceptance.py`: contrato de hashes, Qdrant e scanner OS obrigatório.
- `docs/institucional/R07_S9_INTEGRIDADE_WHEELS_SNAPSHOT_NATIVO_OS_SCAN_2026-11-18.md`: relatório com NO-GO, 24 CVEs HIGH distintas, 78 combinações CVE×pacote; CI `44436559758` (12 PASS / 1 FAIL / 1 SKIPPED).
- `docs/institucional/RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md`: gate de bloqueio S9 e próximo S9.1 de remediação planejado.

**NÃO PROVER AMBIENTE REAL E NÃO DESLIGAR LEGADO:** a CI do S9 não está verde devido aos achados de segurança do SO. Este bloqueio é deliberado; não desabilitar scanner para forçar aceitação.

## Complemento S9.2 — atualização Debian estável sem promoção

- `scripts/r07_s92_stable_update.py` e `tests/test_r07_s92_stable_update.py`: 9 regressões sintéticas de imagens digest-fixadas, lock SHA256, políticas fail-closed e inventário Grype completo; sem leitura/escrita de serviços.
- `.github/workflows/r05-skill-static.yml`: job `r07_s9_2_stable_upgrade` de comparação **somente em runner GitHub**, entre imagem principal Trixie e variante atualizada apenas por Debian stable/security; integrado ao `needs` de aceite, sem substituir scanner bloqueante.
- `docs/institucional/R07_S92_MATRIZ_RESIDUAL_CVES_2026-11-18.md`: 23 CVEs HIGH distintas, status oficial Debian por identificador.
- `docs/institucional/R07_S92_RELATORIO_REMEDIACAO_DEBIAN_ESTAVEL_2026-11-18.md`: relatório S9.2 com 87/87 pacotes, 0 atualizações estáveis novas, 23/23 CVEs e 77/77 ocorrências HIGH mantidas, NO-GO, horas aferidas e próximo gate S9.3.
- Nenhuma mudança S9.2 no Dockerfile rastreado (patch zlib do S9.1 permanece). O `requirements.lock` das 29 wheels, Skilldrum, contratos MCP, revisão humana e snapshot Qdrant sintético foram preservados.
- **NO-GO operacional** até solução comprovada de CVEs HIGH/CRITICAL/UNKNOWN; sem merge, deploy, migração, produção, TestLab ou desligamento legado.

## S9.3 — minimização conservadora por APT (19/11/2026)

- `scripts/r07_s93_minimization.py`: geração de Dockerfile exclusivamente **temporário em CI**, comparação da lista integral de pacotes Debian e de resultados Grype, sondagem de imports/ELF e classificação **O = observado / N = não observado, não dispensável**.
- `tests/test_r07_s93_minimization.py`: 10 testes negativos/sintéticos de base fixada, lock por SHA256, dependências observadas, scanner completo e ausência de aprovação automática.
- `tests/r07_s93_http_smoke.py`: saúde e quatro negativas HTTP em trial isolada (5/5), sem rede externa, sem segredos ou memória real.
- `.github/workflows/r05-skill-static.yml`: job `r07_s93_minimization` dependência do aceite, com build temporário, `pip check`, comparação por Grype e provas HTTP; o scanner OS original permanece fail-closed.
- `docs/institucional/R07_S93_MATRIZ_DEPENDENCIAS_RUNTIME_2026-11-19.md`: inventário das 87 versões Debian e 8 bibliotecas ligadas aos módulos Python testados; 79 outras não observadas **não devem ser removidas sem prova**.
- `docs/institucional/R07_S93_RELATORIO_MINIMIZACAO_RUNTIME_2026-11-19.md`: relatório S9.3 v1.0.0; 87→87 pacotes, 0 removidos, 23 CVEs HIGH/77 ocorrências, CI 16 PASS/1 FAIL/1 SKIPPED, NO-GO.
- **Não houve alteração no Dockerfile principal ou `requirements.lock`.** Sem merge, deploy, publicação, migração ou corte do legado. Próximo gate S9.4 documental/CI para estudar empacotamento multi-stage suportado, sem waiver de CVEs.
