# G14-C — Persistência descartável, concorrência transacional e aprendizagem híbrida com revisão agrupada

**Versão:** 1.0.0 — candidata **somente para teste sintético**.  
**Emissão aferida:** 2026-11-18T20:55:00-03:00; `America/Sao_Paulo`; fonte: ferramenta de horário local do ChatGPT. **Horário de publicação** é o informado pelo commit do GitHub.  
**Escopo exclusivo:** `tight-knit-net/gaia-rag-mini`, branch `feat/gaia-document-mcp-isolado`, PR [#7](https://github.com/tight-knit-net/gaia-rag-mini/pull/7) Draft, base `feat/r07-office-knowledge-assimilation`.  
**Base confirmada antes de escrever:** `95c899f2d51a19c25c8f033852efcfe818047715`, [CI Document MCP](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44423193641) e [CI herdada R05/R07](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44423193737), ambas com `success` no preflight.  
**Autorização:** pedido explícito do titular para G14-C; nenhum acesso/alteração em GitLab, Linear, Google Drive, Qdrant, cloud, OCR/NOM real, PostgreSQL real ou outra branch. A conexão GitHub é utilizada exclusivamente para commits/testes/readback do ramo autorizado.  
**Fontes:** relatório [15 — G14-B](15_G14B_OPERADOR_UNICO_APRENDIZAGEM_HIBRIDA.md), relatório [14 — plano](14_PLANO_GATE_AUTENTICACAO_CONCORRENCIA_PERSISTENCIA.md) com ressalvas revogando ACL por cliente, contratos existentes `contracts.py`, `process_learning.py`, `owner_concurrency.py` e CI GitHub. Não consultar memória como estado vivo.

## 1. Escopo, segurança e objetivo do gate

**Escolha prioritária:** SQLite nativo da biblioteca padrão Python **somente em diretório efêmero `tempfile.TemporaryDirectory`**, como prova de semântica de transação e recuperação após reconexão. **Não instalar PostgreSQL** nem outro banco. SQLite testa atomicidade real local, mas não homologa transações concorrentes do banco/provedor que venha a ser selecionado para produção.

**Proibições e invariantes:**
- Sistema de **operador único**; IDs de cliente ou processo não autorizam/bloqueiam consulta transversal do proprietário. `SyntheticOwnerOnly` é fixture de comparação, não OAuth/JWT nem prova de login real.
- Número oficial, órgão e jurisdição formam `process_key` para separar fatos de processos administrativos; zeros à esquerda são significativos.
- Captura automática de **candidatos mínimos sintéticos** após evento documental, preservando `process_id`, `process_key`, origem, fingerprint e status. Requer arquivo `FILE_DEMO_*` e síntese com prefixo `DEMO: ` para reduzir risco de usar dados reais acidentalmente. **Isso não equivale a minimização/validação LGPD real.**
- Registros candidatos são revisáveis em conjunto por **processo**, sem misturar processos distintos; cada lote usa digest do conjunto **e da evidência**. Se a evidência mudar, a revisão do lote exige novo preview.
- `prepare_proposals` gera apenas `REVIEWED_FOR_PROPOSAL_SYNTHETIC`. Nenhum ponto Qdrant é criado, e o lote não representa aprovação documental ou memória R06. Quando integrados futuramente, o botão real de Salvar memória e sua revisão autenticada devem funcionar também para propostas agrupadas. Propostas pendentes **não** são aprovadas automaticamente.
- Sem leitura semântica externa, sem Groq/iLoveAPI, sem eventos de cliente, sem publicar o MCP ou seu runtime. Os métodos só simulam operações internas e recebem fixtures.
- Os contratos existentes de `DocumentSource`, `DocumentEvent`, `ReviewProofVerifier`, OCR e NOM **não são alterados**.

## 2. Arquitetura implementada no ramo de testes

| Elemento | Contrato candidato | Prova e limite |
|---|---|---|
| `DisposableGate(TemporaryDirectory, SyntheticOwnerOnly)` | Um banco SQLite com transações `BEGIN IMMEDIATE`, bloqueio transacional, readback e fechamento de conexão | Banco desaparece com cleanup do diretório; não é Qdrant ou banco de produção |
| `process_heads` | CAS por `process_key` e versão esperada, sobrescrita concorrente rejeitada | Simula o avanço de uma **string de revisão**, não reescreve documento |
| `requests` | Unicidade `(process_key,idempotency_key)`, fingerprint e estado `RESERVED/COMMITTED/CONFLICT/UNKNOWN_SYNTHETIC` | Mesmo pedido repete `run_id`; payload diferente retorna conflito; recibo não autoriza efeito |
| `candidates` | Captura automática, deduplicação por tema **dentro do mesmo processo**, origens/eventos agregados | Somente síntese curta de **fixture**, não OCR integral; não cria memória aprovada |
| `batch_receipts` | Digest por processo+candidatos+evidências, revisão de conjunto íntegro e recibo local | Nenhum registro de revisão autenticada; nenhuma gravação Qdrant |
| `working_context` | Somente contexto provisório daquele processo, rotulado não autoritativo | Aprendizado institucional aprovado permanece via conector R06/R07 em gate futuro |

Os candidatos não podem migrar silenciosamente entre processos. Dois processos com texto semelhante recebem candidatos separados; a recuperação transversal de memórias **aprovadas** continua permitida para o proprietário conforme o protótipo G14-B, rotulando outros processos como `ANALOGY_ONLY`.

## 3. Testes sintéticos e critérios de aceite

Arquivo `tests/test_g14c_disposable.py`, executado pela CI do ramo. **Contagem a confirmar no log**; os testes definidos abrangem:

| Dimensão | Testes-alvo | Aceite |
|---|---|---|
| Workspace descartável | Exigir `TemporaryDirectory` vivo e impedir caminho arbitrário | Não abrir arquivos fora da bancada |
| Operador | Rejeição sintética de outro sujeito | Não alegar autenticação real |
| SQLite e concorrência | Mesma chave/replay; payload alterado; rollback pré-commit; reinício de conexão; disputa entre transações; versão obsoleta | Apenas um avanço por revisão; conflito explícito; recibos não afirmam escrita externa |
| Recuperação | `UNKNOWN_SYNTHETIC`, `RUN_NOT_FOUND`, readback após reabertura | Nenhum estado desconhecido equivale a sucesso |
| Contexto processual | Numeração oficial, identidade interna, fontes e dois processos similares | Sem fusão de processos; candidatos mínimos |
| Aprendizagem automática | Evento válido cria proposta; OCR `mock` e dados sem marcação DEMO rejeitados | Nenhuma memória institucional é gravada |
| Revisão humana agrupada | Um lote por processo, recibo local, rejeição de membro incorreto, lote obsoleto ou alterado | Proposta somente para revisão autenticada futura |
| Regresso | Suítes anteriores Document MCP 49 + 13 + 39 + 39 = 140 testes | Nenhuma regressão no mesmo commit |

**Riscos de interpretação:** `COMMITTED_SYNTHETIC` indica uma mudança transacional no banco efêmero, não commit documental, save de memória ou comprovante de provedor. Um revisor identificado por string fixture não é prova de usuário autenticado. Reabrir o SQLite não demonstra restore, backup ou disponibilidade de produção. Não transformar CLI/CI em endpoint.

## 4. Gates e dependências

| Gate | Critério de conclusão | Estado inicial |
|---|---|---|
| C0 — preflight | PR #7, HEAD, base e permissões; CI anterior verificada | VERIFICADO |
| C1 — sintaxe e testes | Novos testes de SQLite em CI do commit final; sem serviços | A CONFIRMAR |
| C2 — não regressão | 140 testes antigos aprovados no mesmo SHA | A CONFIRMAR |
| C3 — recuperação/readback | Reinício da conexão, isolamento por processo, estado UNKNOWN e CAS | A CONFIRMAR |
| C4 — segurança da revisão agrupada | Lote obsoleto/misto falha; sem approval/point Qdrant | A CONFIRMAR |
| C5 — diffs e documentação | Apenas módulos/teste/CI/documentação próprios na branch | A CONFIRMAR |
| C6 — integração real | Identidade autenticada, R06/R07 e DB reais, backup e rollback, atendimento a LGPD | **BLOQUEADO** por autorização e homologação próprias |

**Critério de GO:** somente para código/CI **sintéticos** C0–C5 com logs e readback. **NO-GO** para serviço operacional, R06/R07 de verdade, promoção automática, merge, deploy e corte do legado.

## 5. Riscos, rollback e próximo gate proposto

1. **Risco alto:** conteúdo não confiável ou pessoal ser persistido; este teste rejeita formatos que não parecem DEMO, mas isso não é segurança para dados reais. A futura entrada exige minimização, classificação, proteção e política de retenção antes de qualquer operação com clientes.
2. **Risco alto:** interpretação equivocada de similitude léxica entre processos. O teste mantém `process_key` e rótulo de analogia; o motor semântico futuro deve citar fonte/órgão e distinguir fatos de analogias.
3. **Risco alto:** marcar candidato como aprovado a partir de `prepare_proposals`. O status nunca é `approved`; a integração futura R06 deve exigir revisão autenticada e gesto explícito sobre o **lote**, com recibo e readback Qdrant separado.
4. **Risco alto:** usar SQLite de laboratório para supor confiabilidade PostgreSQL ou provedor Drive. Repetir testes em ambiente autorizado e banco escolhido antes de produção.
5. **Risco médio:** se novos documentos chegarem após a prévia do lote, o `batch_id` muda. A revisão exige novo preview, não aprova um conjunto alterado.

**Rollback deste gate:** reverter apenas o(s) commit(s) G14-C no ramo autorizado e deixar PR #7 em Draft. O banco efêmero do runner é apagado pela limpeza do `TemporaryDirectory`; não existe backup real a restaurar. Nenhuma alteração de status em Qdrant, Google Drive ou no motor OCR/NOM.

**Próximo gate recomendado (G14-D — solicitar autorização específica):** revisão de segurança e contratos dos mecanismos de agrupamento; confrontar a revisão autenticada por lote no portal R06 real com o fluxo manual Salvar memória; prova de persistência/backup em TestLab autorizado, com dados DEMO e readback. **Não executar G14-D automaticamente após CI verde.**

## 6. Evidências a adicionar após CI

Este documento deve receber um checkpoint após confirmar o HEAD, a PR, o diff, a contagem da nova suíte, a regressão, a CI herdada e o horário do commit. **Sem esse checkpoint, não declarar homologação do gate.**

## 7. Checkpoint real após CI e readback (G14-C)

**Aferição do relatório:** 2026-11-18T20:57:17-03:00 (America/Sao_Paulo), relógio local do ChatGPT. **Publicação do commit de código**: 2026-11-18T23:56:24Z = 20:56:24 em America/Sao_Paulo, metadados GitHub.

**Commit de código ensaiado:** `2a04cf357fd6633cebb9af4b8ff4d25a834fc5f8`, ainda na PR #7 Draft e somente na branch `feat/gaia-document-mcp-isolado`.

- **C1 + C2:** [CI Document MCP, run 44424935702](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44424935702) **PASSOU** — 49 contratos v2 + 13 OCR/NOM + 39 correlação + 39 aprendizagem G14-B + **46 G14-C** = **186/186 testes sintéticos aprovados**. O workflow confirmou também o bloqueio dos jobs herdados de publicação.
- **CI herdada R05/R07:** [run 44424944990](https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44424944990), **PASSOU** para o mesmo SHA; CI/smoke em runner efêmero não é homologação de serviço real.
- **C3 + C4:** cenários de idempotência sob duas conexões, CAS, queda antes do commit, reabertura SQLite, `UNKNOWN_SYNTHETIC`, captura e deduplicação por processo, origem modificada e rejeição de lotes obsoletos **PASSARAM** na nova suíte. Nenhum `approved=true` real, Qdrant point ou revisão humana autenticada foi produzido.
- **C5:** comparação base `95c899f2d51a19c25c8f033852efcfe818047715` → `2a04cf357fd6633cebb9af4b8ff4d25a834fc5f8` retornou **cinco arquivos**: `g14c_disposable.py`, `test_g14c_disposable.py`, CI própria, relatório 16 e índice. `DocumentSource`, `DocumentEvent`, R07, R06, main e releases não foram modificados.
- **C6:** **BLOQUEADO** para integração com R06/R07, dados reais, armazenamento de produção, backup real, serviços externos, merge/deploy e persistência no Qdrant. Aprovação da PR e CI verde não são autorização de corte.

**Limitação importante:** a classe `DisposableGate` aceita um `TemporaryDirectory` como parâmetro e grava apenas uma base local de teste; a exigência textual `DEMO:` reduz o risco de ingestão acidental, mas **não verifica semanticamente a ausência de dados pessoais**. O acesso de operador é uma fixture de comparação, não autenticação. Reabrir conexão não equivale a recuperação após perda de host. A experiência de revisão agrupada **ainda não dispõe de interface/botão autenticado real**, portanto `prepare_proposals` jamais deve ser interpretado como aprovação.

**Decisão:** **GO de laboratório sintético C0–C5**; **NO-GO de operação C6**. Próximo gate recomendado: G14-D de revisão técnica, interface de revisão de lotes e contratos de autenticação, com solicitação expressa e sem conectar infraestrutura real por padrão.
