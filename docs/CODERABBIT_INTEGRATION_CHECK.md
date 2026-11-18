# Verificação de recepção de eventos CodeRabbit (não operacional)

Este arquivo é um teste de integração da GitHub App CodeRabbit com o repositório privado `tight-knit-net/gaia-rag-mini`.

O objetivo é provocar o evento `pull_request.opened` em um PR novo e obter resposta do CodeRabbit. Não representa feature, código de aplicação, aprovação de arquitetura, publicação de release ou autorização de execução.

Critério: deve surgir comentário, review ou check gerado efetivamente por `coderabbitai` neste PR. Se não surgir, a integração não está comprovadamente funcional mesmo com a configuração de revisão ativa, e deverão ser verificados instalação no repositório, seat, webhooks e permissões da GitHub App.
