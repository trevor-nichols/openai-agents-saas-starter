# HTTP Smoke Suite

Fast, deterministic checks that hit a running api-service over HTTP. Designed for post-deploy/CI confidence without mocks.

## What it covers
- Health/ready, JWKS, Prometheus metrics
- Auth login/refresh/me
- Agents catalog/status
- Status snapshot + RSS
- Tools catalog
- Guardrails catalog + presets
- Conversations list/detail/search/events + delete
- Usage counters
- User profile, consents, and notification preferences
- Tenant settings (get + update)
- Workflows list/runs
- Storage presign + list
- Logs ingestion
- Optional: Billing plans/subscription (`SMOKE_ENABLE_BILLING=1`)
- Optional: Chat + workflow run (`SMOKE_ENABLE_AI=1` and model key available)

See `COVERAGE_MATRIX.md` for the router-to-test mapping and planned coverage.

## Prereqs
- api-service running locally on `SMOKE_BASE_URL` (default `http://localhost:8000`)
- `USE_TEST_FIXTURES=true` in the api-service env (otherwise fixtures endpoint 404s)
- Redis + SQLite/Postgres reachable per your env vars

## Quick start (local)
```bash
# From repo root; starts api-service with sqlite+redis and runs the suite
just smoke-http
```

To run against an already running instance:
```bash
cd apps/api-service
SMOKE_BASE_URL=http://localhost:8000 pytest -m smoke tests/smoke/http --maxfail=1 -q
```

## Env knobs
- `SMOKE_BASE_URL` (default `http://localhost:8000`)
- `SMOKE_TENANT_SLUG`, `SMOKE_USER_EMAIL`, `SMOKE_USER_PASSWORD` (fixture seed)
- `SMOKE_ENABLE_BILLING` (1/0) — exercise billing endpoints
- `SMOKE_ENABLE_AI` (1/0) — exercise chat + workflow run (needs model key)
- `SMOKE_ENABLE_BILLING_STREAM` (1/0) — billing SSE stream
- `SMOKE_ENABLE_AUTH_SIGNUP` (1/0) — public signup flows
- `SMOKE_ENABLE_AUTH_EXTENDED` (1/0) — email verification, password reset/change, session management
- `SMOKE_ENABLE_AUTH_MFA` (1/0) — MFA enroll/verify flows
- `SMOKE_ENABLE_SERVICE_ACCOUNTS` (1/0) — service account issuance/token management
- `SMOKE_ENABLE_CONTACT` (1/0) — contact form endpoint
- `SMOKE_ENABLE_STATUS_SUBSCRIPTIONS` (1/0) — status subscription management + resend
- `SMOKE_ENABLE_OPENAI_FILES` (1/0) — OpenAI file/container download proxy
- `SMOKE_ENABLE_ASSETS` (1/0) — assets list/detail/download/thumbnail/delete
- `SMOKE_ENABLE_VECTOR`, `SMOKE_ENABLE_CONTAINERS` (1/0) — provider-backed storage/runtime tests

## CI usage
Backend CI job `http-smoke` runs `just smoke-http` with sqlite + redis, auto-migrations on, and fixtures enabled. Optional gates stay off unless env overrides are set in the workflow.
