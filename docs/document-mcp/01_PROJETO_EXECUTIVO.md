# GAIA Document MCP — projeto executivo v0.1

Data: 18/11/2026. Estado: **projeto definido, fase inicial isolada, sem integração operacional homologada**.

## 1. Objetivo e escopo
Disponibilizar ao ChatGPT (ou outro cliente MCP autorizado) uma **interface documental central** para solicitar leitura de arquivos, OCR, processamento de PDF, formulários, assinaturas, catalogação/nomenclatura e operações pontuais do Google Workspace. Uma chamada gera eventos estruturados que podem ser examinados pela R07; só **memórias documentais aprovadas** seguem à R06/Qdrant.

O GAIA RAG Mini **não passa a ser o executor de PDFs/Drive**. Ele mantém a semântica de memória e o registro oficial de aprovação de documentos. O novo MCP orquestra adaptadores; não substitui as políticas do Drive1 nem a autoridade de nomes NOM.

## 2. Separação de responsabilidades
- **ChatGPT/LLM**: intenção do usuário, resposta, planejamento. Modelos não têm permissão implícita para escrever nem afirmam fatos sem evidência.
- **GAIA Document MCP**: roteamento, autorização por ferramenta/objeto, limites de lote, idempotência, orquestração, recibos, auditoria e lifecycle de temporários.
- **Stirling-PDF**: PDF/OCR/Office convertidos, preferencialmente em ambiente próprio; original preservado, derivados individualizados.
- **OCR legado**: laboratório independente, contrato comparado antes de migração; não duplicar leitores nem promover de uma vez.
- **Organizador/NOM GAIA**: cliente NNN, origem, manifesto, destino, evidência, revisão da regra, preview e leitura posterior. Controle de MOVE/RENAME continua fora da LLM.
- **GroqCloud**: LLM auxiliar opcional para classificação e sugestão de campos. Sem envio de dados pessoais por padrão; usar apenas com política, consentimento/base legal, minimização e aprovação aplicável.
- **DocuSeal**: criação de template, preparo de campos, solicitações de assinatura e eventos finais; envio/autorização exigem aceite explícito.
- **Workspace**: Drive como fonte canônica de arquivos, Docs/Sheets como artefatos editáveis. Access delegated/OAuth e permissões por recurso.
- **R07**: compara sínteses candidatas com memórias aprovadas por processo exato e sinaliza duplicatas/revisões; nunca substitui registro anterior automaticamente.
- **R06 + Qdrant**: entrada exclusiva da memória persistente aprovada com registro documental, clique humano via portal e readback.

## 3. Linha de processamento
```text
ChatGPT / cliente MCP autorizado
   -> Gateway GAIA Document MCP (identidade, escopo, políticas)
   -> Drive/Docs/Sheets (ler metadados e original por ID)
   -> cópia temporária verificada SHA-256 (só se necessária)
   -> texto nativo OU Stirling-PDF OCR (página/método/idioma/qualidade)
   -> revisão de campos, vínculo do cliente e processo
   -> motor NOM e topologia (PREVIEW / bloqueios / aprovação independente)
   -> registro operacional e derivado autorizado no Drive
   -> extrator de aprendizagem: candidato institucional seletivo
   -> R07 preview (process_id/source_ref, histórico e evidência)
   -> R06 documento aprovado + aprovação humana + readback
   -> Qdrant (síntese aprovada, não conteúdo bruto de OCR)
```

Quando o usuário editar PDF, uma nova versão/derivado gera evento com o hash do original e do derivado. Quando o usuário assinar, webhook não prova sozinho assinatura final; exige reconciliação de status, IDs e documento gerado.

## 4. Duas camadas de conhecimento
**Registro operacional automático** pode guardar fatos da execução (evento, hash, objeto, tentativas, status, erro e recibo, sem OCR bruto), desde que backend de retenção seja implementado e autorizado. **Memória institucional** exige triagem semântica e aprovação da fonte e da memória. Não confundir registro operacional com aprovação de mérito.

A R07 pode rejeitar conhecimento repetido ou indicar revisão. A R06 mantém a única autorização para gravação Qdrant. Se aprovação humana estiver desabilitada, só existe proposta editorial; nunca alegar nova memória persistida.

## 5. Ferramentas de alto nível previstas
`document.inspect`, `document.ocr`, `document.pdf_transform`, `document.catalog_preview`, `document.name_preview`, `document.workspace_read`, `document.workspace_write`, `document.prepare_signature`, `document.send_signature`, `document.external_ai`, `document.memory_preview`, `document.memory_prepare`.
Elas estão **catalogadas no código**, mas ainda não foram registradas como ferramentas MCP remotas. Nomes são interface interna proposta, não funções dos vendors.

Google Drive/Docs/Sheets podem ser disponibilizados como operações nativas secundárias. Evitar centenas de ferramentas sem limites; para chamadas externas impor whitelist, parâmetros de escopo, paginação, rate limits e configuração dinâmica de visibilidade.

## 6. Roadmap e dependências
P0: documentos, contratos, testes unitários e branch isolada.
P1: servidor MCP autenticado e registros duráveis em sandbox (sem rede pública).
P2: adaptador Stirling-PDF + OCR real por página, qualidade e OCR/nativo.
P3: adaptador NOM/triagem com inputs revisados e prefixo NNN; reconciliar branches irmãs.
P4: R07 preview e R06 proposta, sem contornar portal de aprovação.
P5: DocuSeal e Groq; Workspace com OAuth e controles de dados; Dropbox/Notion se necessário.
P6: EC2 e2e sintético, negativo de ACL, digest, snapshot, rollback, homologação humana.
P7: integração final na main, digest de imagem e deploy somente com autorização separada.

## 7. Critérios não negociáveis
Nunca mover/renomear/excluir Drive por inferência. Jamais enviar documentos a LLM externo sem autorização, nunca assinar/enviar a terceiros por inferência. Não expor PostgreSQL, MCP OCR, API PDF e Qdrant publicamente. Separar logs dos binários, configurar retenção real e exclusão verificável. Não misturar evidências de dois clientes num processo e não inferir aprovação jurídica por sucesso técnico.

