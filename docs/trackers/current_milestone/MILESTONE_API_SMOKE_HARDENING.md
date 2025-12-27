<!-- SECTION: Metadata -->
# Milestone: API Smoke Test Hardening (Full Surface Coverage)

_Last updated: 2025-12-27_  
**Status:** In Progress  
**Owner:** TBD  
**Domain:** Backend  
**ID / Links:**
- Template: `docs/trackers/templates/MILESTONE_TEMPLATE.md`
- Smoke suite: `apps/api-service/tests/smoke/http/README.md`
- API router index: `apps/api-service/src/app/api/v1/router.py`
- API service snapshot: `apps/api-service/SNAPSHOT.md`

---

<!-- SECTION: Objective -->
## Objective

Expand the HTTP smoke suite so every public API v1 router has at least one fast, deterministic, end-to-end smoke check. The goal is to catch wiring, auth, and dependency regressions quickly while keeping CI fast and predictable.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Every API v1 router has a smoke test that hits a representative happy-path endpoint.
- Partial areas are expanded to cover the key secondary endpoints (auth, billing, chat/workflows, storage, conversations, replay/ledger).
- Provider-dependent routes are gated behind explicit smoke flags with clear prerequisites documented.
- Smoke fixtures or setup steps cover required seed data without side effects (idempotent suite).
- `apps/api-service/tests/smoke/http/README.md` updated with new flags and prerequisites.
- `just smoke-http` passes with default config; optional paths pass when enabled.
- Backend quality gates pass: `hatch run lint`, `hatch run typecheck`, `hatch run test`.
- This tracker updated with final status and notes.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add smoke coverage for currently missing API groups:
  - activity, assets, contact, containers, guardrails, openai_files, status, tenants, tools, uploads, usage, users (consents/notifications/profile), vector_stores.
- Expand existing smoke coverage for partial groups:
  - auth (beyond token/refresh/me), billing (beyond plans/subscription), chat (stream), workflows (run detail/cancel/stream, replay), conversations (ledger), storage (download/delete).
- Add config gates for provider-dependent or optional paths to keep CI deterministic.
- Extend fixtures or per-test setup to seed the minimal data needed for new endpoints.

### Out of Scope
- Deep correctness and edge cases (covered by unit/contract/integration tests).
- Load/performance testing.
- Streaming contract validation beyond minimal handshake (handled by contract tests and goldens).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | OK | API v1 routers are well-factored; smoke suite is HTTP-based with fixtures. |
| Implementation | ⚠️ | Core endpoints added (status/tools/guardrails/usage/users/tenants); many routers still pending. |
| Tests & QA | WARN | Gaps in coverage across many API groups and streaming/replay surfaces. |
| Docs & runbooks | WARN | Smoke README lists current scope; needs updates for new flags. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- API surface is organized under `apps/api-service/src/app/api/v1/*` and aggregated in `apps/api-service/src/app/api/v1/router.py`.
- HTTP smoke tests live in `apps/api-service/tests/smoke/http` and call a running service via `httpx` (no mocks).
- Fixtures are seeded via `/api/v1/test-fixtures/apply` when `USE_TEST_FIXTURES=true`; current fixture service seeds tenants/users/conversations/usage and subscriptions only.
- Some routers are conditional via settings: billing (`enable_billing`), test fixtures (`use_test_fixtures`), logs (`enable_frontend_log_ingest`). Smoke must respect these gates.
- Streaming endpoints (chat/workflows/ledger/replay) emit `public_sse_v1`; smoke should only verify basic connectivity and termination, not full contract semantics.
- Dependencies include Postgres + Redis by default; some endpoints require external providers (OpenAI, Stripe, storage, vector DB, containers).

---

<!-- SECTION: Smoke Philosophy -->
## Smoke Philosophy

- Smoke tests are shallow, fast, end-to-end checks for wiring + happy-path availability.
- SSE smoke should validate connection + first event + clean termination only; schema/ordering lives in contract tests.
- Provider-dependent smoke stays gated behind explicit env flags; default CI must remain deterministic.
- Use fixtures for baseline state; use public APIs to create and clean up when those APIs are under test.

---

<!-- SECTION: Coverage Gap Checklist -->
## Coverage Gap Checklist (Per-Endpoint)

The list below enumerates endpoints not yet covered by the HTTP smoke suite. Each entry includes a minimal happy-path assertion and a suggested gate when external providers or elevated scopes are required.

### Activity

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/activity | 200 + `items` list | Requires `activity:read` scope. |
| GET | /api/v1/activity/stream | 200 + `text/event-stream` + first data/heartbeat | SSE helper; may need Redis. |
| POST | /api/v1/activity/{event_id}/read | 200 + `unread_count` | Requires seeded `event_id`. |
| POST | /api/v1/activity/{event_id}/dismiss | 200 + `unread_count` | Requires seeded `event_id`. |
| POST | /api/v1/activity/mark-all-read | 200 + `unread_count == 0` | Requires `activity:read` scope. |

### Assets

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/assets | 200 + `items` list | Proposed `SMOKE_ENABLE_ASSETS`; requires seeded assets. |
| GET | /api/v1/assets/{asset_id} | 200 + `id` matches | Needs `asset_id` from seed or create. |
| GET | /api/v1/assets/{asset_id}/download-url | 200 + `download_url` + `method` | Requires storage backing. |
| POST | /api/v1/assets/thumbnail-urls | 200 + `items` array | Accepts missing/unsupported lists. |
| DELETE | /api/v1/assets/{asset_id} | 204 | Idempotent cleanup. |

### Auth - Public Signup and Access

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/auth/signup-policy | 200 + `policy` | Public; no auth required. |
| POST | /api/v1/auth/register | 201 + `tenant_slug` + tokens | Proposed `SMOKE_ENABLE_AUTH_SIGNUP`; depends on signup policy. |
| POST | /api/v1/auth/request-access | 202 + policy response | Public; may be rate-limited. |
| GET | /api/v1/auth/signup-requests | 200 + `requests` list | Requires `auth:signup_requests` scope. |
| POST | /api/v1/auth/signup-requests/{request_id}/approve | 200 + request + invite | Requires seeded `request_id`. |
| POST | /api/v1/auth/signup-requests/{request_id}/reject | 200 + request | Requires seeded `request_id`. |
| GET | /api/v1/auth/invites | 200 + `invites` list | Requires `auth:invites` scope. |
| POST | /api/v1/auth/invites | 201 + `invite_token` | Requires `auth:invites` scope. |
| POST | /api/v1/auth/invites/{invite_id}/revoke | 200 + status updated | Requires seeded `invite_id`. |

### Auth - Email Verification

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/auth/email/send | 202 + success response | Proposed `SMOKE_ENABLE_AUTH_EXTENDED`; delivery may be disabled. |
| POST | /api/v1/auth/email/verify | 200 + success response | Use test-fixture token from `/api/v1/test-fixtures/email-verification-token`. |

### Auth - Password Flows

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/auth/password/forgot | 202 + success response | Proposed `SMOKE_ENABLE_AUTH_EXTENDED`; email delivery may be disabled. |
| POST | /api/v1/auth/password/confirm | 200 + success response | Requires reset token (fixture or captured token). |
| POST | /api/v1/auth/password/change | 200 + success response | Requires current password. |
| POST | /api/v1/auth/password/reset | 200 + success response | Requires `support:read` scope + tenant context. |

### Auth - MFA

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/auth/mfa | 200 + list (may be empty) | Proposed `SMOKE_ENABLE_AUTH_MFA`. |
| POST | /api/v1/auth/mfa/totp/enroll | 201 + `method_id` + `secret` | Proposed `SMOKE_ENABLE_AUTH_MFA`. |
| POST | /api/v1/auth/mfa/totp/verify | 200 + success response | Requires valid TOTP code. |
| DELETE | /api/v1/auth/mfa/{method_id} | 200 + success response | Requires enrolled method id. |
| POST | /api/v1/auth/mfa/recovery/regenerate | 200 + `codes` list | Proposed `SMOKE_ENABLE_AUTH_MFA`. |
| POST | /api/v1/auth/mfa/complete | 200 + tokens | Requires MFA challenge token. |

### Auth - Sessions and Logout

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/auth/logout | 200 + `revoked` | Requires refresh token from login. |
| POST | /api/v1/auth/logout/all | 200 + `revoked` | Requires authenticated user. |
| GET | /api/v1/auth/sessions | 200 + `sessions` list | Requires authenticated user. |
| DELETE | /api/v1/auth/sessions/{session_id} | 200 + `revoked` | Use `session_id` from list. |

### Auth - Service Accounts

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/auth/service-accounts/issue | 201 + token response | Proposed `SMOKE_ENABLE_SERVICE_ACCOUNTS`; requires Vault or dev-demo credentials. |
| POST | /api/v1/auth/service-accounts/browser-issue | 201 + token response | Requires service-account actor headers. |
| GET | /api/v1/auth/service-accounts/tokens | 200 + `items` list | Requires service-account actor. |
| POST | /api/v1/auth/service-accounts/tokens/{jti}/revoke | 200 + success response | Requires `jti` from list. |

### Billing (Optional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/billing/tenants/{tenant_id}/subscription | 201 + subscription payload | `SMOKE_ENABLE_BILLING=1` and billing enabled. |
| PATCH | /api/v1/billing/tenants/{tenant_id}/subscription | 200 + updated fields | Requires existing subscription. |
| POST | /api/v1/billing/tenants/{tenant_id}/subscription/cancel | 200 + status update | Requires existing subscription. |
| POST | /api/v1/billing/tenants/{tenant_id}/usage | 202 + success response | Requires subscription. |
| GET | /api/v1/billing/tenants/{tenant_id}/events | 200 + `items` list | Requires events seeded or empty list. |
| GET | /api/v1/billing/stream | 200 + `text/event-stream` + first ping | Proposed `SMOKE_ENABLE_BILLING_STREAM`. |

### Chat

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/chat/stream | 200 + `text/event-stream` + first data frame | `SMOKE_ENABLE_AI=1`; SSE helper. |

### Contact

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/contact | 202 + success message | Proposed `SMOKE_ENABLE_CONTACT`; delivery may be disabled. |

### Containers (Optional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/containers | 201 + container id | `SMOKE_ENABLE_CONTAINERS=1`; provider configured. |
| GET | /api/v1/containers | 200 + `items` list | Requires containers service configured. |
| GET | /api/v1/containers/{container_id} | 200 + id matches | Needs `container_id`. |
| DELETE | /api/v1/containers/{container_id} | 204 | Idempotent cleanup. |
| POST | /api/v1/containers/agents/{agent_key}/container | 204 | Requires container id + agent key. |
| DELETE | /api/v1/containers/agents/{agent_key}/container | 204 | Clean unbind. |

### Conversations (Additional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/conversations/{conversation_id}/messages | 200 + `items` list | Use seeded conversation. |
| DELETE | /api/v1/conversations/{conversation_id}/messages/{message_id} | 200 + `deleted_message_id` | Requires a user message id. |
| PATCH | /api/v1/conversations/{conversation_id}/memory | 200 + config fields | Requires admin role. |
| PATCH | /api/v1/conversations/{conversation_id}/title | 200 + `display_name` | Use seeded conversation. |
| GET | /api/v1/conversations/{conversation_id}/stream | 200 + SSE + `[DONE]` | SSE helper; title stream. |
| GET | /api/v1/conversations/{conversation_id}/ledger/events | 200 + `items` list | `public_sse_v1` replay. |
| GET | /api/v1/conversations/{conversation_id}/ledger/stream | 200 + SSE + first data frame | SSE helper. |

### Guardrails

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/guardrails | 200 + list | Requires `tools:read` scope. |
| GET | /api/v1/guardrails/presets | 200 + list | Requires `tools:read` scope. |
| GET | /api/v1/guardrails/{guardrail_key} | 200 + key matches | Use first key from list. |
| GET | /api/v1/guardrails/presets/{preset_key} | 200 + key matches | Use first key from list. |

### OpenAI Files (Optional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/openai/files/{file_id}/download | 200 + binary content | `SMOKE_ENABLE_OPENAI_FILES=1`; requires OpenAI file id. |
| GET | /api/v1/openai/containers/{container_id}/files/{file_id}/download | 200 + binary content | Requires container/file ids + OpenAI API access. |

### Status

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/status | 200 + `overview` + `incidents` list | Proposed `SMOKE_ENABLE_STATUS`. |
| GET | /api/v1/status/rss | 200 + RSS XML | Alias `/api/v1/status.rss` optional. |
| POST | /api/v1/status/subscriptions | 201 + subscription id | Proposed `SMOKE_ENABLE_STATUS_SUBSCRIPTIONS`. |
| POST | /api/v1/status/subscriptions/verify | 200 + subscription | Requires verification token. |
| POST | /api/v1/status/subscriptions/challenge | 200 + subscription | Requires challenge token. |
| GET | /api/v1/status/subscriptions | 200 + list | Requires `status:manage` scope. |
| DELETE | /api/v1/status/subscriptions/{subscription_id} | 204 | Requires token or `status:manage` scope. |
| POST | /api/v1/status/incidents/{incident_id}/resend | 202 + dispatched flag | Requires `status:manage` scope. |

### Storage (Additional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/storage/objects/{object_id}/download-url | 200 + `download_url` | Use `object_id` from presign/list. |
| DELETE | /api/v1/storage/objects/{object_id} | 204 | Idempotent cleanup. |

### Tenants

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/tenants/settings | 200 + settings snapshot | Requires admin/owner role. |
| PUT | /api/v1/tenants/settings | 200 + updated snapshot | Use minimal/no-op update. |

### Tools

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/tools | 200 + tool catalog payload | Requires `tools:read` scope. |

### Uploads

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/uploads/agent-input | 201 + `upload_url` | Requires storage service configured. |

### Usage

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/usage | 200 + list | Requires usage counters seeded (can be empty). |

### Users

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/users/me | 200 + profile data | Requires tenant_id in token. |
| POST | /api/v1/users/consents | 201 + success | Provide policy_key + version. |
| GET | /api/v1/users/consents | 200 + list | Can be empty after seed. |
| PUT | /api/v1/users/notification-preferences | 200 + preference payload | Requires tenant context. |
| GET | /api/v1/users/notification-preferences | 200 + list | Can be empty. |

### Vector Stores (Optional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| POST | /api/v1/vector_stores | 201 + store id | `SMOKE_ENABLE_VECTOR=1`; provider configured. |
| GET | /api/v1/vector_stores | 200 + `items` list | Requires vector store service. |
| GET | /api/v1/vector_stores/{vector_store_id} | 200 + id matches | Use created store id. |
| DELETE | /api/v1/vector_stores/{vector_store_id} | 204 | Idempotent cleanup. |
| POST | /api/v1/vector_stores/{vector_store_id}/files | 201 + file metadata | Requires file id (OpenAI or storage). |
| POST | /api/v1/vector_stores/{vector_store_id}/files/upload | 201 + file metadata | Requires storage object id. |
| GET | /api/v1/vector_stores/{vector_store_id}/files | 200 + `items` list | Use created store id. |
| GET | /api/v1/vector_stores/{vector_store_id}/files/{file_id} | 200 + file id matches | Requires file id. |
| DELETE | /api/v1/vector_stores/{vector_store_id}/files/{file_id} | 204 | Clean up file attachment. |
| POST | /api/v1/vector_stores/{vector_store_id}/search | 200 + results list | Requires indexed content. |
| POST | /api/v1/vector_stores/{vector_store_id}/bindings/{agent_key} | 204 | Bind store to agent. |
| DELETE | /api/v1/vector_stores/{vector_store_id}/bindings/{agent_key} | 204 | Unbind store from agent. |

### Workflows (Additional)

| Method | Endpoint | Minimal assertion | Gate / Notes |
| --- | --- | --- | --- |
| GET | /api/v1/workflows/runs/{run_id} | 200 + run details | Use `workflow_run_id` from run smoke. |
| POST | /api/v1/workflows/runs/{run_id}/cancel | 202 + `success=true` | Requires running/active run. |
| DELETE | /api/v1/workflows/runs/{run_id} | 204 | Requires admin role; use soft delete. |
| POST | /api/v1/workflows/{workflow_key}/run-stream | 200 + SSE data frame | `SMOKE_ENABLE_AI=1`; SSE helper. |
| GET | /api/v1/workflows/{workflow_key} | 200 + descriptor | Use `workflow_key` from catalog. |
| GET | /api/v1/workflows/runs/{run_id}/replay/events | 200 + `items` list | Requires ledger records. |
| GET | /api/v1/workflows/runs/{run_id}/replay/stream | 200 + SSE data frame | SSE helper. |

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A - Harness and config hardening

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Tests | Publish a router-to-smoke coverage matrix and agree on minimal smoke assertions per router. | TBD | Planned |
| A2 | Tests | Add/standardize smoke flags for provider-dependent routes (billing stream, status subscriptions, contact delivery, vector, containers, openai files). | TBD | Planned |
| A3 | Fixtures | Extend test fixture seeding or per-test setup to create assets, usage, status data where required. | TBD | Planned |
| A4 | Utils | Add shared helpers for SSE smoke (read first event + graceful close) and idempotent cleanup. | TBD | Planned |

### Workstream B - Identity and tenant surfaces

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Auth | Add smoke coverage for signup, sessions/logout, email verification (test-fixture token), password reset, MFA, invites, service accounts + tokens. | TBD | Planned |
| B2 | Tenants | Add smoke coverage for tenant list/detail/settings endpoints. | TBD | ✅ |
| B3 | Users | Add smoke coverage for consents, notifications, and profile endpoints. | TBD | ✅ |

### Workstream C - AI, conversations, workflows

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Chat | Add `/api/v1/chat/stream` SSE handshake smoke (gated by `SMOKE_ENABLE_AI`). | TBD | Planned |
| C2 | Conversations | Add ledger events + ledger stream smoke tests. | TBD | Planned |
| C3 | Workflows | Expand workflow smoke to include run detail, cancel, descriptor, and run-stream (gated). | TBD | Planned |
| C4 | Workflows | Add workflow run replay endpoints (events + stream). | TBD | Planned |

### Workstream D - Storage and content

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Storage | Add download-url + delete-object smoke (idempotent). | TBD | Planned |
| D2 | Uploads | Add `/api/v1/uploads/agent-input` smoke. | TBD | Planned |
| D3 | Assets | Add assets list/detail/download/thumbnail smoke (requires asset seed/creation). | TBD | Planned |
| D4 | OpenAI files | Add proxy download smoke (gated; requires file id). | TBD | Planned |
| D5 | Vector stores | Add list/create/query/delete smoke (gated by `SMOKE_ENABLE_VECTOR`). | TBD | Planned |
| D6 | Containers | Add container lifecycle smoke (gated by `SMOKE_ENABLE_CONTAINERS`). | TBD | Planned |

### Workstream E - Platform catalog and misc

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Activity | Add activity list + stream smoke. | TBD | Planned |
| E2 | Guardrails | Add guardrails list/presets smoke. | TBD | ✅ |
| E3 | Tools | Add tools catalog smoke. | TBD | ✅ |
| E4 | Usage | Add usage counters smoke (requires seeded usage). | TBD | ✅ |
| E5 | Status | Add platform status + RSS smoke; subscription flows gated by env/config. | TBD | ✅ |
| E6 | Contact | Add /contact smoke with delivery disabled or stubbed provider. | TBD | Planned |

### Workstream F - Billing expansion (optional gate)

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | Billing | Add start/update/cancel subscription, usage record, events list, and stream smoke (gated by `SMOKE_ENABLE_BILLING`). | TBD | Planned |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 - Alignment | Confirm smoke criteria, gates, and data seeding strategy | Coverage matrix signed off | Planned |
| P1 - Core coverage | Auth, tenants, users, status, tools, guardrails, usage | Workstreams B + E complete | Planned |
| P2 - AI and streaming | Chat/workflow streaming + ledger/replay | Workstream C complete | Planned |
| P3 - Provider-dependent | Billing, assets, storage, uploads, vector, containers, openai_files | Workstreams D + F complete | Planned |

---

<!-- SECTION: Dependencies -->
## Dependencies

- `USE_TEST_FIXTURES=true` for deterministic seeding.
- Postgres + Redis available for smoke runs.
- Optional providers (OpenAI, Stripe, storage, vector DB, containers) for gated tests.
- Feature flags in settings for billing/logs/test fixtures must be enabled when those tests run.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Provider-dependent smoke tests are flaky or unavailable | High | Gate behind explicit env flags; default CI remains deterministic. |
| Smoke suite grows too slow | Med | Keep assertions minimal; avoid heavy setup; parallelize where safe. |
| Missing seed data blocks new endpoints | Med | Extend fixtures or add minimal create-and-cleanup flows. |
| SSE tests hang | Med | Add strict timeouts and early termination once a terminal event is observed. |
| Conditional routers disabled in some envs | Low | Detect and skip with clear skip reasons. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `just smoke-http`
- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test`
- Optional: run smoke suite with gated flags enabled for provider-backed endpoints.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags beyond existing settings; smoke tests rely on env gating only.
- Update smoke README with env prerequisites for any new gates.
- No DB migrations expected; any fixture expansion should be additive and safe.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-27 - Added smoke coverage for status, tools, guardrails, usage, users, and tenant settings; updated README.
- 2025-12-27 - Created milestone and initial coverage gap inventory.
