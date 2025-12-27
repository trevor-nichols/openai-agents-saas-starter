<!-- SECTION: Metadata -->
# Milestone: Account & Profile Management (Users API)

_Last updated: 2025-12-27_  
**Status:** Completed  
**Owner:** OpenAI Agents SaaS Starter Team  
**Domain:** Backend  
**ID / Links:** [Reviewer comment], `apps/api-service/src/app/api/v1/users/routes_profile.py`

---

<!-- SECTION: Objective -->
## Objective

Deliver first-class, self-service account/profile management in the API service: profile updates, email change with verification, and account disablement, implemented with clean architecture boundaries and auditable security events.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- `PATCH /users/me/profile` supports partial updates for profile fields (including `timezone` + `locale`)
- `PATCH /users/me/email` verifies current password, updates email, revokes sessions, and sends verification
- `POST /users/me/disable` disables the account and revokes sessions (blocked if last tenant owner)
- User repository + service layers expose clean domain methods for profile update, email change, and owner checks
- Security events recorded for email change + account disable
- Unit tests added for repository, service, and routes
- `hatch run lint` and `hatch run typecheck` pass for backend
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

### Out of Scope
- Hard delete or data erasure workflows
- Admin-managed user lifecycle or tenant role reassignment
- Frontend UI work

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Clear layering (API → service → repo) with existing auth/session patterns to reuse. |
| Implementation | ✅ | Profile updates, email change, and account disable flows implemented. |
| Tests & QA | ✅ | Repository/service/routes covered with unit tests. |
| Docs & runbooks | ✅ | Users service README + tracker updated. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add write-capable methods to `UserRepository` for profile updates + email changes.
- Keep auth/session revocation in route layer to avoid coupling user service to auth service.
- Use soft-disable (`UserStatus.DISABLED`) for self-service delete; block if user is last tenant owner.
- Trigger email verification on change and clear `email_verified_at`.
- Record security events for email change and disable.

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

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Confirm semantics + scope | Tracker approved | ✅ |
| P1 – Domain/Repo | Domain + repository methods | Repo tests green | ✅ |
| P2 – Service/API | Service + routes wired | Route tests green | ✅ |
| P3 – QA/Docs | Lint/typecheck + docs | All checks green | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Postgres and Redis configured for auth subsystem (existing dependency)
- Email verification service + token store (already in use)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Last-owner lockout gaps | High | Explicit repository query + service-level check before disable. |
| Email uniqueness conflict | Med | Normalize + catch integrity error with explicit domain error. |
| Session revocation coupling | Low | Keep revocation in routes, not in user service. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- `cd apps/api-service && hatch run test tests/unit/accounts/test_user_repository.py`
- `cd apps/api-service && hatch run test tests/unit/accounts/test_user_service.py`
- `cd apps/api-service && hatch run test tests/unit/api/test_user_profile_routes.py`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations expected (profile table exists).
- No feature flags; endpoints are immediately available.
- Soft-disable uses existing `UserStatus.DISABLED` behavior.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-27 — Tracker created and plan approved.
- 2025-12-27 — Domain, repository, service, and API updates implemented with tests + QA runs.
