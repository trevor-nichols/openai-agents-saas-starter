<!-- SECTION: Metadata -->
# Billing: Stripe Portal + Payment Methods + Invoice Preview

_Last updated: 2025-12-28_  
**Status:** Complete  
**Owner:** @tan  
**Domain:** Backend + Frontend  
**ID / Links:** [Docs], [Related trackers]

---

<!-- SECTION: Objective -->
## Objective

Deliver a production-grade Stripe billing surface for portal sessions, payment methods, and upcoming invoice previews—plus a complete plan-change API—so cloned repos have a clean, modern billing stack with consistent contracts and tests.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Stripe customer can be created pre-subscription and persisted.
- New billing APIs for portal, payment methods, and invoice preview are available (owner/admin vs viewer role gates enforced).
- Plan-change API is fully implemented and wired to Stripe.
- All new flows are covered by unit + contract tests.
- `hatch run lint` and `hatch run typecheck` pass after each phase.
- Docs/trackers updated.
- Frontend billing surfaces (portal, payment methods, invoice preview, plan-change UX) are wired through BFF routes, query hooks, and Storybook coverage.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add `billing_customers` persistence to support pre-subscription Stripe customers.
- Extend Stripe client + gateway for portal, payment methods, setup intents, invoice preview.
- Implement billing plan-change API (schemas + service + gateway wiring).
- Add new billing endpoints + Pydantic schemas for portal, payment methods, upcoming invoice preview.
- Tests for gateway, billing service, and API contracts.
- Web app billing updates: BFF routes, client fetchers/hooks, and UI surfaces for portal, payment methods, upcoming invoice preview, and plan-change timing.

### Out of Scope
- Data backfills or migrations beyond new billing customer storage.
- Non-Stripe payment providers.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan defined with explicit boundaries and role gates. |
| Implementation | ✅ | Backend and frontend wiring complete. |
| Tests & QA | ✅ | Contract + unit coverage updated; lint/typecheck green. |
| Docs & runbooks | ✅ | Tracker updated with frontend delivery. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add a new `billing_customers` table to store Stripe customer IDs before subscriptions exist.
- Extend `PaymentGateway` and `StripeGateway` to cover portal sessions, payment methods, setup intents, and invoice previews.
- Keep Stripe as the source of truth for payment methods and invoice preview (no extra DB beyond customer linkage).
- Plan-change endpoint is implemented using existing Stripe swap/schedule APIs.
- Frontend follows data-access layering (SDK → server services → BFF routes → client fetchers → hooks → feature UI).

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Confirm scope, roles, and pre-subscription requirements. | Open questions resolved. | ✅ |
| P1 – Persistence + Gateway | Add billing customer model + Stripe client/gateway extensions. | DB model + migration + gateway API compiled. | ✅ |
| P2 – Service + API | Service orchestration + billing endpoints/schemas. | API routes compile and wire correctly. | ✅ |
| P3 – Tests + Docs | Unit/contract tests + billing README + lint/typecheck. | Tests updated; lint/typecheck green. | ✅ |
| P4 – Frontend | BFF routes + hooks + UI for portal/payment methods/invoice preview/plan-change timing. | UI wired, Storybook updated, pnpm lint/type-check green. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Stripe API access for runtime usage.
- Existing billing tables/migrations.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Stripe customer duplication if pre-subscription path not reused | Med | Persist customer ID and reuse for subscription creation. |
| API/DB drift on plan changes | Med | Update subscription metadata and rely on Stripe webhooks for sync. |
| Migration tooling issues locally | Low | Use `just migration-revision` and document manual follow-up if DB unavailable. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/unit/billing` (targeted)
- `cd apps/api-service && hatch run test tests/contract/test_billing_api.py`
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Requires `ENABLE_BILLING=true` to expose new APIs.
- New env: `STRIPE_PORTAL_RETURN_URL` (defaults to `/billing` on `APP_PUBLIC_URL`).
- Frontend billing surfaces are gated by `NEXT_PUBLIC_ENABLE_BILLING`; Stripe Elements (if enabled) requires `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.
- Apply Alembic migration before enabling billing in production.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-28 — Milestone created; implementation kicked off.
- 2025-12-28 — Implementation complete with portal, payment methods, invoice preview, plan-change flows, tests, and docs.
- 2025-12-28 — Frontend wiring shipped (BFF routes, hooks, UI surfaces, Storybook); milestone marked complete.
