#!/bin/sh
set -eu

TRANSIT_KEY="${VAULT_TRANSIT_KEY:-auth-service}"
ROOT_TOKEN="${VAULT_DEV_ROOT_TOKEN_ID:-vault-dev-root}"
HOST_ADDR="${HOST_VAULT_ADDR:-http://127.0.0.1:18200}"

export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_TOKEN="${ROOT_TOKEN}"

echo "[vault-dev] Ensuring transit secrets engine is enabled..."
if ! vault secrets list -format=json | grep -q '"transit/"'; then
  vault secrets enable transit >/dev/null
fi

vault write -f transit/keys/"${TRANSIT_KEY}" >/dev/null 2>&1 || true

cat <<EOM
Vault dev environment is ready.
Add these variables to your shell to use the dev signer:
  export VAULT_ADDR=${HOST_ADDR}
  export VAULT_TOKEN=${ROOT_TOKEN}
  export VAULT_TRANSIT_KEY=${TRANSIT_KEY}
  export VAULT_VERIFY_ENABLED=true

Remember: this mode is for local testing only. Do not use it in production.
EOM
