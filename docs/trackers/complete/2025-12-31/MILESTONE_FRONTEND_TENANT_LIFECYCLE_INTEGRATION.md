<!-- SECTION: Metadata -->
# Milestone: Frontend Tenant Lifecycle Integration

_Last updated: 2025-12-31_  
**Status:** Completed  
**Owner:** Frontend  
**Domain:** Frontend  
**ID / Links:** [Commit ed64a42e309b21c6befa70ae8183ec654f3bb180], [docs/trackers/current_milestones/MILESTONE_PLATFORM_TENANT_LIFECYCLE_API.md]

---

<!-- SECTION: Objective -->
## Objective

Integrate the new tenant lifecycle and operator tenant management API surface into the web app
with clean, auditable UI workflows for tenant admins and platform operators, following the
existing BFF + SDK + TanStack Query architecture.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- OpenAPI artifacts and HeyAPI SDK are regenerated and committed.
- BFF routes exist for `/api/v1/tenants/account` and `/api/v1/platform/tenants/*` with correct auth and error handling.
- Server services use the SDK for all new endpoints; no direct backend calls from the browser.
- Client API and TanStack Query hooks exist for tenant account and operator tenant lifecycle.
- Tenant admin UI adds self-service tenant account controls in the existing tenant settings feature.
- Platform operator UI adds a new tenant operations surface with list + lifecycle actions.
- Navigation and access gating use operator scopes (`support:*` or `platform:operator`) and tenant admin roles.
- Tests and Storybook stories added/updated where appropriate; `pnpm lint` and `pnpm type-check` pass.
- Docs/trackers updated (this milestone + any new snapshots needed).
- **Review follow-ups**: address the engineering review findings captured below.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Tenant account self-service UI (name update) under Settings > Tenant.
- Platform operator tenant management UI (list, details, suspend/reactivate/deprovision, create/update).
- BFF routes + server services + SDK wiring for the new endpoints.
- Query hooks, view models, and UI state management for the above.
- Navigation updates and gating based on operator scopes and tenant admin roles.

### Out of Scope
- Backend API changes (already landed in the API milestone).
- Data deletion/archival workflows for deprovisioning.
- Non-tenant operator tooling beyond the tenant lifecycle scope.
- Any public marketing surface changes.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Existing web app layering supports new endpoints cleanly (BFF -> server services -> SDK). |
| Implementation | ⚠️ | SDK has new endpoints, but no BFF routes or UI integration yet. |
| Tests & QA | ⏳ | No tests for new tenant lifecycle UI or BFF routes yet. |
| Docs & runbooks | ⚠️ | Findings and plan now documented here. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

**Findings from ed64a42 + regenerated SDK**
- New SDK types: `TenantAccountStatus`, `TenantAccountCreateRequest`, `TenantAccountUpdateRequest`,
  `TenantAccountSelfUpdateRequest`, `TenantAccountLifecycleRequest`, `TenantAccountResponse`,
  `TenantAccountOperatorResponse`, `TenantAccountListResponse`.
- New operator endpoints: `/api/v1/platform/tenants` (list/create), `/api/v1/platform/tenants/{tenant_id}`
  (get/update), `/api/v1/platform/tenants/{tenant_id}/{suspend|reactivate|deprovision}`.
- New tenant admin endpoints: `/api/v1/tenants/account` (GET/PATCH).
- Newly regenerated SDK also adds `/api/v1/logs` ingestion (already supported by existing BFF route and logger).

**Proposed frontend placement**
- Tenant self-service account update belongs in the existing Settings -> Tenant feature (`features/settings/tenant`).
- Platform operator controls should be a new feature module (recommended name: `features/tenant-ops`)
  and a new Ops page (`app/(app)/(shell)/ops/tenants`), mirroring `features/status-ops`.
- New BFF routes under `app/api/v1/tenants/account` and `app/api/v1/platform/tenants/**`.
- Data layer added under `lib/api`, `lib/queries`, and `lib/server/services` following current patterns.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Discovery + Regeneration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Analysis | Compare ed64a42 SDK diff + current regeneration outputs. | ✅ |
| A2 | Artifacts | Regenerate OpenAPI JSON + HeyAPI SDK. | ✅ |
| A3 | Findings | Capture findings and plan in a tracker. | ✅ |

### Workstream B – BFF Routes + Server Services

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | BFF | Add `/api/v1/tenants/account` GET/PATCH route. | ✅ |
| B2 | BFF | Add `/api/v1/platform/tenants` list/create routes. | ✅ |
| B3 | BFF | Add `/api/v1/platform/tenants/{tenantId}` get/update routes. | ✅ |
| B4 | BFF | Add lifecycle action routes for suspend/reactivate/deprovision. | ✅ |
| B5 | Server | Add SDK-backed services under `lib/server/services`. | ✅ |

### Workstream C – Client API + Queries

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Client | Add `lib/api/tenantAccount.ts` + types mapping. | ✅ |
| C2 | Client | Add `lib/api/platformTenants.ts`. | ✅ |
| C3 | Query | Add `lib/queries/tenantAccount.ts`. | ✅ |
| C4 | Query | Add `lib/queries/platformTenants.ts`. | ✅ |

### Workstream D – Tenant Admin UI

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | UI | Add tenant account card(s) to `features/settings/tenant`. | ✅ |
| D2 | UI | Wire update flow to PATCH `/tenants/account`. | ✅ |
| D3 | UX | Surface status and lifecycle state read-only for admins. | ✅ |

### Workstream E – Operator UI

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | UI | Create `features/tenant-ops` module with list/detail surface. | ✅ |
| E2 | UI | Add lifecycle actions (suspend/reactivate/deprovision + reason). | ✅ |
| E3 | Nav | Add Ops navigation entry gated by operator scopes. | ✅ |

### Workstream F – Tests + QA + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| F1 | Tests | BFF route tests for tenants account and platform tenant ops. | ✅ |
| F2 | Tests | Feature component tests and/or story updates. | ✅ |
| F3 | QA | Run `pnpm lint` and `pnpm type-check`. | ✅ |
| F4 | Docs | Update SNAPSHOTs if new feature module or routes are added. | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Findings + plan documented; artifacts regenerated. | Tracker updated; SDK regenerated. | ✅ |
| P1 – Plumbing | BFF routes + server services + client API + queries. | All new endpoints reachable from web app. | ✅ |
| P2 – UI | Tenant admin + operator UI wired end-to-end. | UI supports lifecycle actions and updates. | ✅ |
| P3 – QA | Tests + lint/type-check + docs. | Green validation and updated snapshots. | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Backend milestone: `MILESTONE_PLATFORM_TENANT_LIFECYCLE_API.md`.
- Operator scopes (`support:*` / `platform:operator`) and tenant role enforcement.
- Existing BFF/SDK architecture and session cookie auth.

---

<!-- SECTION: Open Questions -->
## Open Questions

Resolved decisions:
- **Tenant Settings gating:** Use tenant admin (owner/admin) gating for tenant account actions; keep
  billing-specific cards gated by `billing:manage`.
- **Ops navigation:** Convert Ops into a grouped nav with sub-items (Status + Tenants) gated by operator scopes.
- **Operator list default:** Default to active-only with a status filter that can expand to all.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Incorrect scope/role gating blocks valid users. | High | Centralize operator scope checks and update tenant admin gating logic. |
| Lifecycle actions missing audit reasons. | Med | Require reason input for suspend/reactivate/deprovision. |
| UI relies on billing scope for tenant account updates. | Med | Separate tenant account actions from billing-only controls. |
| Incomplete BFF coverage breaks frontend layering rule. | High | Ensure all new endpoints go through BFF + server services. |

---

<!-- SECTION: Review Follow-ups -->
## Review Follow-ups (Engineering Review Findings)

**Goal:** Resolve review findings to production-grade standards with clean architecture and maintainable patterns.

### Decisions (Open Questions Resolved)
- **Operator surface:** Operators manage tenants exclusively via `/api/v1/platform/tenants/*`. The tenant admin endpoint `/api/v1/tenants/account` is **self-service only** and must ignore operator override inputs from the browser.
- **Operator scope semantics:** Canonical operator scopes are `support:*` and `platform:operator`. Centralize the check in `lib/auth/roles.ts` and import it in BFF helpers to avoid drift.
- **Operator slug policy:** Slugs are durable identifiers. Operators may update slugs to another valid value, but the UI must **not** allow clearing a slug once set. (Create remains optional.)
- **Post-create detail UX:** After creating a tenant, open the detail **sheet only on mobile**. Desktop already has the detail panel, so avoid the extra overlay.

### Remediation Tasks

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| R1 | Operator UI | Add tenant **detail + create + update** flows in `features/tenant-ops` with a clean, composable UI (table + detail panel/drawer + create/edit dialogs). | ✅ |
| R2 | BFF Security | Remove reliance on client-supplied `X-Tenant-Id` / `X-Operator-*` headers in `/api/v1/tenants/account`; derive access solely from session, or ignore overrides. Add tests for the new behavior. | ✅ |
| R3 | Auth DRY | Deduplicate operator scope logic by reusing `lib/auth/roles.hasOperatorScope` inside `app/api/v1/platform/_utils/auth.ts`. | ✅ |
| R4 | Storybook | Update tenant settings stories (and mocks) to cover `canManageBilling` variations and the tenant account card query path. | ✅ |
| R5 | Docs | Ensure the milestone tracker is tracked/committed with these follow-ups and any snapshot updates. | ✅ |

### Implementation Plan (Review Follow-ups)

**R1 — Operator UI (clean, professional UX)**
- Layout: keep the existing filters + table, add a right-side **detail panel** on desktop; use a **Sheet/Drawer** on mobile for tenant details.
- New components under `features/tenant-ops/components`:
  - `TenantOpsTable` row click selects tenant.
  - `TenantOpsDetailPanel` shows name/slug/status/status history (KeyValueList + InlineTag).
  - `TenantCreateDialog` (name + optional slug) and `TenantEditDialog` (name/slug).
  - Reuse `TenantLifecycleDialog` for lifecycle actions; surface actions in both table rows and detail panel.
- Data flow:
  - `usePlatformTenantsQuery` drives the list.
  - `usePlatformTenantQuery` fetches the selected tenant for the detail panel.
  - `useCreatePlatformTenantMutation` and `useUpdatePlatformTenantMutation` invalidate list + detail.
- UX polish:
  - Empty state CTA to “Create tenant”.
  - Inline status + timestamps.
  - Toasts on success/failure; disable buttons while submitting.

**R2 — BFF Security (tenant account)**
- Remove `X-Tenant-Id` and `X-Operator-*` passthrough from `app/api/v1/tenants/account/route.ts`.
- Keep optional `X-Tenant-Role` down-scope only.
- Add tests asserting headers are ignored and that missing/invalid sessions return 401/403.

**R3 — Auth DRY**
- Import `hasOperatorScope` from `lib/auth/roles` inside `app/api/v1/platform/_utils/auth.ts`.
- Remove duplicate scope list to keep a single canonical source of truth.

**R4 — Storybook Coverage**
- Update `TenantSettingsWorkspace` stories to cover:
  - `canManageBilling=true` (billing cards visible).
  - `canManageBilling=false` (alert shown).
  - Tenant account loading/error states.
- Add/extend Storybook mocks for `/api/v1/tenants/account`.

**R5 — Docs & Snapshots**
- Keep this milestone tracker updated as tasks are completed.
- Update SNAPSHOTs if new components/feature sub-structure are added.

### Acceptance Criteria (Review Follow-ups)
- Operator UI includes: list, detail view, create tenant dialog, edit tenant dialog, lifecycle actions with reason input, and responsive layout (table + detail panel on desktop, drawer/sheet on small screens).
- `/api/v1/tenants/account` ignores client-supplied operator override headers; access is derived from session only; tests cover unauthorized/forbidden behavior.
- Single canonical operator scope check is used across UI gating and BFF auth helpers.
- Storybook shows tenant settings with and without billing scope, and tenant account loading/error states.
- Tracker updated and committed; snapshots updated if new files/components are introduced.

---

<!-- SECTION: Review Addendum -->
## Review Addendum (Post-Completion Findings)

**Scope:** Address remaining production-readiness findings discovered during the resume-grade engineering review.

### Plan (All Findings)

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| R6 | Security | Remove operator override/tenant-id headers from `lib/server/services/tenantAccount.ts` (self-service only). Update `/api/v1/tenants/account` tests to cover 401/403 and confirm overrides are ignored. | ✅ |
| R7 | UX | Disable lifecycle action buttons while a lifecycle mutation is pending to prevent duplicate submissions. | ✅ |
| R8 | UX | Prevent clearing a tenant slug in the edit dialog; show validation if blank, but allow changing to a different valid slug. | ✅ |
| R9 | UX | Open tenant detail sheet after create only on mobile; rely on the desktop detail panel otherwise. | ✅ |
| R10 | QA | Re-run `pnpm lint` and `pnpm type-check` after the fixes land. | ✅ |

### Acceptance Criteria (Review Addendum)
- Tenant account service no longer accepts operator override headers; BFF tests cover missing/invalid session behavior for `/api/v1/tenants/account`.
- Lifecycle actions are disabled during pending lifecycle mutations to prevent duplicate requests.
- Tenant slug cannot be cleared in the edit dialog; validation is explicit and consistent with create/edit rules.
- Mobile-only post-create detail sheet behavior aligns with desktop panel UX.
- Lint and type-check pass after the remediation changes.
---

<!-- SECTION: Review Addendum Round 2 -->
## Review Addendum (Post-Review Polish)

**Scope:** Address remaining correctness/UX/maintainability gaps identified during the resume-grade review.

### Plan (All Findings)

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| R11 | UX | Ensure newly created tenants are selected immediately (detail panel/sheet shows the new tenant even before the list refresh completes). | ✅ |
| R12 | UX | Keep the tenant detail panel resilient to transient detail fetch failures when list summary data exists (avoid blanking the panel). | ✅ |
| R13 | UX | Avoid “No tenants found” empty states when `total > 0`; provide a clear recovery action for offset drift. | ✅ |
| R14 | DRY | Deduplicate tenant date formatting into a shared `lib/utils/time` helper and reuse in settings + ops. | ✅ |
| R15 | Tests | Add focused unit coverage for `TenantAccountCard` validation, save enablement, and error retry flows. | ✅ |

### Acceptance Criteria (Review Addendum Round 2)
- After create, the selected tenant and detail view always reflect the newly created tenant, without relying on list refresh timing.
- Detail panel continues to render tenant summary data when the detail query errors; full error state only appears when no tenant data exists.
- Empty states only appear when `total === 0`; offset drift shows a recovery prompt (reset filters / previous page).
- Tenant date formatting uses a single shared helper across settings + ops.
- TenantAccountCard unit tests cover: save enablement, required name validation, and error retry rendering.

---

<!-- SECTION: Review Addendum Round 3 -->
## Review Addendum (Tenant Settings Access)

**Scope:** Ensure tenant settings access restrictions are communicated clearly without blocking the tenant account surface.

### Plan (All Findings)

| ID | Area | Description | Status |
| --- | --- | --- | --- |
| R16 | UX | Handle tenant settings access restrictions gracefully (non-admin or forbidden), add Storybook coverage, and add unit coverage for the restricted state. | ✅ |
| R17 | UX | Align tenant settings access gate with billing-scope access; keep tenant account updates role-only with a clear restricted state. | ✅ |

### Acceptance Criteria (Review Addendum Round 3)
- Tenant settings workspace surfaces an access-restricted panel when settings cannot be accessed, without blocking the tenant account card.
- Storybook includes a “settings access restricted” state.
- Unit test covers the restricted state rendering.
- Billing-scope users can access billing settings even without owner/admin role; tenant account updates remain restricted to owner/admin with a clear message.

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `pnpm lint` (apps/web-app)
- `pnpm type-check` (apps/web-app)
- Add/extend route tests under `apps/web-app/app/api/v1/**/route.test.ts` as needed.
- Add/extend unit tests for key UI flows (tenant settings + tenant ops).

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No feature flags (repo policy). Changes are active on deploy.
- No DB migrations required on frontend.
- If UI regressions occur, disable new nav entries or hide controls at the feature level.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-31 — Tracker created; findings documented; OpenAPI + SDK regeneration completed.
- 2025-12-31 — P1 complete: BFF routes, server services, client API, queries, and BFF route tests added; pnpm lint/type-check run.
- 2025-12-31 — P2 complete: tenant admin + operator UI wired, nav gating updated, component tests added; pnpm lint/type-check run.
- 2025-12-31 — P3 complete: snapshots updated; pnpm lint/type-check run.
- 2025-12-31 — Engineering review findings recorded and remediation plan added (R1–R5).
- 2025-12-31 — Review follow-ups implemented: operator UI detail/create/edit, BFF hardening, operator scope DRY, Storybook mocks/stories, snapshots updated; pnpm lint/type-check run.
- 2025-12-31 — Review addendum remediation complete (R6–R10): tenant account headers removed, lifecycle actions disabled while pending, slug clearing prevented, mobile-only post-create detail sheet, pnpm lint/type-check run.
- 2025-12-31 — Review addendum round 2 complete (R11–R15): tenant selection fixes, resilient detail panel, offset recovery UI, date formatting DRY, TenantAccountCard tests; pnpm lint/type-check run.
- 2025-12-31 — Review addendum round 3 complete (R16): tenant settings access restricted handling + story/test; pnpm lint/type-check run.
- 2025-12-31 — Review addendum round 3 update (R17): billing-scope access aligned; tenant account restrictions clarified; pnpm lint/type-check run.
