<!-- SECTION: Metadata -->
# HTTP Smoke Suite

_Last updated: 2025-11-30_  
**Status:** Planned  
**Owner:** @platform-foundations  
**Domain:** Backend  
**ID / Links:** TBD (issue/PR to be filed)

---

<!-- SECTION: Objective -->
## Objective

Build a fast, deterministic HTTP smoke suite that hits every critical api-service surface once (health, auth, tenancy, agents, conversations, workflows, storage, billing/AI optional) so post-deploy checks give immediate red/green confidence without mocks.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Smoke suite lives under `apps/api-service/tests/smoke/http/` with shared env loader + httpx client and `@pytest.mark.smoke` tag.
- Deterministic fixture seed via `/api/v1/test-fixtures/apply` (tenant slug `smoke`, pro plan, admin user) runs as first test and is idempotent.
- Core coverage: health/ready/metrics/jwks, login/refresh + tenant gating, agents list/status, conversations (list/detail/search/events/delete), workflows list/runs list, logs ingestion, storage presign/list; optional gates for billing, AI chat/workflow run, vector stores/containers.
- Suite executable locally and in CI via single command; new `just smoke-http` recipe added.
- `hatch run lint`, `hatch run typecheck`, and `pytest -m smoke` pass.
- Docs/trackers updated (this file plus smoke README if added).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- New pytest-based HTTP smoke suite (no mocks) using real FastAPI stack.
- Deterministic test fixtures and tenant seeding for rerunnable runs.
- Optional test gates for AI, billing, vector stores, containers controlled by env flags.
- CI wiring and local dev ergonomics (`just` recipe, docs).

### Out of Scope
- Load/perf testing or chaos scenarios.
- Full contract/regression coverage (remains in contract/unit suites).
- Frontend E2E/Playwright coverage.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan agreed; template selected; phases defined. |
| Implementation | ⏳ | Tests and harness not yet added. |
| Tests & QA | ⏳ | Smoke suite pending; existing contract tests unaffected. |
| Docs & runbooks | ⏳ | Tracker created; smoke README pending. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Location: `apps/api-service/tests/smoke/http/` with shared env/config helper (SMOKE_BASE_URL, SMOKE_TENANT_SLUG, etc.) and httpx AsyncClient.
- First test seeds tenant via `/api/v1/test-fixtures/apply` (requires `USE_TEST_FIXTURES=true`); reruns safe because slug is stable.
- Auth helper logs in via `/api/v1/auth/token`, caches access/refresh, validates JWT against `/.well-known/jwks.json` to detect signing drift.
- Optional surfaces toggled by env (`SMOKE_ENABLE_AI`, `SMOKE_ENABLE_BILLING`, `SMOKE_ENABLE_VECTOR`, `SMOKE_ENABLE_STORAGE`); suite skips gracefully when disabled.
- Outputs concise per-test request/response summaries for fast triage; `--maxfail=1` default.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Harness & Fixtures

| ID | Area | Description | Owner | Status | Target |
|----|------|-------------|-------|--------|--------|
| A1 | Tests | Add smoke folder, env loader, httpx client, smoke marker, base health test | @platform-foundations | ✅ | 2025-11-30 |
| A2 | Data | Implement deterministic fixture spec (tenant `smoke`, pro plan, admin user, sample convo) and seed test | @platform-foundations | ✅ | 2025-11-30 |

### Workstream B – Core Coverage

| ID | Area | Description | Owner | Status | Target |
|----|------|-------------|-------|--------|--------|
| B1 | Auth | Login/refresh + JWKS validation + tenant header enforcement | @platform-foundations | ✅ | 2025-11-30 |
| B2 | Core APIs | Agents list/status; conversations list/detail/search/events/delete; workflows list/runs; logs ingestion | @platform-foundations | ✅ | 2025-11-30 |
| B3 | Storage | Presign upload/list/download/delete (memory provider) | @platform-foundations | ✅ | 2025-11-30 |

### Workstream C – Optional Surfaces & CI

| ID | Area | Description | Owner | Status | Target |
|----|------|-------------|-------|--------|--------|
| C1 | Billing (opt) | Plans/subscription tests gated by `SMOKE_ENABLE_BILLING` | @platform-foundations | ✅ | 2025-11-30 |
| C2 | AI/Workflows (opt) | Chat + workflow run tests gated by `SMOKE_ENABLE_AI` | @platform-foundations | ✅ | 2025-11-30 |
| C3 | CI & Docs | Add `just smoke-http`, wire CI job, author smoke README | @platform-foundations | ✅ | 2025-11-30 |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Scaffolding | Create smoke folder, env loader, health test, fixture spec | ✅ | 2025-11-30 |
| P1 – Readiness | Health/ready/metrics/jwks tests passing locally | ✅ | 2025-11-30 |
| P2 – Core APIs | Auth, agents, conversations, workflows, storage smoke passing | ✅ | 2025-11-30 |
| P3 – Optional Gates | Billing and AI/workflow run paths behind flags | ✅ | 2025-11-30 |
| P4 – CI & Docs | `just smoke-http`, CI step, docs updated | ✅ | 2025-11-30 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- `USE_TEST_FIXTURES=true` and test-fixture router enabled in api-service config.
- Seeded billing plans from baseline migration (starter/pro) already present.
- Redis + database reachable for session and fixture seeding.
- Optional: OpenAI API key and model access for AI path; billing provider config for billing path; storage provider defaults to memory.

---

<!-- SECTION: Risks & Mitigations -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Missing env/flags cause skips or false reds | Med | Clear env validation in harness; skip with reason when optional gates disabled. |
| External AI latency/flakiness | Med | Keep AI tests optional; short timeouts; minimal prompt content. |
| Fixture endpoint disabled in some envs | Med | Fail fast with explicit message; document `USE_TEST_FIXTURES` requirement. |
| CI runtime creep | Low | Cap suite to <2 min; use `--maxfail=1`; avoid heavy payloads. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && pytest -m smoke tests/smoke/http --maxfail=1 -q`
- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- Optional gates: set `SMOKE_ENABLE_AI=1` (with model key), `SMOKE_ENABLE_BILLING=1`, `SMOKE_ENABLE_VECTOR=1`, `SMOKE_ENABLE_STORAGE=1` to exercise extra paths.
- CI: add job invoking `just smoke-http` (wrapper around pytest command above).

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags added; suite relies on `USE_TEST_FIXTURES` and optional env gates.
- Safe to run against staging with seeded smoke tenant; avoid production unless fixtures route is gated/disabled.
- Rollback: disable CI job or unset env gates; no schema/data migrations introduced by this milestone.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-11-30 — P4 completed: `just smoke-http`, CI job `http-smoke` added to backend CI, smoke README authored; C3 marked complete.
- 2025-11-30 — P3 optional gates landed (billing plans/subscription under SMOKE_ENABLE_BILLING; AI chat + workflow run under SMOKE_ENABLE_AI); C1–C2 marked complete.
- 2025-11-30 — P2 core API smoke added (auth login/refresh/me, agents catalog/status, conversations list/detail/search/events/delete, workflows list/runs, storage presign/list, logs ingest); B1–B3 marked complete.
- 2025-11-30 — P1 readiness tests added (JWKS and metrics smoke), P1 marked complete.
- 2025-11-30 — P0 scaffolding delivered (smoke folder, env loader, fixture seed helper, base health test, smoke marker) and tracker targets aligned to same-day delivery.
- 2025-11-30 — Milestone tracker created; scope, phases, and tasks defined.
