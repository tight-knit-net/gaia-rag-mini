# 08 — Arquitetura técnica (sob demanda, NÃO operacional)

**Ler somente quando a solicitação for técnica:** revisão de topologia, embeddings, índice, migração ou instalação. Não carregar no fluxo cotidiano de processos.

## Sistema atual auditado em 17/11/2026

ChatGPT/GAIA RAG MCP → autenticação e aplicação existente publicada via Cloudflare Access/Tunnel → serviço Docker/Uvicorn → Qdrant Cloud. O Qdrant é o repositório de memórias aprovadas. A auditoria R02 observou coleção `chatgpt_memoria_aprovada`, vetores de **384 dimensões**, distância **Cosine** e um ponto fictício de teste; não demonstrou acervo real de processos. Modelo de embedding não foi identificado na auditoria. Snapshot temporal, não garantia permanente.

## Arquiteturas propostas nos documentos-fonte, não implantadas por esta skill

- Relatório híbrido R01: possível benchmarking Qwen3/BGE-M3/E5, Workers AI, AI Gateway, BM25, RRF, reindexação controlada. Proposta com riscos/etapas futuras, sem migração.
- Arquitetura R02: alternativa Cloudflare Workers Free com busca documental keyword-only/AI Search e pontos Qdrant sem vetor. Contradiz o modelo vetorial observado da MCP atual e é tratada como **projeto alternativo**, não estado real.
- Quatro skills R02 (`gaia-contexto`, `gaia-memoria`, `gaia-pesquisa`, `gaia-processos`): utilizadas como fontes conceituais, consolidadas nesta skill **única**, não instaladas separadamente.

## O que pode ser otimizado sem tocar na MCP

1. Sínteses atômicas por processo e fonte.
2. Título com assunto e jurisdição para recuperar por similaridade.
3. `process_id` estável e idêntico em todos os eventos do mesmo processo.
4. Evitar duplicatas, dados excessivos e normas sem data de verificação.
5. Consultar por ID exato antes de pedir casos similares.
6. Distinguir memória de documento e seguir aprovação humana.

## O que NÃO é possível garantir pela skill

- Criar partições físicas, namespaces por assunto, índices de payload, políticas multitenant, vetores/embeddings ou novos campos persistidos.
- Alterar roteamento de buscas no backend ou forçar política de deduplicação transacional.
- Auto-injeção de instruções pela coleção do Qdrant quando a IA se conecta; a coleção armazena dados e não executa uma skill.
- Distribuir `SKILL.md` via `skills/list/get` sem extensão ou endpoint novo no servidor (fora do escopo atual).

Para escalabilidade futura, abrir uma decisão arquitetural e realizar teste isolado. Não alterar o serviço por iniciativa da skill.


## Quadro de decisão AS-IS / TO-BE R04

| Camada | Verificado na auditoria original (snapshot 17/11/2026) | Alternativa documental, NÃO implantada pela skill |
|---|---|---|
| GAIA RAG | conector MCP, política de aprovação por portal, aplicativo Docker/Uvicorn e Cloudflare Access/Tunnel | R02 propõe Worker MCP remoto com quatro skills |
| Armazenamento | `chatgpt_memoria_aprovada`, 384 dimensões, Cosine, 1 ponto fictício observado | proposta R02 de pontos sem vetor e índice AI Search keyword-only |
| Semântica | método real de embedding não foi identificado; não inferir modelo a partir da dimensão | R01 estuda Qwen3/BGE-M3/E5, BM25 e reranking; sem ensaio/homologação comprovados |
| Segurança | aprovação humana habilitada e no exemplo pesquisado | ACLs por tenant e testes multiusuário propostos; **não comprovados** |
| Documentos originais | repositórios externos/Drive; não tratar Qdrant como arquivo probatório | técnicas de indexação documental em AI Search propostas |

A R04 não altera schema, dimensão, índice de payload, coleção, modelo, worker, tunnel, política ou permissões. Uma skill não pode mudar a topologia somente por texto no Qdrant. `embedding` é representação, `payload` é metadado e o backend aplica autorização. Qdrant documenta que filtro de tenant deve ser derivado da identidade autenticada, e não do ID enviado pelo cliente: https://qdrant.tech/documentation/deploy-and-scale/multitenant-search/ .

### ADR proposta, fora da instalação

Caso seja exigido carregamento automático “na porta” do Qdrant, isso requer **implementação separada** em servidor MCP/gateway/host para descoberta e entrega de recursos; não pode ser resolvido somente por inserir o texto da skill no banco de vetores. Não executar esta ideia na Fase 2. Analisar custo, segurança, compatibilidade do host e consentimento antes de projeto futuro.
