# R07 S9.1 — Matriz independente de 24 CVEs HIGH do S9

**Versão:** 1.0.0.
**Emissão:** 18/11/2026, 23:28:36, America/Sao_Paulo (UTC-03:00).
**Origem do relógio:** serviço de hora local do ChatGPT, ISO `2026-11-18T23:28:36-03:00`.
**Escopo:** investigação de 24 identificadores da varredura Grype S9 do contêiner R07, usando avisos oficiais públicos do Debian. Nenhuma operação de infraestrutura ou memória executada.
**Repositório/PR:** tight-knit-net/gaia-rag-mini PR #5 draft, branch feat/r07-office-knowledge-assimilation, base R06, HEAD de referência `0532cfb9d3942738e10c08c080205bb3d8ab18ee`.
**Fonte scanner:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44437213042 e relatório S9 em docs/institucional.

## 1. Matriz de CVEs rastreadas

| CVE / Debian tracker | Pacote de origem | Bookworm | Trixie | Tratamento / observação |
|---|---|---|---|---|
| [CVE-2026-124709](https://security-tracker.debian.org/tracker/CVE-2026-124709) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-95692](https://security-tracker.debian.org/tracker/CVE-2026-95692) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-107496](https://security-tracker.debian.org/tracker/CVE-2026-107496) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-95691](https://security-tracker.debian.org/tracker/CVE-2026-95691) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-88823](https://security-tracker.debian.org/tracker/CVE-2026-88823) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-107493](https://security-tracker.debian.org/tracker/CVE-2026-107493) | OpenSSL | Vulnerável | Vulnerável | Sem correção indicada na versão Debian estável consultada |
| [CVE-2026-119379](https://security-tracker.debian.org/tracker/CVE-2026-119379) | SQLite | Vulnerável | Vulnerável | Corrigido somente em ramo não estável do Debian |
| [CVE-2026-119374](https://security-tracker.debian.org/tracker/CVE-2026-119374) | SQLite | Vulnerável | Vulnerável | Corrigido somente em ramo não estável do Debian |
| [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373) | SQLite | Vulnerável | Vulnerável | Corrigido somente em ramo não estável do Debian |
| [CVE-2026-19499](https://security-tracker.debian.org/tracker/CVE-2026-19499) | glibc | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2026-84243](https://security-tracker.debian.org/tracker/CVE-2026-84243) | glibc | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2026-5435](https://security-tracker.debian.org/tracker/CVE-2026-5435) | glibc | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408) | util-linux | Não afetado (código ausente) | Vulnerável | A troca para Bookworm eliminaria estes casos, mas piora o risco global |
| [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642) | util-linux | Não afetado (código ausente) | Vulnerável | A troca para Bookworm eliminaria estes casos, mas piora o risco global |
| [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409) | util-linux | Não afetado (código ausente) | Vulnerável | A troca para Bookworm eliminaria estes casos, mas piora o risco global |
| [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410) | util-linux | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2026-95619](https://security-tracker.debian.org/tracker/CVE-2026-95619) | GCC/libstdc++ | Vulnerável | Vulnerável | Fixes em versões fora das duas variantes estáveis |
| [CVE-2026-102010](https://security-tracker.debian.org/tracker/CVE-2026-102010) | GCC/libstdc++ | Vulnerável | Vulnerável | Fixes em versões fora das duas variantes estáveis |
| [CVE-2026-82560](https://security-tracker.debian.org/tracker/CVE-2026-82560) | Perl | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538) | Perl | Vulnerável | Vulnerável | Sem patch estável demonstrado |
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720) | ncurses | Vulnerável | Vulnerável | Fix somente em versão posterior; revisão de alcance pendente |
| [CVE-2026-85091](https://security-tracker.debian.org/tracker/CVE-2026-85091) | zlib | Vulnerável | Vulnerável na imagem anterior; pacote de segurança disponível | trixie-security: 1:1.3.dfsg+really1.3.1-1+deb13u1 |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369) | ACL | Vulnerável | Vulnerável | Fix em ramo posterior, não estável |
| [CVE-2026-54370](https://security-tracker.debian.org/tracker/CVE-2026-54370) | ACL | Vulnerável | Vulnerável | Fix em ramo posterior, não estável |

**Contagem:** 24 CVEs distintas, agrupadas por pacote de origem. Os 78 achados HIGH do Grype original são **ocorrências CVE×pacote**, não CVEs distintas. Este documento não declara quantos se tornaram alcançáveis pela aplicação nem os remove da política de bloqueio.

## 2. Comparação em CI / distros oficiais

Imagens Python 3.12 slim-bookworm e slim-trixie são variantes oficiais suportadas pelo catálogo Docker de Python. Resolver o nome da variante para digest SHA-256 imutável antes do build. Examinar **contêiner R07 completo** instalado com 29 wheels hash-locked, não comparar apenas páginas Debian.

O resultado de comparação da CI inicial S9.1, execução https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44444037152, é:

| Candidato | Digest base | Bloqueios CVE×pacote | CVEs distintas bloqueantes | Criticidade adicional | Decisão |
| --- | --- | ---: | ---: | --- | --- |
| slim-trixie | `sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` | 78 HIGH | 24 | 0 CRITICAL/UNKNOWN | Baseline atual; não homologado |
| slim-bookworm | `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` | 124 bloqueantes | 43 | 3 CRITICAL + 24 UNKNOWN | Não recomendado: piora comparativa |

O Bookworm mostra três CVEs util-linux não afetadas, mas mais CVEs novas na base (43 vs 24). Não selecionar por redução pontual de uma família e ignorar o risco total.

## 3. Remediação candidata restrita

Apenas **zlib** tem patch Debian security `zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1` confirmado pelo tracker. Testar apt install da versão exata na **R07/Trixie** e reexecutar Grype sem supressão. Não instalar a versão Debian 13 no Bookworm: a distribuição Debian 12 não a possui. Não recorrer a pacotes unstable/Forky/Sid em imagem Trixie para mascarar CVEs.

Para OpenSSL/SQLite/glibc/Perl/ACL/GCC/ncurses e parte de util-linux, o tracker não apresenta correção estável demonstrada em 18/11/2026. **NO-GO permanece**, a menos que nova fonte oficial com pacote estável fixo e CI demonstrem remediação. Ausência de fix não significa risco aceito. Analise de reachability e eventual aprovação documental do risco pertencem a gate separado.

## 4. Limitações e proibições

- Esta matriz classifica a **versão da distribuição** no tracker, não certifica aplicação nem escolhe prioridade de exploração.
- Scanner Grype ainda deve bloquear **todo** HIGH/CRITICAL/UNKNOWN; sem supressões, ignorar não corrigidos nem waivers automáticos.
- Host real, botão Salvar real, Qdrant real e migração não examinados nesta frente.
- Não alterar R06, main, GitLab, Linear, Cloudflare, DNS, produção, legado ou memórias. Não executar deploy, publicação ou merge.
