# Relatório de inspeção R05 — 17/11/2026


> **Atualização de governança (17/11/2026):** a referência histórica ao CodeRabbit abaixo descreve tentativas anteriores, já canceladas. A ferramenta foi retirada da configuração R05 a pedido do proprietário; a revisão atual será independente, conforme `PROTOCOLO_REVISAO_R05.md`. Nenhum registro histórico constitui requisito ativo.
**Tipo:** inspeção de conectores e hosts; nenhuma migração ou escrita de memória.

## Observações técnicas
- GitHub: repositório privado `tight-knit-net/gaia-rag-mini`, `main` inicialmente com README e `docs/r05-gaia-rag-homologacao` criada para trabalho paralelo. Sem código-fonte completo de produção comprovado neste repositório.
- DigitalOcean: contêiner `gaia-qdrant-memory-gaia-qdrant-memory-candidate-1` usando `gaia-qdrant-memory:candidate-v2`, Uvicorn na porta 8000, healthy, volume Docker mapeado em `/state`, restart unless-stopped. Cloudflared em contêiner separado.
- Cloudflare: túnel `gaia-qdrant-memory-independent-20261117` healthy; ingress `memory.tight-knit.net` ao serviço `gaia-qdrant-memory-candidate:8000`; aplicação Access `GAIA Memory Qdrant (independente)`, tipo MCP; política `GAIA Memory Owner Only` (allow).
- GAIA RAG: `memory_status` confirmou coleção `chatgpt_memoria_aprovada` e enforcement de aprovação; `memory_policy` declara bloqueio de escrita sem portal HTTPS, identidade Access e clique humano; propostas têm TTL informado de 14 dias.
- Akamai: conta `akamai-william` possui Linodes `nestground-ai` (8GB), `gaia-nat-mia-01` (1GB), `Ana` (1GB); `akamai-gogetterhub` possui `gogetterhub-nyc-vm` (8GB).
- Inventário pontual: `nestground-ai` ~5,6GB RAM disponível, ~138GB de disco livre e quatro containers; `gogetterhub-nyc-vm` ~6,2GB RAM disponível, ~42GB disco livre e múltiplos serviços GAIA. A primeira é preferência provisória por espaço e menor colocalização.
- CodeRabbit: ausência de `.coderabbit.yaml` observada no repositório inicial. Isso não verifica nem refuta instalação da GitHub App. Gate de integração/revisão pendente.

## Pendências objetivas
Código e digest reais do runtime e topologia de compose/portal; ACL backend; embedding exato; capacidade de host para R05; negociação de Skills over MCP; plugin compatível; CodeRabbit App; testes reais sintéticos e rollback.

## Interpretação
Health do container e túnel é somente verificação de processo, não comprovação de isolamento, de aprovação do portal ou de carregamento da skill no ChatGPT.
