# 09 — Instalação, Work, ChatGPT e alternativa de distribuição

## Plano presente

Este pacote é uma skill no padrão Agent Skills: único `SKILL.md` com YAML e módulos `references/` abertos sob demanda, `agents/openai.yaml` opcional e testes. **Não foi instalado** nem há plugin publicado por este pacote. Um ZIP de skill standalone não é por si só um plugin distribuído para todas as superfícies do ChatGPT; nesse cenário é necessário empacotamento e associação com o MCP conforme a documentação vigente.

## R06 prévia no servidor Linode

A imagem R06 empacota a pasta canônica da skill em `/app/skills/gaia-rag-processos-administrativos/`, disponibiliza `gaia_skill_catalog` e `gaia_skill_read` com allowlist e três recursos MCP `skill://...`. Isso comprova **distribuição de conteúdo no servidor**, não instalação no catálogo ChatGPT/Work nem ativação automática. A descoberta real depende de uma conexão ao host com credenciais e negociações suportadas; não anunciar que a extensão beta `skills/list/get` foi implementada. O pacote só fica utilizável por cliente configurado com conexão MCP e concessões reais.

## No Work

1. Importar/abrir a pasta `gaia-rag-processos-administrativos` no ambiente de criação de skills disponível.
2. Usar `@skill-creator` se disponível para revisar nome, descrição e gatilhos; manter apenas uma skill com anexos em `references/`.
3. Homologar 2 fluxos: consulta restrita a `process_id` e proposta pós-aprovação, ambos contra a **MCP atual**.
4. Testar descoberta implícita e explícita; observar se a skill é efetivamente carregada, não assumir.
5. Instalar/compartilhar segundo os controles da conta e do workspace. ChatGPT Skills pode ser disponibilizado por Plugin Directory > Skills > Create > Upload, quando a conta tiver essa capacidade; ela varia por plano/ambiente.

## Alternativa sem mexer no MCP

Um **plugin** pode distribuir a skill e utilizar o conector GAIA RAG já autorizado, sujeito à forma de empacotamento e capacidades do workspace. Não declarar manifesto com URL/ID de MCP não verificado.

## Porta do Qdrant: ideia para etapa futura

A base Qdrant em si não carrega instruções executáveis ao conectar. Para descoberta automática, seria necessário um componente **fora** do banco: skill instalada no cliente; plugin; ou servidor MCP fornecendo catálogo/recurso `SKILL.md` em endpoint explicitamente implementado e homologado. Isso exigiria alteração da MCP/aplicação, que o titular não quer nesta fase; portanto **não implementar**. Uma entrada de memória com texto de skill não garante ativação segura nem carrega diretivas privilegiadas.

## Compatibilidade

A partir de documentação pública OpenAI consultada em 17/11/2026, Skills usam `SKILL.md` e disclosure progressivo; distribuição e elegibilidade variam por superfície e plano. Consultar fontes oficiais antes da instalação final.


## Checkpoints de instalação atualizados R04

**Especificação Agent Skills:** pasta com `SKILL.md`, `name`/`description` em YAML válido e referências opcionais. A descrição deve representar o gatilho de trabalho; módulos ficam fora do arquivo principal para carregamento progressivo. https://openagentskills.dev/docs/specification ; https://developers.openai.com/plugins/concepts/skills

**No ChatGPT:** a documentação distingue skills independentes (desktop/Codex CLI/IDE) de skills distribuídas por plugins (Chat e Work no web/mobile/desktop); o caminho efetivo depende das capacidades do host. https://learn.chatgpt.com/docs/build-skills

**Procedimento de aceitação real após importação:** (a) verificar que a skill aparece no catálogo; (b) testar seleção automática e explícita, (c) inspecionar que `references/02` é carregada para BUSCA sem carregar `08`, (d) executar apenas buscas read-only em fixture de prova, (e) demonstrar que falta de aprovação documental bloqueia `memory_prepare_after_approval`; (f) inspecionar logs ou traces de ativação quando disponíveis. Sem evidência desses passos, registrar `INSTALACAO_NAO_HOMOLOGADA`.

**Se não houver suporte a skills no host:** oferecer o pacote para revisão humana/Work ou instrução manual do fluxo; não afirmar injeção automática via Qdrant. **Não** criar MCP paralelo/novo endpoint, token, plugin.json ou arquivo de conexão inventado.

**Verificador de estrutura**: `python scripts/validate_skill.py`. **Teste de regressão**: `python tests/test_regressao_r04.py`. Scripts rodam localmente sobre arquivos, sem internet, sem escrita na MCP. Relatório de evidências do projeto não integra a pasta de skill standalone.
