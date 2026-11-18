#!/usr/bin/env bash
# Operational isolation check for R07 in a disposable GitHub-hosted runner.
# No secrets, no Cloudflare, no Qdrant client records, no public ports.
set -Eeuo pipefail
name="gaia-rag-r07-operational-ci"
image="gaia-rag-mini:r07-operational-$GITHUB_SHA"
cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker build --tag "$image" .
docker run --detach --name "$name" \
  --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cpus 1 --memory 768m --pids-limit 128 \
  --cap-drop ALL --security-opt no-new-privileges:true \
  -e GAIA_RAG_ENABLE_REVIEW=0 \
  "$image" >/dev/null

ready=0
for attempt in $(seq 1 30); do
  if docker exec "$name" python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read()" \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  docker logs "$name" --tail 35 || true
  echo 'R07_RUNTIME_NOT_READY' >&2
  exit 1
fi

docker exec -i "$name" python - <<'PY'
import json
import urllib.error
import urllib.request

base = "http://127.0.0.1:8000"
with urllib.request.urlopen(base + "/healthz", timeout=5) as res:
    health = json.load(res)
assert health["alive"] is True, health
assert health["service"] == "gaia-rag-mini-r07", health
assert health["mode"] == "staging-controlled", health
assert health["writes_enabled"] is False, health
assert health["qdrant_configured"] is False, health
assert health["approval_registry_configured"] is False, health
print("R07_01_HEALTH_STAGING_PASS")

def assert_denied(path, method, body=None):
    try:
        req = urllib.request.Request(
            base + path,
            data=body, method=method,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401, (path, exc.code)
    else:
        raise AssertionError("UNAUTHORIZED_REQUEST_ACCEPTED: " + path)

assert_denied("/mcp", "POST", b'{"jsonrpc":"2.0","id":1,"method":"tools/list"}')
print("R07_02_MCP_ANONYMOUS_DENY_PASS")
assert_denied("/review/11111111-1111-4111-8111-111111111111", "GET")
print("R07_03_REVIEW_ANONYMOUS_DENY_PASS")
assert_denied("/review/11111111-1111-4111-8111-111111111111/approve",
              "POST", b'{"confirm":"APROVAR"}')
print("R07_04_SAVE_ANONYMOUS_DENY_PASS")
assert_denied("/review/11111111-1111-4111-8111-111111111111/discard",
              "POST", b'{"confirm":"DESCARTAR"}')
print("R07_05_DISCARD_ANONYMOUS_DENY_PASS")
print("R07_EPHEMERAL_RUNTIME_SMOKE_PASS=5/5")
PY

network="$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$name")"
read_only="$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$name")"
public_ports="$(docker port "$name" 2>/dev/null || true)"
test "$network" = "none"
test "$read_only" = "true"
test -z "$public_ports"
echo 'R07_NO_PUBLIC_PORTS_READONLY_NETWORK_NONE_PASS'
