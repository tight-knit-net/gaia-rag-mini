# Linode staging gateway — GAIA RAG Mini

## Deployment architecture
- Origin: GitHub repository `tight-knit-net/gaia-rag-mini` private, branch `main`.
- Build: `rag-ghcr-image.yml` (only after Dockerfile/runtime code present) to private GHCR package with SHA/digest.
- Deploy: `rag-linode-staging.yml` must be manually dispatched with `mode=preflight` or `mode=deploy` and an explicit immutable image digest.
- GitHub secret: repository-level `LINODE_DEPLOY_KEY` (private SSH key, never committed). The generated public key is installed in a forced-command account on Linode.
- Host key: pinned in `.github/deploy/linode/known_hosts` (fingerprint SHA256:ZMZvkvsd4M0EChR+UFXjBVyPxPtpYyArfDlqwcs4XbQ).
- Linode hostname `nestground-ai`, account `akamai-william`, SSH user `gaia-rag-deploy`; host code in `/usr/local/sbin/gaia-rag-mini-deploy`; Compose `/opt/gaia-rag-mini/staging/compose.yml`.
- Container `gaia-rag-mini-staging` exposed ONLY at `127.0.0.1:18081`; 1 CPU, 1GiB RAM, distinct local volume/network. Original DigitalOcean MCP/Cloudflare/Qdrant untouched.

## Staging verified on 17/11/2026

An isolated **local Docker build** was installed on `nestground-ai` as `gaia-rag-mini-staging`, image `gaia-rag-mini:staging-77e487efef29`, with loopback port `18081`. `healthz` returned 200; unauthenticated MCP returned 401. The Docker network must use `172.19.41.0/24`; the original dynamically allocated `172.17.0.0/16` was intercepted by the host Cloudflare WARP routing table and prevented host HTTP access. This host installation was manual; GHCR and GitHub Actions deployment workflows remain disabled.

No Qdrant secrets, Cloudflare JWT configuration or per-client grants were installed, and no production migration occurred. Read-only health is **not** end-to-end functional readiness. See [staging diagnostic](../../docs/projeto-executivo/RELATORIO_STAGING_INSTALACAO_2026-11-17.md).

## Existing GHCR deployment path (future authorization only)
1. In repository Settings > Secrets and variables > Actions > New repository secret, add `LINODE_DEPLOY_KEY` using the supplied PRIVATE key file. Never paste a key into issues, PRs, chat, or workflow YAML.
2. Authorize CodeRabbit via GitHub app for this repo; automatic reviews are configured by `.coderabbit.yaml`. Draft PR review is enabled, but the GitHub App must have access.
3. After approved code lands on `main`, build a GHCR image and check the resulting digest. Configure GHCR package access for this repository if GitHub does not link it automatically.
4. On Linode, staging runtime configuration is deliberately disabled: `/opt/gaia-rag-mini/secrets/runtime.env` has no Qdrant/Cloudflare credentials and must explicitly include `RAG_STAGING_APPROVED=1` after synthetic backend, identity and approval portal are prepared. Do not use real production secrets before homologation.
5. Trigger manual preflight. Trigger `deploy` only with code/image reviewed and the staging approval gate intentionally enabled.

## Safeguards
No automatic production deploy, no public container port, no privileged runner on Linode, no preinstalled secrets, no changes to existing Cloudflare Tunnel/Access policies or Qdrant schema. GitHub token for GHCR is sent over pinned SSH stdin and not persisted on disk; deployment key is restricted to a forced command and the host script accepts only a fixed image repository and valid SHA-256 digest. If code has not been delivered, build is intentionally blocked.

## User-facing verification
GitHub Actions preflight is UNTESTED until `LINODE_DEPLOY_KEY` is configured and the workflow exists on `main`. Host SSH alias/installation will be tested independently by the admin connector before claiming readiness.
