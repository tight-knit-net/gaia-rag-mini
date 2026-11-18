#!/usr/bin/env bash
# GAIA RAG Mini R05 - host-local staging installation, never production cutover.
# Run as root on nestground-ai with the checked-out repo as the only argument.
set -Eeuo pipefail
umask 077
SOURCE="${1:-$PWD}"
BASE=/opt/gaia-rag-mini
COMPOSE="$BASE/staging/compose.yml"
RUNTIME_ENV="$BASE/secrets/runtime.env"
IMAGE_FILE="$BASE/staging/.env"
BACKUP="$(mktemp)"
PREVIOUS=''
SUCCESS=0
cleanup() {
  if [[ "$SUCCESS" != 1 ]]; then
    if [[ -s "$BACKUP" ]]; then
      cp "$BACKUP" "$IMAGE_FILE"
      chmod 600 "$IMAGE_FILE"
      docker compose --project-directory "$BASE/staging" -f "$COMPOSE" up -d --pull never --no-build --wait --wait-timeout 90 || :
    else
      rm -f "$IMAGE_FILE"
      docker compose --project-directory "$BASE/staging" -f "$COMPOSE" stop || :
    fi
  fi
  rm -f "$BACKUP"
}
trap cleanup EXIT
[[ "$(id -u)" == 0 ]] || { echo "Run as root on the intended staging host" >&2; exit 2; }
[[ "$(hostname -s)" == "nestground-ai" ]] || { echo "Refusing wrong host" >&2; exit 2; }
[[ -f "$SOURCE/Dockerfile" && -f "$SOURCE/app/server.py" ]] || { echo "Missing R05 runtime sources" >&2; exit 2; }
[[ -f "$COMPOSE" && -f "$RUNTIME_ENV" && ! -L "$RUNTIME_ENV" ]] || { echo "Staging preflight incomplete" >&2; exit 2; }
grep -Fxq 'RAG_STAGING_APPROVED=1' "$RUNTIME_ENV" || { echo "Staging gate not approved" >&2; exit 2; }
grep -Fq '127.0.0.1:18081:8000' "$COMPOSE" || { echo "Staging must bind to loopback only" >&2; exit 2; }
if [[ -f "$IMAGE_FILE" ]]; then cp "$IMAGE_FILE" "$BACKUP"; fi
COMMIT="$(git -C "$SOURCE" rev-parse --verify HEAD)"
[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] || exit 2
IMAGE="gaia-rag-mini:staging-${COMMIT:0:12}"
echo "Building R05 isolated image locally: $IMAGE"
docker build --pull -t "$IMAGE" "$SOURCE"
printf 'RAG_IMAGE=%s\n' "$IMAGE" > "$IMAGE_FILE"
chmod 600 "$IMAGE_FILE"
docker compose --project-directory "$BASE/staging" -f "$COMPOSE" config -q
docker compose --project-directory "$BASE/staging" -f "$COMPOSE" up -d --pull never --no-build --wait --wait-timeout 90
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18081/healthz > /tmp/gaia-rag-r05-install-health.json; then
    break
  fi
  sleep 2
done
python3 - <<'PY'
import json
with open('/tmp/gaia-rag-r05-install-health.json') as f:
    status=json.load(f)
assert status.get('alive') is True
assert status.get('mode') == 'staging-read-only'
assert status.get('writes_enabled') is False
PY
rm -f /tmp/gaia-rag-r05-install-health.json
STATUS="$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  http://127.0.0.1:18081/mcp)"
[[ "$STATUS" == 401 ]] || { echo "Unauthenticated MCP unexpectedly returned HTTP $STATUS" >&2; exit 1; }
SUCCESS=1
echo "INSTALLED_STAGING image=$IMAGE host=nestground-ai loopback_port=18081 writes=disabled"
