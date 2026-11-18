# Plano de acoplamento e evolução de branches — GAIA RAG Mini
**Data-base:** 2026-11-18 | **Finalidade:** acoplar módulos isolados sem interromper o conector em uso.

## 1. Topologia Git verificada (não é mera convenção)
Relação de PRs existente na consulta ao GitHub:

main
  └── PR #1: docs/r05-gaia-rag-homologacao -> main (aberta)
       └── PR #3: feat/r05-mcp-acl-offline -> docs/r05-gaia-rag-homologacao (aberta)
            └── PR #4: feat/r06-lifecycle-skill-staging -> feat/r05-mcp-acl-offline (draft)
                 └── PR #5: feat/r07-office-knowledge-assimilation -> feat/r06-lifecycle-skill-staging (draft)

As branches feat/ocr-documental-isolado e feat/catalogacao-triagem-isolada derivam de histórico R06 anterior e estão **divergidas** da R06 atual (consulta compare_commits em 18/11/2026):
- OCR versus R06: ahead_by=3, behind_by=2.
- Catalogação versus R06: ahead_by=2, behind_by=2.

Não há evidência de que OCR e catalogação estejam incorporadas ao runtime ou que possuam uma integração à R07. São laboratórios isolados. O arquivo GAIA_OCR_BRIDGE_IMPORT_README.md da branch OCR informa que parte da ponte depende de módulos drive1/ e nomenclature/ presentes no snapshot da branch catalogação. Essa dependência deve ser resolvida no momento da integração, sem importar pastas inteiras cegamente.

A main observada contém apenas o README inicial, não o conjunto R05/R06/R07. Ela precisa receber gradualmente a cadeia ou uma estratégia de rebase revisada; esta etapa não faz isso.

## 2. O que significa branch estática neste projeto
- **Baseline documental:** o conjunto de arquivos e testes é aceito para análise e preservado em um SHA exato; a PR permanece aberta em draft e não é integrada.
- **Nenhum deploy:** pipelines de publicação GHCR e Linode continuam com jobs bloqueados; staging CI é efêmero e sintético.
- **Nenhum acoplamento automático:** PR base permanece R06, não main; nenhuma sincronização de arquivos por nome no GitHub.
- **Congelamento administrativo, não técnico:** no momento da consulta, main e R07 retornaram protected=false. A API de rulesets devolveu 403 por exigência de plano GitHub superior para repositório privado; não há proteção de branch tecnicamente configurada por esta homologação.
- **Controle futuro:** qualquer alteração ao SHA homologado reinicia o aceite de regressão, exige atualização do termo, da topologia e nova CI.

## 3. Contratos para interfaces futuras
Separar quatro adaptadores, que só serão efetivos quando houver implementação e teste:
| Adaptador | Fonte de entrada | Envelope mínimo exigido | Não deve fazer |
|---|---|---|---|
| OCR | arquivo/página e derivado textual | original_id, derived_id, processo_id, páginas, idioma/método, qualidade, revisão, evidência | Memorizar OCR bruto ou alegar autenticação |
| Catalogação/triagem | dossiê, tipo e destino proposto | documento_id, cliente_id, processo_id, tipo, estado, fonte, confiança, classificação | Mover/renomear sem autorização |
| NOM e organização | regras e colisões verificadas | versão da regra, nome anterior/proposto, file_id, pasta origem/destino, decisão humana | Tratar proposta como execução |
| Editor PDF | split, merge, conversão e versão de documento | original_id, derivados, páginas, operação, hash quando confirmado, recibo | Descartar o original sem política arquivística |
| Curadoria R07 | dados reduzidos e fonte validada | process_id, source_ref, resumo, classificação, evidência, vínculo anterior | Gravar Qdrant, revogar memória ou invocar executores |
| Memória R06 | proposta documental aprovada | source_ref, document_approval_ref, document_sha256, process_id e resumo | Contornar clique humano/CSRF/readback |

Antes do acoplamento, negociar versão do envelope, valores obrigatórios/opcionais, compatibilidade backward, tratamento de documento sem process_id, política LGPD, validade temporal, idempotência, erro de OCR, recuperabilidade e rastreabilidade. A R07 ainda não materializa um protocolo externo interoperável com essas branches; o contrato atual é **proposta arquitetural**.

## 4. Ordem recomendada de integração
1. Validar na cadeia: PR #1 -> #3 -> #4, respeitando as aprovações e eventuais alterações de base. Não fazer merges cegos em lote.
2. Avaliar a PR #5 R07 **contra a R06 revisada**. Se R06 tiver avançado, calcular novo merge_base, reavaliar API da skill/portal e executar todos os testes antes do merge.
3. Preservar OCR e catalogação isoladas. Para cada uma, calcular compare_commits com a base atual e reconciliar as mudanças incrementais; resolver primeiro a dependência pontual OCR bridge <-> catalogação.
4. Criar uma PR de integração específica, pequena, que contenha apenas adaptadores necessários e testes ponta-a-ponta **com arquivos sintéticos**. Não copiar laboratórios inteiros diretamente em app/ e src/.
5. Testar desativação da integração, falha de fonte, hash divergente, OCR de baixa qualidade, colisão NOM, documento sem aprovação e prova de não-gravação Qdrant.
6. Após todas as PRs serem aprovadas e integrar main em ordem, publicar digest imutável e rodar homologação operacional somente com autorização separada; registrar rollback de versão anterior e readback.
7. Adicionar supersessão efetiva apenas após deliberação da Issue #6. Revisão candidata R07 não deve permitir que uma memória antiga desapareça dos resultados por inferência.

## 5. Política de compatibilidade e prevenção de colisão
- Ninguém duplica app/server.py, revisão R06, permissões Access ou política de memória numa outra branch. Mudança transversal requer contrato e PR de integração.
- O versionamento de cada branch deve declarar explicitamente sua dependência (ref + commit base) e identificar arquivos exclusivos versus arquivos compartilhados.
- Se duas branches alterarem SKILL.md ou app/server.py, fazer comparação semântica e testes de contrato antes de rebase/merge. Conflitos “resolvidos” sem revisão de comportamento não são homologação.
- Arquivos laboratórios de OCR/NOM sob docs/ não equivalem a runtime integrado. Regras de nomenclatura não são migradas silenciosamente para a memória.
- Evitar rebase após a assinatura de uma baseline congelada; se necessário, abrir nova revisão (ex. R07.1), preservar a antiga e registrar novo SHA/novo parecer.
- Uma CI verde do commit A não se transfere ao commit B.

## 6. Gates obrigatórios da integração
I-01: cadeia documental/PR e base exata verificadas.
I-02: contratos de dados e proveniência versionados com testes negativos/positivos.
I-03: avaliação de privacidade, autorização e segregação de fatos por processo.
I-04: CI e testes E2E sintéticos de OCR/PDF/NOM/curadoria/aprovação sob ambiente descartável.
I-05: rollback, idempotência, logs de evidência sem dados sensíveis e readback.
I-06: aceite humano da PR e autorização operacional de merge.
I-07: autorização separada de deploy, habilitação do runtime e exposição de ferramentas.
I-08: homologação real com documento autorizado, sem alterar originais indevidamente.

**Parecer de dependência:** a R07 está preparada para acoplamento **conceitual e contratual**, mas o acoplamento operacional com OCR/catálogo ainda não foi implementado nem homologado.
