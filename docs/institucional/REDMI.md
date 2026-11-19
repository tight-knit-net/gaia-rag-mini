# REDMI — Protocolo de gravação e indexação

1. Antes de escrever, conferir README.md, REDME.md, TOPOLOGIA.md e arquivos existentes na branch.
2. Verificar nome e finalidade, não criar segunda fonte de verdade e não sobrescrever sem conferir o blob SHA atual.
3. Registrar cada novo arquivo na topologia com caminho, finalidade, situação, dependências e data.
4. Em revisão de documento, preservar história de fonte/versão; em atualização de memória, preservar origem e status da revisão humana.
5. Não gravar dados pessoais de clientes, segredos, PDFs ou conteúdo bruto em documentação e testes.
6. Não declarar PR, arquivo ou síntese como aprovação, homologação, merge ou publicação.

## Marco de congelamento R07
Após a homologação inicial, qualquer modificação na branch exige decisão de reabertura, confronto com a baseline SHA da PR #5, atualização de TOPOLOGIA.md e MATRIZ_RASTREABILIDADE_R07.md, novos testes e revisão do TERMO_HOMOLOGACAO_INICIAL_R07.md. A PR draft é uma salvaguarda de processo, não impede pushes. O GitHub não apresentou proteção de branch habilitada para R07.
