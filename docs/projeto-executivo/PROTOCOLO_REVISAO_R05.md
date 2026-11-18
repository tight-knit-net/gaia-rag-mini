# Protocolo de revisão técnica independente — GAIA RAG Mini R05

**Status:** documentos consolidados; revisão técnica independente PENDENTE; desenvolvimento e publicação NÃO autorizados.

## Decisão de governança
Após a retirada anterior, o proprietário solicitou expressamente a **reintegração do CodeRabbit**. O arquivo `.coderabbit.yaml` foi restaurado na branch R05 para revisão automática e manual do PR. O parecer do bot é **consultivo e não canônico**: cada observação será verificada de forma independente contra o código, a arquitetura e a documentação técnica. A revisão independente permanece como gate obrigatório até decisão explícita de governança.

## Escopo da revisão humana/independente
1. Consistência entre o AS-IS observado na DigitalOcean, o TO-BE da Linode e a topologia Cloudflare Access/Tunnel/Qdrant Cloud.
2. Autorização por identidade verificada e `process_id` em todas as leituras, incluindo UUID, fonte e similaridade. Não assumir isolamento por namespace.
3. Separação dos estados de aprovação documental, proposta, clique humano no portal, persistência e readback.
4. Contratos da MCP e capacidade real do host em receber Skills over MCP ou plugin ChatGPT; não supor ativação automática.
5. Rastreabilidade RF/RNF → backlog → plano de testes → gates DG/G.
6. Ausência de upload de artefatos e congelamento de publicação e deploy nos workflows (GHCR/Linode desabilitados por `if: false`).
7. Proveniência e preservação integral de R04/R03.1; nenhuma mudança em Qdrant/Access/Cloudflare.
8. Custos, limites e riscos de concorrência de cargas na Linode; rollback descrito sem falsa declaração de teste.

## Parecer exigido
O revisor deve identificar a versão/commit, os arquivos/linhas analisados, os achados materiais (com severidade, evidência e recomendação), itens inconclusivos e conclusão **APROVADO DOCUMENTALMENTE**, **AJUSTES SOLICITADOS** ou **BLOQUEADO**. Registrar o parecer no próprio PR, ou em documento versionado e assinado pelo responsável.

A ausência de observações não significa aprovação. Nenhum comentário externo é canônico: toda sugestão deve ser confrontada com a arquitetura verificada, contrato de segurança e fonte oficial antes de correção.

## Gate DG-03 e decisões separadas
- DG-03: **PENDENTE** até existir parecer independente verificável e tratamento dos pontos materiais.
- DG-04: aceite da arquitetura pelo responsável, separado da conclusão de revisão.
- DG-06: autorização expressa para começar a escrever código, nunca inferida do aceite do projeto.
- Publicação, GHCR, container, Linode, Cloudflare, Qdrant, merge e mudanças de segurança permanecem proibidos sem autorização específica posterior.

## Reintegração e evidência de autorização
O usuário relatou ter concedido novas autorizações no GitHub e pediu reativar o CodeRabbit. O vínculo efetivo da GitHub App ao repositório **não pode ser concluído pela existência do `.coderabbit.yaml`** e deve ser comprovado por resposta do bot ou por registro autenticado de instalação. O pedido `@coderabbitai full review` somente solicita revisão; sem comentário/check/review do bot, o status é **PENDENTE**, nunca aprovado. Os pedidos antigos cancelados permanecem no histórico do PR.
