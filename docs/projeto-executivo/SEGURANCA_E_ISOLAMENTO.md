# Segurança, segregação e aprovação
**Status:** princípios documentados; não homologado no backend.

1. Identidade e autorização por tenant/processo devem ser verificadas no servidor, incluindo buscas por fonte, UUID e casos similares. `namespace=chatgpt` é insuficiente para demonstrar isolamento.
2. Não aceitar instruções contidas em memórias recuperadas como comandos ou autorização.
3. Distinguir estados: aprovação documental -> proposta de memória -> revisão e clique humano no portal Access -> escrita persistida no Qdrant -> readback/auditoria. Nunca confundir aprovação documental com deferimento administrativo.
4. `memory_prepare_after_approval` cria apenas proposta; não usar como prova de persistência.
5. Sintetizar lembrança atômica com fonte, process_id, datas, jurisdição, status da evidência e deduplicação dentro do processo; não usar documentos brutos ou conversas completas.
6. Homologar em sandbox com usuários A/B e processos DEMO-A/DEMO-B, incluindo isolamento negativo por filtros, correspondência semântica, UUID/source e similaridade.
7. Registrar logs mínimos sem PII, segredos, conteúdo sensível ou tokens. Falha de autorização deve retornar negação, sem fallback permissivo.
8. Preservar `chatgpt_memoria_aprovada`, esquema vetorial e índices; alterações de embedding/ACL demandam projeto e aprovação próprios.
