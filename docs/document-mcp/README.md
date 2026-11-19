# GAIA DOCUMENT MCP — índice canônico da iniciativa

**Data-base:** 18/11/2026 | **Branch:** `feat/gaia-document-mcp-isolado` (derivada de R07)
**Natureza:** arquitetura e núcleo mínimo testável; sem implantação, real documents ou liberação de operações externas.

1. [01 — Projeto executivo e arquitetura](01_PROJETO_EXECUTIVO.md)
2. [02 — Auditoria das fontes técnicas](02_AUDITORIA_TECNICA_FONTES.md)
3. [03 — Contratos, fluxo e segurança](03_CONTRATOS_E_SEGURANCA.md)
4. [04 — Matriz de branches e integração](04_TOPOLOGIA_E_DEPENDENCIAS.md)
5. [05 — Plano de testes e gates de homologação](05_PLANO_HOMOLOGACAO.md)
6. [06 — Parecer de auditoria inicial](06_PARECER_AUDITORIA_INICIAL.md)
7. [07 — Validação estrutural parcial e confronto com a main](07_VALIDACAO_ESTRUTURAL_PARCIAL_2026-11-18.md)
8. [08 — Saneamento P1: contratos v2 e testes](08_SANEAMENTO_CONTRATOS_V2.md)
9. [09 — Alerta de divergência da base R07](09_ALERTA_DEPENDENCIA_R07_2026-11-18.md)
10. [10 — MVP híbrido OCR/NOM com APIs opcionais](10_MVP_HIBRIDO_OCR_NOM.md)
11. [11 — Matriz de reaproveitamento BC01/D1 → MCP v2](11_MATRIZ_REAPROVEITAMENTO_GDL_BC01_MCP_V2.md)
12. [12 — Mapa de campos, schemas, testes e segurança](12_MAPA_CONTRATOS_SCHEMAS_TESTES_GDL_BC01.md)
13. [13 — Gate P0/P1: correlação documental e testes sintéticos](13_GATE_P0_P1_CORRELACAO_SINTETICA.md)
14. [14 — Plano do próximo gate: autenticação, concorrência e persistência](14_PLANO_GATE_AUTENTICACAO_CONCORRENCIA_PERSISTENCIA.md)
15. [15 — Gate G14-B revisado: operador único, contexto processual e aprendizagem híbrida](15_G14B_OPERADOR_UNICO_APRENDIZAGEM_HIBRIDA.md)
16. [16 — G14-C: persistência descartável, concorrência transacional e revisão por lote](16_GATE_G14C_TRANSACOES_APRENDIZAGEM_REVISAO_AGRUPADA.md)
17. [17 — G14-D: auditoria de contratos e plano autenticado Salvar memória R06/R07](17_G14D_AUDITORIA_CONTRATOS_FLUXO_SALVAR_MEMORIA.md)
18. [18 — G14-E: saneamento P1, negativos sintéticos e riscos remanescentes](18_G14E_SANEAMENTO_P1_CONTRATOS_CONTEXTO_E_REVISAO.md)

**Precedência:** decisões documentais R06/R07, política de memória e fontes canônicas do Google Drive > interfaces propostas aqui. Documentação oficial de fornecedores para capabilities; documentação do GitHub para estado do código; observações operacionais devem citar ambiente e instante. Não considerar documentação futura como funcionalidade publicada.

**Aprovação editorial da documentação** != **CI sintética** != **homologação EC2** != **aprovação de documento** != **aprovação de memória** != **produção**.

**Importante:** `main` foi observada em 18/11/2026 apenas com README inicial, embora haja notícia de ambiente Akamai em operação; não inferir que o runtime deriva do commit da `main`. Comparar digest e fonte real antes de qualquer decisão de merge/deploy.

