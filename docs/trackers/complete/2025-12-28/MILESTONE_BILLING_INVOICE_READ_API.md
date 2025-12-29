<!-- SECTION: Metadata -->
# Milestone: Billing Invoice Read API

_Last updated: 2025-12-29_  
**Status:** Completed  
**Owner:** @platform  
**Domain:** Cross-cutting  
**ID / Links:** Internal review comment (invoice read/list gaps)

---

<!-- SECTION: Objective -->
## Objective

Expose subscription invoice read/list surfaces (repository, service, and API) with consistent error handling and tests so billing invoices are queryable without relying on streaming events.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Billing repository implements invoice read/list with tenant-safe filters and stable ordering.
- Billing service exposes invoice read/list with consistent error mapping.
- Billing API exposes `GET /billing/tenants/{tenant_id}/invoices` and `GET /billing/tenants/{tenant_id}/invoices/{invoice_id}` (viewer-accessible).
- Contract + service tests cover invoice read/list.
- `hatch run lint` and `hatch run typecheck` pass for api-service.
- Billing docs updated with the new endpoints.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Domain/repository contract updates for invoice read/list.
- Postgres repository query implementations.
- Billing service wiring and API router/schema updates.
- Unit + contract tests for the new surfaces.
- Update billing service documentation.
- Web app BFF routes, client helpers, query hooks, and invoice ledger UI.

### Out of Scope
- Invoice editing or cancellation workflows.
- New billing events or webhook changes.
- Pagination cursoring or advanced filters beyond limit/offset.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan aligned with existing billing service patterns. |
| Implementation | ✅ | Backend + frontend complete. |
| Tests & QA | ✅ | Backend tests complete; frontend lint/type-check green. |
| Docs & runbooks | ✅ | Billing README updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Extend `BillingRepository` with `get_invoice` + `list_invoices` and map ORM invoices to domain records.
- Add a small `BillingInvoiceService` to keep invoice queries separate from subscription/usage flows.
- API endpoints mirror existing billing routes and enforce tenant role gates (`viewer` and above).
- Responses expose Stripe invoice IDs (external) plus period, amount, status, currency, and hosted URL.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Domain + Repository

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Domain | Extend billing repository contract for invoice read/list. | ✅ |
| A2 | Persistence | Implement Postgres invoice read/list queries + mapping. | ✅ |

### Workstream B – Service + API

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Service | Add invoice query service and wire into BillingService. | ✅ |
| B2 | API | Add invoice schemas + list/get endpoints with role gating. | ✅ |

### Workstream C – Tests + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Tests | Add service/repository coverage + billing API contract tests. | ✅ |
| C2 | Docs | Update billing service README with new endpoints. | ✅ |

### Workstream D – Web App (BFF + UI)

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | BFF | Add Next.js API routes for invoice list/get. | ✅ |
| D2 | Client | Add fetch helpers + query hooks + query keys for invoices. | ✅ |
| D3 | UI | Add invoice ledger page + overview tab/CTA. | ✅ |
| D4 | Tests | Add API route + client helper tests. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Review gaps + design | Plan approved | ✅ |
| P1 – Implementation | Domain/repo/service/API | Endpoints wired, tests in place | ✅ |
| P2 – Validation | Lint/typecheck + targeted tests | Green checks | ✅ |
| P3 – Frontend | BFF routes + client hooks + UI ledger | Invoice history UI wired | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (uses existing billing tables and webhook ingestion).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Invoice IDs missing in persistence | Low | Stripe snapshots always provide invoice IDs; fall back to period matches already exists. |
| API contract drift | Low | Add contract tests for list/get endpoints. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/unit/billing/test_billing_service.py`
- `cd apps/api-service && hatch run test tests/contract/test_billing_api.py`
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations required; uses existing `subscription_invoices` table.
- Endpoints are immediately available when `ENABLE_BILLING=true`.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-29 — Milestone created and approved for implementation.
- 2025-12-29 — Repository/service/API updates completed with tests and docs.
- 2025-12-29 — Frontend workstream planned (BFF routes, client hooks, UI ledger).
- 2025-12-29 — Frontend invoice ledger + helpers complete; lint/type-check green.
