# GAIA RAG & Knowledge — Gate de aceite técnico R07 no GitHub Actions

**Versão:** 1.0.0  
**Emissão:** 18/11/2026, 20:01:33 — America/Sao_Paulo (UTC−03:00).  
**Fonte do relógio:** serviço de hora local integrado ao ChatGPT, que retornou 2026-11-18T20:01:33-03:00.  
**Repositório:** tight-knit-net/gaia-rag-mini.  
**Área exclusiva de desenvolvimento:** feat/r07-office-knowledge-assimilation, PR #5 draft, base feat/r06-lifecycle-skill-staging.  
**Escopo:** substituir a dependência do TestLab em descontinuação por CI isolada em GitHub Actions; sem merge, deploy, DNS, produção, migração de Qdrant, gravação de memórias reais, Cloudflare ou desativação do legado.

## 1. Decisão e limites

Por instrução do proprietário, o TestLab gaia-m7i foi retirado do **caminho crítico** da R07. Os relatórios e scripts do TestLab permanecem como evidência histórica e não autorizam novos acessos ou reparos naquele ambiente.

O GitHub Actions passa a ser o mecanismo de **aceite técnico da candidata**, com contêineres efêmeros, Qdrant sintético e identidade de demonstração. Isso **não substitui** homologação de um endpoint operacional com Cloudflare Access real, clique humano real, backup e readback Qdrant autorizado.

Git armazena o código; o Qdrant guarda memórias aprovadas e os ledgers de revisão guardam propostas. CI verde não significa migração nem equivalência integral das bases.

## 2. Implementação na branch R07

- `scripts/r07_candidate_acceptance.py` verifica a presença dos contratos MCP R07, rotas de aprovação e descarte humano, indisponibilidade de gravação sem habilitação explícita, ausência de ativação de Groq e bloqueio da publicação.
- `.github/workflows/r05-skill-static.yml` incorpora job `r07_candidate_acceptance` com dependências explícitas: `validate`, `staging_image_smoke`, `r06_lifecycle_synthetic`, `r07_operational_isolated`. O job só prossegue após sucesso de todos.
- Resultado de aceite é registrado no `GITHUB_STEP_SUMMARY`; sem criação de artifacts ou publicação de imagem.
- `docs/institucional/PLANO_VALIDACAO_R07.md`, `PLANO_FECHAMENTO_GAPS_E_CUTOVER_R07_2026-11-18.md` e `TOPOLOGIA.md` foram atualizados para registrar a substituição do gate sem alterar provas históricas.

## 3. Evidências

**CI implementada testada no commit:** `3c91719db417178526b313c8d5e81f397981acc5`.

**Execução GitHub Actions:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44416835853

| Job de CI | Resultado |
| --- | --- |
| validate | PASSOU |
| staging_image_smoke | PASSOU |
| r06_lifecycle_synthetic | PASSOU |
| r07_operational_isolated | PASSOU |
| r07_candidate_acceptance | PASSOU |

**Verificações adicionais do job de aceite:** 11/11 PASS. Incluem ferramentas MCP, rotas de salvar e descartar, status R07, flag conservadora de revisão, leitura pós-clique, Groq desativada, jobs presentes, sem publicação, testes e documentos obrigatórios.

Os testes de integração com Qdrant e aprovação humana usam dados fictícios e JWT de demonstração. Não acessam o Qdrant real do proprietário nem confirmam que a skill esteja automaticamente carregada em cada chat.

**Commit de atualização documental:** o HEAD final será revalidado com readback GitHub e execução da CI antes de alegar resultado consolidado.

## 4. Situação dos gates

| Gate | Status | Condição |
| --- | --- | --- |
| Código R07 em branch isolada | PASSOU nesta entrega | PR #5 permanece draft, baseada na R06 |
| Testes sintéticos unitários e E2E | PASSOU | CI efêmera |
| Gate técnico candidato GitHub Actions | PASSOU na execução documentada | 5/5 jobs e 11/11 verificações do aceite |
| Skill carregada efetivamente pelo host externo | PENDENTE | catálogo e código não provam seleção automática |
| Revisão humana autenticada em ambiente operacional | PENDENTE | exige endpoint futuro definido e autorização |
| Reconciliação completa do Qdrant e propostas legadas | PENDENTE | não copiar dados sem inventário e backup |
| Publicação/cutover/desativação do legado | BLOQUEADO | autorização independente após candidata homologada |

## 5. Riscos, rollback e próximo gate

**Riscos:** confundir CI com operação real, travar o projeto na infraestrutura descontinuada, perder propostas pendentes na migração, carregar skill apenas no repositório sem carregamento no host, ou habilitar a API externa Groq sem autorização LGPD.

**Rollback:** nenhuma alteração foi feita fora da branch R07. A PR #5 permanece draft; a imagem de CI é descartável e nada foi enviado a registry. Os sistemas R06/legado, Cloudflare, DNS, Qdrant e `main` permanecem fora da escrita deste gate.

**Próxima ação:** concluir a revisão técnica da PR #5 e definir, em decisão separada, o destino operacional permanente para validar Cloudflare Access, botão Salvar memória, backup e readback reais. A escolha futura do host não é pré-condição para encerrar este gate CI; também não pode ser suprida fingindo que o GitHub Actions oferece um endpoint de produção persistente.

**Decisão:** GO apenas para **candidata técnica validada por CI**; NO-GO para implantação operacional, migração ou desativação do legado.
