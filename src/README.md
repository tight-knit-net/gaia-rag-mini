# GAIA RAG R05 — primeiro módulo de código (isolado)

Implementação preliminar de autorização **fail-closed** e consultas Qdrant com escopo obrigatório por cliente/processo. Não é substituto completo do servidor e não está conectada ao runtime da DigitalOcean.

Teste sem rede e somente com dados sintéticos:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

As permissões dos testes usam `DEMO-*` e e-mails `example.invalid`. Nenhuma permissão real foi inferida. Para uso efetivo faltam a fonte confiável de grants, a associação com JWT Cloudflare validado no servidor e o mapeamento `tenant_id` dos pontos existentes. **Não ativar essas rotas em produção até resolver essas três condições.**

Detalhes: [contrato observado](../docs/projeto-executivo/CONTRATO_ORIGEM_MCP_R05.md).
