# Protocolo de revisão técnica independente — GAIA RAG Mini R05

**Status:** documentos consolidados; revisão técnica independente PENDENTE; desenvolvimento e publicação NÃO autorizados.

## Decisão de governança
Por decisão expressa do proprietário em 17/11/2026, o CodeRabbit deixa de ser requisito ou ferramenta de revisão deste projeto. O arquivo de integração `.coderabbit.yaml` foi retirado da branch R05. A revisão independente continua obrigatória, mas **sem dependência de uma GitHub App de revisão automática**.

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

## Registro de retirada da ferramenta anterior
O projeto já teve solicitações históricas de revisão automática no PR #1, sem parecer observado. Essa tentativa foi encerrada por decisão do proprietário. A revogação da **GitHub App** em nível de conta/repositório precisa ser confirmada nas instalações do GitHub; remoção do arquivo não revoga o acesso que o aplicativo eventualmente tenha. A configuração de GitHub App para outros repositórios não pode ser alterada como efeito colateral.
