# Evidência operacional — PostgreSQL temporário para OCR (18/11/2026)

**Ambiente:** EC2 GAIA Test Lab, via SSH alias gaia-m7i. Nenhum PDF real de cliente foi carregado.

**Imagem utilizada:** postgres:16-alpine (imagem existente agora em cache EC2). Banco PostgreSQL 16.16.

**Segurança conferida:**
- Docker network internal:true, nenhum acesso externo necessário.
- Nenhuma porta do PostgreSQL publicada no host; inspeção Docker mostrou "5432/tcp":null.
- PGDATA em tmpfs com limite 512 MiB, root filesystem read-only, sem volume persistente do banco.
- Credencial temporária criada fora do repositório em diretório 0700 e arquivo modo 0600, montado read-only no container e depois descartado.
- Usuário do processo DB UID 70, sem capacidades Linux adicionais, no-new-privileges.

**Provas executadas:**
1. A imagem PostgreSQL 16 foi baixada com sucesso.
2. Um container temporário isolado com PGDATA tmpfs recebeu DDL de tabela sintética e uma linha de teste via psql.
3. O template pilot/ocr_postgres_tmpfs.compose.yaml foi iniciado em ambiente de QA com docker compose --wait e passou o healthcheck.
4. O comando SQL de escrita, leitura e verificação retornou TESTED.
5. O script pilot/scripts/temp_pg.sh foi executado com operação start em lote fictício, seguida de consulta SQL e operação stop com --commit após relatório de teste.
6. O container, a rede Docker e a credencial desapareceram após a operação de descarte; não restaram dados no volume do banco. Os originais do Drive 1 não foram acessados nem alterados nesta prova.

**Limites:** é descarte lógico de dados em memória pelo ciclo do container. Não constitui prova de apagamento físico contra swap, snapshots externos ou mecanismos de recuperação de hardware. Este teste valida o banco, **não** comprova que a API OCR esteja instalada ou rodando nem executou OCR real.

**Pendências do OCR encontrado em outro worktree:** código localizado em gaia-drive15-ocr-isolated, branch feature/ocr-iloveapi (f02e99e na inspeção), serviço não estava rodando e .env ausente. Atualização observada depois: commit 1421e3e inclui restore.py, corrigindo essa pendência. Compose OCR passou a usar network_mode host e volume persistente pgdata, ainda NÃO vinculado ao banco isolado tmpfs. Não modificado para evitar conflito com desenvolvimento independente.

**Ponte documental:** o repositório de nomenclatura contém pilot/ocr_bridge.js e pilot/ocr_batch.js com 86/86 testes sintéticos e protocolo REST local simulado; não faz escrita no Drive 1.
