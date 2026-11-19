# R07 — Plano de testes e gates

Os testes são sintéticos offline, sem dados reais, sem escrita Qdrant, sem deploy.

| Cenário | Evidência esperada |
|---|---|
| Nova candidata | persisted=false; requer duas aprovações |
| Síntese duplicada | não preparar gravação |
| Mesma fonte, redação diferente | revisão candidata; original intacto |
| ID anterior do processo exato | vínculo válido, sem revogação |
| Outro processo/sem aprovação | rejeitado na comparação |
| Simulação e alegação | não se converter em precedente/fato |
| Mesmo título | mera relação, não superação |
| Histórico paginado | cobertura parcial sinalizada |
| Falta de fonte | rejeição da prévia |
| OCR/PDF futuro | não validar sem origem e revisão |

G1 — topologia, escopo e privacidade conferidos.
G2 — validação de skill, testes offline R05/R06 e R07, build local, CI.
G3 — revisão da PR R07 contra a branch R06, sem mudanças em identidade, gravação, rede ou Access.
G4 — definir e homologar posteriormente política efetiva de supersessão/revogação e índice de estado vigente.
G5 — merge controlado R07 -> R06, somente após aprovação.
G6 — integração main e deploy em processo próprio, com evidências e rollback. Não executar neste escopo.

O Gate de revisão humana existente na R06 permanece obrigatório.

## Atualização de governança — 18/11/2026: GitHub Actions como único laboratório de candidata

Por determinação do proprietário, o antigo TestLab `gaia-m7i` deixou de ser requisito de avanço da R07. Registros anteriores do TestLab permanecem no repositório como **evidência histórica**, não gates ativos. Não realizar SSH, configuração, instalação, manutenção ou deploy nele por esta frente.

A homologação técnica candidata passa a exigir, no **HEAD exato** da PR #5, cinco jobs:
1. `validate` — skill, estrutura, testes unitários e congelamento de deploy.
2. `staging_image_smoke` — contêiner descartável e Qdrant sintético.
3. `r06_lifecycle_synthetic` — contrato MCP, identidade simulada, botão, revisão, Qdrant de demonstração e readback.
4. `r07_operational_isolated` — runtime R07 sem rede, portas públicas ou credenciais, com negativas HTTP.
5. `r07_candidate_acceptance` — executado **somente após sucesso dos quatro anteriores**; confere contratos e ausência de habilitação de produção e publica recibo em GitHub Actions Job Summary.

Status `CI_CANDIDATE_PASS` significa **aptidão para revisão técnica e preparação de implantação futura**, não homologação operacional real. A integração com Cloudflare Access, acesso ao Qdrant real, backup/restauração, migração de propostas, ativação do botão para o proprietário, migração/cutover e desligamento do legado dependem de ambiente operacional futuro identificado, autorização específica e readback.

**A PR #5 permanece draft, sem merge ou deploy automático.** A próxima etapa não deve solicitar o antigo TestLab como pré-condição.

## Gate de compatibilidade Skilldrum → R07 (18/11/2026)

**ESCOPO:** incorporar somente o contrato de seleção e leitura progressiva de módulos de uma skill já instalada. Não copiar o motor Skilldrum, alterar GRC/GitLab, adicionar autorização por cliente ou ativar memória automática.

**Implementação isolada:** `src/gaia_rag_r05/skill_router.py`, ferramentas MCP `gaia_skill_route` e `gaia_skill_route_read` no `app/server.py`, testes `tests/test_r07_skill_router.py` e 10 verificações MCP em `tests/r06_live_review_e2e.py`.

**Missões reconhecidas:** `process_context`, `memory_search`, `memory_assimilation`, `memory_proposal`, `administrative_document`, `evidence_governance`, `skill_maintenance`. Missão desconhecida retorna `NO_ROUTE`. Módulos são selecionados por uma tabela fixa: nenhum caminho ou regra arbitrária é executado.

**Compatibilidade:** plano vinculado a `namespace`, `process_id`, arquivos e hashes; leitura somente de módulos selecionados com validação SHA-256, offsets progressivos e negativa de symlinks/caminhos inválidos. `process_id` é contexto, não ACL por cliente. A autorização continua exclusivamente no servidor pelo proprietário autenticado. O host deve efetuar o carregamento: leitura MCP não prova ativação automática da skill.

**Evidências:** GitHub Actions [execução 44419478201](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44419478201): 6/6 jobs aprovados; suite do roteador 14/14 testes unitários; integração MCP 10/10 verificações positivas/negativas. A suíte R06/R07 completa terminou com 59 verificações, inclusive aprovação humana sintética, Qdrant de demonstração e ausência de escrita pelo roteador.

**Fonte comparada:** Skilldrum GitLab `gaia_workspace1/gaia-mcp-100-update`, branch `work/gaia-skilldrum-isolado-20261113`, HEAD observado `1017fc9a9ca3e65388f07d067d5f241a7910e7ec`; AMP09 9 PASS/3 FAIL e AMP10 24 PASS/0 FAIL de protótipo *offline*, não código homologado do GRC. O contrato foi reimplementado em escopo reduzido, não copiado para a R07.

**STATUS:** PASS da compatibilidade do núcleo por CI; PENDENTE de host real e publicação da R07. PR #5 permanece draft, sem merge, deploy, chamada Groq, migração de Qdrant ou alteração da R06 e do legado.
