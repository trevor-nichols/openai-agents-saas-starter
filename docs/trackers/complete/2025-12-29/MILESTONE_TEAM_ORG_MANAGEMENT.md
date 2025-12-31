<!-- SECTION: Metadata -->
# Milestone: Team / Org Management

_Last updated: 2025-12-29_  
**Status:** In Progress (API + frontend complete; SDK export deferred)  
**Owner:** TBD  
**Domain:** Cross-cutting  
**ID / Links:** TBD

---

<!-- SECTION: Objective -->
## Objective

Deliver tenant-scoped team management for existing tenants, including member list/add/remove/role updates and invite-by-email with self-serve password creation, without altering the existing signup invite system.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Tenant membership CRUD endpoints exist and are tenant-role gated (admin/owner).
- Invite-by-email flow exists for existing tenants; invite acceptance supports new user creation and password set.
- New invite table migrated with clean repository/service boundaries and audit logging.
- UI includes a Team settings page with member list, role changes, removes, and invites.
- BFF routes + SDK regeneration completed; no direct backend calls from browser.
- Tests cover service invariants (last owner protection), invite lifecycle, and API contracts.
- `hatch run lint` + `hatch run typecheck` (backend) and `pnpm lint` + `pnpm type-check` (frontend) pass.
- Docs/trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- New domain module for team/org (members + invites) with repository protocols.
- Persistence repositories:
  - Membership repository (tenant_user_memberships).
  - Invite repository (new tenant member invite table).
- Services:
  - Member list/add/remove/role update.
  - Invite issue/list/revoke/accept (accept creates user + membership when needed).
- API endpoints under `/api/v1/tenants/*` for member management and tenant invites.
- Invite acceptance endpoint that returns session tokens on success.
- Web app settings page (`/settings/team`) + feature module.
- OpenAPI export + HeyAPI client regeneration.
- Tests (unit + contract + smoke) for new surfaces.

### Out of Scope
- Tenant account CRUD (list/create/update/delete tenants).
- SCIM/SAML/SSO provisioning or external directory sync.
- Billing changes or cross-tenant operator management.
- Console workflows (starter-console) unless explicitly requested later.
- Feature flags or backward-compat layers.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Plan aligned to existing auth/signup/invite patterns. |
| API service (A–C, E) | ✅ | Team/org backend complete; `hatch run lint`, `hatch run typecheck`, `hatch run test` pass. |
| Frontend/SDK (D, F) | ✅ | Frontend phases complete; QA + closeout done; SDK export deferred. |
| Docs & runbooks | ✅ | Tracker updated for API-service closeout. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Role model:** standard roles `owner`, `admin`, `member`, `viewer`. Map to scopes via `services/users/scopes.py`; gate endpoints with `require_tenant_role`.
- **Invite strategy:** new invite type for existing tenants; acceptance flow supports new user creation and password set (self-serve). Invite token acts as email verification.
- **Data model:** new `tenant_member_invites` table with token hash, status, expiry, inviter, invitee email, role, accepted_by_user_id.
- **Services:** separate `TenantMembershipService` and `TenantInviteService` to avoid coupling with signup invites.
- **Email delivery:** use existing Resend adapter path (or logging fallback) for invite emails; keep audit events for issue/accept/revoke.
- **API surface:** new tenant-scoped endpoints (members + invites) under `api/v1/tenants` plus public invite-accept endpoint.
- **Frontend:** new Settings/Team page + feature module; BFF proxy routes under `app/api/v1/tenants`.

---

<!-- SECTION: Review Findings -->
## Review Findings (2025-12-29)

- **Role taxonomy drift:** `member` exists in team service but not in `TenantRole` or scope mapping, which would down-scope members to viewers at runtime. Must unify roles across domain, scopes, and API gating.
- **Invite acceptance atomicity:** Current flow can create users/memberships before marking an invite accepted; races or revocations can leave orphaned records.
- **Invite lifecycle integrity:** Revocation can overwrite accepted/expired invites, breaking auditability.
- **Cross-tenant revoke gap:** Revoke accepts invite UUID without tenant scoping, enabling cross-tenant revoke if a UUID leaks.
- **Owner role governance:** Admins can currently assign/demote `owner` via member add/update or invites; require owner-only policy.
- **Audit completeness:** `team.invite_revoked` log omits tenant_id/user_id, weakening auditability.
- **Delivery failure audit gap:** invite delivery failures revoke the invite without emitting `team.invite_revoked`, leaving audit logs incomplete. (Addressed)
- **Layering note:** Team invite service directly queries `TenantAccount` to resolve tenant name (service → ORM coupling). Track for follow-up once functional issues are stabilized.

---

<!-- SECTION: Decisions -->
## Decisions (2025-12-29)

- **Tenant roles:** `member` is a first-class tenant role. Canonical order is `viewer < member < admin < owner`, and all tenant role gates that allow `viewer` must also allow `member`.
- **Owner-only assignment:** Only existing owners can grant or revoke the `owner` role. Admins may assign up to `admin` but cannot promote/demote owners.
- **Invite revocation:** Only `ACTIVE` invites are revocable. `ACCEPTED`/`EXPIRED` invites are immutable; revoke attempts return a conflict.
- **Revocation strictness:** `REVOKED` invites are also immutable; repeat revoke returns conflict for audit integrity.
- **Invite acceptance:** Acceptance must be atomic (single transaction) to prevent orphaned users/memberships and ensure invite state is consistent.
- **Settings navigation:** Add a `/settings` layout with a left-rail nav; main entry points route to `/settings/team` for intuitive default.
- **Member onboarding UI:** Provide both “Add existing user by email” and “Invite by email” flows in the Team settings surface.
- **Role visibility:** Surface `viewer`, `member`, `admin`, `owner` in UI; enforce owner-only assignment/demotion for `owner`.
- **Invite acceptance UX:** Allow logged-in users to accept invites directly from `/accept-invite` using “accept as current user.”
- **Pagination UX (initial):** Ship single-page list views with client pagination; server pagination to follow once list sizes demand it.

---

<!-- SECTION: Frontend Phase Plan -->
## Frontend Phase Plan (Web App)

### Phase 1 — Data & BFF (Team domain)
- Add team types, server services, BFF routes, client fetch helpers, query hooks, and query keys.
- BFF routes for tenant members + invites (list/issue/revoke/update/remove).
- Unit tests for API helpers + route tests for core BFF endpoints.
- Run `pnpm lint` + `pnpm type-check`.

### Phase 2 — Settings UI
- New `features/settings/team` module with Members + Invites panels and dialogs.
- Add `/settings/team` page and a `/settings` layout with left-rail nav.
- Update user menus to link to `/settings/team`.
- Add component tests for dialog validation or role gating where appropriate.
- Run `pnpm lint` + `pnpm type-check`.

### Phase 3 — Invite Acceptance
- Add public `/accept-invite` page with new-user form + password policy surface.
- Add “accept as current user” mutation.
- Add server action to accept invites and persist session cookies.
- Add tests for form validation and server action error handling.
- Run `pnpm lint` + `pnpm type-check`.

### Phase 4 — QA & Closeout
- Run relevant unit tests + Playwright happy path (if applicable).
- Update tracker statuses and close out Workstream D (F1 remains deferred).
  - Status: ✅ Completed 2025-12-29 (unit tests run; lint/type-check green).

---

<!-- SECTION: Refactor Plan -->
## Invite Acceptance Refactor Plan (Clean Port + UoW)

Goal: remove ORM coupling from `TeamInviteService` and execute invite acceptance through a dedicated port + transactional repository, while keeping password policy and audit behavior consistent.

1. **Domain port + DTO**
   - Add `TeamInviteAcceptanceRepository` + `TeamInviteAcceptResult` to `app/domain/team.py`.
   - Move team error types to `app/domain/team_errors.py` so API + services depend on domain, not service layer shims.
2. **Transactional repository (UoW)**
   - Implement `PostgresTeamInviteAcceptanceRepository` to lock invite rows, validate status/expiry, create user + membership + password history, and mark accepted in one transaction.
3. **Service wiring**
   - Inject acceptance repository into `TeamInviteService`; remove ORM/session usage from the service.
   - Preserve password policy validation and audit logging.
4. **Tests**
   - Add acceptance success coverage (new user) verifying user, membership, password history, and invite status.
   - Update existing tests for new injection.
5. **Cleanup**
   - Remove service-layer error shim.
   - Align role/scopes mapping and audit fields.

Status: In progress (active refactor to keep clean architecture).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Domain + Persistence

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Domain | Add team/org domain models + repo protocols | ✅ |
| A2 | DB | Migration for `tenant_member_invites` | ✅ |
| A3 | Persistence | Implement membership + invite repositories | ✅ |
| A4 | Persistence | Tenant account lookup repository for invite emails | ✅ |

### Workstream B – Services

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | Service | TenantMembershipService (list/add/remove/role update) | ✅ |
| B2 | Service | TenantInviteService (issue/list/revoke/accept) | ✅ |
| B3 | Service | Audit logging + last-owner protection | ✅ |
| B4 | Service | Owner-only role policy enforcement (member + invite flows) | ✅ |
| B5 | Service | Tenant-scoped revoke + strict revoke semantics | ✅ |
| B6 | Service | Resolve tenant name via repository (remove ORM coupling) | ✅ |
| B7 | Service | Log `team.invite_revoked` on delivery-failure revocations | ✅ |

### Workstream C – API

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | API | Member endpoints in `api/v1/tenants` | ✅ |
| C2 | API | Invite endpoints + accept flow | ✅ |
| C3 | API | Pydantic schemas + error mapping | ✅ |
| C4 | API | Enforce owner-only role changes + tenant-scoped revoke | ✅ |

### Workstream D – Frontend

| ID | Area | Description | Status |
|----|------|-------------|--------|
| D1 | BFF | Add proxy routes under `app/api/v1/tenants` | ✅ |
| D2 | Feature | New `features/settings/team` module | ✅ |
| D3 | UI | Add `/settings/team` page + nav link | ✅ |
| D4 | Data | Team types + API helpers + query hooks | ✅ |
| D5 | Auth | Add `/accept-invite` flow + server action | ✅ |

### Workstream E – Tests & QA

| ID | Area | Description | Status |
|----|------|-------------|--------|
| E1 | Tests | Unit tests for services + invariants | ✅ |
| E2 | Tests | API contract tests (members + invites) | ✅ |
| E3 | Tests | Smoke/e2e happy-path coverage | ✅ |
| E4 | Tests | Coverage for owner-only role changes + strict revoke conflicts | ✅ |

### Workstream F – SDK + Docs

| ID | Area | Description | Status |
|----|------|-------------|--------|
| F1 | OpenAPI | Export superset schema + regenerate HeyAPI client | ⏸️ Deferred |
| F2 | Docs | Update trackers and any public docs | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Alembic migration process via `just migration-revision` + `just migrate`.
- Email delivery config (Resend) for invite emails; logging fallback acceptable.
- OpenAPI export + HeyAPI regeneration before frontend work that depends on new fields.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Invite token misuse or replay | High | Hash tokens at rest, enforce TTL + one-time redemption, log audit events. |
| Role/scopes mismatch (API vs tokens) | Med | Centralize role mapping + tests for role gates. |
| Last-owner removal regression | High | Explicit invariant checks + unit tests. |
| Coupling with signup invites | Med | Separate domain/service/repo for tenant member invites. |
| Email delivery failures block onboarding | Med | Logging fallback + clear UI error; allow resend/reissue. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `hatch run lint`, `hatch run typecheck`, plus targeted tests under `apps/api-service/tests`.
- Frontend: `pnpm lint`, `pnpm type-check`, relevant unit tests + Playwright happy path.
- OpenAPI + SDK regen:
  - `cd packages/starter_console && starter-console api export-openapi --output apps/api-service/.artifacts/openapi-fixtures.json --enable-billing --enable-test-fixtures`
  - `cd apps/web-app && OPENAPI_INPUT=../api-service/.artifacts/openapi-fixtures.json pnpm generate:fixtures`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Apply migration before deploying new API routes.
- No feature flags; ship end-to-end once tests pass.
- Invite emails rely on `APP_PUBLIC_URL` for links; ensure correct environment config.
- Rollback: revert API + UI changes only after migrating data safety is ensured; keep invite table intact.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-29 — Tracker created; plan approved (self-serve invite accept with password set).
- 2025-12-29 — Review findings + decisions updated (owner-only role changes, strict revoke, tenant-scope); new tasks added.
- 2025-12-29 — Full backend suite (`hatch run test`) + lint/typecheck run; tracker marked ready for closeout.
- 2025-12-29 — Added HTTP smoke coverage for tenant members/invites (issue/list/revoke) and updated smoke docs.
- 2025-12-29 — Phase 1 web app complete: team data types, server services, BFF routes, client API + queries, and unit tests. `pnpm lint` + `pnpm type-check` run.
- 2025-12-29 — Phase 2 web app complete: settings layout + team workspace (members/invites), nav updates, and UI utils/tests. `pnpm lint` + `pnpm type-check` run.
- 2025-12-29 — Phase 3 web app complete: `/accept-invite` page, accept-invite form + server action, existing-user accept, and validation tests. `pnpm lint` + `pnpm type-check` run.
- 2025-12-29 — Phase 4 web app QA: mocked `server-only` in Vitest setup, fixed route test mocks + tooltip provider, ran targeted Vitest suites, `pnpm lint`, and `pnpm type-check`.
