#!/usr/bin/env bash
set -euo pipefail

VAULT_ADDR=${VAULT_ADDR:-http://127.0.0.1:18200}
TIMEOUT=${TIMEOUT:-60}
SLEEP=2

printf "[vault-dev] Waiting for Vault at %s" "$VAULT_ADDR"
end=$((SECONDS + TIMEOUT))
while (( SECONDS < end )); do
  if curl -sSf "$VAULT_ADDR/v1/sys/health" >/dev/null; then
    echo " - ready"
    exit 0
  fi
  printf '.'
  sleep "$SLEEP"

done

echo
echo "[vault-dev] Vault did not become healthy within ${TIMEOUT}s" >&2
exit 1
