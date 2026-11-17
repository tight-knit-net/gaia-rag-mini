# Gates de homologação R05
Evidências exigidas para cada cenário: data/hora, executor, commit, hash de imagem, host, entradas DEMO, trace sanitizado, resultado, decisão e link.

| Gate | Critério observável | Estado 17/11/2026 |
|---|---|---|
| G00 | R04/R03.1 intactas; repo e branch R05 isolados | PARCIAL |
| G01 | YAML/JSON/Python parse, recursos internos, hashes e ZIP | PENDENTE na R05 |
| G02 | SAST, segredos, SBOM, dependências e imagem imutável | PENDENTE |
| G03 | Código/imagem real da Droplet e Cloudflare inventariados | PARCIAL |
| G04 | Skills over MCP list/get/resources-read ou plugin empacotado | NÃO EXECUTADO |
| G05 | Seleção e ativação efetiva no host ChatGPT/Work | NÃO EXECUTADO |
| G06 | Busca exata por process_id autorizado, fontes/status/jurisdição | NÃO EXECUTADO |
| G07 | Identidades sintéticas A/B isoladas também por UUID/source/similaridade | NÃO EXECUTADO |
| G08 | Aprovação documental, síntese atômica/dedup e prepare sem persistência | NÃO EXECUTADO |
| G09 | Portal humano, Access, clique explícito, readback e auditoria | NÃO EXECUTADO |
| G10 | Falha segura, replay, timeout, redes e testes negativos | NÃO EXECUTADO |
| G11 | Cutover Linode, disponibilidade, performance e rollback ensaiado | NÃO EXECUTADO |
| G12 | CodeRabbit ou revisão independente, CI e PR aprovado | NÃO VERIFICADO |

Sem G02 e G04–G12 comprovados, NÃO implantar em produção nem declarar a skill homologada. Testes locais da R04 são evidência histórica documental, não substituto.
