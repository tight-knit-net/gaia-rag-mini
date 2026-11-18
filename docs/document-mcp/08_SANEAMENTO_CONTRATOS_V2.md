# GAIA Document MCP — Saneamento P1 dos contratos e provas sintéticas

**Versão:** 0.2.0-contratos | **Escopo:** exclusivamente `feat/gaia-document-mcp-isolado` | **PR:** #7 (draft, base R07).
**Aferição do relógio:** `2026-11-18T19:41:47-03:00` (America/Sao_Paulo), obtida da ferramenta de hora local do ChatGPT durante a emissão documental.
**Emissão:** 18/11/2026; registro da aferição acima, sem afirmar segundo exato do commit posterior.
**Commit técnico testado:** `6a5db124a23b0f5edae7a8679804797fd3364e7c`.

## 1. Objeto e critérios
Corrigir as lacunas P1 identificadas no relatório 07, mantendo integrações, servidores e memória aprovados fora da área de escrita. Não há alteração em R06, R07, OCR, nomenclatura, `main`, ambientes ou deploy.

## 2. Mudanças implementadas
1. **Identidade e proveniência:** `DocumentSource` permite fontes `drive`, `dropbox`, `local`, `generated` e `notion`. Cliente NNN e processo podem estar ausentes durante triagem; referências são validadas já na construção. Hash original opcional antes do processamento; sem ele, a candidata à memória é bloqueada.
2. **Deduplicação de eventos:** `operation_id` e `event_revision` são parte da identidade; o fingerprint incorpora fonte, cliente, processo, operação, evidências, flags e hash do resumo. Reenvio idêntico gera o mesmo evento; revisão distinta recebe chave distinta.
3. **Autoridade e revisão:** `ReviewProofVerifier` somente confere assinatura HMAC vinculada ao hash do evento e das evidências e com expiração controlada. `ReviewAttestation` não equivale a aprovação documental ou memória. **Emissor confiável com JWT e revisão real ainda não implementado.**
4. **Prévia editorial:** a presença de flags booleanas não é suficiente. Sem atestação válida, a candidata permanece bloqueada. OCR `mock`, processo não associado, hash desconhecido, fonte não revisada ou uso de LLM externa não liberada geram impedimentos.
5. **Envelopes separados:** `gaia.document-event.v2` (evento) e `gaia.document-receipt.v2` (recibo sintético sem persistência), mantendo schema v1 histórico para consulta; integrações futuras devem negociar v2 explicitamente.
6. **CI própria:** valida compilação, JSON básico, regressões sintéticas e condição `if: false` do job esperado nos workflows de publicação. Continua sem deploy, credenciais, dados reais ou ligação com provedores.

## 3. Evidências de testes
- GitHub Actions: https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44413971856 — execução concluída com **success** para o commit técnico `6a5db124`.
- A contagem de casos do commit técnico deve ser obtida no log da suíte, não inferida de um teste antigo.
- Não executado: EC2, E2E autenticado, API Stirling-PDF, DocuSeal, Groq, Drive, Qdrant ou fluxo de memória R06. CI de unidade não significa integração real.

## 4. Matriz de gates
| Gate | Estado | Evidência/pendência |
|---|---|---|
| P1a — contratos, identidade, versão e negativos sintéticos | PROCESSADO; CI PASSOU no commit técnico | Contratos v2 e testes unitários; validar HEAD após este documento |
| P1b — origem e revisão realmente atestadas | PENDENTE | Backend emissor autenticado, verificação de bytes/identidade e revogação |
| P1c — recibos duráveis/idempotência transacional | PENDENTE | Store transacional, TTL, concorrência, readback e backup |
| P2 — servidor MCP + autorização de ferramentas | PENDENTE | Autenticação conforme especificação MCP, audience e permissões por objeto |
| P3 — Stirling/OCR/NOM/DocuSeal/Groq/Workspace | NÃO INICIADO | Adaptadores e testes sintéticos end-to-end em sandbox |
| Merge/deploy/memória Qdrant | BLOQUEADO | Autorização específica após gates técnicos e humanos |

## 5. Riscos remanescentes
- A assinatura HMAC prova posse de chave, não autoridade documental: o emissor autenticado e o registro de aprovação permanecem ausentes.
- `KnowledgeCapture` é armazenamento em RAM apenas para teste; não é memória operacional persistente.
- Hash informado no contrato só é evidência se conferido contra o binário na fronteira confiável; `matches_original` permite teste, não o executa automaticamente.
- A candidata editorial não passa pelo motor R07 nem pelo portal R06; aprovação de documento e aprovação de memória permanecem eventos independentes.
- Contratos v2 não substituem regras normativas NOM; nomes/destinos dependerão da branch própria homologada, sem duplicação.
- CI estática não representa teste de acesso Google, assinatura DocuSeal ou políticas de tratamento de dados por fornecedor.

## 6. Fontes metodológicas
- JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core (semântica de required/properties e versões).
- MCP authorization 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization (validação de audiência, escopo e recurso protegido).
- Fontes do código: GitHub, PR #7, commit técnico informado, arquivos `gaia_document_mcp` e workflows, sem confiança em memórias históricas como estado vivo.

## 7. Decisão e próxima ação
**FAVORÁVEL COM RESSALVAS** à continuidade de desenvolvimento somente na branch isolada, após CI no HEAD documental. O próximo incremento tecnicamente seguro é implementar um verificador de fronteira confiável/test harness sintético para autenticação e store local descartável; integração externa, deploy, escrita no Drive ou Qdrant exigem gate e autorização fora desta fase.
