<!-- SECTION: Metadata -->
# Billing Usage Totals API

_Last updated: 2025-12-29_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** Internal review comment (usage totals), apps/api-service/src/app/services/billing/billing_service.py, apps/api-service/src/app/infrastructure/persistence/billing/postgres.py

---

<!-- SECTION: Objective -->
## Objective

Expose a read-only billing usage totals endpoint and wire it through the web app so tenants can retrieve and view metered usage totals by feature and period.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

Bullet list of concrete, verifiable end state:

- `GET /api/v1/billing/tenants/{tenant_id}/usage-totals` is implemented and documented in OpenAPI.
- Response schema mirrors `UsageTotal` (feature_key, unit, quantity, window_start, window_end).
- Contract tests cover the endpoint and query parameters.
- Web app has BFF route + client fetch helper + TanStack Query hook and uses the data in billing usage UI.
- `hatch run lint` / `hatch run typecheck` / targeted tests pass.
- `pnpm lint` / `pnpm type-check` / targeted web tests pass.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add billing usage totals response schema in `apps/api-service/src/app/api/v1/billing/schemas.py`.
- Add `GET /billing/tenants/{tenant_id}/usage-totals` endpoint with tenant guard + billing error mapping.
- Add contract tests for the new endpoint in `apps/api-service/tests/contract/test_billing_api.py`.
- Regenerate OpenAPI fixtures + web client.
- Add billing usage totals server service + BFF route + client fetch helper + query hook.
- Wire usage totals into billing usage UI (and overview usage table if appropriate).

### Out of Scope
- Any changes to usage accounting logic or billing persistence behavior.
- Billing UX redesigns beyond using the new endpoint.
- Database migrations.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Backend + frontend follow data-access layering. |
| Implementation | ✅ | Backend complete; frontend integration complete. |
| Tests & QA | ✅ | Backend + frontend validations run. |
| Docs & runbooks | ✅ | Tracker updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Reuse existing `BillingService.get_usage_totals` and repository aggregation logic (no new data model changes).
- Keep tenant enforcement consistent with other read-only billing endpoints.
- Map `BillingError` through existing `_handle_billing_error` for consistent HTTP responses.
- Follow frontend data-access layering: server service → Next.js BFF route → `lib/api` fetch helper → TanStack Query hook → billing feature UI.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – API Surface

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Schema | Add `UsageTotalResponse` with `from_domain` helper. | ✅ |
| A2 | API | Implement `GET /billing/tenants/{tenant_id}/usage-totals` with query params. | ✅ |

### Workstream B – Tests

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Contract | Add contract test for usage totals endpoint + query passthrough. | ✅ |

### Workstream C – Validation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | QA | Run `hatch run lint` and `hatch run typecheck`. | ✅ |
| C2 | QA | Run targeted contract test for usage totals. | ✅ |

### Workstream D – Web App Integration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | SDK | Regenerate OpenAPI fixtures + web client. | ✅ |
| D2 | Service | Add billing usage totals server service call. | ✅ |
| D3 | BFF | Add `/api/v1/billing/tenants/[tenantId]/usage-totals` route. | ✅ |
| D4 | Client | Add fetch helper + query hook + query keys. | ✅ |
| D5 | UI | Wire usage totals into billing usage view. | ✅ |

### Workstream E – Web App Tests & Validation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | Tests | Add BFF route test and fetch helper test. | ✅ |
| E2 | QA | Run `pnpm lint` and `pnpm type-check`. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Confirm endpoint shape + roles. | Plan approved. | ✅ |
| P1 – Backend Implementation | Schema + endpoint + tests + validation. | Backend DoD satisfied. | ✅ |
| P2 – Web App Integration | BFF + hooks + UI + tests + validation. | Frontend DoD satisfied. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (existing billing service + repository already support usage totals).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Query period semantics are misunderstood by consumers. | Low | Document params clearly and return window_start/window_end in response. |
| Timezone handling surprises clients. | Low | Accept ISO-8601 datetimes; return UTC-aware datetimes in responses. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/contract/test_billing_api.py -k usage_totals`
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- `cd apps/web-app && pnpm vitest run <relevant tests>`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations or backfills required.
- Endpoint is immediately available when the API service deploys.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-29 — Milestone created; scope and plan defined.
- 2025-12-29 — Implemented usage totals endpoint, schema, tests, and validation.
- 2025-12-29 — Added web app integration plan and regenerated SDK fixtures.
- 2025-12-29 — Implemented web app usage totals flow with tests and validation.
