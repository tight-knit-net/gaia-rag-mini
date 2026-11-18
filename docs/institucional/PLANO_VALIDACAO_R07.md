# R07 — Plano de testes e gates

Os testes são sintéticos offline, sem dados reais, sem escrita Qdrant, sem deploy.

| Cenário | Evidência esperada |
|---|---|
| Nova candidata | persisted=false; requer duas aprovações |
| Síntese duplicada | não preparar gravação |
| Mesma fonte, redação diferente | revisão candidata; original intacto |
| ID anterior do processo exato | vínculo válido, sem revogação |
| Outro processo/sem aprovação | rejeitado na comparação |
| Simulação e alegação | não se converter em precedente/fato |
| Mesmo título | mera relação, não superação |
| Histórico paginado | cobertura parcial sinalizada |
| Falta de fonte | rejeição da prévia |
| OCR/PDF futuro | não validar sem origem e revisão |

G1 — topologia, escopo e privacidade conferidos.
G2 — validação de skill, testes offline R05/R06 e R07, build local, CI.
G3 — revisão da PR R07 contra a branch R06, sem mudanças em identidade, gravação, rede ou Access.
G4 — definir e homologar posteriormente política efetiva de supersessão/revogação e índice de estado vigente.
G5 — merge controlado R07 -> R06, somente após aprovação.
G6 — integração main e deploy em processo próprio, com evidências e rollback. Não executar neste escopo.

O Gate de revisão humana existente na R06 permanece obrigatório.
