# Registro de riscos e dependências — projeto executivo R05
**Estado:** análise preventiva. Os mitigadores dependentes de runtime são tarefas futuras, não controles homologados.

| ID | Risco e impacto | Gravidade qualitativa | Mitigação/controle proposto | Status |
|---|---|---|---|---|
| RK-01 | Falha de ACL cross-tenant via UUID/fonte/similaridade com vazamento de cliente | Crítica | autorização backend por identidade, cliente e processo; testes negativos A/B | NÃO TESTADO |
| RK-02 | Proposta de memória confundida com gravação; bypass do clique humano | Crítica | máquina de estados, portal Access, recibo de clique, prova de não persistência | NÃO TESTADO |
| RK-03 | Dependência de Cloudflare Access sem verificação backend | Alta | validar JWT/identidade na origem e negar por padrão | NÃO TESTADO |
| RK-04 | Troca de embedding ou coleção afetando consistência do Qdrant | Crítica | invariantes imutáveis e exclusão de mudança vetorial do escopo | BLOQUEADO POR ESCOPO |
| RK-05 | GHCR ou workflow automático publicar imagem antes de autorização | Alta | `if: false`, remover `push` do workflow GHCR | CONTROLADO NA BRANCH |
| RK-06 | Linode compartilhada saturar com OpenWebUI/Opencode e GAIA RAG | Alta | limites de CPU/RAM, benchmark, política de capacidade e rollback | BENCHMARK PENDENTE |
| RK-07 | Código de origem em DO divergir do conteúdo no GitHub | Alta | inventário sanificado, digest, diff e fonte canônica por commit | PENDENTE |
| RK-08 | Host ChatGPT não implementar Skills over MCP | Média | piloto de capabilities; alternativa plugin ChatGPT a partir da mesma skill | PENDENTE |
| RK-09 | Ausência de revisão independente do PR específico | Alta | requerer parecer técnico independente com achados e evidência no PR | REVISÃO PENDENTE |
| RK-10 | Segredo de deploy mal gerenciado ou chave compartilhada | Alta | sem uso nesta fase; inventário e rotação antes de homologação | PENDENTE |
| RK-11 | Duplo escritor durante cutover DO/Linode | Crítica | roteamento exclusivo de escrita, ensaio em sandbox, rollback | PENDENTE |
| RK-12 | Estado `/state` ou propostas expiradas perdidas em migração | Alta | inventário de TTL, backup e teste idempotência/recuperação | PENDENTE |
| RK-13 | Prompt injection em memórias, documentos ou feedback de revisão | Alta | tratar material externo como dado não executável; revisão humana | PENDENTE |
| RK-14 | CI estático usado como prova falsa de homologação host | Alta | separar DG (projeto) de G (operação); traces reais obrigatórios | DOCUMENTADO |
| RK-15 | PR misturar documentação, skill e scripts infra antes de review | Média | índice por finalidade e revisão técnica independente; nada de merge automático | DOCUMENTADO |

## Dependências externas e decisões em aberto
- **D-01:** confirmação do contrato real e pontos de autorização da MCP Python da DO.
- **D-02:** plataforma de distribuição que o host consumidor realmente suporta (Skills over MCP versus plugin).
- **D-03:** revisão técnica independente comprovada e resolução de achados materiais.
- **D-04:** proprietário aceita o projeto executivo; só depois autoriza escrever código.
- **D-05:** definição de SLOs e recursos após benchmark de homologação na Linode.
- **D-06:** política definitiva de custo/isolamento e janela de migração.
- **D-07:** tratamento de proposal TTL, persistência /state e recuperação sem escrita concorrente.
- **D-08:** aprovação específica e futura para reabilitar workflows GHCR/deploy.

**Não preencher lacunas com suposições.** Uma decisão pendente pode estar documentada e ainda impedir código ou deploy.
