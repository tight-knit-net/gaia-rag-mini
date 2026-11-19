# GAIA RAG & Knowledge — S9 | SHA256 das wheels, snapshot Qdrant nativo e scanner Debian

**Versão:** 1.0.0 — relatório técnico de gate com bloqueio explícito.
**Emissão:** 18/11/2026 às 22:26:09 (America/Sao_Paulo, UTC−03:00).
**Fonte do relógio:** serviço de hora local integrado ao ChatGPT; resposta `2026-11-18T22:26:09-03:00`.
**Repositório:** `tight-knit-net/gaia-rag-mini`.
**Branch-alvo única:** `feat/r07-office-knowledge-assimilation`; PR #5 **aberta, draft, sem merge**.
**Base somente leitura:** `feat/r06-lifecycle-skill-staging` SHA `14cca2e325b8919506c9a95b917e02ae6bf293c7`, PR #4.
**HEAD funcional auditado:** `a3993ad0a3cf5b577add9fc999fa172d1af47b4f`.
**CI:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44436559758
**Escopo:** código e testes exclusivamente na R07; pacotes públicos PyPI, scanner de CVEs público, Qdrant fictício em container efêmero do GitHub Actions. **Sem merge, deploy, publicação GHCR, TestLab, GitLab, Linear, Cloudflare, DNS, Qdrant real, memórias reais, migração ou corte de legado.**

## 1. Resultado executivo

**S9 = NO-GO para fechamento completo da cadeia de suprimentos.** Três dimensões técnicas avançaram, mas o Grype detectou **78 achados HIGH em combinações CVE×pacote**, correspondentes a **24 identificadores CVE HIGH distintos**, na imagem baseada em Debian da candidata. Não mascarar esse resultado ou desabilitar o scanner para obter CI verde.

**PASSOU parcialmente:** lock SHA256 de 29 wheels e instalação `--require-hashes --only-binary=:all:`; snapshot nativo Qdrant de 3 pontos DEMO com verificação de checksum e restauração em coleção nova; 79 verificações MCP/Qdrant sintéticas; 140 testes unitários; inventário de 87 pacotes Debian e geração efêmera de CycloneDX da imagem.

**CI completa do HEAD de código:** 14 jobs: **12 sucesso / 1 falha esperada de política de segurança / 1 aceite agregado pulado**. CI não está verde; não declarar homologação operacional.

## 2. Matriz de evidências por dimensão

| Dimensão | Status | Fonte/prova |
| --- | --- | --- |
| PR #5, ramo e permissões | CONFERIDO | HEAD `a3993ad0`, base R06 `14cca2e`; revisão antes de cada escrita |
| Hash de wheels Python | **PASSOU 29/29** | `requirements.lock` contém 29 hashes SHA256 de wheel real Linux AMD64/CPython 3.12; obtidos por download público e rechecados em runner |
| SHA256 do lock de wheels | **VERIFICADO** | `bb2aacbc1249159b1625222731a443e86b73e65fca32b056d6c4f4188efe3903` |
| Build Docker hash-only | **PASSOU** | `pip install --require-hashes --only-binary=:all:`, Python base por digest, non-root; `pip check` |
| SBOM Python (S8 atualizado) | **PASSOU** | CycloneDX 1.6 de 29 pacotes sincronizado com novo lock |
| CVEs Python PyPI | **PASSOU no feed público da data** | scanner S8 das 29 versões sem vulnerabilidade conhecida (não certifica o SO) |
| Inventário Debian | **PASSOU 87 pacotes** | `dpkg-query` em imagem do próprio CI, CycloneDX 1.6 gerado em runner descartável |
| Grype OS | **FALHOU por achados HIGH reais do scanner** | Grype v0.122.0 em imagem fixada por digest, 78 HIGH em 24 CVEs distintas; dados públicos, ver seção 3 |
| OS LOW/MEDIUM/NEGLIGIBLE | PROCESSADO | 16 LOW, 78 MEDIUM, 49 NEGLIGIBLE; 0 CRITICAL reportadas; requer classificação e acompanhamento |
| Snapshot Qdrant nativo | **PASSOU 8/8** | Qdrant `v1.15.5` descartável, snapshot `.snapshot`, bytes SHA256, `priority=snapshot`, restore em coleção nova, paridade ponto/payload/vetor, rollback preservando origem |
| Memórias DEMO | **PASSOU 3/3** | apenas pontos sintéticos `approved=true`; nenhuma proposta pendente foi promovida |
| Regressões MCP/identidade/botão | **PASSOU 79 verificações E2E** | JWT fictício, fluxo CSRF, aprovação manual simulada, readback e consultas transversais do proprietário |
| Testes unitários | **PASSOU 140 casos** | inclui 6 hashlock e 8 OS, além dos gates anteriores |
| CI agregada S9 | **NO-GO** | 12/14 jobs success; 1 security fail; 1 skipped por `needs` |
| Cloudflare Access, host real, Qdrant real, produção | **NÃO EXECUTADO** | escopo operacional excluído |

## 3. Vulnerabilidades Debian reportadas pelo scanner

**Interpretação correta:** 78 são **ocorrências CVE×pacote**, não 78 CVEs independentes. Os 24 identificadores HIGH distintos aparecem em bibliotecas e utilitários da base Debian 13. A ferramenta não demonstrou exploração concreta da aplicação, mas os achados impedem o GO de segurança no critério definido.

| Família afetada | CVEs HIGH exemplificadas |
| --- | --- |
| OpenSSL (`openssl`, `libssl3t64`, `openssl-provider-legacy`) | `CVE-2026-124709`, `CVE-2026-95692`, `CVE-2026-107496`, `CVE-2026-95691`, `CVE-2026-88823`, `CVE-2026-107493` |
| SQLite (`libsqlite3-0`) | `CVE-2026-119379`, `CVE-2026-119374`, `CVE-2026-119373` |
| libc (`libc6`, `libc-bin`) | `CVE-2026-19499`, `CVE-2026-84243`, `CVE-2026-5435` |
| util-linux e libs associadas | `CVE-2026-78408`, `CVE-2026-76642`, `CVE-2026-78410`, `CVE-2026-78409` |
| gcc/libstdc++ | `CVE-2026-95619`, `CVE-2026-102010` |
| Perl (`perl-base`) | `CVE-2026-82560`, `CVE-2026-9538` |
| ncurses / libtinfo | `CVE-2025-69720` |
| zlib | `CVE-2026-85091` |
| ACL | `CVE-2026-54369`, `CVE-2026-54370` |

Os 24 IDs acima são os 24 achados distintos reportados como HIGH. A próxima revisão deve reconciliar com avisos oficiais Debian e verificar `fixed_versions`, se existem atualizações suportadas e quais bibliotecas são realmente alcançáveis. **Não reclassificar HIGH automaticamente como sem risco.**

**Ferramenta:** `anchore/grype:v0.122.0`, imagem imutável `sha256:013e16ae96bd64108973e3e9fecec63f7ff276358d34c46c25d33e2aac96539f`. Scanner executado com filesystem raiz read-only, sem Docker socket e com a imagem candidata em arquivo tar somente leitura. A base de advisories pública e temporários foram carregados apenas no runner descartável.

**Escolha de scanner:** não foi utilizada a GitHub Action antiga do Trivy por conta de comprometimento documentado em 2026 (GHSA-69fq-xp46-6x23). Ref: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23

## 4. Modificações restritas à R07

- `requirements.lock`: 29 hashes SHA256 das wheels CPython 3.12 linux-amd64.
- `Dockerfile`: `--require-hashes --only-binary=:all:` sem resolução flutuante.
- `scripts/r07_s7_package_preflight.py`: parser e política compatíveis com lock por hashes.
- `scripts/r07_s9_wheel_lock.py` + `tests/test_r07_s9_hashlock.py`: obtém/valida em CI as mesmas wheels e rejeita divergência ou entrada sem hash.
- `docs/institucional/R07_SBOM_PYTHON_LOCK_S8.cdx.json`: reemitido com novo digest do lock.
- `tests/r06_live_review_e2e.py`: 8 verificações adicionais de snapshot Qdrant nativo em dados fictícios.
- `scripts/r07_s9_os_audit.py` + `tests/test_r07_s9_os_audit.py`: inventário Debian/CycloneDX e avaliação fail-closed de CVEs de SO.
- `.github/workflows/r05-skill-static.yml`: job `r07_s9_hash_bootstrap` validando wheels e `r07_s9_os_scan` com imagem e banco de advisories efêmeros, ambos pré-requisitos do aceite.
- `scripts/r07_candidate_acceptance.py`: acrescentados critérios de hashes, snapshot e scanner OS.

## 5. Limitações, privacidade e rollback

- O lock de wheels **é específico de Linux x86_64 com Python 3.12**; outra arquitetura exige hashes adicionais e testes de pacote separados.
- O CycloneDX de **87 pacotes Debian foi gerado somente no runner efêmero**, sem upload nem armazenamento integral no repositório nesta etapa. O relatório registra a contagem e a falha de segurança. A próxima etapa pode publicar o SBOM homologado na documentação se aprovado.
- A consulta de vulnerabilidades é fotografia do feed Grype, não prova de exploração. O scanner **não foi desabilitado** e continua falhando a CI ante achados HIGH.
- A CI de Qdrant usou contêiner e snapshot temporários; não existe backup de acervo real nem migração para homologação. Em produção, preservar a sequência candidata homologada → backup/inventário legado → migração autorizada → readback → autorização de corte.
- GitLab, Linear, Cloudflare, TestLab, Qdrant real, dados de clientes, produção e legado não foram acessados nem alterados.
- **Rollback:** reverter alterações somente na branch R07 após reconferir HEAD; o CI Docker/Qdrant era descartável. Não existe rollback de produção nesta etapa porque não houve deploy.

## 6. Parecer GO/NO-GO

**Gate S9: NO-GO técnico de supply chain** enquanto permanecerem os 24 CVEs HIGH (78 ocorrências) sem remediação/decisão de risco documentada. O pacote Python por hashes e a restauração Qdrant nativa sintética **PASSARAM**, mas o gate agregado permanece bloqueado por desenho de segurança. **NO-GO absoluto para merge, deploy, migração Qdrant ou desativação do legado.**

## 7. Próximo gate proposto — S9.1 (NÃO EXECUTADO)

**S9.1 — Remediação dos CVEs da imagem base e verificação independente.** Escopo: classificar os 24 CVEs HIGH com advisories oficiais Debian/Grype, `fixed_versions` e exposição; comparar em GitHub Actions apenas imagens-base suportadas e/ou atualizações de Debian, sempre com digest explícito; selecionar versão com redução de risco demonstrada sem alterar contratos MCP ou política de memória; reemitir lock/SBOM se necessário; rodar Grype e regressões completas; produzir matriz residual com severidade, versão corrigida, justificativa e parecer GO/NO-GO. Não aplicar supressões, `--ignore-unfixed`, filtros de severity ou waivers automáticos. Requerer aprovação específica para exceções de risco.

**Critérios de aceite S9.1:** ausência de HIGH/CRITICAL/UNKNOWN não tratados; scanner efetivo sem falha de cobertura; hashes de wheels válidos; snapshot e revisão humana sintéticos aprovados; CI do HEAD final verificada. Caso não seja possível corrigir todos os CVEs, manter NO-GO e apontar alternativas com riscos e custos.

**Exclusões S9.1:** merge, publicação, acesso a contas/serviços externos, TestLab, Cloudflare, DNS, GitLab/Linear, produção, Qdrant real, migração ou corte do legado.

**Acionamento:** somente novo pedido no chat via botão após apresentação do escopo. Botão não autoriza operação externa.
