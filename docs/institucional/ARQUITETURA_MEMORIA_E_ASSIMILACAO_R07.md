# R07 — Arquitetura de assimilação institucional

Data-base: 2026-11-18. Situação: branch isolada; não implantada.

## Princípio
A GAIA OFFICE poderá usar a memória associada a PDF, OCR, catalogação, nomenclatura, revisão, documentos e processos administrativos. A fonte canônica permanece no Drive e nos autos: Qdrant guarda somente sínteses selecionadas e aprovadas.

## Seis níveis que não devem ser confundidos
1. Original documental: arquivo, ID, versão, páginas, hash quando verificado.
2. Observação derivada: OCR, classificação e conferência; OCR sem revisão não é prova.
3. Memória de processo: fatos, atos, checkpoints, pendências e origem do caso exato.
4. Conhecimento do escritório: modelos, regras, checklists e procedimentos aprovados.
5. Precedente/norma: ato confirmado, fonte oficial, competência e vigência verificada.
6. Sabedoria institucional: lição revisada do que funcionou, não funcionou e limites de reaplicação.

## Ciclo operacional
Documento original -> leitura e validação -> classificação -> comparação com memória do processo -> prévia sem escrita -> aprovação documental registrada -> proposta MCP R06 -> botão humano no portal protegido -> escrita e readback -> recuperação contextualizada futura.

A nova ferramenta memory_assimilation_preview localiza memórias do processo exato, detecta duplicata exata, relação por título, possível revisão pela mesma fonte ou pelo ID anterior e declara cobertura parcial quando a paginação não foi integral. Nunca grava, altera, revoga ou despublica pontos. Uma revisão não se torna vigente por pontuação do vetor ou data isolada.

## Evolução sem apagar histórico
Se um documento mais preciso contraria memória aprovada, preparar análise ANTES/DEPOIS contendo ID anterior, evidência nova, fonte, versão, jurisdição, data comprovada, efeito e limites. O registro antigo continuará recuperável até existir uma política de supersessão transacional homologada. Na R07, a superação é somente candidata.

## Segurança e integração
Manter acesso transversal do proprietário verificado definido na R06. O process_id identifica o caso, não cria ACL por cliente. Não copiar fatos privados entre casos semelhantes; conservar minimização LGPD. Não promover simulações, alegações ou OCR não validado a fatos comprovados.

## Fronteiras desta PR
Implementado: prévia institucional read-only, skill, documentação, testes sintéticos.
Não implementado: atualização/revogação Qdrant, integrações OCR/PDF/NOM, ativação universal da skill, implantação Cloudflare, homologação de dados reais, merge main.

## Fluxo das PRs
R06 permanece com PR #4 em draft. A R07 deriva da R06 e deverá ser revisada contra R06 primeiro. Integração main só após gates da linha base e autorização explícita de publicação. Nenhum deploy nesta PR.
