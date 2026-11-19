# GAIA RAG & Knowledge R07 — Gate S9.3 | Minimização segura do runtime Debian

**Versão:** 1.0.0 — relatório de execução, não homologação operacional.
**Disparo exato aferido:** **19/11/2026, 00:17:45**, America/Sao_Paulo (UTC−03:00). Fonte: ferramenta de hora local ChatGPT, resposta ISO `2026-11-19T00:17:45-03:00`, consultada antes da primeira análise.
**Última execução técnica do gate anterior S9.2:** **18/11/2026, 23:59:59**, America/Sao_Paulo. Fonte: último log do ensaio GitHub Actions `44448066628`, job `135304968780`, UTC `2026-11-19T02:59:59.6226872Z`. Não confundir com a emissão do relatório S9.2 às 23:55:50.
**Última execução técnica S9.3 aferida até esta emissão:** **19/11/2026, 00:33:41**, America/Sao_Paulo. Fonte: último log GitHub Actions do job `135317490755` na execução `44451858328`, UTC `2026-11-19T03:33:41.1114601Z`.
**Emissão exata deste relatório:** **19/11/2026, 00:35:30**, America/Sao_Paulo. Fonte: ferramenta de hora local ChatGPT, ISO `2026-11-19T00:35:30-03:00`.

**Objetivo:** avaliar minimização legítima de pacotes Debian e comprovar compatibilidade do runtime GAIA RAG R07, sem remover pacotes apenas para mascarar CVEs e sem mudar infraestrutura.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Alvo único de escrita:** `feat/r07-office-knowledge-assimilation`, PR [#5](https://github.com/tight-knit-net/gaia-rag-mini/pull/5), aberta, draft, sem merge.
**Base de comparação apenas leitura:** `feat/r06-lifecycle-skill-staging`, SHA `14cca2e325b8919506c9a95b917e02ae6bf293c7`.
**Commit de código testado:** `c522c599cd4927574e6409a498d9c2e2aa2de31f`.
**HEAD observado ao criar relatório:** `6c3c8feac08716d05b725d5c9916954535ba2ad9`.
**CI completa do código:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44451858328
**Matriz detalhada de dependências:** [R07_S93_MATRIZ_DEPENDENCIAS_RUNTIME_2026-11-19.md](R07_S93_MATRIZ_DEPENDENCIAS_RUNTIME_2026-11-19.md).
**Baseline documental:** [R07_S92_RELATORIO_REMEDIACAO_DEBIAN_ESTAVEL_2026-11-18.md](R07_S92_RELATORIO_REMEDIACAO_DEBIAN_ESTAVEL_2026-11-18.md), v1.0.0.

## 1. Decisão

**S9.3 = NO-GO técnico para conclusão da segurança e NO-GO operacional para publicação, merge, deploy, migração ou corte do legado.** A comparação de minimização passou, mas o Debian APT não encontrou pacote auto-removível na candidata. Não ocorreu nenhuma eliminação verificada dos **23 CVEs HIGH distintos / 77 ocorrências CVE×pacote**. Não se alterou o `Dockerfile` principal.

**GO limitado:** prosseguir com planejamento/revisão isolada da próxima hipótese arquitetural. Este GO não é homologação de segurança, nem autorização de infraestrutura.

## 2. Método executado e fontes

1. Reconferidas PR #5, HEAD, base R06, status draft e CI antes de cada escrita; GitHub/Actions como fonte de execução, não RAG histórico.
2. Gerada **somente no runner** variante temporária do mesmo `Dockerfile` com imagem base Python 3.12 Debian Trixie fixada por digest e `apt-get update; apt-get autoremove --purge -y` antes da instalação Python. Nenhuma alteração nos 29 hashes SHA-256 das wheels ou no pacote de segurança zlib do S9.1.
3. Construídas imagem R07 original e variante temporária em Linux/AMD64; `dpkg-query` gerou inventários integrais, comparados por nome, arquitetura e versão.
4. Executada prova interna, **sem rede externa e com filesystem read-only**, importando módulos Python (`ssl`, `sqlite3`, `zlib`, `bz2`, `lzma`, `ctypes`, `cryptography`, `jwt`, `mcp`, `uvicorn`, `app.server`) e rastreando bibliotecas ELF com `ldd`/`dpkg-query`. `pip check` executado em ambas as imagens.
5. Executado teste HTTP com loopback apenas dentro da variante, `GAIA_RAG_ENABLE_REVIEW=0`, sem porta pública: `/healthz` saudável, `401` para MCP anônimo, portal de revisão, aprovação e descarte anônimos. Nenhuma memória real gravada.
6. Executada auditoria Grype **do contêiner completo**, inclusive todos os pacotes do SO, sem filtros por famílias, waivers, `--ignore-unfixed` ou rebaixamento de severidade. Comparação de conjuntos CVE e ocorrência.

**Referências metodológicas:** [Debian Administrator’s Handbook — apt-get e autoremove](https://www.debian.org/doc/manuals/debian-handbook/sect.apt-get.html); [Grype — imagem e pacotes](https://oss.anchore.com/docs/guides/vulnerability/getting-started/). A metodologia APT sozinha não comprova que todas as dependências indiretas da aplicação são dispensáveis.

## 3. Matriz consolidada do inventário

| Medida | R07 principal | S9.3 descartável | Status |
| --- | ---: | ---: | --- |
| Pacotes Debian instalados | **87** | **87** | PASSOU inventário completo |
| Pacotes removidos por APT | — | **0** | Nenhuma minimização comprovada |
| Versões Debian alteradas | — | **0** | Preservada compatibilidade de versões |
| Bibliotecas Debian observadas por ligação ELF | **8** | **8** | PASSOU escopo observado |
| Outros pacotes sem ligação observada neste probe | **79** | **79** | **NÃO comprova removibilidade** |
| CVEs HIGH distintas | **23** | **23** | **FALHOU critério de segurança** |
| Ocorrências bloqueantes HIGH/CRITICAL/UNKNOWN | **77** | **77** | **FALHOU critério de segurança** |
| Novos identificadores bloqueantes | — | **0** | Sem agravamento comprovado |
| CVEs bloqueantes resolvidas | — | **0** | Sem remediação |

**Pacotes ligados aos módulos Python testados:** `libbz2-1.0` (`1.0.8-6`), `libc6` (`2.41-12+deb13u4`), `libffi8` (`3.4.8-2`), `liblzma5` (`5.8.1-1+deb13u2`), `libsqlite3-0` (`3.46.1-7+deb13u2`), `libssl3t64` (`3.5.7-1~deb13u3`), `libzstd1` (`1.5.7+dfsg-1`), `zlib1g` (`1:1.3.dfsg+really1.3.1-1+deb13u1`).

A **matriz individual dos 87 pacotes com versões, estado de preservação e classificação de evidência O/N** foi arquivada em MD separado, a partir do resultado real `R07_S93_COMPARISON` da CI. Classe **N** não significa vulnerabilidade irrelevante nem pacote desnecessário.

## 4. Testes por dimensão — execução final do código

**GitHub Actions `44451858328`: 18 jobs, 16 SUCCESS / 1 FAILURE (Grype bloqueante, esperado) / 1 SKIPPED (aceite agregado).** Não declarar CI verde ou homologação operacional.

| Dimensão | Resultado | Limitação |
| --- | --- | --- |
| Regressão unitária | **165/165 PASSOU** | Inclui os 10 testes sintéticos S9.3; não somar novamente |
| Regressão Skill estática | **23/23 PASSOU** | Não prova carregamento da skill no host real |
| MCP, identidade, aprovação humana simulada e Qdrant descartável | **79 verificações PASSOU** | Somente dados DEMO, sem Qdrant/Cloudflare reais |
| Snapshot Qdrant nativo e restauração | **8/8 PASSOU**, incluídos nos 79 E2E | Coleção temporária e 3 pontos fictícios |
| Integridade de wheels Python | **29/29 PASSOU** | CPython 3.12/linux-amd64 |
| Testes de contratos S9.3 | **10/10 PASSOU** | Subconjunto da suíte unitária 165 |
| Runtime Python em ambas as imagens | **PASSOU** | Imports e ELF dos caminhos amostrados |
| HTTP da variante minimizada | **5/5 PASSOU** | Saúde e acesso anônimo negado; não é fluxo autenticado real |
| Grype completo no comparativo | **PASSOU a comparação**, permaneceu **NO-GO** | Mesmos 23 CVEs / 77 ocorrências |
| Scanner bloqueante da imagem principal | **FALHOU conforme política** | Nenhum HIGH/CRITICAL/UNKNOWN ignorado |
| Aceite agregado candidato | **SKIPPED/BLOQUEADO** | Dependência de scanner com falha |
| Host ChatGPT, Cloudflare Access, Salvar memória real e Qdrant real | **NÃO EXECUTADO** | Escopo externo proibido |

## 5. Alterações e evidências

- `scripts/r07_s93_minimization.py`: gera variante Dockerfile temporária (não a publica), compara dois inventários completos e todos os bloqueios Grype, gera matriz por pacote, registra libs ELF e recusa perda de dependências realmente observadas.
- `tests/test_r07_s93_minimization.py`: 10 testes sintéticos de base imutável, hash lock, zlib fixada, negação de remoção de biblioteca observada, auditoria completa e ausência de auto-GO.
- `tests/r07_s93_http_smoke.py`: 5 provas locais de saúde e autorização anônima na variante descartável.
- `.github/workflows/r05-skill-static.yml`: job `r07_s93_minimization`, obrigatório para o aceite da candidata, sempre em runner GitHub, sem publicação. Mantido também o scanner OS original como pré-requisito bloqueante.
- `docs/institucional/R07_S93_MATRIZ_DEPENDENCIAS_RUNTIME_2026-11-19.md`: inventário completo de 87 pacotes, versão e evidência de ligação ELF.
- Este relatório e atualização do índice `TOPOLOGIA.md`. **Nenhum arquivo fora da R07 alterado.**

## 6. Riscos, dependências e rollback

- **P1 — segurança:** 23 CVEs HIGH distintas/77 ocorrências permanecem, apesar de runtime funcional. Ausência de fix estável comprovado é **bloqueio**, não waiver.
- **P1 — prova incompleta de necessidade:** 8 pacotes observados são evidência positiva de ligação ELF; os 79 restantes não podem ser rotulados como desnecessários. Os imports e o smoke HTTP são verificações sintéticas, não cobrem todas as funções possíveis da aplicação.
- **P1 — homologação:** revisão humana autenticada com Cloudflare Access, botão Salvar real, Qdrant real e persistência interprocessos continuam sem validação operacional.
- **P2 — fonte de vulnerabilidades:** Grype e Debian oficiais são fotografia temporal. Atualizações dos advisories podem mudar o inventário sem alterar a imagem.
- **Rollback:** os únicos efeitos persistentes são commits dentro da branch R07; builds, variantes, Qdrant, snapshots e scanners CI são descartáveis. Reverter somente commits próprios da R07 após nova conferência de HEAD/CI; nenhum rollback externo é necessário porque produção/legado não foram alterados.

## 7. Próximo gate S9.4 — plano de arquitetura de runtime isolado (NÃO EXECUTADO)

**Escopo recomendado:** revisar independentemente a arquitetura de empacotamento do contêiner R07 e comparar **somente em GitHub Actions** uma candidata multi-stage Debian Trixie oficialmente suportada com separação de dependências de construção e runtime. Inventariar os arquivos e dependências necessários ao interpretador CPython 3.12, às 29 wheels imutáveis, à CA/TLS, SQLite, libc e revisão humana; usar somente imagens/digests oficiais e binários derivados de fontes suportadas, sem misturar releases. Medir o SBOM e Grype sem filtros, importação de todos os módulos, smoke HTTP, contratos MCP/Skilldrum, aprovação humana sintética, idempotência e snapshot Qdrant nativo descartável. Não substituir o Dockerfile principal enquanto faltar prova funcional e ausência de CVEs bloqueantes.

**Critérios de GO técnico:** runtime efetivamente funcional, integridade das 29 wheels, paridade de dados/identidade, nenhum HIGH/CRITICAL/UNKNOWN na candidata, scanner sem falhas de cobertura e CI no HEAD final. Caso persistam CVEs, manter **NO-GO** e documentar dependências de upstream; nenhum risco é automaticamente aceito.

**Exclusões S9.4:** sem merge, deploy, publicação GHCR, Cloudflare, DNS, TestLab, GitLab, Linear, Qdrant real, migração, dados de clientes ou desligamento do legado. O botão no chat é apenas uma nova solicitação, não autoriza operação externa.
