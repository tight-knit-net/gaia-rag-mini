# R07 — Protocolo de continuidade por gates acionados pelo titular

**Versão:** 1.0.0
**Emissão:** 18/11/2026, 20:32:21 (America/Sao_Paulo).
**Relógio:** serviço de horário local do ChatGPT (ISO 8601 `2026-11-18T20:32:21-03:00`).
**Escopo:** convenção operacional do projeto GAIA_RAG; não altera controles de aprovação de código ou dados.

## Regra solicitada pelo titular (18/11/2026)

Ao finalizar **cada gate**, entregar o resultado observado e, em seguida, o escopo detalhado do **próximo gate**: propósito, inclusões, exclusões, fonte/ambiente, testes e evidências exigidas, riscos, rollback e condições de PASS/FAIL/NO-GO. A apresentação deve concluir com **um único botão funcional** que submete uma nova solicitação ao chat, exclusiva desse gate.

- O botão é um gatilho de **nova solicitação**, não autorização genérica de merge, deploy, DNS, migração Qdrant, escrita de memória, desligamento legado ou qualquer operação externa.
- Não executar automaticamente dois gates em uma única solicitação nem inferir autorização para os seguintes. Se houver bloqueio, registrar NO-GO e propor um gate corretivo com escopo restrito.
- Ações dentro da branch R07 obedecem à autorização do gate; leitura das branches legadas e GitLab é referência, nunca escrita implícita.
- Se o host não suportar o botão interativo, oferecer uma frase de disparo pronta para envio manual.
- Os elementos acima são instruções documentais guardadas **na branch R07**; não alegar que foram inseridos na memória do ChatGPT ou no Qdrant. O projeto ChatGPT está atualmente com Memory desativada.

## Gates após integração do roteador Skilldrum

- **S5 — Compatibilidade do carregamento explícito:** cliente-hospedeiro sintético executa seleção, leitura integral em blocos, conferência de hash e controles negativos pelo MCP. Nunca considerar o host real homologado por simulação.
- **S6 — Revisão independente de segurança e contratos:** auditoria do diff R07, testes de regressão/controles de autorização, análise de gaps e preparação de parecer GO/NO-GO técnico. Ainda sem implantação ou migração.
- **Gates de operação e migração:** só após definição/autorização separada de destino operacional, homologação de Cloudflare Access, portal humano, inventário Qdrant/ledger e backup/rollback. Preservar legado.

**Limitação:** esta convenção documental é local ao repositório R07, não uma preferência de memória entre chats nesta conta.
