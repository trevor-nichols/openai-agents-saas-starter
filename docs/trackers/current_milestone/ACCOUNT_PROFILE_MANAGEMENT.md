<!-- SECTION: Metadata -->
# Milestone: Account & Profile Management (Users API + Web App)

_Last updated: 2025-12-27_  
**Status:** Completed  
**Owner:** OpenAI Agents SaaS Starter Team  
**Domain:** Backend + Frontend  
**ID / Links:** [Reviewer comment], `apps/api-service/src/app/api/v1/users/routes_profile.py`, `apps/web-app/features/account/components/ProfilePanel.tsx`

---

<!-- SECTION: Objective -->
## Objective

Deliver end-to-end, self-service account/profile management: API endpoints plus a web app experience for profile updates, email changes with verification, and account disablement, all implemented with clean architecture boundaries and auditable security controls.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `PATCH /users/me/profile` supports partial updates for profile fields (including `timezone` + `locale`)
- `PATCH /users/me/email` verifies current password, updates email, revokes sessions, and sends verification
- `POST /users/me/disable` disables the account and revokes sessions (blocked if last tenant owner)
- User repository + service layers expose clean domain methods for profile update, email change, and owner checks
- Security events recorded for email change + account disable
- Web app BFF routes proxy the new endpoints (`/api/v1/users/me/profile`, `/email`, `/disable`)
- Client fetchers + TanStack Query hooks added for profile update, email change, and disable
- Account Profile UI supports profile edits, timezone/locale, email change with verification messaging, and disable
- Storybook mocks updated for account/profile queries
- `hatch run lint` and `hatch run typecheck` pass for backend
- `pnpm lint`, `pnpm type-check`, and `pnpm test:unit` pass for frontend
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Profile update endpoints + schemas (display name, given/family name, avatar URL, timezone, locale)
- Email change with verification flow and session revocation
- Self-service account disable (soft delete)
- Block disable/email change if user is the last tenant owner
- Repository + service contracts for profile/email/ownership checks
- Security event logging for sensitive actions
- Web app BFF routes, client fetchers, and React Query hooks for new endpoints
- Account Profile UI for profile updates, email change, and account disable

### Out of Scope
- Hard delete or data erasure workflows
- Admin-managed user lifecycle or tenant role reassignment
- Avatar upload tooling (URL-only for now)

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Clear layering (API → service → repo → BFF → client hooks → UI). |
| Implementation | ✅ | Backend and frontend flows implemented. |
| Tests & QA | ✅ | Backend + frontend lint/typecheck/tests green. |
| Docs & runbooks | ✅ | Tracker updated with frontend completion details. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add write-capable methods to `UserRepository` for profile updates + email changes.
- Keep auth/session revocation in route layer to avoid coupling user service to auth service.
- Use soft-disable (`UserStatus.DISABLED`) for self-service delete; block if user is last tenant owner.
- Trigger email verification on change and clear `email_verified_at`.
- Record security events for email change and disable.
- Web app follows the SDK → server services → BFF → client fetchers → TanStack hooks → feature UI layering.
- Profile UI composes account session metadata with the user profile endpoint for editable fields.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Domain + Repository

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Domain | Add DTOs + repository contract methods for profile/email/owner checks | Team | ✅ |
| A2 | Repo | Implement profile upsert and email update in Postgres repository | Team | ✅ |
| A3 | Repo | Implement last-owner detection query | Team | ✅ |

### Workstream B – Service Layer

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Service | Add `update_profile`, `change_email`, `disable_account` methods | Team | ✅ |
| B2 | Service | Enforce current-password checks and owner blocking | Team | ✅ |
| B3 | Service | Emit security events for sensitive actions | Team | ✅ |

### Workstream C – API Layer

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | API | Add schemas for profile update/email change/disable | Team | ✅ |
| C2 | API | Implement `/users/me/profile`, `/users/me/email`, `/users/me/disable` routes | Team | ✅ |
| C3 | API | Revoke sessions after email change/disable | Team | ✅ |

### Workstream D – Tests & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Tests | Repository tests for profile upsert, email uniqueness, owner checks | Team | ✅ |
| D2 | Tests | Service tests for email change + disable flows | Team | ✅ |
| D3 | Tests | Route tests for new endpoints + error mapping | Team | ✅ |
| D4 | Docs | Update users service README and trackers | Team | ✅ |

### Workstream E – Web App Data Access

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | BFF | Add `/api/v1/users/me/profile`, `/email`, `/disable` route handlers | Team | ✅ |
| E2 | Services | Extend `lib/server/services/users` for update/email/disable | Team | ✅ |
| E3 | Client | Add `lib/api/users` fetchers + `lib/queries/users` mutations | Team | ✅ |

### Workstream F – Web App UX

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | UI | Profile edit form (display name, avatar URL, names, timezone, locale) | Team | ✅ |
| F2 | UI | Email change form with verification messaging | Team | ✅ |
| F3 | UI | Account disable dialog + last-owner warning copy | Team | ✅ |
| F4 | UX | Resend verification CTA remains visible | Team | ✅ |

### Workstream G – Web App Tests & QA

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| G1 | Tests | Unit tests for profile form mapping utilities | Team | ✅ |
| G2 | Storybook | Update mocks for account + users queries | Team | ✅ |
| G3 | QA | `pnpm lint`, `pnpm type-check`, `pnpm test:unit` | Team | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Confirm semantics + scope | Tracker approved | ✅ |
| P1 – Domain/Repo | Domain + repository methods | Repo tests green | ✅ |
| P2 – Service/API | Service + routes wired | Route tests green | ✅ |
| P3 – QA/Docs | Lint/typecheck + docs | All checks green | ✅ |
| P4 – Web App Data | BFF + services + hooks | Data access verified | ✅ |
| P5 – Web App UI | Account profile UX | UI flows complete | ✅ |
| P6 – Web App QA | Lint/typecheck/tests | Frontend checks green | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Postgres and Redis configured for auth subsystem (existing dependency)
- Email verification service + token store (already in use)
- Web app BFF routing + generated SDK updated from OpenAPI

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Last-owner lockout gaps | High | Explicit repository query + service-level check before disable. |
| Email uniqueness conflict | Med | Normalize + catch integrity error with explicit domain error. |
| Session revocation coupling | Low | Keep revocation in routes, not in user service. |
| UX confusion after email change | Med | Inline copy + forced logout after successful change. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/unit/accounts/test_user_repository.py`
- `cd apps/api-service && hatch run test tests/unit/accounts/test_user_service.py`
- `cd apps/api-service && hatch run test tests/unit/api/test_user_profile_routes.py`
- `cd apps/web-app && pnpm lint`
- `cd apps/web-app && pnpm type-check`
- `cd apps/web-app && pnpm test:unit`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations expected (profile table exists).
- No feature flags; endpoints are immediately available.
- Soft-disable uses existing `UserStatus.DISABLED` behavior.
- Email change and account disable flows should log the user out immediately after success.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-27 — Tracker created and plan approved (backend).
- 2025-12-27 — Backend domain, repository, service, and API updates implemented with tests + QA runs.
- 2025-12-27 — Frontend plan added (data access + profile management UX).
- 2025-12-27 — Frontend data access + UI implemented; lint/typecheck/test:unit green.
