# GAIA RAG R05 — primeiro módulo de código (isolado)

Implementação preliminar de autorização **fail-closed** e consultas Qdrant com escopo obrigatório por cliente/processo. Cobre busca textual, listagem de processo, fonte, UUID e similares autorizados. A rota de UUID usa `POST /points/scroll` com filtro obrigatório de `has_id` + namespace + cliente + processo + aprovação, sem GET global. Capabilities montadas manualmente são rejeitadas pelo processo. Não é substituto completo do servidor e não está conectada ao runtime da DigitalOcean.

Teste sem rede e somente com dados sintéticos:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Os 35 testes unitários de backend usam `DEMO-*` e e-mails `example.invalid`; a CI também executa verificações estáticas da skill e os 7 testes de `tests/test_live_qdrant_synthetic.py` em Qdrant real, efêmero, com dois tenants DEMO. O Qdrant de produção não é consultado por esses testes. Nenhuma permissão real foi inferida. Para uso efetivo faltam a fonte confiável de grants, a associação com JWT Cloudflare validado no servidor e o mapeamento `tenant_id` dos pontos existentes. **Não ativar essas rotas em produção até resolver essas três condições.** O registro em memória das capabilities evita construção direta por argumentos MCP, mas não protege contra código Python malicioso no mesmo processo e não dispensa validação criptográfica do JWT, grants atualizados por requisição e proteção de revogação.

Detalhes: [contrato observado](../docs/projeto-executivo/CONTRATO_ORIGEM_MCP_R05.md).
