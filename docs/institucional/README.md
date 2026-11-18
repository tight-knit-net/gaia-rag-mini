# GAIA OFFICE — Conhecimento institucional R07

Área de documentação, rastreabilidade e controle da camada de memória administrativa e assimilação. Não armazenar PDFs reais, arquivos de clientes, credenciais nem cópias de Qdrant.

Leia nesta ordem:
1. PROJETO_EXECUTIVO_R07.md — projeto executivo consolidado e critérios de aceite.
2. TERMO_HOMOLOGACAO_INICIAL_R07.md — parecer condicional, escopo e congelamento administrativo.
3. MATRIZ_RASTREABILIDADE_R07.md — fontes do Drive, requisitos e evidências.
4. PLANO_ACOPLAMENTO_BRANCHES_R07.md — cadeia real de PRs e interoperabilidade futura.
5. TOPOLOGIA.md — índice de 100% dos arquivos R07.
6. ARQUITETURA_MEMORIA_E_ASSIMILACAO_R07.md — arquitetura base, decisões e limites.
7. CONTRATOS_ENTRADA_DOCUMENTAL_R07.md — interfaces futuras OCR, catalogação, NOM e PDF.
8. PLANO_VALIDACAO_R07.md — teste e gates futuros.
9. REDMI.md — prevenção de colisões e registro de baseline; REDME.md — uso editorial.

Código vinculado: app/server.py, src/gaia_rag_r05/institutional_memory.py, tests/test_institutional_memory.py e skill gaia-rag-processos-administrativos.

Status: R07 em branch isolada, sem merge e sem deploy.

A documentação institucional completa de avaliação permanece no Google Drive 16; esta branch guarda os contratos, sínteses rastreáveis, testes e o projeto executivo. O estado de branch estática significa congelamento administrativo pelo SHA final registrado no comentário da PR #5, não branch protection técnica. Não modificar a baseline sem revalidar e documentar novo SHA.
