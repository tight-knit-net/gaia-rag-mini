# GAIA RAG & Knowledge — R07/G4: preflight de homologação no TestLab

**Versão:** 1.0.0
**Emissão:** 18/11/2026 às 19:52:09, fuso America/Sao_Paulo.
**Fonte verificável do horário:** utilitário de hora local do ChatGPT (retornou ISO 8601 `2026-11-18T19:52:09-03:00`).
**Repositório:** tight-knit-net/gaia-rag-mini
**Branch única de desenvolvimento:** feat/r07-office-knowledge-assimilation
**Pull request:** https://github.com/tight-knit-net/gaia-rag-mini/pull/5
**Referência anterior:** 81c4da2e8885cf145f175d594ce257a2369589d7
**CI do código novo:** https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44415584710
**Ambiente alvo:** SSH alias gaia-m7i, diretório exclusivo `/home/ubuntu/gaia-test-lab-homologacao/gaia-rag-r07-operational-d6f5a3e4-20261118`.
**Papel deste gate:** verificar o acesso de operação e preparar checagens não mutativas antes da implantação persistente, sem extrapolar a autorização para produção.

## Resultado executivo

**G4: BLOQUEADO para instalação persistente e homologação operacional.** O TestLab respondeu a leituras, mas a tentativa controlada de inicialização do diretório R07 foi recusada pelo executor com HTTP 503 `RECEIPT_CAPACITY` e `retry_safe=false`. O caminho não foi executado por outro canal. O readback posterior encontrou **diretório ausente** e **nenhum contêiner R07**.

**PASSOU na dimensão de software:** a atualização isolada criou o preflight `scripts/r07_testlab_preflight.py` e testes sintéticos `tests/test_r07_testlab_preflight.py`, cobrindo identidade de branch/HEAD, isolamento do workspace/container e negativa de homologação sem prova de implantação. A CI executou quatro jobs, todos concluídos com sucesso.

## Matriz de evidências

| Fase | Teste real realizado | Estado | Evidência/limitação |
| --- | --- | --- | --- |
| 1. Identidade do repositório | PR #5 draft; base R06; branch isolada | PASSOU | Consulta GitHub PR #5 |
| 2. Conector de memória | R06 Knowledge `controlled_staging`; gravação humana desativada | PROCESSADO | Resposta de `memory_status`, sem alterar memória |
| 3. Acesso de leitura TestLab | SSH gaia-m7i, verificação do diretório e contêineres | PASSOU | Diretório e contêiner R07 ausentes |
| 4. Inicialização de diretório R07 | Comando exclusivamente no caminho da candidata | FALHOU/BLOQUEADO | Executor HTTP 503 `RECEIPT_CAPACITY`; `retry_safe=false` |
| 5. Readback pós-bloqueio | SSH read-only de caminho e lista de contêineres | PASSOU | Diretório ausente, nenhum contêiner R07 |
| 6. Script de preflight somente leitura | Implementação R07 com validação de SHA, branch, workspace, rede, rootfs, portas | PASSOU em testes sintéticos | Não é implantação no host |
| 7. Regressão do HEAD de código | 4/4 jobs GitHub Actions concluídos com sucesso | PASSOU | https://github.com/tight-knit-net/gaia-rag-mini/actions/runs/44415584710 |
| 8. Instalação persistente e teste do portal real | Não executados | PENDENTE | Ausência de runtime candidato e bloqueio do executor |
| 9. Cloudflare Access com proprietário real | Não executado | PENDENTE | Não inserir credenciais no chat nem criar exceção de identidade |
| 10. Salvar memória real no piloto controlado | Não executado | PENDENTE | Requer Qdrant isolado e documento sintético previamente aprovado |
| 11. GroqCloud | Integração opcional desligada | NÃO ANALISADO operacionalmente | Nenhuma chave, custo ou transferência externa autorizada |
| 12. Migração/rollback/corte | Sem alteração do legado | NÃO EXECUTADO | Fora do gate atual |

## Evidências das mudanças

O arquivo `scripts/r07_testlab_preflight.py` é **somente leitura**. Ele recusa diretórios fora da área R07 e nomes de contêiner que não pertençam à candidata; inspeciona `git` e `docker inspect` sem executar `mkdir`, `docker run`, `docker stop` ou quaisquer alterações remotas. Mesmo quando todas as verificações locais estão corretas, mantém `testlab_homologated=false`: o script não faz alegações de homologação por si só.

O arquivo `tests/test_r07_testlab_preflight.py` cobre diretório válido/inválido, filtro do nome de contêiner, ausência de diretório, SHA inválido, cenário sintético de contêiner isolado e detecção de contêiner não isolado. Nenhuma informação de clientes é utilizada.

## Riscos, dependências e critérios do próximo gate

1. **Bloqueio de execução:** o executor exige recibos, mas retornou `RECEIPT_CAPACITY` com `retry_safe=false`. Não contornar por outro host, canal SSH ou ferramenta de escrita. O operador responsável precisa restaurar a operação de maneira regular e informar que a capacidade foi restabelecida; verificar de novo o ambiente antes de qualquer mutação.
2. **Repositório privado:** no inventário anterior do TestLab, o `git ls-remote` não tinha autenticação utilizável. Uma entrega de artefato/checkout deverá usar mecanismo autorizado, sem colocar token/segredo em chat ou log.
3. **Candidato sem runtime real:** a R07 está na branch e passou testes de laboratório, mas **não está implantada no TestLab persistente**.
4. **Botão Salvar memória:** preservado na candidata, mas ainda não testado no portal real autenticado Cloudflare Access. Nunca declarar gravação autorizada apenas por teste sintético.
5. **Coleção e fila legada:** permaneceram intactas. Pontos aprovados e propostas pendentes exigem reconciliação posterior, sem promover propostas pendentes a aprovadas.

**Critério de avanço:** executor autorizado com recibos operacionais, checkout R07 do commit exato em diretório exclusivo, contêiner e dados estritamente sintéticos, verificação de identidade autenticada, aprovação humana real e readback demonstrados, além de backup/rollback e decisão GO documentada.

**Rollback desta etapa:** nenhum rollback de serviços/dados é necessário; TestLab permanece sem diretório R07 ou contêiner novo. Todo código criado está no ramo R07 e pode ser revisado/revertido na PR #5 sem tocar R06, main, DNS, Cloudflare, Qdrant real ou legado.

**Decisão:** NO-GO para ativação da candidata, migração de memórias e desativação do legado. Nenhuma etapa posterior foi disparada.
