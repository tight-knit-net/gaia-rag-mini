# Plano de validação e homologação — GAIA Document MCP

**Status em 18/11/2026:** Gates D00-D02 podem ser executados em CI no núcleo sintético; todos os testes operacionais permanecem pendentes. Não extrapolar aprovação unitária para serviços reais.

| Gate | Teste / evidência exigida | Resultado inicial |
|---|---|---|
| D00 | GitHub branches, SHAs, arquivo de origem, main não tocada; baseline R07 | VERIFICADO no GitHub, sujeito a mudanças |
| D01 | Fontes oficiais, limitações, versão de API, licença e privacidade documentadas | REVISÃO DOCUMENTAL INICIAL |
| D02 | Compilação, schemas v1/v2, regressões sintéticas e checagem job-level dos workflows | PASSOU na CI do commit 6a5db124 (antes da documentação); revalidar HEAD documental |
| D03 | MCP server remoto funcional, autenticação OAuth/Access, negative tests por objeto | PENDENTE |
| D04 | Stirling Docker pinned digest, REST OCR com PDF nativo e scan, por/eng, hashes | PENDENTE |
| D05 | Pipeline OCR para NOM; campos revisados, vínculo NNN, rule_id, conflito e colisões | PENDENTE |
| D06 | E2E R07: duplicata/revisão/alegação/simulação e preview sem Qdrant write | PENDENTE |
| D07 | R06: fonte no registry, pedido de proposta, negativa sem aprovação, CSRF e readback | PENDENTE |
| D08 | DocuSeal via API e webhook verificado, assinatura DEMO, sem envio indevido | PENDENTE |
| D09 | Groq em dados sintéticos, minimização de contexto e proteção contra prompt injection | PENDENTE |
| D10 | Workspace: OAuth least privilege, shared drive, expected revision, rename/move readback | PENDENTE |
| D11 | Segurança/retention: arquivos temporários, Postgres, containers, redes, quotas, TTL, logs | PENDENTE |
| D12 | Suíte EC2 reproduzível com corpus sintético, SHA, relatórios e rollback sem produção | PENDENTE |
| D13 | Revisão humana do PR e gate de merge após anteriores | NÃO AUTORIZADO AINDA |
| D14 | Publicação Akamai, smoke remoto, observabilidade e aceite de cliente | NÃO AUTORIZADO AINDA |

## Evidência mínima por execução
Registrar: commit do código, hashes de arquivos de entrada e saída (fictícios), serviço/imagem/digest, versão das bibliotecas, operador autorizado, data/hora, comando, resultado, artefatos de teste, negativas esperadas, limitações, rollback e decisão. Não salvar segredos, arquivos reais nem assinaturas nos logs da CI.

## Casos obrigatórios
- PDF sem texto nativo -> OCR local -> revisão -> NOM preview; comparar seis campos conhecidos.
- PDF digital com texto -> extrair nativamente sem reprocessar desnecessariamente.
- Tesseract vs cliente legado `ocr_bridge.js`: teste negativo de incompatibilidade e teste positivo após atualização.
- DOCX: extrator nativo e preservação de estilo/versão quando aplicável.
- documento de cliente errado, terceiro, ETag/revisão alterada, SHA divergente, nome sem NNN, regra NOM ambígua, destino inexistente: **BLOQUEAR**.
- erro/quota API, interrupção depois de upload, webhook duplicado/fora de ordem: reconciliar por ID, não repetir às cegas.
- OCR não revisado, simulação, alegação, falta de documento no registry: não preparar memória aprovada.
- R07 relaciona histórico somente do processo exato; similaridade com cliente distinto é orientação analógica, não transposição de fato.
- tentativa de instrução maliciosa dentro de PDF: ignorar como comando, nunca acionar Drive/share/sign.
- exclusão temporária e SQL: provar os dois caminhos, sem alegar prova de eliminação física em fornecedor.
- `main` e deploy Akamai mantidos sem alterações durante toda a fase isolada.

## EC2
Ambiente de laboratório **existente** segundo documentação: `gaia-m7i`, pasta `/home/ubuntu/gaia-test-lab-homologacao`. A verificação SSH read-only de 18/11/2026 confirmou diretório e Python 3.12.3; não significa que a nova suíte foi instalada ou executada. Preparar checkout de branch e executar testes apenas em diretório isolado e com corpus DEMO, preservando os demais laboratórios.

## Homologação documental inicial
Parecer preliminar favorável **apenas a desenvolver em isolamento**. Versões, licenças, OAuth, dados de clientes, assinaturas e produção ficam sob gates próprios. Reexecutar CI no HEAD depois da publicação deste documento; se falhar, não conceder D02.

