# GAIA OFFICE — Projeto Executivo R07 de assimilação e memória institucional
**Revisão:** 2026-11-18 | **Natureza:** baseline para homologação executiva inicial | **Branch:** feat/r07-office-knowledge-assimilation
**Objeto:** memória, assimilação, evolução do entendimento e governança de processos administrativos no conector GAIA RAG Mini.

## 1. Problema e decisão de negócio
O conector já fornece consultas às memórias aprovadas e uma linha R06 de proposta, revisão humana e readback. A GAIA OFFICE pretende utilizá-lo continuamente em documentos e processos: PDFs, OCR, catalogação, nomenclatura, requerimentos, contratos, procurações, relatórios, exigências e acompanhamento administrativo. O problema institucional não é acumular todo texto lido, mas **reter conhecimento confiável com origem e capacidade de correção**.

A solução R07 é uma **camada de prévia de assimilação sem mutação**, derivada da R06, preservando os mecanismos existentes de autenticação e aprovação. Ela distingue informação nova, duplicada, relacionada e revisão candidata, mas não resolve ainda vigência e supersessão efetiva.

## 2. Fontes de decisão verificadas
- Avaliação sistemática do conector R06, 18/11/2026, Google Doc 1xGoQTfQj9Hai_5uPOXHKUV9bHj0q8nG6LggF2JKIS10: teste de pesquisa, processo exato, fonte, UUID, continuidade; identifica mistura entre escritório, engenharia e simulações, sem testar gravações reais.
- Relatório executivo GitHub R07, 18/11/2026, Google Doc 1DpOyjf-9X5tML8pZ05M-3mBMt2_-KVc2ckGcmd4Xhu0: escopo, branch, PR, 15 arquivos originais de alteração, CI, limites e Issue #6.
- Caderno institucional GAIA OFFICE, Google Doc 1t6NydW_QqSOzfhWQAj67QQh2rWkSRBEUmuy5BPEbudk: cliente, processo, documento e assunto separados; distinção entre alegação, ato, protocolo e deferimento; LGPD e limites jurídicos.
- R06: docs/projeto-executivo/R06_MEMORIA_UNIFICADA_SEM_TRAVA_CLIENTE_2026-11-18.md e PR #4: proprietário verificado pode consultar todos os clientes; process_id é localizador exato e não autorização por cliente.
- R05: docs/projeto-executivo/PROJETO_EXECUTIVO_R05.md, CONTRATO_ORIGEM_MCP_R05.md e ADR-0002-FREEZE-PUBLICACAO.md; são documentos históricos de evolução, não devem prevalecer quando conflitarem com decisão R06 explicitamente posterior.

As fontes externas ao GitHub permanecem no Drive canônico; este projeto guarda **síntese e links rastreáveis**, não cópias integrais de documentos de clientes ou do acervo de pesquisa.

## 3. Escopo e fronteiras
**Entregue na R07:** ferramenta MCP memory_assimilation_preview autenticada; comparação com até 300 registros aprovados do processo exato, com paginação e aviso de cobertura parcial; avaliação determinística; campos de classificação editorial e status da evidência; 14 cenários unitários sintéticos; referência 10 da skill; política editorial R07; documentação de arquitetura, interfaces e testes.

**Herdado e preservado da R06:** acesso do proprietário com validação de identidade; busca transversal sem travas por cliente; aprovação documental por registro do servidor; preparação de proposta; portal humano com CSRF; persistência somente após clique e confirmação de readback. A R07 não reimplementa esses controles.

**Fora do escopo já implantado:** OCR, manipulação de PDF, edição, catalogação, NOVA regra NOM, implantação de skill em todos os chats, atualização ou revogação transacional de memória, algoritmo de escolha de versão vigente, integração à main, produção, Cloudflare, deploy e leitura real do fluxo documental completo.

## 4. Arquitetura funcional em camadas
1. **Fonte documental canônica:** Drive, órgão administrativo ou outro sistema com ID, versão, integridade e proveniência.
2. **Processador documental independente:** OCR, extração, editor PDF, catalogador ou NOM publica um envelope de evidência verificável; não produz automaticamente memória.
3. **Curadoria institucional:** classifica documento, fato, interpretação, norma, procedimento, precedente, lição, pendência e simulação; minimiza dados pessoais e verifica contexto.
4. **R07 — prévia somente leitura:** usa memória já aprovada no process_id exato e retorna duplicidade/revisão candidata/relação sem aplicar efeitos; informa limites de cobertura.
5. **R06 — proposta e aprovação:** requer documento registrado como aprovado, link real de revisão e clique humano autenticado; grava e confere readback; nunca delegar o clique à IA.
6. **Entrega de conhecimento:** memória de caso, procedimento geral e lições são apresentados com fonte, data, jurisdição e ressalvas; pontos históricos permanecem consultáveis.

A autorização de consulta transversal do proprietário não autoriza mistura editorial entre processos. Fatos de um cliente não são transformados em política geral sem anonimização e revisão.

## 5. Estados e vocabulário obrigatórios
- Origem: ORIGINAL | DERIVADO_OCR | DERIVADO_EDICAO | SINTETICO.
- Evidência editorial: ALEGADA | DOCUMENTADA | CONFIRMADA | SIMULADA; não elevar automaticamente estado.
- Processo: EM_TRIAGEM | MINUTA | PROTOCOLADO | EM_EXIGENCIA | DECIDIDO | ENCERRADO, apenas com evidência.
- Memória: CANDIDATA_LOCAL | PREVIA_R07 | PROPOSTA_R06 | AGUARDANDO_CLIQUE | CONFIRMADA_READBACK | HISTORICA. Estes nomes são **editoriais**; não constituem campos técnicos persistidos na R07.
- Revisão: NOVA_CANDIDATA | DUPLICATA_NAO_PROPOR | REVISAO_CANDIDATA | RELACAO_A_VERIFICAR | EXEMPLO_NAO_PROMOVER. Uma revisão candidata **não** é substituição aprovada.

## 6. Contrato observável da R07
**Entrada:** process_id, title, summary, source_ref; kind, evidence_status, prior_point_id, namespace opcionais. Identificação exata do processo e fonte exigida.
**Saída:** disposition, IDs de itens relacionados/duplicados no mesmo processo, prior_verified, prior_history_complete, blockers, next_step, exigências de duas aprovações, persisted=false e old_points_unchanged=true.
**Execução:** somente leitura do Qdrant via adaptador da R06; no máximo três páginas de cem, com consulta por UUID do ponto anterior se fornecido. Não é busca geral de versão vigente. O registro de fonte indicado pelo usuário ainda deve ser validado antes de qualquer proposta R06.
**Falha conservadora:** simulação/alegação/duplicata ficam bloqueadas para promoção factual, índice incompleto não permite declarar ausência definitiva, contexto com outro process_id é rejeitado.

## 7. Compatibilidade e acoplamento gradual
Os módulos OCR e catalogação são branches separadas, derivadas de uma R06 anterior; comparar a respectiva merge base e reconciliar commits ao integrá-las. O contrato de integração deve ser um **envelope documental versionado**, não compartilhamento ad hoc de banco nem dependência direta de pasta interna de um laboratório. Ver PLANO_ACOPLAMENTO_BRANCHES_R07.md.

Invariantes obrigatórios após cada integração:
- main conserva origem rastreável dos arquivos e teste de compatibilidade da skill/contratos;
- somente executor documental autorizado altera Drive/PDF, com recibo e readback; a memória não executa MOVE/RENAME;
- Qdrant não vira depósito de PDF/OCR bruto; somente sínteses aprovadas;
- nenhuma integração contorna a revisão humana R06;
- cada PR tem teste positivo e negativo, plano de rollback e matrizes de impacto no restante do repositório;
- nenhuma branch deve realizar deploy automático por existir ou ser integrada sem autorização expressa.

## 8. Critérios para homologação inicial (documental e sintética)
H01. Inventário completo dos arquivos R07 no diff contra R06, README/REDMI/REDME/topologia, sem duplicação de código.
H02. Revisão de arquitetura, dependências e fronteiras confirmada por documentos oficiais do GitHub e Drive.
H03. CI no HEAD após as últimas alterações: validate, r06_lifecycle_synthetic e staging_image_smoke aprovados; nenhuma publicação GHCR/Linode.
H04. PR R07 aberta em draft contra R06, sem merge em nenhuma branch superior.
H05. Matriz de requisitos, evidências e pendências rastreável; Issues futuras registradas.
H06. Marco de commit e orientação de congelamento editorial publicados no parecer; sem afirmar proteção técnica do GitHub se não houver.
H07. Nenhum dado de cliente nem segredo adicionado; nenhuma alteração em Qdrant, autenticação, rede ou produção.

A conclusão destes itens **habilita congelamento de projeto executivo**, não produção. Para uso real serão necessários testes de contrato do novo tool via MCP autenticado, continuidade da cadeia R05/R06 e liberação operacional independente.

## 9. Riscos, responsabilidades e decisões pendentes
R-01: divergência de branches quando R06/main avançarem. Medida: integrar pela ordem das PRs com comparações de merge base e regressões.
R-02: memória histórica reaparecer como vigente. Medida: Issue #6 e bloqueio de alegação de supersessão automática.
R-03: OCR pouco confiável e dados privados. Medida: validação documental, fonte e LGPD antes de candidatos.
R-04: confundir documentos do Drive com arquivos incorporados no GitHub. Medida: matriz de rastreabilidade com links e fronteiras de custódia.
R-05: congelamento não protegido pelo GitHub. Medida: baseline SHA, PR draft, status documental e verificação de SHA antes do merge; avaliar proteção de branch separadamente quando o plano permitir.
R-06: teste unitário não equivale a contrato MCP hospedado. Medida: gate futuro com ambiente autorizado, entradas sintéticas, interface real e confirmação da revisão humana.

**Responsabilidade:** o proprietário delibera integração/publicação; a revisão executiva atesta apenas conteúdo documental e provas observáveis. Uma PR draft não é autorização de execução.

## 10. Deliberação proposta
Aceitar a R07 como **baseline de arquitetura/implementação sintética para congelamento estático administrativo**, condicionada à verificação da CI no HEAD final e ao inventário. Manter PR #5 draft, preservar a cadeia #1 → #3 → #4 → #5 e não integrar à main ou ao runtime já publicado. A liberação operacional exige fase própria.

**Documentos correlatos:** MATRIZ_RASTREABILIDADE_R07.md; PLANO_ACOPLAMENTO_BRANCHES_R07.md; TERMO_HOMOLOGACAO_INICIAL_R07.md; TOPOLOGIA.md.
