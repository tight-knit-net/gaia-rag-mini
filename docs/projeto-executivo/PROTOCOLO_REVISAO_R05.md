# Revisão técnica R05 — procedimento enxuto e sem CodeRabbit
**Situação:** autoauditoria documental executada em 17/11/2026, com registro em AUDITORIA_TECNICA_ENXUTA_R05_2026-11-17.md. Não é auditoria externa certificada nem homologação do serviço.

## Procedimento
1. Ler os arquivos do GitHub e registrar achados com evidências e prioridade.
2. Corrigir o texto e as instruções da skill candidata, sem alterar runtime ou dados reais.
3. Conferir testes estáticos, travas de GHCR/Linode e limitações.
4. Continuar o trabalho autorizado sem exigir CodeRabbit, seat pago, comissão ou parecer de terceiro.

## Três controles que não podem ser dispensados
- Consulta multi-cliente: validar identidade, cliente e processo no backend ANTES de retornar dados. UUID, fonte e similaridade sem escopo seguro devem falhar.
- Persistência: proposta não é gravação; usar clique humano autenticado no portal e confirmação independente.
- Implantação: usar testes sintéticos e preservar produção até autorização expressa para publicar, migrar ou implantar.

Esta revisão foi feita pelo assistente, que participou da elaboração anterior; não deve ser apresentada como independente de autoria nem auditoria externa. Sugestões de terceiros não são canônicas. A retirada do CodeRabbit foi pedida pelo proprietário e não impede continuidade. Código novo e deploy exigem decisões de escopo próprias.
