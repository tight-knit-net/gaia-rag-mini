# GAIA RAG Mini — Projeto Executivo R05
**Data:** 17/11/2026. **Estado:** pré-homologação; não há deploy R05.

## Objetivo
Evoluir a skill R04 para R05, distribuí-la pelo MCP existente/Cloudflare ou por plugin ChatGPT compatível e preparar a migração do container GAIA RAG da DigitalOcean para Akamai Linode. Preservar integralmente Qdrant Cloud, dimensão/coleção/índices, autenticação, Cloudflare Access e clique humano para persistir memória.

## AS-IS comprovado em leituras
- Container DigitalOcean gaia-qdrant-memory-gaia-qdrant-memory-candidate-1, imagem gaia-qdrant-memory:candidate-v2, Uvicorn 8000, saudável, volume local /state.
- Cloudflare: tunnel gaia-qdrant-memory-independent-20261117 saudável, hostname memory.tight-knit.net -> gaia-qdrant-memory-candidate:8000. Access: app GAIA Memory Qdrant (independente), política GAIA Memory Owner Only.
- GAIA RAG informa Qdrant Cloud configurado, coleção chatgpt_memoria_aprovada; aprovação humana obrigatória pelo portal Access. Namespace chatgpt não significa ACL por cliente.
- Linodes candidatos 8GB/4vCPU: nestground-ai (Miami, 138GB disco livre, 5,6GB RAM disponível), gogetterhub-nyc-vm (Nova York, 42GB disco livre, 6,2GB RAM disponível). Valores transitórios.
- GitHub privado tight-knit-net/gaia-rag-mini: originalmente README inicial, sem fonte completa do runtime demonstrada.

## Entregas R05
1. Skill única versionada em skills/gaia-rag-processos-administrativos/ com módulos e templates derivados da R04.
2. Arquitetura de referência, ADR de distribuição, plano de migração, rollback e matriz de homologação.
3. CI de parsing e regressão estática, sem acesso a segredos ou serviço real.
4. Testes reais de host, ACL, portal e rollback apenas após gates de segurança.

## Regra de proteção
Nenhum commit desta branch autoriza deploy, mutação do Qdrant, mudança de túnel/DNS, alteração Access ou persistência sem clique humano. Outros trabalhos poderão continuar na main; R05 será entregue em PR de rascunho e sem merge automático.

Fonte R04: https://drive.google.com/drive/folders/1UVHd6Vz0FaI7QLVcZCNbVOyy5b6WcQ2-
R03.1 preservada: https://drive.google.com/drive/folders/15X-POHeZGrzQlY8ZeJYxgrW0eJYvZmMf
