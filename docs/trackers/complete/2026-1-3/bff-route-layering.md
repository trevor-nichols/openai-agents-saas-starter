<!-- SECTION: Metadata -->
# Milestone: BFF Route Layering Cleanup

_Last updated: 2026-01-03_  
**Status:** Completed  
**Owner:** @frontend  
**Domain:** Frontend  
**ID / Links:** docs/frontend/data-access.md, apps/web-app/app/api/SNAPSHOT.md

---

<!-- SECTION: Objective -->
## Objective

Bring all web-app BFF routes into the documented service-first layering so every route calls a server service (no direct SDK or raw fetch), with consistent auth handling, proxy behavior, and maintainable module boundaries.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- All `apps/web-app/app/api/**` handlers delegate to `lib/server/services/*`
- No direct `sdk.gen` imports or `fetch(API_BASE_URL...)` usage in route handlers
- New/extended services cover activity, logs, status RSS, test fixtures, usage, containers, storage objects, vector stores, workflows, auth MFA/SSO, and user consents/preferences
- Route tests updated to mock services instead of SDK
- ESLint + ast-grep guardrails enforce BFF boundaries in `app/api/**`
- `pnpm lint` and `pnpm type-check` pass after each phase
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Refactor BFF routes under `apps/web-app/app/api/**`
- Add/extend server services in `apps/web-app/lib/server/services/**`
- Update route unit tests affected by service refactors
- Minor doc updates to reinforce layering conventions

### Out of Scope
- Backend API changes or schema updates
- UI/feature changes outside BFF routes
- New functionality beyond standardizing layering

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Routes now flow through services consistently. |
| Implementation | ✅ | Service layer covers all BFF endpoints. |
| Tests & QA | ✅ | Route tests updated to mock services. |
| Docs & runbooks | ✅ | Data-access notes updated + guardrails documented. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Enforce the documented flow: **Route → Server Service → SDK client**.
- Introduce service wrappers for proxy-style endpoints (logs, RSS, downloads, test fixtures) so routes stay thin and consistent.
- Add/extend domain services to cover: activity, usage, auth MFA/SSO, user consents/preferences, containers, storage objects, vector stores, workflows, and OpenAI downloads.
- Maintain existing route response shapes/status codes to avoid behavioral drift.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Audit & Alignment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Inventory | Catalog routes using SDK or raw fetch | ✅ |
| A2 | Plan | Define service modules + proxy helpers | ✅ |

### Workstream B – Service Layer

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Activity | Add list/read/dismiss/mark-all services | ✅ |
| B2 | Logs | Add frontend log forward service | ✅ |
| B3 | Status | Add RSS service wrapper | ✅ |
| B4 | Test Fixtures | Add apply/email-token services | ✅ |
| B5 | Usage/Auth/Users | Add usage, MFA, SSO, consent/prefs services | ✅ |
| B6 | Storage/Containers/VectorStores/Workflows | Add domain services | ✅ |
| B7 | OpenAI Files | Add download proxy service | ✅ |

### Workstream C – Route Refactors & Tests

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Routes | Update BFF handlers to call services | ✅ |
| C2 | Tests | Update route tests to mock services | ✅ |

### Workstream D – Docs & Cleanup

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Docs | Update data-access notes if needed | ✅ |
| D2 | Validation | Lint/type-check each phase | ✅ |

### Workstream E – Guardrails & Enforcement

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | ESLint | Add no-restricted-imports + boundaries rules for BFF routes | ✅ |
| E2 | ast-grep | Add sgconfig + rules + CI lint:arch step | ✅ |
| E3 | Docs | Document new guardrails in data-access guide | ✅ |
| E4 | Validation | `pnpm lint`, `pnpm type-check`, `pnpm lint:arch` | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Inventory + service plan | Tracker created, routes inventoried, service map agreed | ✅ |
| P1 – Services | Implement/extend server services | Services compiled, lint/type-check pass | ✅ |
| P2 – Routes & Tests | Route refactor + test updates | Routes updated + tests pass, lint/type-check pass | ✅ |
| P3 – Docs & Closeout | Docs updates + final cleanup | Tracker completed, lint/type-check pass | ✅ |
| P4 – Guardrails | ESLint + ast-grep enforcement | Lint rules + CI check + docs updated | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (frontend-only refactor)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Behavior drift in proxy endpoints | Med | Preserve response shapes/status handling in services. |
| Test failures due to new mocks | Med | Update tests alongside route changes in Phase 2. |
| Incomplete coverage of routes | Med | Keep inventory list and verify via rg checks. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- Spot-check affected BFF routes with existing unit tests.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No rollout changes; purely internal refactor.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-03 — Tracker created and alignment phase started.
- 2026-01-03 — P0 alignment completed; service map captured.
- 2026-01-03 — P0 validation: `pnpm lint`, `pnpm type-check`.
- 2026-01-03 — P1 services implemented; validation: `pnpm lint`, `pnpm type-check`.
- 2026-01-03 — P2 route refactor + tests; validation: `pnpm lint`, `pnpm type-check`.
- 2026-01-03 — P3 docs/closeout complete; validation: `pnpm lint`, `pnpm type-check`. Milestone completed.
- 2026-01-03 — P4 guardrails added (ESLint + ast-grep + CI); validation: `pnpm lint`, `pnpm type-check`, `pnpm lint:arch`.
- 2026-01-03 — P4 follow-up: pinned ast-grep CLI via devDependency + pnpm build allow-list; validation re-run.
- 2026-01-04 — Follow-up: added ast-grep rule to block direct `fetch` usage in BFF routes; validation: `pnpm lint`, `pnpm type-check`, `pnpm lint:arch`.
