<!-- SECTION: Metadata -->
# Milestone: Billing Plan Change (Schedules + Immediate Upgrades)

_Last updated: 2025-12-28_  
**Status:** Completed  
**Owner:** Platform Foundations  
**Domain:** Backend + Frontend  
**ID / Links:** [Reviewer comment], [apps/api-service/src/app/services/billing/README.md]

---

<!-- SECTION: Objective -->
## Objective

Enable plan changes that support immediate upgrades and deferred downgrades using Stripe subscription schedules, while keeping subscription state consistent, exposing pending change details to the API, and maintaining clean architecture boundaries.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Plan change endpoint accepts `timing` and returns `timing` + `effective_at`.
- Billing service resolves auto timing (upgrade immediate, downgrade period end for matching intervals) and supports explicit overrides.
- Stripe gateway uses immediate swaps with proration for upgrades and subscription schedules for period-end changes.
- Pending plan details + schedule ID persist without new DB columns.
- Unit tests cover service timing and gateway swap/schedule behavior.
- `hatch run lint` and `hatch run typecheck` pass after each phase.
- Billing docs updated with the new plan-change flow.
- Web app wires plan changes through BFF routes, query hooks, and plan management UI, displaying pending plan state.
- `pnpm lint` and `pnpm type-check` pass after each frontend phase.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Update plan-change request/response schema and endpoint.
- Service-level timing resolution and state persistence for pending plan changes.
- Stripe gateway/client support for subscription schedules and schedule release.
- Repository support for pending plan metadata storage.
- Tests and billing README updates.

### Out of Scope
- Frontend or console wiring.
- Complex proration policies beyond default `always_invoice` for immediate upgrades.
- New database columns or migrations.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Timing-based plan change with schedules documented. |
| Implementation | ✅ | API, service, gateway, Stripe client, and repo updates complete. |
| Tests & QA | ✅ | Service + gateway tests updated; full suite run succeeded. |
| Docs & runbooks | ✅ | Billing README updated with schedule-based plan changes. |
| Frontend integration | ✅ | BFF route, client helpers/hooks, and UI plan change flow wired with pending plan display. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Use a dedicated action endpoint (`POST /billing/tenants/{tenant_id}/subscription/plan`) with explicit `timing`.
- Auto timing: upgrades (higher price, same interval) apply immediately with proration; downgrades schedule at period end.
- Period-end changes use Stripe subscription schedules with a two-phase plan swap.
- Pending plan details and Stripe schedule ID are stored in `tenant_subscriptions.metadata_json` and surfaced in domain/API fields.
- Seat handling is dynamic: preserve current quantity unless the request provides an explicit seat count.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – API Contract

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Schema | Add `timing` and pending plan fields to request/response. | ✅ |
| A2 | API | Update plan-change route to pass timing and return enriched response. | ✅ |

### Workstream B – Persistence + Domain

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Domain | Add pending plan + schedule ID to `TenantSubscription`. | ✅ |
| B2 | Repo | Store pending plan metadata + schedule ID in `metadata_json`. | ✅ |

### Workstream C – Service + Gateway

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Service | Implement timing resolution and schedule-aware plan changes. | ✅ |
| C2 | Gateway | Add immediate swap + schedule methods in `PaymentGateway`. | ✅ |
| C3 | Stripe | Implement schedule create/update/release in Stripe client. | ✅ |

### Workstream D – Tests + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Tests | Update service + Stripe gateway tests for timing and schedules. | ✅ |
| D2 | Docs | Update billing README with schedule-based flow. | ✅ |

### Workstream E – Web App Integration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | SDK | Regenerate OpenAPI fixtures + HeyAPI client. | ✅ |
| E2 | BFF | Add `/subscription/plan` API route + server service wrapper. | ✅ |
| E3 | Client | Add plan-change fetch helper + TanStack mutation + types. | ✅ |
| E4 | UI | Update plan management dialog + pending plan display. | ✅ |
| E5 | Tests | Add client helper + BFF route tests. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Plan agreement and milestone doc. | Tracker created and approved. | ✅ |
| P1 – API Contract | Schemas + endpoint. | Endpoint compiles and lint/typecheck pass. | ✅ |
| P2 – Service + Gateway | Timing logic + Stripe schedule wiring. | Plan change orchestration complete. | ✅ |
| P3 – Tests + Docs | Tests + README + validation. | Tests added, docs updated, lint/typecheck pass. | ✅ |
| P4 – Web App Integration | BFF route + client hooks + UI updates. | `pnpm lint`/`pnpm type-check` pass; tests updated. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Stripe subscription schedules (create/update/release).
- `STRIPE_PRODUCT_PRICE_MAP` configuration for all plan codes.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Schedule misconfiguration leads to wrong effective timing | High | Use two-phase schedule with explicit period boundaries. |
| Pending state becomes stale after schedule release | Med | Clear pending fields when schedule ID disappears or plan matches pending. |
| Seat count defaults surprise operators | Med | Preserve current quantity unless explicitly overridden. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test` (full suite run; billing tests included)
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- `cd apps/web-app && pnpm vitest run lib/api/__tests__/billingSubscriptions.test.ts app/api/v1/billing/tenants/[tenantId]/subscription/plan/route.test.ts`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Requires `STRIPE_PRODUCT_PRICE_MAP` to include all plan codes.
- No DB migrations required (pending change data is stored in `metadata_json`).
- Upgrades bill immediately via proration; downgrades execute at period end via schedules.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-28 — Milestone updated for subscription schedules and immediate upgrades; implementation complete.
- 2025-12-28 — Web app plan-change integration (SDK regen, BFF route, hooks, UI pending-plan state, tests).
