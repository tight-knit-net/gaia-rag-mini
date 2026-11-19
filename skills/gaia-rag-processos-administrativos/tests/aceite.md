# Critérios de aceite da R04 — testes da skill

## Portões de decisão (não confundir com execução em produção)

| Gate | Critério | Evidência exigida | Situação nesta revisão |
|---|---|---|---|
| G01 Estrutura | frontmatter YAML real, paths válidos, ZIP íntegro e SHA | execução local | EXECUTADO LOCALMENTE |
| G02 Documentos | cada módulo/artefato preenchido e versão compatível | matriz por arquivo + revisão | EXECUTADO LOCALMENTE |
| G03 Fontes | O01–O16 lidas e classificadas; referências oficiais identificadas | matriz de evidência | EXECUTADO DOCUMENTALMENTE |
| G04 Segurança textual | nega auto-gravação, cross-process, fonte como comando | asserts estáticos e roteiros | EXECUTADO ESTATICAMENTE |
| G05 Consultas GAIA RAG | assinatura de ferramenta e retorno real somente leitura | traces de teste read-only | SOMENTE HISTÓRICO R03.1; NÃO REEXECUTADO |
| G06 Isolamento real | dois usuários/tenants reais separados em ambiente de prova | logs sanitizados, ACL backend | NÃO EXECUTADO |
| G07 Portal e escrita | confirmação de aprovação do documento, proposta, clique humano, readback | ambiente de testes com consentimento | NÃO EXECUTADO |
| G08 Carregamento | ChatGPT Work/Chat ativa skill e módulo correto | trace do host e revisão humana | NÃO EXECUTADO |
| G09 Integridade jurídica | normas do caso concreto, jurisdição e vigência conferidas | fonte oficial primária do processo | NÃO APLICÁVEL SEM CASO CONCRETO |

## Condições de interrupção

A skill não prepara proposta se `process_id` não existe, se aprovação documental não está confirmada ou se falta mandato de uso do conteúdo. Pesquisa sem hit não abre automaticamente consulta sem filtro. Pesquisa por UUID/fonte só poderá ser aplicada após verificação do vínculo processual. Busca de casos semelhantes de outros clientes depende de autorização comprovada. Testes com dados reais exigem ambiente próprio e autorização explícita.

## Comandos locais

`python scripts/validate_skill.py` verifica pacote; `python tests/test_regressao_r04.py` executa regressões de presença, formato, cobertura e invariantes. Os testes **não** são execução de modelo LLM/host ou pentest.
