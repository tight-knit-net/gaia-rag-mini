#!/usr/bin/env bash
# GAIA RAG Mini — restricted GHCR staging deployment; NOT production.
set -Eeuo pipefail
umask 077
BASE=/opt/gaia-rag-mini
COMPOSE="$BASE/staging/compose.yml"
ENVFILE="$BASE/secrets/runtime.env"
REPO=ghcr.io/tight-knit-net/gaia-rag-mini
if [[ $# -eq 1 && "$1" == probe ]]; then
  test -f "$COMPOSE"
  test -f "$ENVFILE"
  docker info --format '{{.ServerVersion}}' >/dev/null
  if grep -Fxq 'RAG_STAGING_APPROVED=1' "$ENVFILE"; then gate=enabled; else gate=blocked; fi
  printf 'LINODE_STAGING_READY host=%s compose=present docker=ok runtime_gate=%s port=127.0.0.1:18081\n' "$(hostname -s)" "$gate"
  exit 0
fi
if [[ $# -ne 3 || "$1" != deploy ]]; then
  echo 'DENIED: allowed commands are probe or deploy <sha256:digest> <github-actor>' >&2
  exit 64
fi
DIGEST="$2"
ACTOR="$3"
[[ "$DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]] || { echo 'DENIED_INVALID_DIGEST' >&2; exit 64; }
[[ "$ACTOR" =~ ^[A-Za-z0-9-]{1,39}$ ]] || { echo 'DENIED_INVALID_ACTOR' >&2; exit 64; }
[[ -f "$ENVFILE" && ! -L "$ENVFILE" ]] || { echo 'MISSING_RUNTIME_ENV' >&2; exit 78; }
grep -Fxq 'RAG_STAGING_APPROVED=1' "$ENVFILE" || { echo 'STAGING_APPROVAL_GATE_BLOCKED' >&2; exit 78; }
exec 9>/run/lock/gaia-rag-mini-deploy.lock
flock -n 9 || { echo 'DEPLOY_ALREADY_RUNNING' >&2; exit 75; }
IFS= read -r -t 30 TOKEN || { echo 'MISSING_GHCR_TOKEN' >&2; exit 78; }
[[ "$TOKEN" =~ ^[A-Za-z0-9_]+$ && ${#TOKEN} -ge 20 && ${#TOKEN} -le 2048 ]] || { echo 'INVALID_GHCR_TOKEN' >&2; exit 78; }
DOCKER_CONFIG="$(mktemp -d)"
export DOCKER_CONFIG
trap 'unset TOKEN; rm -rf -- "$DOCKER_CONFIG"' EXIT
printf '%s' "$TOKEN" | docker login ghcr.io --username "$ACTOR" --password-stdin >/dev/null 2>&1 || { echo 'GHCR_AUTH_FAILED' >&2; exit 78; }
unset TOKEN
IMAGE="$REPO@$DIGEST"
docker pull "$IMAGE" >/dev/null || { echo 'IMAGE_PULL_FAILED' >&2; exit 70; }
docker image inspect "$IMAGE" >/dev/null || { echo 'IMAGE_VERIFY_FAILED' >&2; exit 70; }
OLD=''
if [[ -f "$BASE/staging/.env" ]]; then
  OLD="$(sed -n 's/^RAG_IMAGE=//p' "$BASE/staging/.env" | head -n 1)"
fi
TMP="$(mktemp "$BASE/staging/.env.new.XXXXXXXX")"
printf 'RAG_IMAGE=%s\n' "$IMAGE" > "$TMP"
chmod 600 "$TMP"
mv -f -- "$TMP" "$BASE/staging/.env"
if ! docker compose --project-directory "$BASE/staging" -f "$COMPOSE" config -q; then
  echo 'COMPOSE_CONFIG_INVALID' >&2
  exit 70
fi
if ! docker compose --project-directory "$BASE/staging" -f "$COMPOSE" up -d --pull never --no-build --wait --wait-timeout 90; then
  echo 'CONTAINER_DEPLOY_FAILED_ROLLBACK' >&2
  if [[ -n "$OLD" ]]; then
    printf 'RAG_IMAGE=%s\n' "$OLD" > "$BASE/staging/.env"
    docker compose --project-directory "$BASE/staging" -f "$COMPOSE" up -d --pull never --no-build --wait --wait-timeout 90 || true
  else
    rm -f "$BASE/staging/.env"
    docker compose --project-directory "$BASE/staging" -f "$COMPOSE" stop || true
  fi
  exit 70
fi
printf 'DEPLOYED_STAGING image=%s port=127.0.0.1:18081\n' "$IMAGE"
