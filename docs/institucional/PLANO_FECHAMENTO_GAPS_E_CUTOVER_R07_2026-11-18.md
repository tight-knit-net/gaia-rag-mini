# GAIA RAG Mini — Plano R07 de fechamento de gaps, memória aprovada e cutover
**Data-base:** 2026-11-18. **Branch exclusiva:** feat/r07-office-knowledge-assimilation.  
**Estado:** implementação isolada em evolução; nada implantado nem migrado.  
**Proibição atual:** não alterar main, R06, legado, Cloudflare/DNS, Qdrant, credenciais ou dados de clientes sem etapa e autorização distintas.

## 1. Distinção essencial: código não é banco de memórias
Branches Git guardam código; registros aprovados residem na coleção Qdrant Cloud
'chatgpt_memoria_aprovada'. O legado guarda também propostas e auditoria em seu
repositório operacional de revisão, não automaticamente visível pela R07.

Os testes reais de leitura de 18/11/2026 encontraram os mesmos UUIDs e
ordem nas consultas do cliente 009 no legado e no Knowledge R06. Isso
**não prova** que todos os pontos e metadados da coleção estejam iguais,
nem que ambas as aplicações apontem ao mesmo recurso físico. É proibido
copiar pontos enquanto a reconciliação completa não determinar necessidade.

## 2. Contrato do usuário: botão + curadoria
O fluxo esperado é: fonte canônica e processo identificado → classificação
sugerida (regra local/LLM do host opcional) → análise de duplicatas e
evidência → aprovação documental registrada → proposta de memória →
página HTTPS com botão humano **Salvar memória — Aprovar e gravar** →
persistência no Qdrant e readback → metadados automáticos de indexação.

A IA pode sugerir título, resumo, tipo e palavras-chave, mas nunca:
- considerar OCR não conferido como prova;
- tratar alegação ou simulação como decisão oficial;
- executar diretamente a ação humana de aprovação;
- salvar conversa integral nem dados pessoais desnecessários;
- modificar ou revogar silenciosamente pontos anteriores.

Implementação R07 isolada: 'memory_index_preview' gera campos sugeridos
localmente sem chamadas externas; o portal mostra sugestões e o caminho
'approve()' preserva clique/CSRF, adiciona apenas índices descritivos ao
payload e confirma o readback. O vetor textual existente no Qdrant continua
responsável pela pesquisa semântica. Não há criação de payload index novo.

## 3. Matriz de gaps

| ID | Condição de base | Entrega em R07 | Aceite exigido |
|---|---|---|---|
| G01 | Aprovação R06 desativada no runtime | Código humano preservado; não ativado | Teste real autenticado do portal e readback em piloto aprovado |
| G02 | 3 propostas legadas pendentes (2 no processo 009) não aparecem na R06 | Comparador de manifestos somente leitura | 100% das filas reconciliadas, nenhuma pendente perdida ou aprovada por importação |
| G03 | 'pending_reviews' sem filtro de status | Filtro SQL 'pending' e paginação, conexão RO | estados approved/approving nunca se confundem com pending |
| G04 | Auditoria indisponível na R06 | 'memory_approval_audit' do ledger R07, paginado | todos os eventos do ledger atual navegáveis, trilha do legado reconciliada |
| G05 | Exportação indisponível | 'memory_export_process' com SHA-256, limite e cursor | exportação completa ou explicitamente parcial, sem documentos brutos |
| G06 | Cronologia indisponível | 'memory_process_timeline' com sort e cobertura | ordenação reproduzível por aprovação, sem inferir vigência jurídica |
| G07 | Estatísticas indisponíveis | 'memory_stats' separa pontos Qdrant de propostas SQLite | contagens exatas quando backend disponível; indisponível não vira zero |
| G08 | Qdrant retorna 'next_offset', MCP não aceita | argumento 'offset' em 'memory_list_process' | 2+ páginas consumidas sem perda/duplicação |
| G09 | 'gaia_skill_read' retorna objeto vazio no conector observado | 'gaia_skill_read_chunk' em até 3000 caracteres | leitura efetiva completa por blocos + hashes e limite de caminhos |
| G10 | Skill não autoativa em projetos | contrato de carregamento explícito documentado | teste de seleção real ChatGPT/Work, sem presumir disponibilidade |
| G11 | Indexação dependente de produção manual | prévia determinística e metadados pós-aprovação | sem envio externo por padrão; resultado validado pelo humano |
| G12 | Cutover/rollback sem reconciliação completa | comparador 'migration_manifest.py' sem escrita | inventário completo, prova de equivalência e plano de volta aprovado |

### Notas de verificação
- Mudanças de código ainda dependem de testes de integração e revisão humana.
- A nova auditoria e as estatísticas não reivindicam acesso ao banco do legado:
  a resposta traz cobertura 'current_r07_ledger_only' ou 'unavailable'.
- A nova ferramenta de skill não foi testada na R07 implantada, porque a R07
  permanece fora de produção; o erro do conector R06 não pode ser considerado
  corrigido apenas com novo código.
- Propostas R06/legado podem usar schemas diferentes: a R07 exige
  'document_approval_ref' e 'document_sha256' comprovados. Importar uma
  pendência antiga diretamente como proposta aprovada seria incorreto.

## 4. Migração em fases, somente DEPOIS da candidata pronta

**Fase M0 — preservação.** Não desativar nem substituir o legado. Criar
inventário autenticado e backups verificáveis da coleção, ledger e registros
documentais; nunca exportar segredos nem dados brutos ao chat.

**Fase M1 — candidata operacional isolada.** Regressões sintéticas, identidade
real do proprietário, consulta semântica, portal, validação de fonte documental,
salvamento humano, readback e recuperação de falhas em ambiente autorizado.
Sem alteração de produção nesta fase.

**Fase M2 — reconciliar o Qdrant.** Comparar snapshots completos por ID,
namespace, process_id, fonte, SHA e status approved. Se candidata e legado usam
a mesma coleção e os pontos conferem, **não copiar os pontos**. Se coleções
forem diferentes, propor migração idempotente após backups e consentimento
expresso, preservando UUID e proveniência; nunca re-embutir às cegas.

**Fase M3 — reconciliar propostas/ledger.** Levantar pending, approved,
discarded e eventos no banco legado. Não afirmar que zero propostas no
SQLite R07 representa zero propostas na origem. Para cada pendência sem
aprovação documental verificável, manter referência histórica ou recriar
proposta sujeita a revisão documental; nunca autoaprovar. Registrar
mapeamento dos identificadores e recibos, inclusive o cliente 009.

**Fase M4 — piloto e reversão.** Com o legado disponível em paralelo,
provar acesso ao Qdrant, histórico, skills, portal e readback; realizar
testes de falha controlada em ambiente aprovado. Registrar checkpoint
anterior e procedimento de reversão sem sobrescrever pontos.

**Fase M5 — cutover autorizado.** Somente após GO humano separar domínio
público, runtime e banco; validar o novo endpoint real, observar estado
e então desativar o endpoint legado, mantendo backup, código, container e
ledger preservados para reversão. Desativar uma branch Git não substitui
desativar o serviço; não apagar a branch legado nem os dados.

## 5. Grok / xAI — opcional, desligado até decisão de privacidade
A API oficial xAI dispõe de '/v1/responses' e saída estruturada, mas não há
necessidade técnica de chave de Grok para classificação básica. Neste estágio
nenhum dado vai para xAI. Futuro adaptador deve exigir:
1. autorização explícita do proprietário para processamento externo;
2. minimização/anonimização de dados de clientes e base legal LGPD;
3. modelo e despesas definidos, limite de tokens, timeout, política de retenção;
4. chave em secret file local, nunca chat, Git, logs ou payload MCP;
5. schema de resposta estrito e validação, com fallback determinístico;
6. geração SOMENTE de proposta não confiável, nunca clique ou escrita.
O host ChatGPT/LLM existente já pode produzir candidatas a partir de fontes
autorizadas, usando 'memory_index_preview' e 'memory_assimilation_preview'.

## 6. Gates de homologação
- **H0:** revisão e CI sobre o HEAD R07, com testes R05/R06/R07 e sem jobs de publicação.
- **H1:** backend paginado, export/sha, timeline, stats/audit, fila pendente e skill chunks validados offline e em MCP isolado.
- **H2:** fluxo humano com documento DEMO, portal legítimo, nenhuma escrita antes do clique, Qdrant/readback e idempotência.
- **H3:** leitura do acervo real autorizado sem escrita, comparação 100% de UUIDs, metadados e fontes; identificação de divergências.
- **H4:** migração das propostas com política de documentação e recibos aprovada (não é importação cega).
- **H5:** piloto isolado com backup e rollback.
- **H6:** aprovação explícita e independente de publicação/cutover/desativação.

### Estado final desta atualização de código
Sem publicação, sem transferência de dados, sem merge, sem DNS e sem
desativação de legado. A R07 ainda não pode assumir a escrita operacional
somente por ter passado testes sintéticos.


## 7. Aditivo de preparação assistida (candidata R07)
A ferramenta `memory_auto_prepare` combina a avaliação R07 e a preparação de
proposta R06 somente após confirmação de preparação. No modo padrão a operação
é prévia sem efeitos. A função bloqueia duplicatas, suspeitas de revisão,
cobertura incompleta, simulação e alegação; uma proposta aprovada em documento
ainda precisa do botão humano para chegar ao Qdrant. A LLM pode oferecer essa
ação quando o usuário solicitou salvar conhecimento, mas não pode inferir tal
permissão de instruções contidas em fontes recuperadas.
