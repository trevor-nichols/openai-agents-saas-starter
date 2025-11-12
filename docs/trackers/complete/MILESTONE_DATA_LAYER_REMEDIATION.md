# Milestone: Frontend Data Layer Remediation

**Status:** Not Started  
**DOR (Definition of Ready):** Backend contracts exist for all flows; HeyAPI SDK v0.5.0 generated 10 Nov 2025; design approves consolidation of redundant hooks.  
**Milestone Owner:** *@codex*  
**Target Window:** 12–19 Nov 2025  

## Objective
Close the remaining data-layer gaps uncovered during the 11 Nov 2025 review so the Next.js frontend consistently routes through the generated HeyAPI client, enforces auth boundaries via Next API routes, and eliminates dead code that could drift from production pathways.

## Success Criteria
1. Service-account issuance UX can hit the Vault-signed endpoint with the correct headers and user feedback.
2. Billing subscription hooks call HTTP fetchers (or TanStack Query `fetchFn`s) rather than importing server modules, so client bundles no longer break when consumed in RSC/client components.
3. There is exactly one supported billing stream hook and one supported silent refresh hook, both documented and tested.
4. Session list UI can filter by tenant, matching FastAPI’s `tenant_id` query contract.
5. Lint/type-check suites (`pnpm lint`, `pnpm type-check`) and backend linters (`hatch run lint`, `hatch run pyright`) pass after the changes.

## Workstreams & Tasks

### 1. Vault-Signed Service-Account Issuance
- [x] Add `issueVaultServiceAccountToken()` helper under `lib/server/services/auth/serviceAccounts.ts` that wraps `issueServiceAccountTokenApiV1AuthServiceAccountsIssuePost` with Vault headers and error mapping.
- [x] Create `/app/api/auth/service-accounts/issue/route.ts` to proxy authenticated requests (owner-only) to the new helper and enforce Vault header presence.
- [x] Update UI/CLI (Automation tab or starter CLI) to surface the new path and toggle between browser bridge vs. Vault issuance.
- [x] Document the flow in `docs/frontend/features/account-service-accounts.md` and `docs/security/vault-transit-signing.md`.

### 2. Billing Subscription Fetchers & Hooks
- [x] Add REST fetchers under `agent-next-15-frontend/lib/api/billingSubscriptions.ts` for get/start/update/cancel/usage that call the existing Next API endpoints.
- [x] Refactor `lib/queries/billingSubscriptions.ts` to depend on the new fetchers (no direct `use server` imports) and update related tests/mocks.
- [x] Ensure server components still use server helpers via actions where appropriate (document best practice in `docs/frontend/data-access.md`).

### 3. Remove Duplicate Realtime/Session Hooks
- [x] Delete or re-export `hooks/useBillingStream.ts` and `hooks/useSilentRefresh.ts` after confirming no call sites remain.
- [x] Update Storybook/tests/docs to reference `lib/queries/billing.ts` and `lib/queries/session.ts` as the single sources of truth.
- [x] Add lint rule or simple unit test that prevents future `hooks/use*.ts` duplicates for these flows (optional stretch).

### 4. Tenant-Aware Session Lists
- [x] Extend `lib/api/accountSessions.ts` to accept `tenantId`, pass it through the query string, and update runtime validation.
- [x] Propagate the new option through `lib/queries/accountSessions.ts` and any UI call sites (sessions table filters, profile sidebars).
- [x] Add regression tests to `app/api/auth/sessions/route.test.ts` validating tenant-id propagation and to the React Query hook to ensure query keys include the filter.

### 5. Quality Gates
- [x] Run `pnpm lint` / `pnpm type-check` inside `agent-next-15-frontend`.
- [x] Run `hatch run lint` / `hatch run pyright` inside `anything-agents`.
- [x] Update `docs/trackers/ISSUE_TRACKER.md` statuses to “In Progress” / “Resolved” as tasks complete.

## Open Questions / Dependencies
- How do we authenticate Vault-signature headers in local dev without blocking contributors? (Proposal: keep `dev-local` fallback behind `ENABLE_VAULT_ISSUANCE`.)
- Should the session tenant filter default to the user’s primary tenant or expose a dropdown? (Needs Product input.)
- Do we want to keep the legacy hooks as thin wrappers re-exporting the new ones for backwards compatibility, or remove them outright? (My vote: remove to avoid drift.)

## Reporting
- Progress gets reviewed in the next Frontend UI Foundation stand-up; update this doc and the issue tracker after each pull request.
