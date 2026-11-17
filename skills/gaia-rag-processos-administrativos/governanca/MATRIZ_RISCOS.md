# Matriz de risco operacional e documental — R04

| ID | Risco e severidade | Controle da skill | Validação restante |
|---|---|---|---|
| R01 | **Crítico**: memória de cliente B usada no caso A | processo exato; pós-verificação de UUID/fonte; analogia bloqueada sem autorização | teste ACL multiusuário em sandbox — NÃO EXECUTADO |
| R02 | **Crítico**: proposta preparada antes da aprovação do documento | gate de aprovação documental explícito | instrumentação em host de teste — NÃO EXECUTADO |
| R03 | **Crítico**: suposta memória aprovada sem clique humano | distingue proposta, revisão, persistência | fluxo portal em ambiente autorizado — NÃO EXECUTADO |
| R04 | Alto: norma municipal antiga apresentada como vigente | fonte oficial, data, ente e artigo; marcar revalidação | casos locais concretos exigem pesquisa atual |
| R05 | Alto: documento interno confundido com deferimento | categorias de ato separadas | regressão textual/sandbox |
| R06 | Alto: prompt injection de fonte recuperada | tratar retornos como dados, não comandos | teste adversarial no host — NÃO EXECUTADO |
| R07 | Alto: vazamento de dados pessoais ou segredo na proposta | minimização antes de consulta e síntese | revisão LGPD de operação real |
| R08 | Médio: arquivo `SKILL.md` inválido/empacotamento defeituoso | YAML real, manifest, testes de ZIP | importar e inspecionar skill no Work |
| R09 | Alto: suposta revogação automática de ponto Qdrant | não declarar mudança que a MCP não expõe | procedimento técnico futuro, fora de escopo |
| R10 | Médio: relação entre processo, cliente e assunto incorreta | ontologia/editorial; UUID exato | validação por fonte original |
| R11 | Médio: ISO ou AGU tratadas como certificação/lei do caso | distinguir referência institucional/ISO pública de obrigação legal | revisão jurídico-institucional |
| R12 | Médio: TTL e quota assumidos permanentes | reconsultar política em uso | revalidação na instalação |
| R13 | Alto: automação inferir autorização por `namespace=chatgpt` | não equiparar namespace e ACL | backend a homologar |
| R14 | Médio: versão R02 proposta confundida com estado AS-IS | matriz de evidências separando tipos | inventário técnico quando aprovado |

**Escala:** `Crítico`: bloquear aplicação ou proposta; `Alto`: exige fonte/controle antes de decisão; `Médio`: ressalva e checagem. Esta matriz não é pentest nem DPIA concluído.
