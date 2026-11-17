# Resultados de regressão R04

**Escopo:** testes locais determinísticos de estrutura, sintaxe, existência, conteúdo e integridade. Usar `python tests/test_regressao_r04.py` e `python scripts/validate_skill.py` para reproduzir. Um caso de teste é uma asserção de contrato documental, **não** a execução de uma LLM de terceiro.

Os 30 roteiros `tests/cenarios_r04.json` são entradas sintéticas com comportamento esperado e `executado_em_host=false`. Servem para homologação futura no ChatGPT Work; nunca indicam testes E2E executados.

**Bloqueios remanescentes:** (i) teste ACL com múltiplos usuários; (ii) teste de aprovação real com portal e persistência; (iii) medição de seleção e carregamento progressivo no host; (iv) revisão jurídica de cada caso concreto. Sem esses quatro gates, **não** utilizar status “homologado para produção”.
