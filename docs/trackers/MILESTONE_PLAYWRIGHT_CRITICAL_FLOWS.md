<!-- SECTION: Title -->
# Playwright Critical Flow Coverage — Milestone

_Last updated: November 19, 2025_

## Objective
Guarantee that every revenue- or security-impacting workflow in the Next.js 15 surface is exercised end-to-end through Playwright before the December 2025 launch preview. This milestone tracks the coverage gap, data dependencies, and implementation tasks required to evolve from a single auth smoke test to a resilient suite that fails fast when critical UX flows regress.

## Scope & Principles
- Validate outcomes, not pixels. Favor role-based selectors (`getByRole`, `getByLabel`) so future copy polish does not cause churn.
- Keep flows hermetic. Tests must seed-or-stub their own data (see `tests/README.md`) and clean up using API helpers rather than relying on shared state.
- Mirror the documented architecture. Each spec should live under `tests/` and rely on orchestrators/hooks already in `features/**` (per `docs/frontend/data-access.md`).
- Ship iteratively. We can keep tests `test.skip(true, 'reason')` until fixtures are ready, but the file must compile so `pnpm type-check` succeeds.

## Critical Flow Inventory
| # | Flow | Surfaces Exercised | Why it’s Critical | Current Coverage | Primary Blockers |
| - | ---- | ------------------ | ----------------- | ---------------- | ---------------- |
| 1 | **Auth + chat handshake** | `/login` → `/dashboard` → `/chat` → logout (`tests/auth-smoke.spec.ts`) | Baseline guard that access control + chat shell never regress. | ✅ Passing | None |
| 2 | **Self-serve signup + email verification** | `/register`, `/auth/email/verify`, `/login` | Ensures SaaS funnel works when invite-only is disabled. | ✅ Passing | Uses Playwright helper + `/api/v1/test-fixtures/email-verification-token` endpoint for deterministic inbox. |
| 3 | **Plan upgrade/downgrade + audit trail** | `/billing` plan cards, TanStack mutations, SSE toast feed | Revenue path; verifies optimistic UI + Stripe webhook replay. | ⛔ Not implemented | Seeder for Starter/Scale plans + Stripe stubs; backend mutation fixtures. |
| 4 | **Billing events ledger & usage metering** | `/billing/events`, `/billing/usage` filters + SSE bridge | Confirms SSE wiring, filters, and usage aggregation match backend. | ⛔ Not implemented | Need Redis-backed stream fixture + usage deltas inserted via `/api/v1/billing/tenants/{id}/usage`. |
| 5 | **Service-account issue & revoke** | `/account/service-accounts` modal + revoke actions | Protects Vault integration + admin permission boundaries. | ⛔ Not implemented | Vault test signer container + seeded operator tenant. |
| 6 | **Tenant settings (contacts/webhook) update** | `/settings/tenant` forms | Ensures billing contacts + webhook plumbing remain writable. | ⛔ Not implemented | Stable tenant fixture + webhook echo endpoint for assertion. |
| 7 | **Chat transcript export** | `/chat` drawer export CTA + download artifact | Guarantees compliance/export promises; exercises storage callback. | ⛔ Not implemented | Conversation fixture + ephemeral storage mock + download verification helper. |
| 8 | **Conversations archive management** | `/chat` → archive table filter/delete/restore | Prevents regressions in retention controls tied to billing tiers. | ⛔ Not implemented | Seeded archive rows + feature flag forcing retention UI on. |

## Milestone Task Board
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| A | Convert placeholder `test.skip` calls to boolean form so `pnpm type-check` passes (`tests/app-regressions.spec.ts`). | Platform Foundations | ✅ Completed | Nov 19 |
| B | Land deterministic fixture harness (seed tenants, plans, conversations, service accounts) documented in `tests/README.md`. | Platform Foundations + Backend | ✅ Completed | Nov 19 |
| C | Implement signup + email verification spec (Flow 2) guarded by feature flag toggles. | Platform Foundations | ✅ Completed | Nov 19 |
| D | Implement billing plan mutation spec (Flow 3) including optimistic UI + SSE event assertion. | Platform Foundations | ⛔ Not Started | Nov 19 |
| E | Implement billing ledger + usage spec (Flow 4) verifying filters + SSE merge. | Platform Foundations | ⛔ Not Started | Nov 19 |
| F | Implement service-account lifecycle spec (Flow 5). | Platform Foundations | ⛔ Not Started | Nov 19 |
| G | Implement tenant settings spec (Flow 6) ensuring webhook + contacts persisted. | Platform Foundations | ⛔ Not Started | Nov 19 |
| H | Implement chat transcript export spec (Flow 7) ensuring file download and toast. | Platform Foundations | ⛔ Not Started | Nov 19 |
| I | Implement conversations archive spec (Flow 8) covering delete/restore + billing gate. | Platform Foundations | ⛔ Not Started | Nov 19 |

## Data & Infrastructure Dependencies
- **Seed scripts**: Extend the existing `tests/README.md` guidance with a reusable `pnpm test:seed` that provisions tenants/plans using FastAPI admin APIs (requires `anything-agents` running with `USE_TEST_FIXTURES=true`).
- **Stripe + billing stubs**: Use the `billing_service` fake gateway to emit invoices/events without hitting Stripe; ensure Redis (`agents-redis` on 6380) is running for SSE coverage.
- **Vault signer**: `just vault-up` launches the dev transit signer required for service-account tests; pair with a fixture service-account scope in Postgres.
- **Storage mock**: Transcript export spec needs a deterministic storage stub (local/S3 fake); document the toggle + helper script inside `tests/README.md` before enabling Flow 7.

## Exit Criteria
1. `pnpm type-check` and `pnpm lint` pass without muting the Playwright suite.
2. Each flow above has an implemented Playwright spec merged to `tests/` with CI hooks in `package.json`.
3. Specs run in CI nightly against seeded fixtures (documented in `tests/README.md`), with flake tracking piped to `docs/trackers/ISSUE_TRACKER.md`.
4. Tracker updated with ✅ status for every flow and linked PR references.

## Changelog
- **2025-11-21**: Added backend `test-fixtures` router, deterministic seed service, and `pnpm test:seed` harness outputting `tests/.fixtures.json`.
- **2025-11-19**: Self-serve signup Playwright spec (`tests/signup-email-verification.spec.ts`) added with deterministic email-token helper (`/api/v1/test-fixtures/email-verification-token`). Tracker updated (Flow 2 + Task C) after verifying `pnpm type-check`/`pnpm lint` pass.
- **2025-11-19**: Tracker created with flow inventory, blockers, and task board after billing-enabled OpenAPI regeneration. Task A completed by switching `tests/app-regressions.spec.ts` to boolean `test.skip` form and re-running `pnpm type-check` to confirm a clean build.
