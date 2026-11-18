# Plano de atualização e saneamento R06 — GAIA RAG Mini

**Origem:** [Auditoria funcional R05](AUDITORIA_FUNCIONAL_E2E_R05_2026-11-17.md) executada em 17/11/2026 com corpus e Qdrant DEMO reais e descartáveis.

## Premissa central

**Não liberar produção nem afirmar memória operante antes de demonstrar este ciclo completo:**

`PDF/MD e fonte -> process_id/tenant autorizado -> consulta -> documento aprovado -> candidato atômico -> deduplicação -> proposta sem persistência -> clique humano protegido -> gravação exatamente uma vez -> readback/auditoria -> recuperação em nova sessão`.

A skill é instrução, não ACL; a origem DigitalOcean e Qdrant Cloud existentes continuam preservados.

## Backlog priorizado, evidências e gates

| Fase | Prioridade | Entrega | Aceite obrigatório |
|---|---|---|---|
| **R06.0 Contrato** | P0 | Congelar baseline do código e comparar as 7 tools R05 contra 16 da MCP antiga. Atualizar `SKILL.md`, `references/07`, testes, respostas e runbook | Não anunciar método inexistente; CI e revisão de código verdes |
| **R06.1 Identidade** | P0 | JWT Cloudflare real assinado, issuer/audience; fonte **autoritativa e revogável** de grants por subject/tenant/processo; proteger cada tool inclusive similares/fonte/UUID | Dois tenants, 0 vazamentos, revogação demonstrada, falha fechada. Pontos legados sem `tenant_id` permanecem bloqueados até mapeamento demonstrado |
| **R06.2 Produção** | P0 | Implementar `memory_process_start`, `memory_prepare_after_approval`, preview/pending/portal, recibo humano e readback com trilha | Antes do clique 0 pontos; depois 1 ponto; clique repetido não duplica; expiração/negação não grava; documento aprovado não implica memória aprovada |
| **R06.3 Documentos** | P1 | Ingestão de PDF/MD em sandbox, extração, validação de fonte e hash, resumos atômicos, deduplicação com chave de tenant/processo/fonte/versão | Mesmo corpus DEMO recuperável sob ACL; documento bruto não vira memória sem revisão; fonte/vigência verificáveis |
| **R06.4 Skill real** | P1 | Escolher Skills over MCP **se host negociar** ou Plugin ChatGPT com dependência MCP verificada; empacotar 9 refs e templates | Traces de ChatGPT/Work para seleção implícita/explicita, resources/list/read, carregamento progressivo e prompt injection como DADO |
| **R06.5 Homologação** | P1 | Testes A/B, fonte/UUID/similares, signed JWT real, Qdrant/embeddings compatíveis, portal, replays, concorrência, rede, timeout, restart, rollback | Zero vazamento; 0 escrita antes do clique; 1 escrita após; readback em sessão independente; limpeza da fixture comprovada |
| **R06.6 Supply chain** | P1 | Lock/pinning de libs, SBOM, secrets scan, audit de imagem, digest, rollback de staging e medição P50/P95/CPU/RAM | Imagem imutável e reproduzível; sem deploy automático de produção; SLO definido por benchmark, não inventado |
| **R06.7 Cutover** | P2 | Somente após aceite dos gates anteriores, planejar substituição controlada de origem DO mantendo Cloudflare Access/Qdrant | Autorização distinta e explícita; origem única de escrita, rollback exercitado e verificado |

### Ordem eficiente de engenharia

1. Corrigir **contrato e grants** antes de tentar distribuir skill ou melhorar UI.
2. Entregar **proposta + clique humano + readback** com corpus sintético e prova exata de uma persistência.
3. Conectar a skill ao **host real**, observando seleção e uso sob demanda sem inventar funções.
4. Só depois avaliar importação de dados reais, adequação legal, segurança, carga e migração.

### Pendência de outro produto — GAIA MCP100

O executor SSH externo ainda tem limitação `RECEIPT_CAPACITY` por teto de 64 recibos em memória. Corrigir na origem upstream com reconciliação, retenção auditável/idempotência e teste de crash recovery; **não reiniciar e não apagar recibos arbitrariamente**. Não misturar esse serviço compartilhado com deploy da R05.

### Critério único de pronto

A R05 poderá ser classificada como **pronta para homologação** somente quando uma peça DEMO aprovada produzir candidato, o portal proteger o segundo clique, exatamente uma memória for armazenada sob tenant/processo/fonte, uma sessão autorizada independente recuperá-la, outro cliente não puder recuperá-la e a skill instalada conduzir tudo com rastreabilidade; rollback e exclusão de dados de teste também devem passar.

**Este plano não autoriza merge, GHCR, alteração Cloudflare/Qdrant produtivos ou cutover.**
