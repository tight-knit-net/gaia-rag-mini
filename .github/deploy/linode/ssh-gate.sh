#!/usr/bin/env bash
# SSH forced-command gate: no interactive shell or arbitrary remote command.
set -Eeuo pipefail
ORIG="$SSH_ORIGINAL_COMMAND"
if [[ "$ORIG" == probe ]]; then
  exec sudo -n /usr/local/sbin/gaia-rag-mini-deploy probe
fi
if [[ "$ORIG" =~ ^deploy[[:space:]](sha256:[a-f0-9]{64})[[:space:]]([A-Za-z0-9-]{1,39})$ ]]; then
  exec sudo -n /usr/local/sbin/gaia-rag-mini-deploy deploy "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
fi
echo 'SSH_COMMAND_DENIED' >&2
exit 64
