# HTTP Smoke Coverage Matrix (API v1)

This matrix maps each API v1 router to its smoke coverage, the minimal assertion, and any gating requirements.
Keep it in sync with `apps/api-service/src/app/api/v1/router.py` and the smoke suite under `apps/api-service/tests/smoke/http`.

## API v1 routers

| Router prefix | Smoke test(s) | Minimal assertion(s) | Gate / Notes |
| --- | --- | --- | --- |
| `/api/v1/auth` | `test_auth_smoke.py`, `auth.py` | Token issuance, refresh, and `/auth/me` return valid user/tokens | Uses fixtures for seed user; extended auth flows tracked in Workstream B1. |
| `/api/v1/chat` | `test_ai_smoke.py` | `/chat` returns 200 with `conversation_id` | `SMOKE_ENABLE_AI=1` + model key; streaming handshake in Workstream C1. |
| `/api/v1/agents` | `test_agents_smoke.py` | Catalog includes `triage`; status endpoint returns `active` | Requires seeded auth user. |
| `/api/v1/assets` | Planned | List/detail/download/thumbnail/delete | `SMOKE_ENABLE_ASSETS=1` + storage backing; Workstream D3. |
| `/api/v1/guardrails` | `test_guardrails_smoke.py` | Guardrails + presets list and optional detail lookups | Requires `tools:read` scope on token. |
| `/api/v1/workflows` | `test_workflows_smoke.py`, `test_ai_smoke.py` | Catalog list + runs list; `/workflows/{key}/run` returns run id | `SMOKE_ENABLE_AI=1` for run; detail/cancel/stream in Workstream C3. |
| `/api/v1/workflows/replay` | Planned | Replay events + stream return data | Workstream C4; uses SSE helper. |
| `/api/v1/conversations` | `test_conversations_smoke.py` | List/search/detail/events + delete idempotently | Requires seeded conversation via fixtures. |
| `/api/v1/conversations/ledger` | Planned | Ledger events + stream return data | Workstream C2; uses SSE helper. |
| `/api/v1/tools` | `test_tools_smoke.py` | Tool catalog returns lists/maps | Requires `tools:read` scope on token. |
| `/api/v1/activity` | Planned | Activity list/stream + mark read | Requires seeded activity events + `activity:read` scope; Workstream E1. |
| `/api/v1/containers` | Planned | Create/list/detail/delete + agent bind/unbind | `SMOKE_ENABLE_CONTAINERS=1`; Workstream D6. |
| `/api/v1/vector_stores` | Planned | Create/list/detail/query/delete | `SMOKE_ENABLE_VECTOR=1`; Workstream D5. |
| `/api/v1/storage` | `test_storage_smoke.py` | Upload-url + list returns items | Storage provider configured; download/delete in Workstream D1. |
| `/api/v1/uploads` | Planned | Agent-input upload returns URL | Storage provider configured; Workstream D2. |
| `/api/v1/openai` (files) | Planned | Proxy download returns bytes | `SMOKE_ENABLE_OPENAI_FILES=1`; Workstream D4. |
| `/api/v1/contact` | Planned | Contact submission returns 202 | `SMOKE_ENABLE_CONTACT=1`; Workstream E6. |
| `/api/v1/status` | `test_status_smoke.py` | Snapshot contains `overview` + `incidents`; RSS returns XML | Subscriptions gated separately by `SMOKE_ENABLE_STATUS_SUBSCRIPTIONS`; Workstream E5 (subscriptions pending). |
| `/api/v1/tenants` | `test_tenants_smoke.py` | Settings GET/PUT roundtrip | Requires owner token. |
| `/api/v1/users` | `test_users_smoke.py` | Profile + consents + notification prefs | Requires authenticated user with tenant context. |
| `/api/v1/usage` | `test_usage_smoke.py` | List returns array (may be empty) | Requires tenant context. |
| `/api/v1/billing` | `test_billing_smoke.py` | Plans list + subscription detail | `SMOKE_ENABLE_BILLING=1`; additional endpoints in Workstream F1. |
| `/api/v1/logs` | `test_observability_smoke.py` | Ingest endpoint returns 202 | Requires `ENABLE_FRONTEND_LOG_INGEST=1` in api-service. |
| `/api/v1/test-fixtures` | `fixtures.py`, `test_conversations_smoke.py` | Fixture apply returns 201 | Requires `USE_TEST_FIXTURES=true`; harness-only. |

## Non-v1 endpoints covered

| Endpoint | Smoke test(s) | Minimal assertion(s) |
| --- | --- | --- |
| `/health`, `/health/ready` | `test_health_smoke.py` | `status` is `healthy` / `ready` |
| `/.well-known/jwks.json` | `test_readiness_smoke.py` | JWKS contains keys with `kid` |
| `/metrics` | `test_readiness_smoke.py` | Prometheus scrape includes auth metrics |
