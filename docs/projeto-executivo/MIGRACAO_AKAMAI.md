# Plano reversível DigitalOcean → Linode/Akamai
**Estado:** não executado; depende de gates.

## Seleção
Candidato preferencial CONDICIONAL: nestground-ai (conta akamai-william, Miami). Docker funcional, quatro workloads NestGround, ~138GB livres e ~5,6GB de RAM disponível no snapshot. Comparativo: gogetterhub-nyc-vm (conta akamai-gogetterhub, Nova York) tem ~6,2GB de RAM disponível, porém ~42GB livres e vários serviços GAIA em operação. Decisão final após benchmark/cotas/isolamento.

## Pré-migração
1. Inspecionar o repositório/código real da Droplet, Dockerfile, compose, digest da imagem, storage /state, health endpoints e rotas do portal — sem ler nem copiar segredos.
2. Identificar origem e backup de propostas pendentes, TTL, chave de idempotência e mecanismo de readback humano.
3. Preparar imagem reproduzível fixada por digest, SBOM e varredura; definir CPU/RAM limites no Linode.
4. Subir candidato isolado, sem escrita real, em rede privada e com domínio de homologação protegido por Access, sem alterar memory.tight-knit.net.
5. Testar busca exata, isolamento, negativas, falha, portal, proposals e rollback em identidades e processos DEMO sintéticos.
6. Aprovar formalmente janela de mudança e rollback. Só então executar cutover controlado de ingress/tunnel.

## Rollback
Manter imagem/stack DO original operacional, captura de configuração do Tunnel/Access, backups e healthcheck. Se negar por ACL, persistir sem clique, perder portal, falhar health/latência, reverter ingress para origem anterior e validar read-only com identity autorizada. Não restaurar/recriar Qdrant, não executar duas escritas concorrentes e não declarar rollback ensaiado sem recibos.

## Itens vedados
Sem migração de dados Qdrant; sem alteração de embeddings, coleções, índices, políticas Access, autenticação ou aprovação humana.
