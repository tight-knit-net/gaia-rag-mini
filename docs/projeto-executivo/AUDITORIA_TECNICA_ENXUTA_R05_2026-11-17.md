# Auditoria técnica enxuta — GAIA RAG Mini R05
**Data:** 17/11/2026 (revisão documental).
**Revisor:** ChatGPT, **independente do CodeRabbit**, mas não independente da autoria dos documentos; não é auditoria externa nem certificação.
**Objeto:** repositório tight-knit-net/gaia-rag-mini, PR #1, branch docs/r05-gaia-rag-homologacao. Não acessa produção.
**Veredito:** **DOCUMENTAÇÃO APTA PARA ORIENTAR A PRÓXIMA ETAPA AUTORIZADA**, com riscos de runtime ainda abertos. Sem liberação implícita de código, merge ou deploy.

## Verificações e medidas aplicadas
| ID | Constatação fundamentada | Ação | Situação |
|---|---|---|---|
| A-01 | Ferramenta CodeRabbit havia sido reintegrada, mas o proprietário a desinstalou e pediu exclusão definitiva do projeto | Excluir .coderabbit.yaml, retirar dependência do workflow de validação e do CODEOWNERS; atualizar índice, protocolo e PR | CORRIGIDO NA BRANCH |
| A-02 | SKILL.md R05 admitia consultar memory_get / memory_find_by_source e validar process_id após o retorno, o que não substitui ACL no backend | Instruções R05 mudadas para **não chamar rotas sem escopo demonstrado** para dados multi-cliente; manter o teste de ACL do backend como pendência real | CORRIGIDO DOCUMENTALMENTE; RUNTIME NÃO TESTADO |
| A-03 | A documentação tratava parecer externo como obrigatório até para iniciar planejamento de um projeto pequeno | Gate DG-03 passa a registrar a autoauditoria rastreável; não exige bot ou terceiro; autorização de código e de deploy continuam decisões separadas | GOVERNANÇA SIMPLIFICADA |
| A-04 | O uso de Skills over MCP, ou de plugin com MCP, ainda é uma decisão condicionada ao host | Manter ADR de alternativas, sem obrigar implementar as duas nem inventar dependências | PENDÊNCIA TÉCNICA FUTURA |
| A-05 | Workflows GHCR e Linode, presentes apenas na branch, preservam bloqueio explícito de jobs; CI estática não é execução operacional | Manter os jobs bloqueados, sem alteração de segredos/infra; conferir no CI do HEAD | PENDENTE DE CONFIRMAÇÃO FINAL DO HEAD |

## Pontos essenciais ainda sem prova operacional
1. **ACL real:** autorização de identidade, cliente e processo no backend ANTES de pesquisar/retornar dados, inclusive acesso por UUID, fonte e similaridade. Nenhuma informação real de cliente pode aparecer nos testes.
2. **Aprovação humana:** proposta de memória não é escrita. A persistência exige clique autenticado no portal, idempotência e readback.
3. **Integração efetiva:** determinar se o host suporta Skills over MCP ou plugin, testar somente a alternativa real.
4. **Infra futura:** se ocorrer migração ou deploy, validar isolamento, credenciais, capacidade e rollback sem interferir na DigitalOcean existente.

## Fronteira da auditoria
A inspeção foi documental e dos arquivos versionados. Os testes de regressão R05 são estáticos; execução de Docker, Cloudflare Access, Qdrant Cloud, porta do portal, MCP real e rollback **não ocorreu nesta etapa**. A desinstalação da GitHub App foi informada pelo proprietário; o acesso do aplicativo à conta não é diretamente verificável por esta revisão.

## Recomendação executiva — mínimo viável
Continuar com escopo reduzido: (1) obter fonte/contrato do runtime da DO de forma somente leitura; (2) desenhar ou corrigir ACL server-side; (3) validar proposta e aprovação humana com fixtures; (4) escolher e provar uma forma de carregar a skill. Não fazer implantação, mudança de Qdrant, merge ou build como consequência automática desta auditoria.

**Conclusão:** retirar burocracia não significa afrouxar os controles que impedem mistura de clientes e gravação indevida. A documentação está pronta para continuidade quando o proprietário definir/autorizar o próximo escopo de implementação.
