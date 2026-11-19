# R07 S9.2 — Matriz residual das 23 CVEs HIGH reportadas pelo Grype

**Versão:** 1.0.0 — matriz de evidências do gate S9.2 (não é aceite de risco).
**Emissão aferida:** 18/11/2026 às 23:53:50, fuso America/Sao_Paulo (UTC−03:00).
**Fonte do relógio:** serviço de hora local ChatGPT, `2026-11-18T23:53:50-03:00`.
**Escopo:** somente imagem da R07, Debian 13 Trixie e avisos públicos oficiais; pesquisa e comparação em GitHub Actions, sem serviços reais.
**Branch/PR:** `feat/r07-office-knowledge-assimilation`, PR #5 em draft, base R06; HEAD de referência `84717cd9f614e03fa43159ddb787b04f65b48b51`.
**Fonte do inventário inicial:** [CI S9.1 final](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44445365216); 23 CVEs HIGH distintas/77 combinações CVE×pacote, após correção da zlib.
**Fontes primárias de verificação:** https://security-tracker.debian.org/tracker/source-package/openssl ; https://security-tracker.debian.org/tracker/source-package/sqlite3 ; https://security-tracker.debian.org/tracker/source-package/glibc ; https://security-tracker.debian.org/tracker/source-package/util-linux ; https://security-tracker.debian.org/tracker/source-package/gcc-14 ; https://security-tracker.debian.org/tracker/source-package/perl ; https://security-tracker.debian.org/tracker/source-package/ncurses ; https://security-tracker.debian.org/tracker/source-package/acl .

## 1. Matriz por identificador

| CVE | Família Debian | Estado do tracker oficial (18/11/2026) | Evidência |
|---|---|---|---|
| CVE-2026-124709 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-124709) |
| CVE-2026-107493 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-107493) |
| CVE-2026-107496 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-107496) |
| CVE-2026-95691 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-95691) |
| CVE-2026-95692 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-95692) |
| CVE-2026-88823 | OpenSSL | Trixie vulnerável; sem versão corrigida estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-88823) |
| CVE-2026-119373 | SQLite | Trixie vulnerável (no DSA); correções em releases posteriores | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-119373) |
| CVE-2026-119374 | SQLite | Trixie vulnerável (no DSA); correções em releases posteriores | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-119374) |
| CVE-2026-119379 | SQLite | Trixie vulnerável (no DSA); correções em releases posteriores | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-119379) |
| CVE-2026-19499 | glibc | Trixie vulnerável; sem correção estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-19499) |
| CVE-2026-5435 | glibc | Trixie vulnerável; sem correção estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-5435) |
| CVE-2026-84243 | glibc | Trixie vulnerável; sem correção estável comprovada | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-84243) |
| CVE-2026-76642 | util-linux | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-76642) |
| CVE-2026-78408 | util-linux | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-78408) |
| CVE-2026-78409 | util-linux | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-78409) |
| CVE-2026-78410 | util-linux | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-78410) |
| CVE-2026-102010 | GCC/libstdc++ | Trixie vulnerável; versões posteriores não autorizadas | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-102010) |
| CVE-2026-95619 | GCC/libstdc++ | Trixie vulnerável; versões posteriores não autorizadas | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-95619) |
| CVE-2026-82560 | Perl | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-82560) |
| CVE-2026-9538 | Perl | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-9538) |
| CVE-2025-69720 | ncurses | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2025-69720) |
| CVE-2026-54369 | ACL | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-54369) |
| CVE-2026-54370 | ACL | Trixie vulnerável (no DSA) | [Debian Security Tracker](https://security-tracker.debian.org/tracker/CVE-2026-54370) |

**Cobertura:** 23/23 CVEs residuais reportadas no S9.1. A severidade HIGH provém do **Grype**, enquanto "vulnerável"/"no DSA" é status do **Debian**. Um status "no DSA" não implica que a aplicação esteja segura, nem autoriza rebaixamento ou supressão no scanner.

## 2. Avaliação de patches suportados

O pacote `zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1` já foi instalado e verificado no S9.1, removendo a CVE-2026-85091; ele **não integra** as 23 linhas residuais. Nas fontes oficiais consultadas nesta rodada, **não foi comprovada versão corrigida disponível nos repositórios estáveis Trixie para estas 23 CVEs**. Algumas aparecem como corrigidas apenas em releases posteriores e não devem ser importadas para a imagem estável.

O ensaio S9.2 compara a candidata atual com um contêiner descartável da mesma imagem, sem alteração do Dockerfile rastreado, usando `apt-get update; apt-get upgrade -y --no-install-recommends` somente sobre os repositórios estáveis/segurança Trixie. O teste em GitHub Actions deve conferir inventário completo de pacotes e Grype antes/depois. A simples instalação de pacotes mais novos não equivale a remediação.

## 3. Bloqueio e próximos critérios

**NO-GO enquanto houver HIGH/CRITICAL/UNKNOWN na imagem.** Manter consulta oficial Debian, registro de `fixed_version`, scanner fail-closed, hashes das 29 wheels, segurança do botão Salvar memória e testes de snapshot Qdrant nativo exclusivamente descartáveis. Não adotar fork, versão unstable, mistura de distribuições ou waiver automático.

**Limitações:** o tracker identifica o status da distribuição e não comprova a atingibilidade da vulnerabilidade na aplicação; a investigação de exposição deve ser controlada e sem exploração. As fontes são fotografia de 18/11/2026, e as regras de gate permanecem mesmo após nova publicação de advisories.
