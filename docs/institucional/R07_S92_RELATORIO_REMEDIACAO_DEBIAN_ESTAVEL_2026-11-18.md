# GAIA RAG & Knowledge — Gate S9.2 | Atualizações Debian estáveis e CVEs residuais

**Versão:** 1.0.0 — relatório de execução com parecer NO-GO técnico de segurança.
**Disparo S9.2 aferido:** 18/11/2026, **23:45:40**, America/Sao_Paulo (UTC−03:00). Origem: serviço de hora local ChatGPT, resposta `2026-11-18T23:45:40-03:00`, consultada ao início do gate.
**Última execução do gate anterior S9.1:** 18/11/2026, **23:36:31**, America/Sao_Paulo. Fonte: último registro temporal do job Grype na CI final S9.1 `44445365216`, `2026-11-19T02:36:31.0057814Z`.
**Última execução técnica S9.2 verificada nesta emissão:** 18/11/2026, **23:54:57**, America/Sao_Paulo. Fonte: última linha do log GitHub Actions S9.2 trial `135302967027`, run `44447458356`, `2026-11-19T02:54:57.9561373Z`.
**Emissão do relatório:** 18/11/2026 às **23:55:50**, America/Sao_Paulo. Origem: serviço de hora local ChatGPT, ISO `2026-11-18T23:55:50-03:00`.
**Escopo:** somente PR #5 / branch R07, pesquisa em advisories oficiais Debian e GitHub Actions sintéticos com imagens Docker/Qdrant descartáveis. Nenhum merge, deploy, publicação, TestLab, GitLab, Linear, Cloudflare, DNS, Qdrant real, migração de memória ou corte do legado.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Branch única de escrita:** `feat/r07-office-knowledge-assimilation`, PR #5 draft e aberta, sem merge.
**Base somente leitura:** `feat/r06-lifecycle-skill-staging` SHA `14cca2e325b8919506c9a95b917e02ae6bf293c7`, PR #4.
**HEAD de código/auditoria antes do relatório:** `ac6f2017172d0327f1611ff927033656511e9734`.
**CI de validação do código S9.2:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44447458356
**Matriz residual homologada apenas documentalmente:** [R07_S92_MATRIZ_RESIDUAL_CVES_2026-11-18.md](R07_S92_MATRIZ_RESIDUAL_CVES_2026-11-18.md).

## 1. Escopo e decisão

**S9.2: NO-GO técnico de cadeia de suprimentos / NO-GO para qualquer implantação, migração ou desativação de legado.** A tentativa de atualizar o contêiner R07 por repositórios oficiais **Trixie/Trixie-security/Trixie-updates** não encontrou pacotes adicionais para atualizar. O scanner Grype permaneceu com **23 CVEs HIGH distintas em 77 ocorrências CVE×pacote**. O comparativo não foi usado para emitir aprovação indevida.

Os resultados do S9.1 e o lock de wheels foram preservados. Não foram importados pacotes Bookworm/Forky/Sid/unstable; não houve waiver, ignore, `--ignore-unfixed`, mudança de severidade, remoção seletiva de achados ou desligamento de scanner. A PR permaneceu draft.

## 2. Investigação de avisos oficiais Debian

| Família | Quantidade de IDs HIGH residuais | Observação do tracker Debian Trixie |
| --- | ---: | --- |
| OpenSSL | 6 | Trixie vulnerável, sem versão corrigida suportada comprovada para o conjunto consultado; [Debian](https://security-tracker.debian.org/tracker/source-package/openssl) |
| SQLite | 3 | Vulnerável, alguns `no DSA`, correções disponíveis em distribuições posteriores; [Debian](https://security-tracker.debian.org/tracker/source-package/sqlite3) |
| glibc | 3 | Vulnerável, alguns `no DSA`; [Debian](https://security-tracker.debian.org/tracker/source-package/glibc) |
| util-linux | 4 | Trixie vulnerável em 4 IDs; [Debian](https://security-tracker.debian.org/tracker/source-package/util-linux) |
| GCC/libstdc++ | 2 | Trixie vulnerável; correções posteriores não autorizam mistura de releases; [Debian gcc-14](https://security-tracker.debian.org/tracker/source-package/gcc-14) |
| Perl | 2 | Vulnerável, `no DSA`; [Debian](https://security-tracker.debian.org/tracker/source-package/perl) |
| ncurses | 1 | Trixie vulnerável `no DSA`; [Debian](https://security-tracker.debian.org/tracker/CVE-2025-69720) |
| ACL | 2 | Trixie vulnerável `no DSA`; [Debian](https://security-tracker.debian.org/tracker/source-package/acl) |
| **Total** | **23** | **Não foi comprovada correção estável disponível para estes 23 na pesquisa deste gate.** |

**Ressalva:** o tracker Debian pode considerar um caso de menor urgência ou `no DSA`, enquanto o Grype lhe atribui HIGH. São fontes e taxonomias diferentes; a discrepância **não autoriza** rebaixar a severidade na CI, muito menos declarar a aplicação segura. Nenhuma avaliação de explorabilidade específica ou dados reais foi executada.

## 3. Ensaio GitHub Actions S9.2, dados sintéticos

Um Dockerfile **temporário, somente no runner** foi derivado da R07 digest-fixada. Ele adicionou `apt-get update; apt-get upgrade -y --no-install-recommends` mantendo somente repositórios Debian 13 estáveis/segurança. O Dockerfile rastreado da R07 **não** recebeu `apt upgrade`, porque o ensaio não mostrou remediação. O Grype (imagem por digest), a consulta de pacotes `dpkg-query` e as 29 wheels SHA256 foram executados na CI efêmera. O ensaio foi explicitamente classificado como **comparação de pesquisa**, não como gate de publicação.

| Medida na comparação pareada do mesmo runner | Baseline R07 | Trial oficial Trixie |
| --- | ---: | ---: |
| Pacotes Debian instalados | 87 | 87 |
| Pacotes atualizados/removidos | — | **0** |
| Pacotes adicionados | — | **0** |
| CVEs bloqueantes distintas | **23** | **23** |
| Ocorrências bloqueantes HIGH/CRITICAL/UNKNOWN | **77** | **77** |
| Novos identificadores CVE bloqueantes | — | **0** |
| Identificadores bloqueantes resolvidos | — | **0** |
| Permissões de publicação | Não | Não |

Fonte: job `R07 S9.2 official Debian stable/security update trial (no promotion)` do run `44447458356`, comparador `S92_STABLE_COMPARISON`, retornou `candidate_eligible=false`, `scanner_waivers=0`, `production_homologated=false`.

## 4. Testes e critérios por dimensão

**CI no commit de código `84717cd9f614e03fa43159ddb787b04f65b48b51`: 17 jobs, 15 SUCCESS / 1 FAILURE OS (correto) / 1 SKIPPED (aceite agregado bloqueado).** A CI não está verde e não há homologação operacional.

| Dimensão | Resultado CI | Limitação |
| --- | --- | --- |
| Testes unitários R07 | **155 PASSOU** | Inclui **9 testes S9.2**, não somar separadamente |
| Regressão Skill R05 | **23 PASSOU** | Estática, carregamento real do host não provado |
| MCP, revisão humana sintética, identidade, Qdrant descartável | **79 verificações PASSOU** | Sem Access real ou persistência Qdrant de produção |
| Snapshot Qdrant nativo sintético | **8/8 PASSOU**, subconjunto E2E | Apenas 3 pontos DEMO e recuperação em coleção nova |
| 29 wheels Python hash-locked | **29/29 PASSOU** | CPython 3.12/Linux AMD64, nenhuma alteração da versão de dependência |
| Docker e zlib Debian 13 corrigido no S9.1 | **PASSOU** | Versão específica `1:1.3.dfsg+really1.3.1-1+deb13u1` preservada |
| Teste dos repositórios oficiais e upgrade controlado | **PASSOU como ensaio, 0 upgrades** | Não equivale a aprovação de segurança |
| Grype Debian da candidata R07 | **FALHOU** | 23 CVEs HIGH e 77 ocorrências; bloqueio intencional |
| Job agregador de aceite candidato | **SKIPPED** | Depende de Grype PASS; não executado |
| Host ChatGPT real, Cloudflare Access e botão Salvar real | **NÃO EXECUTADO** | Fora do S9.2 |
| Migração SQLite/Qdrant reais e corte | **NÃO EXECUTADO** | Proibidos neste gate |

## 5. Mudanças feitas somente na R07

- `scripts/r07_s92_stable_update.py`: gera Dockerfile temporário, valida pinagem da base e política das wheels, compara inventários completos de packages e resultados Grype, rejeita relatório truncado/insuficiente e nunca marca promoção automática.
- `tests/test_r07_s92_stable_update.py`: 9 casos unitários sintéticos incluindo controles de no-waiver, base imutável e recusa de CVEs novas/relatório truncado.
- `.github/workflows/r05-skill-static.yml`: job adicional `r07_s9_2_stable_upgrade` testando upgrade Debian oficial exclusivamente no runner, Grype antes/depois, exigido no gate agregado.
- `docs/institucional/R07_S92_MATRIZ_RESIDUAL_CVES_2026-11-18.md`: 23 CVEs, fontes e status.
- Este relatório S9.2. **O Dockerfile principal da R07 não mudou** neste gate, pois não houve patch estável adicional demonstrado.

## 6. Riscos e rollback

- **P1:** 23 CVEs HIGH sem correção Debian stable demonstrada para a imagem R07. Não suprimir os achados para forçar CI verde.
- **P1:** CI validada apenas com dados sintéticos; serviço R07 não homologado em Access, host ChatGPT nem banco Qdrant real.
- **P1:** esquema SQLite legado / propostas pendentes / pontos Qdrant aprovados ainda aguardam inventário e gate posterior separado. Nunca promover propostas pendentes.
- **P2:** snapshot Qdrant nativo em runner efêmero não demonstra recuperação real em outra infraestrutura.
- **P2:** fontes oficiais e feed Grype evoluem. Revisar CVEs antes de futura decisão de implantação.
- **Rollback S9.2:** nenhuma alteração de serviço externo, nenhum Dockerfile principal alterado. Caso necessário, reverter exclusivamente os três arquivos de código/CI S9.2 na branch R07 após reconferência de HEAD; manter R06, main e legado intactos.

## 7. Próximo gate recomendado — S9.3 (NÃO EXECUTADO)

**S9.3 — minimização comprovada do runtime Debian da candidata e análise de alternativas suportadas somente em CI.** Objetivo: identificar bibliotecas/pacotes Debian estritamente necessários ao funcionamento do runtime, investigar alternativas de empacotamento suportadas **sem importar pacotes instáveis** e executar, em CI com dados fictícios, variantes temporárias com inventário OS completo, scanner Grype sem ignorar CVEs, hashes das 29 wheels, contratos MCP, skill router, segurança de identidade, fluxo manual Salvar memória e backup/restore Qdrant sintético. Nenhuma remoção de pacote será incorporada sem testes funcionais e redução de risco comprovada; pacote ausente do inventário não pode ser equivalente a um waiver.

**Critério GO do S9.3:** nenhuma CVE HIGH/CRITICAL/UNKNOWN no artefato candidato sem solução oficial e testes verdes em regressões; se houver achados residuais, manter NO-GO e documentar cada dependência externa, sem aprovação presumida.

**Exclusões S9.3:** nenhuma alteração fora da branch R07, merge, publicação, deploy, Cloudflare/DNS, Qdrant real, GitLab, Linear, TestLab, migração, memória ou corte legado. O botão do chat apenas solicita execução posterior e **não autoriza operações externas**.
