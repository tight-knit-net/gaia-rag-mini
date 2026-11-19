# GAIA RAG Knowledge R07 — S9.3 | Matriz completa de pacotes Debian

**Versão:** 1.0.0 — evidência de diagnóstico, sem homologação operacional.
**Emissão:** 19/11/2026 às 00:34:19 (America/Sao_Paulo, UTC−03:00).
**Origem do horário:** serviço de hora local do ChatGPT, resposta `2026-11-19T00:34:19-03:00`.
**Escopo:** inventário de pacotes OS em imagens Docker R07 de CI, dados sintéticos, nenhuma ação em ambiente real.
**Fonte primária:** [GitHub Actions run 44451858328](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451858328), job `135317490755`, marcador `R07_S93_COMPARISON`.
**PR/HEAD no momento do registro:** [#5](https://github.com/tight-knit-net/gaia-rag-mini/pull/5), `c522c599cd4927574e6409a498d9c2e2aa2de31f`, base `feat/r06-lifecycle-skill-staging`, sem merge.

## Definições e limites de classificação

- **O — observado:** pacote Debian identificado como fornecedor de biblioteca ELF carregada por amostras de módulos Python no runner (`python`, `_ssl`, `_sqlite3`, `_bz2`, `_lzma`, `_ctypes`, `zlib`); isso comprova uso nos caminhos inspecionados, não todas as dependências do produto.
- **N — não observado:** não apareceu no conjunto limitado de `ldd`/`dpkg-query`; **não** significa supérfluo, removível, não vulnerável ou desnecessário. Não há autorização para remover com essa classificação.
- A variante foi gerada apenas com `apt-get autoremove --purge`, respeitando a base Python/Debian 13 fixada por digest. Nenhum pacote foi removido; todos os 87 mantiveram a mesma versão.
- A varredura Grype abrangeu o contêiner completo sem filtros: **23 CVEs HIGH distintas, 77 ocorrências bloqueantes** em ambas as imagens; scanner principal da R07 permanece FAIL, sem supressões.

## Matriz de 87 pacotes (Debian 13 / linux-amd64)

| Nº | Pacote | Versão baseline | Versão trial | Evidência de uso | Preservado |
|---:|---|---|---|:---:|:---:|
| 1 | `adduser` | `3.152` | `3.152` | N | Sim |
| 2 | `apt` | `3.0.4` | `3.0.4` | N | Sim |
| 3 | `base-files` | `13.8+deb13u7` | `13.8+deb13u7` | N | Sim |
| 4 | `base-passwd` | `3.6.7` | `3.6.7` | N | Sim |
| 5 | `bash` | `5.2.37-2+b10` | `5.2.37-2+b10` | N | Sim |
| 6 | `bsdutils` | `1:2.41.5-0+deb13u1` | `1:2.41.5-0+deb13u1` | N | Sim |
| 7 | `ca-certificates` | `20250419+deb13u1` | `20250419+deb13u1` | N | Sim |
| 8 | `coreutils` | `9.7-3` | `9.7-3` | N | Sim |
| 9 | `dash` | `0.5.12-12` | `0.5.12-12` | N | Sim |
| 10 | `debconf` | `1.5.91` | `1.5.91` | N | Sim |
| 11 | `debian-archive-keyring` | `2025.1` | `2025.1` | N | Sim |
| 12 | `debianutils` | `5.23.2` | `5.23.2` | N | Sim |
| 13 | `diffutils` | `1:3.10-4` | `1:3.10-4` | N | Sim |
| 14 | `dpkg` | `1.22.22` | `1.22.22` | N | Sim |
| 15 | `findutils` | `4.10.0-3` | `4.10.0-3` | N | Sim |
| 16 | `gcc-14-base` | `14.2.0-19` | `14.2.0-19` | N | Sim |
| 17 | `grep` | `3.11-4` | `3.11-4` | N | Sim |
| 18 | `gzip` | `1.13-1+deb13u1` | `1.13-1+deb13u1` | N | Sim |
| 19 | `hostname` | `3.25` | `3.25` | N | Sim |
| 20 | `init-system-helpers` | `1.69~deb13u1` | `1.69~deb13u1` | N | Sim |
| 21 | `libacl1` | `2.3.2-2+b1` | `2.3.2-2+b1` | N | Sim |
| 22 | `libapt-pkg7.0` | `3.0.4` | `3.0.4` | N | Sim |
| 23 | `libattr1` | `1:2.5.2-3` | `1:2.5.2-3` | N | Sim |
| 24 | `libaudit-common` | `1:4.0.2-2+deb13u1` | `1:4.0.2-2+deb13u1` | N | Sim |
| 25 | `libaudit1` | `1:4.0.2-2+deb13u1` | `1:4.0.2-2+deb13u1` | N | Sim |
| 26 | `libblkid1` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 27 | `libbsd0` | `0.12.2-2` | `0.12.2-2` | N | Sim |
| 28 | `libbz2-1.0` | `1.0.8-6` | `1.0.8-6` | **O** | Sim |
| 29 | `libc-bin` | `2.41-12+deb13u4` | `2.41-12+deb13u4` | N | Sim |
| 30 | `libc6` | `2.41-12+deb13u4` | `2.41-12+deb13u4` | **O** | Sim |
| 31 | `libcap-ng0` | `0.8.5-4+b1` | `0.8.5-4+b1` | N | Sim |
| 32 | `libcap2` | `1:2.75-10+deb13u1+b3` | `1:2.75-10+deb13u1+b3` | N | Sim |
| 33 | `libcrypt1` | `1:4.4.38-1` | `1:4.4.38-1` | N | Sim |
| 34 | `libdb5.3t64` | `5.3.28+dfsg2-9` | `5.3.28+dfsg2-9` | N | Sim |
| 35 | `libdebconfclient0` | `0.280` | `0.280` | N | Sim |
| 36 | `libffi8` | `3.4.8-2` | `3.4.8-2` | **O** | Sim |
| 37 | `libgcc-s1` | `14.2.0-19` | `14.2.0-19` | N | Sim |
| 38 | `libgdbm6t64` | `1.24-2` | `1.24-2` | N | Sim |
| 39 | `libgmp10` | `2:6.3.0+dfsg-3` | `2:6.3.0+dfsg-3` | N | Sim |
| 40 | `libhogweed6t64` | `3.10.1-1` | `3.10.1-1` | N | Sim |
| 41 | `liblastlog2-2` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 42 | `liblz4-1` | `1.10.0-4` | `1.10.0-4` | N | Sim |
| 43 | `liblzma5` | `5.8.1-1+deb13u2` | `5.8.1-1+deb13u2` | **O** | Sim |
| 44 | `libmd0` | `1.1.0-2+b1` | `1.1.0-2+b1` | N | Sim |
| 45 | `libmount1` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 46 | `libncursesw6` | `6.5+20250216-2` | `6.5+20250216-2` | N | Sim |
| 47 | `libnettle8t64` | `3.10.1-1` | `3.10.1-1` | N | Sim |
| 48 | `libpam-modules` | `1.7.0-5` | `1.7.0-5` | N | Sim |
| 49 | `libpam-modules-bin` | `1.7.0-5` | `1.7.0-5` | N | Sim |
| 50 | `libpam-runtime` | `1.7.0-5` | `1.7.0-5` | N | Sim |
| 51 | `libpam0g` | `1.7.0-5` | `1.7.0-5` | N | Sim |
| 52 | `libpcre2-8-0` | `10.46-1~deb13u3` | `10.46-1~deb13u3` | N | Sim |
| 53 | `libreadline8t64` | `8.2-6` | `8.2-6` | N | Sim |
| 54 | `libseccomp2` | `2.6.0-2` | `2.6.0-2` | N | Sim |
| 55 | `libselinux1` | `3.8.1-1` | `3.8.1-1` | N | Sim |
| 56 | `libsemanage-common` | `3.8.1-1` | `3.8.1-1` | N | Sim |
| 57 | `libsemanage2` | `3.8.1-1` | `3.8.1-1` | N | Sim |
| 58 | `libsepol2` | `3.8.1-1` | `3.8.1-1` | N | Sim |
| 59 | `libsmartcols1` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 60 | `libsqlite3-0` | `3.46.1-7+deb13u2` | `3.46.1-7+deb13u2` | **O** | Sim |
| 61 | `libssl3t64` | `3.5.7-1~deb13u3` | `3.5.7-1~deb13u3` | **O** | Sim |
| 62 | `libstdc++6` | `14.2.0-19` | `14.2.0-19` | N | Sim |
| 63 | `libsystemd0` | `257.13-1~deb13u1` | `257.13-1~deb13u1` | N | Sim |
| 64 | `libtinfo6` | `6.5+20250216-2` | `6.5+20250216-2` | N | Sim |
| 65 | `libudev1` | `257.13-1~deb13u1` | `257.13-1~deb13u1` | N | Sim |
| 66 | `libuuid1` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 67 | `libxxhash0` | `0.8.3-2` | `0.8.3-2` | N | Sim |
| 68 | `libzstd1` | `1.5.7+dfsg-1` | `1.5.7+dfsg-1` | **O** | Sim |
| 69 | `login` | `1:4.16.0-2+really2.41.5-0+deb13u1` | `1:4.16.0-2+really2.41.5-0+deb13u1` | N | Sim |
| 70 | `login.defs` | `1:4.17.4-2` | `1:4.17.4-2` | N | Sim |
| 71 | `mawk` | `1.3.4.20250131-1` | `1.3.4.20250131-1` | N | Sim |
| 72 | `mount` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 73 | `ncurses-base` | `6.5+20250216-2` | `6.5+20250216-2` | N | Sim |
| 74 | `ncurses-bin` | `6.5+20250216-2` | `6.5+20250216-2` | N | Sim |
| 75 | `netbase` | `6.5` | `6.5` | N | Sim |
| 76 | `openssl` | `3.5.7-1~deb13u3` | `3.5.7-1~deb13u3` | N | Sim |
| 77 | `openssl-provider-legacy` | `3.5.7-1~deb13u3` | `3.5.7-1~deb13u3` | N | Sim |
| 78 | `passwd` | `1:4.17.4-2` | `1:4.17.4-2` | N | Sim |
| 79 | `perl-base` | `5.40.1-6+deb13u1` | `5.40.1-6+deb13u1` | N | Sim |
| 80 | `readline-common` | `8.2-6` | `8.2-6` | N | Sim |
| 81 | `sed` | `4.9-2+deb13u1` | `4.9-2+deb13u1` | N | Sim |
| 82 | `sqv` | `1.3.0-3+b2` | `1.3.0-3+b2` | N | Sim |
| 83 | `sysvinit-utils` | `3.14-4` | `3.14-4` | N | Sim |
| 84 | `tar` | `1.35+dfsg-3.1` | `1.35+dfsg-3.1` | N | Sim |
| 85 | `tzdata` | `2026f-0+deb13u1` | `2026f-0+deb13u1` | N | Sim |
| 86 | `util-linux` | `2.41.5-0+deb13u1` | `2.41.5-0+deb13u1` | N | Sim |
| 87 | `zlib1g` | `1:1.3.dfsg+really1.3.1-1+deb13u1` | `1:1.3.dfsg+really1.3.1-1+deb13u1` | **O** | Sim |

## Consolidação e riscos

- Total comparado: **87/87 pacotes**; **0 removidos**, **0 versões alteradas**.
- Bibliotecas observadas: **8**; outros pacotes: **79** sem evidência de vinculação nesse probe.
- CVEs bloqueantes: **23 → 23 identificadores**, **77 → 77 ocorrências**.
- **Política:** nenhum pacote classificado N pode ser excluído sem estudo independente de dependências e prova de compatibilidade; remover um pacote apenas para sumir do inventário não é waiver aceitável.
- **Fonte metodológica:** [Debian Handbook — apt-get, aptitude e auto-removal](https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.html), [Grype — scanner de imagens](https://oss.anchore.com/docs/guides/vulnerability/getting-started/).
- **Gate de segurança:** NO-GO para promoção ou implantação enquanto qualquer HIGH/CRITICAL/UNKNOWN permanecer no contêiner candidato.
