# Protocolo de revisão do projeto executivo R05
**Estado:** revisão solicitável; não aprova automaticamente código nem publicação.

## Escopo do parecer exigido
1. **Arquitetura:** Cloudflare Access/Tunnel e MCP Python atuais separados de agentes Cloudflare Think não confirmados; estratégias de skill por extensão MCP e plugin, com suporte de host verificado.
2. **Segurança:** autorização por identidade de origem, tenant e process_id em TODAS as ferramentas de leitura; proibição de side effects sem clique humano; logs mínimos e anti-prompt-injection.
3. **Controle de mudança:** documentação só em branch/PR; `main` não sofre merge; os workflows de GHCR e Linode foram explicitamente desabilitados por `if: false`.
4. **Dados:** coleção `chatgpt_memoria_aprovada` e schema preservados; nenhuma migração de vetor ou índice.
5. **Qualidade:** rastreabilidade RF/RNF → backlog → matriz de testes; reconhecimento de evidências reais x simuladas.
6. **Runbooks:** preflight, deploy/rollback apenas documentados, sem executar; avaliação de capacidade Linode concorrente.
7. **Riscos de infraestrutura:** credenciais de deploy provisionadas anteriormente devem ter inventário, validação de origem/rotação futura e não serem exibidas em PR.
8. **Prontidão para codificar:** DG-01..DG-06, com autorização formal independente da aprovação de revisão.

## Critérios para parecer
- **APROVADO DOCUMENTALMENTE:** sem bloqueadores críticos, decisões explícitas, requisitos rastreáveis e eventos observados sustentados por evidência.
- **AJUSTES SOLICITADOS:** comentários acionáveis com arquivo, linha, risco, proposta de correção e teste/verificação.
- **BLOQUEADO:** review não executado, CodeRabbit não respondeu, segredo exposto, autenticação enfraquecida, capacidade não demonstrada tratada como fato, publicação/deploy habilitados sem autorização.
- **NÃO AVALIADO:** ausência de evidência. Nunca equiparar à aprovação.

## Submissão e conferência
- PR: https://github.com/tight-knit-net/gaia-rag-mini/pull/1
- Manual CodeRabbit: comentar `@coderabbitai full review` no PR; a emissão do comentário apenas **solicita** a revisão.
- Checar PR reviews, conversação, comentários inline, status checks e eventual review bot. Registrar autor, data, link, conclusão e achados.
- Não converter feedback do bot em merge automático; qualquer correção fica na branch de documentos e será reavaliada.
- Se não houver revisão observável, registrar `REVISÃO NÃO COMPROVADA` e não declarar DG-03 aprovado.
- Não aceitar revisão executada em outro repositório/PR como evidência deste pacote.

## Formulário de decisão (preenchimento após recebimento dos pareceres)
| Campo | Estado atual |
|---|---|
| Código e documentação revisados | Aguardando parecer |
| CodeRabbit no PR #1 | A verificar após solicitação |
| Achados críticos pendentes | Não avaliados |
| DG-03 (revisão) | BLOQUEADO até evidência real |
| Autoridade de aceite do projeto | A definir |
| Autorização para iniciar código | NÃO CONCEDIDA |
| Autorização para build/publish/deploy | NÃO CONCEDIDA |

## Regras de segurança do pedido de review
Não usar comandos CodeRabbit de autofix, merge, aprovação automática, workflow_dispatch, publicação de pacote, instalação na Linode ou transferência de secrets. Solicitar **somente análise**.
