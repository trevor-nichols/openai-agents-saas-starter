#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
api_dir="${repo_root}/apps/api-service"
log_file="${PERF_LOG_FILE:-/tmp/api-perf-smoke.log}"

if ! command -v k6 >/dev/null 2>&1; then
  echo "k6 is required. Install it first (https://k6.io/)" >&2
  exit 1
fi

export PERF_BASE_URL="${PERF_BASE_URL:-http://127.0.0.1:8000}"
export PERF_TENANT_SLUG="${PERF_TENANT_SLUG:-smoke}"
export PERF_TENANT_NAME="${PERF_TENANT_NAME:-Smoke Test Tenant}"
export PERF_ADMIN_EMAIL="${PERF_ADMIN_EMAIL:-smoke-admin@example.com}"
export PERF_ADMIN_PASSWORD="${PERF_ADMIN_PASSWORD:-SmokeAdmin!234}"
export PERF_DURATION="${PERF_DURATION:-30s}"
export PERF_VUS="${PERF_VUS:-1}"

export USE_TEST_FIXTURES="${USE_TEST_FIXTURES:-true}"
export AUTO_RUN_MIGRATIONS="${AUTO_RUN_MIGRATIONS:-true}"
export ENVIRONMENT="${ENVIRONMENT:-test}"
export DEBUG="${DEBUG:-false}"
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./perf-smoke.db}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export RATE_LIMIT_REDIS_URL="${RATE_LIMIT_REDIS_URL:-$REDIS_URL}"
export AUTH_CACHE_REDIS_URL="${AUTH_CACHE_REDIS_URL:-$REDIS_URL}"
export SECURITY_TOKEN_REDIS_URL="${SECURITY_TOKEN_REDIS_URL:-$REDIS_URL}"
export USAGE_GUARDRAIL_REDIS_URL="${USAGE_GUARDRAIL_REDIS_URL:-$REDIS_URL}"
export ENABLE_BILLING="${ENABLE_BILLING:-false}"
export ENABLE_BILLING_RETRY_WORKER="${ENABLE_BILLING_RETRY_WORKER:-false}"
export ENABLE_RESEND_EMAIL_DELIVERY="${ENABLE_RESEND_EMAIL_DELIVERY:-false}"
export ALLOW_PUBLIC_SIGNUP="${ALLOW_PUBLIC_SIGNUP:-true}"
export ENABLE_FRONTEND_LOG_INGEST="${ENABLE_FRONTEND_LOG_INGEST:-true}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-smoke-key}"
export STARTER_CONSOLE_SKIP_ENV="${STARTER_CONSOLE_SKIP_ENV:-true}"
export STARTER_CONSOLE_SKIP_VAULT_PROBE="${STARTER_CONSOLE_SKIP_VAULT_PROBE:-true}"
export AUTH_KEY_STORAGE_PATH="${AUTH_KEY_STORAGE_PATH:-${repo_root}/apps/api-service/tests/fixtures/keysets/test_keyset.json}"

cd "${repo_root}"

(cd "${api_dir}" && hatch run python ../../tools/smoke/http_smoke_server.py) >"${log_file}" 2>&1 &
api_pid=$!
trap "kill ${api_pid} >/dev/null 2>&1 || true" EXIT

sleep 0.2
if ! kill -0 "${api_pid}" >/dev/null 2>&1; then
  echo "api-service failed to start; see ${log_file}" >&2
  tail -n 200 "${log_file}" || true
  exit 1
fi

health_ok=false
for _ in {1..30}; do
  if curl -fsS "${PERF_BASE_URL}/health" >/dev/null 2>&1; then
    health_ok=true
    break
  fi
  sleep 1
done

if [ "${health_ok}" != "true" ]; then
  echo "api-service never became healthy; see ${log_file}" >&2
  tail -n 200 "${log_file}" || true
  exit 1
fi

k6 run "${repo_root}/tools/perf/k6/smoke.js"
