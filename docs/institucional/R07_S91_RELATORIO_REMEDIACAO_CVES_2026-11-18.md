# GAIA RAG Knowledge — Gate S9.1 | Remediação das vulnerabilidades Debian

**Versão:** 1.0.0 — relatório técnico versionado, gate S9.1 concluído com NO-GO de segurança.
**Disparo S9.1 aferido:** 18/11/2026 às 23:20:13, fuso America/Sao_Paulo (UTC−03:00); origem: serviço de horário local do ChatGPT, ISO `2026-11-18T23:20:13-03:00`, consultado no início do gate.
**Última execução do gate anterior S9:** 18/11/2026 às 22:30:41, America/Sao_Paulo; origem: última linha temporal do log GitHub Actions do scanner OS, execução `44437213042`, job `135268988159`, `2026-11-19T01:30:41.1816998Z`. Não confundir com emissão do relatório S9 às 22:26:09.
**Última execução técnica S9.1 aferida para o relatório:** 18/11/2026 às 23:32:20, America/Sao_Paulo; origem: última linha temporal do scanner OS no GitHub Actions run `44444855208`, job `135294404540`, UTC `2026-11-19T02:32:20.6871362Z`.
**Emissão deste relatório:** 18/11/2026 às 23:33:12, America/Sao_Paulo; origem: serviço de horário local do ChatGPT, ISO `2026-11-18T23:33:12-03:00`.
**Escopo:** consulta pública a avisos Debian, comparação de variantes Docker Python 3.12 por digest em GitHub Actions, correções apenas na R07, regressões sintéticas. **Nenhuma escrita ou consulta em GitLab, Linear, TestLab, Cloudflare, DNS, Qdrant real, memória real, produção ou serviços legados.**
**Alvo único de alterações:** `tight-knit-net/gaia-rag-mini`, branch `feat/r07-office-knowledge-assimilation`, PR [#5](https://github.com/tight-knit-net/gaia-rag-mini/pull/5), aberta, draft, sem merge; base somente leitura `feat/r06-lifecycle-skill-staging` SHA `14cca2e325b8919506c9a95b917e02ae6bf293c7`, PR #4.
**HEAD de código S9.1:** `63ebfda949c7ac640c1cff4af3c75f5ffec1bfca`.
**GitHub Actions do código S9.1:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444855208
**Matriz oficial por CVE:** [R07_S91_MATRIZ_CVES_DEBIAN_2026-11-18.md](R07_S91_MATRIZ_CVES_DEBIAN_2026-11-18.md).

## 1. Decisão executiva

**S9.1 = NO-GO técnico para fechar a segurança da imagem**. Foi aplicada uma correção comprovada para uma CVE HIGH da zlib no Debian 13, sem desvios de segurança, porém permanecem 23 CVEs HIGH no inventário Grype. Não promover a candidata, publicar imagem, fazer merge, implantar, migrar dados, nem desabilitar legado.

**Trabalho concluído no escopo permitido:** as duas variantes oficialmente suportadas (`python:3.12-slim-trixie`, `python:3.12-slim-bookworm`) foram construídas como candidatos R07 completos em runners GitHub Actions, com imagens-base resolvidas para digest imutável. A comparação demonstrou Bookworm com risco global maior. A versão de segurança zlib do Trixie foi aplicada e validada no contêiner. Foram preservados o lock das 29 wheels SHA256, a autenticação do proprietário, o roteador Skilldrum, o fluxo humano de aprovação e o snapshot Qdrant sintético.

## 2. Matriz comparativa quantitativa — Grype sem supressão

| Estado da candidata | Base por digest | CVEs bloqueantes distintas | HIGH ocorrências | CRITICAL ocorrências | UNKNOWN ocorrências | Elegível para GO |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| S9: Trixie anterior | `sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` | 24 | 78 | 0 | 0 | NÃO |
| S9.1: Bookworm comparativo | `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` | 43 | 97 | 3 | 24 | NÃO — piora global |
| S9.1: Trixie corrigido zlib | `sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` | **23** | **77** | **0** | **0** | **NÃO — residual HIGH** |

**Grype é mantido fail-closed.** A CI do produto falha propositalmente na presença de 23 CVEs HIGH e impede o job de aceite agregado. Já os dois jobs de comparação de imagens **PASSAM apenas como pesquisa**, mesmo exibindo `candidate_eligible=false`; isso não significa aprovação da cadeia de suprimentos.

**Evidências CI:** comparação inicial https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444037152 ; comparação já com correção https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444554282 ; código final, inclusive verificação de versão dpkg-query, https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444855208 .

## 3. Remediação real e limites de disponibilidade de patches

- **CVE-2026-85091 (zlib):** Debian Security Tracker indica Trixie-security corrigido em `1:1.3.dfsg+really1.3.1-1+deb13u1` (https://security-tracker.debian.org/tracker/CVE-2026-85091). A versão exata foi incluída em `Dockerfile` via `apt-get install -y --no-install-recommends`, sobre a imagem-base digest-fixada, e `dpkg-query` no contêiner provou o pacote instalado. Scanner posterior deixou de listar essa CVE: 24→23 IDs, 78→77 ocorrências HIGH.
- **Bookworm não selecionado:** embora parte das falhas util-linux não afete Debian 12, o contêiner completo introduz 43 CVEs bloqueantes distintas, incluindo 3 ocorrências CRITICAL e 24 UNKNOWN. O pacote Trixie-only zlib foi retirado **somente do Dockerfile temporário de comparação** Bookworm, sem alteração do Dockerfile rastreado da R07 nem exceção no scanner. Critério de base imutável mantido.
- **Sem patch suportado demonstrado para os demais 23 no conjunto consultado:** Debian tracker relaciona OpenSSL 3.0/3.5 (p.ex. CVE-2026-124709), SQLite3 3.40/3.46, glibc, util-linux, GCC/libstdc++, Perl, ncurses e ACL ainda vulneráveis em Bookworm/Trixie. Algumas versões posteriores de ramos não estáveis têm correção, mas **não** foram importadas para a imagem Debian estável. Fonte e classificação por CVE na matriz acima.
- **Sem supressão nem falso GO:** nenhuma regra `ignore`, `--ignore-unfixed`, waiver, rebaixamento arbitrário de severidade ou exclusão de pacotes vulneráveis do inventário foi aplicada.
- A ausência de atualização estável não equivale a aceitação de risco. Análise de atingibilidade e mitigação de arquitetura precisam avaliação separada com evidência, e não desativam automaticamente o gate técnico bloqueado.

## 4. Testes por dimensão no GitHub Actions

**Execução `44444855208`, HEAD de código indicado acima, 16 jobs no total: 14 SUCCESS / 1 FAILURE OS por vulnerabilidades HIGH / 1 SKIPPED (aceite agregado dependente do scanner).** Não chamar a CI de verde.

| Dimensão | Resultado | Observação |
| --- | --- | --- |
| Unidade/segurança/contratos | **146 testes PASSOU** | `validate`, inclui 6 novos testes comparativos, sem dupla contagem |
| Skill base | **23 testes PASSOU** | suíte de arquivo/skill estática no `validate` |
| MCP, identidade, revisão humana, leitura de memória e Qdrant sintéticos | **79 verificações PASSOU** | `r06_lifecycle_synthetic`, nunca memória real |
| Snapshot Qdrant nativo, checksum e restauração descartável | **8/8 PASSOU** | subconjunto dos 79 E2E, restaurou 3/3 pontos fictícios em coleção nova sem alterar origem |
| Integridade Python SHA256 | **29/29 PASSOU** | `requirements.lock`, `--require-hashes`, `--only-binary=:all:`; Linux AMD64, Python 3.12 |
| Build Docker e verificação do zlib1g exato | **PASSOU** | imagem R07 construída em GitHub runner; versão comprovada com `dpkg-query` |
| Comparação de imagem suportada Bookworm | **PASSOU como estudo, NO-GO como candidata** | 43 CVEs bloqueantes distintas e 3 CRITICAL |
| Comparação de imagem suportada Trixie | **PASSOU como estudo, NO-GO como candidata** | 23 CVEs HIGH distintas no contêiner corrigido |
| Grype da imagem final R07 | **FALHOU conforme política de segurança** | 23 CVEs HIGH / 77 combinações CVE×pacote, sem CRITICAL ou UNKNOWN no Trixie |
| Aceite agregado de CI | **PULADO / BLOQUEADO** | depende do sucesso do scanner; não é homologação |
| Host ChatGPT real/Cloudflare Access/portal Salvar real | **NÃO EXECUTADO** | fora do S9.1; exige gate próprio posterior |
| Qdrant, banco de propostas ou memórias reais | **NÃO EXECUTADO** | fora do S9.1; legado preservado |

**Rastreabilidade do scanner:** `anchore/grype` fixado no digest `sha256:013e16ae96bd64108973e3e9fecec63f7ff276358d34c46c25d33e2aac96539f`, sem tokens de produção. Relatório interno da CI discrimina pacote, CVE e versão, sem informações de clientes. Fonte oficial adicional: https://security-tracker.debian.org/tracker/ .

## 5. Mudanças exatas autorizadas na branch R07

- `scripts/r07_s9_1_compare_os.py`: gera comparação de imagens por digest e CVEs distintas, recusa relatórios incompletos/sem fonte Debian, não altera serviços.
- `tests/test_r07_s9_1_compare_os.py`: seis casos sintéticos de contagem, correções sugeridas e negativos de integridade/variante.
- `.github/workflows/r05-skill-static.yml`: matriz Bookworm/Trixie em runners temporários, digest fixado antes do build, Grype completo sem ignorar vulnerabilidades. O teste Bookworm remove o pacote Trixie-only exclusivamente no Dockerfile TEMPORÁRIO de análise; `r07_s9_os_scan` não foi afrouxado.
- `Dockerfile`: fixação explícita de `zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1` no Debian Trixie, com `apt-get` e limpeza de índice. Base Python original continua imutável.
- `.github/workflows/r05-skill-static.yml`: prova `dpkg-query` da versão efetivamente instalada da zlib antes do Grype.
- `docs/institucional/R07_S91_MATRIZ_CVES_DEBIAN_2026-11-18.md`: matriz de 24 identificadores, fontes oficiais, comparação quantitativa e lacunas de patch.
- Este relatório Markdown de conclusão; sem gravação em R06, main, GitLab, Linear, Qdrant, Cloudflare ou outros serviços.

## 6. Riscos, dependências e rollback

- **P1 — NO-GO de imagem:** 23 CVEs HIGH no contêiner corrigido; 77 ocorrências CVE×pacote. Não afirmar exposição explorável sem estudo de alcance, mas também não liberar sem remediação/decisão humana formal apropriada.
- **P1 — sem homologação real:** a candidata R07 ainda não foi testada no host definitivo com Cloudflare Access e clique humano efetivo; `human_review_enabled=false` foi reportado no legado R06, e CI sintética não prova mudança disso.
- **P1 — dados/migração:** esquema SQLite anterior e memórias Qdrant reais não foram inventariados, reconciliados ou migrados; propostas pendentes não podem virar aprovadas durante uma migração futura.
- **P2 — portabilidade:** `zlib1g` fixado por versão Debian 13 não instala em Bookworm; esta variação foi tratada somente na comparação. Hashes Python são específicos a CPython 3.12/linux-amd64.
- **P2 — atualização de feed:** CVEs e fixed versions são fotografia de 18/11/2026; exigem nova checagem antes de qualquer publicação futura.
- **Rollback:** reversão somente de commits da branch isolada R07 após nova conferência da PR/HEAD. As imagens, bancos, snapshots e scans no GitHub Actions foram descartáveis; nenhum banco ou serviço externo requer rollback deste gate.

## 7. Parecer final e próximo gate proposto — S9.2 (NÃO INICIADO)

**S9.1 NO-GO para homologação de cadeia de suprimentos, GO somente para continuidade de investigação isolada.** Preservar scanner bloqueante e PR #5 em draft. Não solicitar aprovação de deploy, merge, migração ou desligamento do legado.

**S9.2 — tratamento controlado dos 23 CVEs residuais em imagem estável.** Escopo sugerido: reconfirmar advisories oficiais e releases de segurança suportados; mapear `fixed_version` por pacote, alcance/uso no runtime de forma não exploratória, estratégias de atualização sem misturar Debian stable/unstable, e testar apenas correções comprovadas em imagens digest-fixadas dentro do GitHub Actions, com OS scan fail-closed. Reexecutar os 29 hashes de wheel, regressões MCP/identidade/Salvar memória sintético e snapshot Qdrant efêmero. Documentar decisões, contagens e bloqueios; não aplicar ignore, waiver, `--ignore-unfixed`, rebaixamento ou migração de SO não homologada.

**Critério S9.2:** se restarem CVEs HIGH/CRITICAL/UNKNOWN não tratadas por versões corrigidas suportadas, manter NO-GO e registrar dependências externas; não transformar relatório ou análise de reachability em autorização de corte.

**Exclusões S9.2:** sem merge, deploy, publicação GHCR, TestLab, GitLab, Linear, Cloudflare/DNS, Qdrant real, migração de memória ou desativação de legado. **O botão da resposta ao titular apenas solicita uma nova execução do S9.2; não aprova operações externas.**
