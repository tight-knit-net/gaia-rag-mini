# R07 — Gate único: implantação isolada e homologação operacional

**Versão:** 1.0.0
**Data/hora aferida de emissão:** 18/11/2026 19:41:47, fuso America/Sao_Paulo.
**Origem do relógio:** serviço de hora local do ChatGPT; evidência adicional independente no log GitHub Actions: 18/11/2026 22:41:27 UTC (19:41:27 America/Sao_Paulo).
**Escopo:** executar apenas um gate de implantação isolada da R07; sem publicação, credenciais reais, migração, alteração de DNS ou desligamento do legado.
**Repositório:** tight-knit-net/gaia-rag-mini
**Branch exclusiva de código:** feat/r07-office-knowledge-assimilation
**PR:** https://github.com/tight-knit-net/gaia-rag-mini/pull/5 (draft, base feat/r06-lifecycle-skill-staging).
**SHA testado:** 2a868d157a58c680551f446e8137b487e68577ce
**CI:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44413908543
**Job R07:** 135189009145

## 1. Verificações efetivamente executadas
- PASS — 4/4 jobs CI: validate; staging_image_smoke; r06_lifecycle_synthetic; r07_operational_isolated.
- PASS — runtime R07 real em Docker efêmero no GitHub Actions: 5/5 testes HTTP de saúde, acesso MCP não autenticado negado, portal de revisão negado, POST salvar negado, POST descartar negado.
- PASS — isolamento do contêiner: Docker network none, root filesystem read-only, nenhuma porta pública. Log R07_NO_PUBLIC_PORTS_READONLY_NETWORK_NONE_PASS.
- PASS — testes sintéticos Qdrant/SQLite demonstrativos já existentes: proposta, documento sintético aprovado, clique humano simulado, idempotência e readback.
- BLOQUEADO — instalação persistente no TestLab gaia-m7i: SSH read-only conferiu o host e os contêineres, mas o comando inicial de criação do diretório isolado recebeu 503 RECEIPT_CAPACITY, retry_safe=false. Nenhum recibo comprova mudança no TestLab. Não repetir, não reiniciar executor e não contornar o controle.
- PENDENTE — validação operacional com JWT real Cloudflare Access, proprietário autenticado, revisão humana verdadeira, fonte aprovada e backup verificável.
- NO-GO — migração de memórias, promoção de R07 e desabilitação do legado.

## 2. Alterações exclusivamente no ramo R07
1. Correção oficial do nome da API opcional: GroqCloud, Groq com Q, não Grok/xAI. Documentação https://console.groq.com/docs/openai e https://console.groq.com/docs/structured-outputs. Não instalar dependências, configurar chaves, ligar chamadas ou transmitir dados de clientes.
2. Runtime candidato identificado separadamente como gaia-rag-mini-r07.
3. Script tests/r07_isolated_runtime_smoke.sh: build e runtime real Docker no runner, offline e sem dados ou segredos; limpa contêiner no encerramento.
4. CI .github/workflows/r05-skill-static.yml: novo job r07_operational_isolated, sem publicação de imagem, sem merge ou deploy externo.
5. Mantido botão manual Salvar memória — Aprovar e gravar, ainda não publicado ou homologado sob Cloudflare real.

## 3. Critério de aceite
Aceitar apenas execução isolada efêmera com evidências de CI e testes sintéticos. A homologação operacional persistente no TestLab exige: recibo de instalação, readback dos arquivos/containers, autenticação JWT real e acesso não proprietário negado, funcionamento real do botão, readback Qdrant em ambiente autorizado, plano de backup/rollback e observabilidade. Nenhum desses testes de produção foi declarado aprovado.

## 4. Riscos e rollback
- Risco ALTO: executor remoto esgotou capacidade de recibos. Sem ação de manutenção ou repetição, por segurança. Deve-se verificar estado antes de qualquer próxima tentativa.
- Risco ALTO: fila de propostas pendentes do legado não está reconciliada; memórias aprovadas não equivalem a pendências.
- Risco ALTO: testes de laboratório não provam identidade Cloudflare real nem disponibilidade operacional permanente.
- Groq segue OFF; eventual integração requer consentimento, escopo LGPD, custos e política de retenção.
- Runner efêmero remove o contêiner automaticamente; branch R07 isolada e PR draft preservam código reversível.
- Qdrant real, R06, main, Cloudflare, DNS e serviço legado não foram modificados.

**Decisão deste único gate: PASS do runtime efêmero sintético; BLOQUEADO no TestLab persistente; NO-GO para produção/migração/desativação.**
