<!-- SECTION: Metadata -->
# API Service Critical Test Coverage

_Last updated: 2025-12-27_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Backend  
**ID / Links:** docs/trackers/current_milestone/api-service-critical-test-coverage.md, docs/trackers/ISSUE_TRACKER.md

---

<!-- SECTION: Objective -->
## Objective

Expand CI-safe test coverage for the API service’s critical flows by adding focused contract tests, enabling stubbed AI smoke runs, and gating integration suites (Stripe replay, OTLP) behind explicit CI toggles.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Stubbed AI smoke server is available and used by CI smoke runs
- Contract tests are split into domain-focused files (agents, chat, chat-stream, conversations, billing)
- Billing contract coverage validates catalog + subscription flows with deterministic stubs
- CI includes opt-in jobs for Stripe replay and OTLP integration suites
- `hatch run lint` / `hatch run typecheck` / `hatch run test` (or scoped test runs) are green
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Chat + conversation contract coverage (sync + streaming)
- Billing contract coverage for plan catalog + subscription read
- Stubbed AI smoke server for CI-safe chat/workflow smoke tests
- CI toggles for Stripe replay and OTLP integration suites
- Test file decomposition to avoid monolithic contract tests

### Out of Scope
- Live OpenAI/Stripe calls in default CI
- Frontend feature work
- Production infra changes

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Clear separation of stub provider, smoke harness, and contract tests |
| Implementation | ✅ | Core files and workflows updated |
| Tests & QA | ⚠️ | Full suite not yet executed in this change |
| Docs & runbooks | ✅ | Milestone tracker updated |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Stubbed provider for smoke:** `apps/api-service/tests/utils/stub_agent_provider.py` supplies a deterministic AgentProvider used only in smoke runs.
- **Smoke server harness:** `tools/smoke/http_smoke_server.py` patches `build_openai_provider` to ensure hermetic AI runs.
- **Contract test decomposition:** split into `test_agents_api.py`, `test_chat_api.py`, `test_chat_stream_api.py`, `test_conversations_api.py`, `test_billing_api.py` for maintainability.
- **CI toggles:** optional jobs for Stripe replay and OTLP integration are gated via `workflow_dispatch` inputs or repo vars.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract Coverage Expansion

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add chat contract tests (sync + policy/rate-limit) | Platform Foundations | ✅ |
| A2 | API | Add chat stream contract tests with SSE assertions | Platform Foundations | ✅ |
| A3 | API | Add conversations contract coverage (list/search/events/delete) | Platform Foundations | ✅ |
| A4 | API | Add billing contract coverage (plans + subscription read) | Platform Foundations | ✅ |

### Workstream B – Smoke Harness & CI Toggles

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Infra | Stubbed AI smoke server entrypoint | Platform Foundations | ✅ |
| B2 | CI | Enable AI smoke in CI with stub provider | Platform Foundations | ✅ |
| B3 | CI | Gate Stripe replay integration suite | Platform Foundations | ✅ |
| B4 | CI | Gate OTLP integration suite | Platform Foundations | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Coverage gaps + design outline | Plan approved | ✅ |
| P1 – Implementation | Tests, smoke harness, CI toggles | Code merged | ✅ |
| P2 – Validation | Run targeted suites | All green | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (all work is internal, hermetic, CI-safe)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Stub provider diverges from real provider behavior | Medium | Keep stub minimal; validate critical flows with integration suites on demand |
| Contract tests become duplicated across files | Low | Centralize shared env/auth helpers in `tests/utils` |
| CI toggle jobs silently drift | Medium | Document triggers and keep inputs/vars explicit |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test:contract`
- `cd apps/api-service && hatch run test:smoke` (with `SMOKE_ENABLE_AI=1`)
- Optional: `hatch run pytest -m stripe_replay --enable-stripe-replay tests/integration`
- Optional: `hatch run pytest tests/integration/test_observability_collector.py -m integration`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- **CI smoke:** uses `SMOKE_USE_STUB_PROVIDER=1` and `SMOKE_ENABLE_AI=1` to run chat + workflow smoke safely.
- **Stripe replay:** run via `workflow_dispatch` input `run_stripe_replay=true` or repo var `RUN_STRIPE_REPLAY=true`.
- **OTLP integration:** run via `workflow_dispatch` input `run_otlp_integration=true` or repo var `RUN_OTLP_INTEGRATION=true`.
- No production flags introduced; all changes are test harness or CI-only.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-27 — Added stubbed smoke harness, split contract tests, and CI toggles for integration suites.
