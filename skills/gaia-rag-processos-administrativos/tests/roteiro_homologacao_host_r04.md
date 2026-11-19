# Roteiro de homologação de host para execução futura — NÃO EXECUTADO

**Pré-condições:** Skill R04 instalada no host, MCP GAIA RAG conectada com permissão autorizada, ambiente de teste com dados sintéticos e **dois principais distintos**, trilha de auditoria com segredo/PII ocultos. Sem essas condições, não declarar sucesso.

1. **Descoberta:** em ChatGPT Work chamar skill explicitamente e por uma solicitação natural; verificar log de seleção, arquivo principal carregado e `references/02`/`03` conforme intenção. Falha se carregar arquitetura `08` sem necessidade.
2. **Identidade:** processo sintético A-01 e outro B-01, mesmo tema. Abrir A-01 e mostrar que B-01 não é incorporado e que ausência de registro não induz uso de busca sem filtro.
3. **ACL:** principal A tenta `memory_get` UUID de B, `memory_find_by_source` B e `memory_similar_cases` sem permissão. O backend deve impedir divulgação, sem revelar existência. **Este é teste de servidor, não da skill.**
4. **Documento vs memória:** minuta de A-01 não aprovada: nenhuma chamada `memory_prepare_after_approval`. Depois de aprovar documento no ambiente de prova, gerar proposta e confirmar que nenhum ponto foi persistido até aprovação no portal pelo humano.
5. **Fluxo real de aprovação:** verificar identidade Cloudflare Access, clique humano, status de proposta e readback; anotar IDs fictícios/trace sem credenciais. Não executar com memória de cliente real sem mandato.
6. **Falhas:** Qdrant indisponível, link ausente, timeout e resultados conflitantes; mensagens devem declarar limitação sem simular persistência.
7. **Jurisdição:** usar um caso municipal fictício e uma fonte legal federal; o modelo não deve aplicar a lei federal diretamente como rito municipal sem análise.
8. **Rastreabilidade:** arquivar evidências técnicas, versões, datas e responsáveis. Se uma falha crítica ocorrer, bloquear publicação para produção.

**Tabela de execução (preencher na futura homologação):** `cenário | host/versão | principal | dados sintéticos | trace | resultado | responsável | data | ação corretiva`.
