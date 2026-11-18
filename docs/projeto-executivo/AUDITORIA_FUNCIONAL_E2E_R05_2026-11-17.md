# Auditoria funcional GAIA RAG Mini R05 — 17/11/2026

**Escopo:** comparação do Projeto Executivo R05, skills e runtime Linode com testes reais de corpus sintético. **Não é homologação de produção.**

## Parecer

O staging `gaia-rag-mini-staging` está `running/healthy`, em `127.0.0.1:18081`, com gate `RAG_STAGING_APPROVED=0`, sem JWT Cloudflare, grants nem Qdrant reais configurados. `GET /healthz` retornou 200; MCP sem JWT 401. Quatro cargas NestGround existentes foram preservadas.

O servidor real expõe **7** ferramentas: `memory_status`, `memory_policy`, `memory_search`, `memory_list_process`, `memory_get`, `memory_find_by_source` e `memory_similar_cases`. A skill documenta **16** ferramentas da MCP legada; `memory_process_start` e `memory_prepare_after_approval` estão **ausentes** na R05. Não há integração de skill por `skills/list/get`, recursos MCP, nem dependência funcional de plugin. O pacote é versionado no GitHub, **não está instalado no servidor**.

## Teste real sintético, sem clientes

- Qdrant v1.15.5 temporário, armazenamento tmpfs, rede Docker `--internal` e nenhuma porta publicada.
- 5 registros artificiais de 2 tenants, 3 processos e pontos negativos `approved=false` ou sem `tenant_id`.
- Cliente MCP ASGI exercitou a própria imagem de runtime R05; JWT RS256 assinado no laboratório e verificado por `jwt.decode`; JWKS foi simulado localmente e `_reader` apontado ao Qdrant de teste. **Não equivale à autenticação Cloudflare real**.
- Vetores 4D determinísticos exercitaram a consulta Qdrant e filtros reais; **não provam embeddings 384D do Qdrant Cloud**.
- **19 assertivas S00–S18 passaram:** descoberta real de 7 tools, listagem, busca, fonte, UUID, similares, isolamento de tenant/processo, rejeição de JWT anônimo/falso/expirado/audiência errada, ausência da proposta e ausência de escrita.
- Uma segunda sessão de cliente independente recuperou A1 de forma controlada antes da limpeza.
- A inserção dos 5 pontos foi **diretamente via API Qdrant de laboratório**, NÃO pela MCP R05. Chamada da ferramenta de proposta foi recusada; total de pontos permaneceu **5 antes / 5 depois**.
- Corpus DEMO de três processos também foi gerado em **MD e PDF**, com extração de texto do PDF testada fora da MCP. Não há pipeline de ingestão PDF/MD na R05.
- Instrução adversarial foi guardada como dado DEMO, mas **não houve teste de comportamento de modelo LLM real**.

**Limpeza:** Qdrant temporário, rede interna, imagem de teste e script removidos; ambiente oficial permaneceu `healthy`, gate 0, HTTP 200 e 401 anônimo.

## Aderência ao projeto executivo

| Requisito | Estado | Motivo |
|---|---|---|
| RF-01 | PARCIAL | `process_id` exigido na leitura; `memory_process_start` ausente |
| RF-02 | PARCIAL | search/list comprovados em DEMO; start ausente |
| RF-03 | PARCIAL | ACL por tenant/processo comprovada em laboratório, não em identidade real |
| RF-04 | PARCIAL | metadata DEMO retornada; validação de fonte e norma não automatizada |
| RF-05 | NÃO ATENDE | Não gera síntese/candidato idempotente após peça aprovada |
| RF-06 | NÃO ATENDE | Não há proposta, portal, clique, gravação ou readback |
| RF-07 | NÃO ATENDE | Skill não carregada pelo host |
| RF-08 | PARCIAL | Falhas de JWT sintético negadas; Cloudflare/Qdrant reais não ensaiados |
| RF-09 | PARCIAL | R04/R03.1 referenciadas no Drive, sem revalidação dos hashes nesta auditoria |
| RF-10 | NÃO ATENDE | Estados bem documentados, sem workflow de implementação |

**Aceite: 0/10 plenamente homologados em ambiente operacional; 6 parciais e 4 não atendidos.**

## Skill: achados

A pasta contém uma skill canônica com **9 referências**, templates, governança, `agents/openai.yaml` e regressões estáticas. São pontos fortes: separação por processo, proveniência, recusa de gravação automática e distinção aprovação interna/protocolo/deferimento. Defeitos: `references/02-recuperacao.md` ainda orienta conferir vínculo **após** resposta, mesmo quando o `SKILL.md` corretamente alerta que filtragem pós-hit não é ACL; `agents/openai.yaml` não vincula MCP; `tests/aceite.md` cita `test_regressao_r04.py` ausente (existe `test_regressao_r05.py`); 30 cenários R04 continuam `executado_em_host=false`.

## Bloqueios e decisões

Não conectar clientes, alterar Qdrant Cloud ou habilitar cutover até: identidade JWT/tenant/grants reais; reconciliação segura de pontos legados sem `tenant_id`; fluxo de proposta + aprovação humana + readback; instalação real da skill; teste host/LLM, falhas, capacidade, supply chain e rollback. O defeito `RECEIPT_CAPACITY` de 64 recibos no GAIA MCP100 é **upstream separado**; nenhum recibo foi apagado/reiniciado.

Ver [Plano de saneamento R06](PLANO_SANEAMENTO_R06_2026-11-17.md) e [PR #3](https://github.com/tight-knit-net/gaia-rag-mini/pull/3).
