#!/usr/bin/env bash
set -euo pipefail

USE_TEST_FIXTURES="${USE_TEST_FIXTURES:-true}"
AUTO_RUN_MIGRATIONS="${AUTO_RUN_MIGRATIONS:-true}"
ENVIRONMENT="test"
DEBUG="${DEBUG:-false}"
DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./smoke.db}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
RATE_LIMIT_REDIS_URL="${RATE_LIMIT_REDIS_URL:-$REDIS_URL}"
AUTH_CACHE_REDIS_URL="${AUTH_CACHE_REDIS_URL:-$REDIS_URL}"
SECURITY_TOKEN_REDIS_URL="${SECURITY_TOKEN_REDIS_URL:-$REDIS_URL}"
USAGE_GUARDRAIL_REDIS_URL="${USAGE_GUARDRAIL_REDIS_URL:-$REDIS_URL}"
ENABLE_BILLING="${ENABLE_BILLING:-false}"
ENABLE_BILLING_RETRY_WORKER="${ENABLE_BILLING_RETRY_WORKER:-false}"
ENABLE_RESEND_EMAIL_DELIVERY="${ENABLE_RESEND_EMAIL_DELIVERY:-false}"
ALLOW_PUBLIC_SIGNUP="${ALLOW_PUBLIC_SIGNUP:-true}"
ENABLE_FRONTEND_LOG_INGEST="${ENABLE_FRONTEND_LOG_INGEST:-true}"
OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-smoke-key}"
STARTER_CONSOLE_SKIP_ENV="${STARTER_CONSOLE_SKIP_ENV:-true}"
STARTER_CONSOLE_SKIP_VAULT_PROBE="${STARTER_CONSOLE_SKIP_VAULT_PROBE:-true}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
SMOKE_ENABLE_BILLING="${SMOKE_ENABLE_BILLING:-0}"
SMOKE_ENABLE_AI="${SMOKE_ENABLE_AI:-0}"
SMOKE_ENABLE_VECTOR="${SMOKE_ENABLE_VECTOR:-0}"
SMOKE_ENABLE_CONTAINERS="${SMOKE_ENABLE_CONTAINERS:-0}"

export USE_TEST_FIXTURES
export AUTO_RUN_MIGRATIONS
export ENVIRONMENT
export DEBUG
export DATABASE_URL
export REDIS_URL
export RATE_LIMIT_REDIS_URL
export AUTH_CACHE_REDIS_URL
export SECURITY_TOKEN_REDIS_URL
export USAGE_GUARDRAIL_REDIS_URL
export ENABLE_BILLING
export ENABLE_BILLING_RETRY_WORKER
export ENABLE_RESEND_EMAIL_DELIVERY
export ALLOW_PUBLIC_SIGNUP
export ENABLE_FRONTEND_LOG_INGEST
export OPENAI_API_KEY
export STARTER_CONSOLE_SKIP_ENV
export STARTER_CONSOLE_SKIP_VAULT_PROBE
export SMOKE_BASE_URL
export SMOKE_ENABLE_BILLING
export SMOKE_ENABLE_AI
export SMOKE_ENABLE_VECTOR
export SMOKE_ENABLE_CONTAINERS

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "${script_dir}/.." && pwd)"
AUTH_KEY_STORAGE_PATH="${AUTH_KEY_STORAGE_PATH:-${project_dir}/tests/fixtures/keysets/test_keyset.json}"
export AUTH_KEY_STORAGE_PATH
cd "${project_dir}"

python -m hatch run serve >/tmp/api-smoke.log 2>&1 &
api_pid=$!
trap "kill ${api_pid}" EXIT

sleep 0.2
if ! kill -0 "${api_pid}" >/dev/null 2>&1; then
  echo "api-service failed to start; see /tmp/api-smoke.log" >&2
  exit 1
fi

# Wait for health endpoint (fail fast if it never comes up)
health_ok=false
for _ in {1..30}; do
  if curl -fsS "${SMOKE_BASE_URL}/health" >/dev/null 2>&1; then
    health_ok=true
    break
  fi
  sleep 1
done

if [ "${health_ok}" != "true" ]; then
  echo "api-service never became healthy; see /tmp/api-smoke.log" >&2
  tail -n 200 /tmp/api-smoke.log || true
  exit 1
fi

if ! python -m hatch run pytest -m smoke tests/smoke/http --maxfail=1 -q; then
  echo "Smoke tests failed; tailing /tmp/api-smoke.log" >&2
  tail -n 200 /tmp/api-smoke.log || true
  exit 1
fi
