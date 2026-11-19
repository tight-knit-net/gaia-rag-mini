# GAIA RAG & Knowledge — GATE S8 | Auditoria final de segurança, cadeia de suprimentos e prontidão

**Versão:** 1.0.0 — relatório de auditoria técnica, não de homologação operacional.
**Data/hora de emissão exatas:** 18/11/2026 às 22:01:41 (America/Sao_Paulo; UTC−03:00).
**Origem verificável do relógio:** ferramenta de hora local ChatGPT; resposta ISO `2026-11-18T22:01:41-03:00`.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Branch exclusiva de escrita:** `feat/r07-office-knowledge-assimilation`; PR #5 ainda draft, aberta e sem merge.
**Base de comparação somente leitura:** `feat/r06-lifecycle-skill-staging`; SHA observado `14cca2e325b8919506c9a95b917e02ae6bf293c7` (PR #4).
**Código S8 aprovado na CI:** commit `d267f5ff9ea76fc8a8f1cc69c1b2a18eaa3c5fa4` (antes das atualizações documentais).
**Execução CI de código:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44433484833
**SBOM versionado:** [R07_SBOM_PYTHON_LOCK_S8.cdx.json](R07_SBOM_PYTHON_LOCK_S8.cdx.json).
**Runbook revisto:** [RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md](RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md).
**Escopo S8:** revisão/implementação somente na branch R07 + GitHub Actions com dados sintéticos, sem merge, deploy, publicação de imagem, acesso ao Qdrant real, Cloudflare/DNS, GitLab, Linear, TestLab, legado ou produção.

## 1. Parecer

**GO técnico CONDICIONAL — S8 passou na auditoria e CI da candidata.** O fluxo de revisão humana teve um risco de readback em replay corrigido; os testes sintéticos passaram e a auditoria pública das 29 distribuições Python fixadas retornou **zero vulnerabilidades conhecidas** na data aferida. Este GO significa apenas possibilidade de continuar com o próximo gate CI.

**NO-GO para implantação, ativação operacional, migração e desligamento legado**: hashes das wheels ainda não estão presos, pacotes do SO na imagem Docker não foram inspecionados em scanner dedicado, e autenticação Cloudflare Access/snapshot nativo de Qdrant não estão homologados em runtime real.

## 2. Achados e tratamentos

| ID | Severidade | Achado | Situação S8 |
| --- | --- | --- | --- |
| S8-01 | P1 — integridade de aprovação | `review.approve` devolvia `stored=True` para proposta já `approved` sem confirmar novamente a existência/integridade do ponto no Qdrant. | **CORRIGIDO na R07:** `_verify_approved_point` verifica Qdrant também em replay, com ID, namespace, processo, origem, hash, referência documental, conteúdo e `approved=true`. Falha não afirma persistência. |
| S8-02 | P2 — SBOM | O pacote anterior possuía lock por versões e digest da base, mas faltava SBOM versionado e prova de que correspondia ao lock. | **CORRIGIDO:** CycloneDX 1.6 com 29 dependências públicas Python, serial determinístico, origem SHA do lock; CI regenera e compara o artefato versionado. |
| S8-03 | P2 — vulnerabilidades Python | Faltava auditoria automatizada de vulnerabilidades contra fonte pública. | **TRATADO:** `pip-audit==2.10.1` em runner efêmero; auditoria 29/29, 0 vulnerabilidades conhecidas, com validação fail-closed de cobertura/versões. Não há garantia para o futuro. |
| S8-04 | P2 — integridade de wheels | `requirements.lock` fixa 29 versões, mas não cada distribuição por SHA (`--require-hashes`). | **PENDENTE — próximo S9**. Não afirmar reprodução bit a bit do contêiner. |
| S8-05 | P2 — risco da imagem OS | SBOM Python não inclui pacotes Debian/OS da imagem `python:3.12-slim`; nenhuma varredura de OS CVE nesta etapa. | **PENDENTE — próximo S9**; não afirmar cobertura completa da cadeia de suprimentos. |
| S8-06 | P1 — snapshot e rollback de dados | Recuperação Qdrant com prioridade `replica` por padrão pode restaurar vazio em coleção nova; endpoint de upload pode sobrescrever coleção existente. | **CONTRATO DOCUMENTADO/TESTADO SINTETICAMENTE:** exigir destino ausente, prioridade `snapshot`, SHA verificado, inventário e backup ledger. Não houve snapshot nativo executado neste gate. |
| S8-07 | P1 — autorização operacional | R07 ainda não roda no host definitivo; não há prova real Cloudflare Access nem clique do operador no portal. | **PENDENTE / NO-GO operacional.** Testes usam JWT, memória e Qdrant DEMO. |
| S8-08 | P1 — risco de migração | Propostas pendentes, esquema SQLite legado e memórias aprovadas ainda não reconciliadas no mundo real. | **PENDENTE / NO-GO migração.** Não promover propostas ao status `approved`. |

## 3. Matriz de testes de CI — código S8

**Execução verificada:** run `44433484833`, commit `d267f5ff9ea76fc8a8f1cc69c1b2a18eaa3c5fa4`, **12/12 jobs SUCCESS**.

| Dimensão | Resultado | Prova/limitação |
| --- | --- | --- |
| `validate` | PASS — 23 regressões da skill e **126 testes unitários** | Includes S6/S7/S8 unit cases; not separate increments |
| `r06_lifecycle_synthetic` | PASS — **71 verificações E2E** | MCP, JWT DEMO, Qdrant descartável, CSRF, botão e readback |
| `r07_operational_isolated` | PASS | Runtime sem rede pública, chaves ou persistência real |
| `r07_skill_router_synthetic` | PASS — 14 testes | Seleção de missão, SHA e bloqueio de rotas |
| `r07_host_contract_synthetic` | PASS — 9 testes | Host emulado, não ChatGPT real |
| `r07_s6_security` | PASS — 5 testes | Negativas de acesso e ledger legado |
| `r07_s7_package` | PASS | Docker por digest, 29 versões, usuário não-root |
| `r07_s7_sqlite_recovery` | PASS — 5 testes | Snapshot SQLite WAL e restauração em arquivo isolado |
| `staging_image_smoke` | PASS | Contêiner/Qdrant apenas efêmeros |
| `r07_s8_supplychain` | PASS — 8 testes unitários + 29/29 advisory audit | PyPI feed público, 0 vulnerabilidades conhecidas; SBOM confere |
| `r07_s8_review_and_snapshot` | PASS — 6 testes de replay + 8 de contrato nativo Qdrant | São subconjuntos da suíte unitária, **não** snapshot real |
| `r07_candidate_acceptance` | PASS | Verifica congelamento do deploy e contratos R07 |

**Sem dupla contagem:** os 8 testes SBOM e os 14 casos do job de replay/snapshot integram os 126 testes unitários executados em `validate`. As 71 verificações E2E são uma dimensão separada. O job do scanner verificou as 29 versões uma única vez por execução.

## 4. Verificações de identidade, contratos e persistência

- Protocolo MCP R06 preservado; as ferramentas R07 de roteamento são somente seleção e leitura de skills instaladas, sem autoridade para gravar memória.
- Consulta transversal do proprietário permanece autorizada: `process_id` contextual, não ACL por cliente. Acesso continua exigindo identidade do proprietário verificada e `approved=true` para leitura de memórias.
- Rotas do botão `Salvar memória` são apenas browser POST com origem, CSRF, aprovação documental e check de idempotência; replay agora depende de readback atual do Qdrant.
- A coleção de pontos aprovados e a fila SQLite de propostas são entidades separadas. Esquema legado que não admite `discarded` continua bloqueado até migração consentida com backup.
- Restore de Qdrant: fonte oficial https://qdrant.tech/documentation/snapshots/ e https://api.qdrant.tech/api-reference/snapshots/recover-from-uploaded-snapshot. O controle S8 `native_snapshot_plan.py` é puro: `network_requests=0`, `writes=0`, `production_homologated=false`.

## 5. Arquivos alterados somente na PR #5

- `src/gaia_rag_r05/review.py`: confirmação de ponto em Qdrant tanto no primeiro clique quanto no replay da proposta aprovada.
- `tests/test_r07_s8_review_integrity.py`: seis casos sintéticos de readback idempotente e negativo.
- `scripts/r07_s8_supplychain.py`: gerador/validador determinístico de SBOM e cobertura de auditoria pública.
- `tests/test_r07_s8_supplychain.py`: oito casos de integridade, adulteração, cobertura e vulnerabilidades sintéticas.
- `docs/institucional/R07_SBOM_PYTHON_LOCK_S8.cdx.json`: SBOM CycloneDX 1.6 derivado do lock.
- `src/gaia_rag_r05/native_snapshot_plan.py` e `tests/test_r07_s8_snapshot_contract.py`: contrato sem efeitos e oito casos de recusa de restauração perigosa.
- `.github/workflows/r05-skill-static.yml`: dois novos jobs S8 exigidos antes do aceite final.
- `scripts/r07_candidate_acceptance.py`: validação do SBOM armazenado, replay e gate de snapshots.
- `docs/institucional/RUNBOOK_R07_IMPLANTACAO_AUTENTICADA_BACKUP_ROLLBACK.md`: adendo de regras nativas de snapshot, fontes oficiais e gaps de supply chain.

## 6. Riscos, rollback e dependências

- O inventário SBOM aqui é **somente Python**. SHA256 do lock `f5c6b0757685093c77c2f994cb7b104e900b81077f0f0c43d196f1a857f8df82` prova o documento de versões, **não** as wheels baixadas.
- O scanner de vulnerabilidades usa dados **públicos** de PyPI, sem enviar documentos ou informações de clientes. Seu resultado muda com o tempo; revisar antes de ativação.
- Container Docker e Qdrant só ocorreram em runners temporários do GitHub Actions; nenhum upload/push de imagem, nem alteração de Qdrant real, Cloudflare/DNS, produção ou legado.
- Se um teste falhar, reverter revisando unicamente a branch R07; nenhum rollback externo é aplicável neste gate. Legado preservado.
- Proteção de produção não depende apenas de CI verde; requer destino autorizado, Cloudflare Access real, backup/readback Qdrant e humano autenticado.

## 7. Próximo gate recomendado — S9 (NÃO EXECUTADO)

**S9 — fechamento dos gaps de integridade do pacote e ensaio de snapshot Qdrant nativo sintético**. Restrito a GitHub Actions, com: (1) wheel SHA-256 por requisito e instalação `--require-hashes` sem dependências flutuantes; (2) SBOM/scan OS da imagem descartável, registro de vulnerabilidades e remediação somente na branch R07; (3) ensaio de snapshot Qdrant nativo e restauração em coleção **nova e descartável** no CI, com `priority=snapshot`, checksums, inventário aprovado e prova de não alteração da origem; (4) regressão do fluxo Salvar memória; (5) relatório GO/NO-GO e checklist de integração futura.

**Gate S9 não autoriza:** merge, publicação GHCR, escolha/configuração de destino, Cloudflare, Qdrant real, migração ou desligamento legado. **Aceite S9:** CI íntegra no HEAD final, cadeia de dependências coberta com hashes verificáveis ou bloqueios explícitos, risco OS classificado e snapshot sintético com rollback; falha implica NO-GO sem contorno.

**Próxima ação:** solicitar S9 por botão do chat. O botão solicita execução isolada, não autoriza alterações externas.
