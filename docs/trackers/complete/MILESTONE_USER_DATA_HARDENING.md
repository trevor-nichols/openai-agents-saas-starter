<!-- SECTION: Metadata -->
# Milestone: User Data Hardening

_Last updated: 2025-12-06_  
**Status:** In Progress  
**Owner:** @codex  
**Domain:** Backend  
**ID / Links:** (internal) | SNAPSHOT: apps/api-service/SNAPSHOT.md

---

<!-- SECTION: Objective -->
## Objective

Add first-class security/privacy primitives around users (MFA, consent logging, notification preferences, usage rollups, security events) so the starter ships with production-grade defaults without introducing API-key management for end users.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- New tables for MFA, recovery codes, user consents, notification prefs, usage rollups, and security events are modeled and migrated.
- ORM models align with existing auth/tenant shapes and keep SQLite test compatibility.
- Auth/session flow enforces MFA for users with verified factors; TOTP verification is rate limited and emits security events with context.
- Notification preference and usage counter writes are tenant-scoped, membership-validated, and concurrency-safe (ON CONFLICT upserts).
- Security event records include hashed IP/UA when available.
- Docs tracker updated with design + rollout notes.
- `hatch run lint` and `hatch run typecheck` are green.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- SQLAlchemy models + Alembic migration for new user-centric tables.
- Baseline docs in tracker (this file) and schema notes.

### Out of Scope
- User-facing UI/flows for MFA or preferences.
- End-user API key management (intentionally omitted).
- Stripe/customer billing profile changes.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Tables finalized for MFA/consent/notifications/usage/security events; MFA enforcement + tenant guardrails approved. |
| Implementation | 🟡 | Core tables/endpoints done; pending MFA enforcement, rate limiting, tenant checks, and atomic upserts. |
| Tests & QA | 🟡 | Stub tests merged; add integration for TOTP and upsert conflicts. |
| Docs & runbooks | ✅ | Rollout notes captured; migration applied locally. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add durable tables: `user_mfa_methods`, `user_recovery_codes`, `user_consents`, `user_notification_preferences`, `usage_counters`, `security_events`.
- Keep data minimization: hash/obscure IPs and UAs; no plaintext secrets; no user API keys.
- Multi-tenant aware: preferences/usage include optional tenant_id; FKs reuse existing `users` / `tenant_accounts`.
- Migration will merge existing two heads (`fd0d6a8ba881`, `b6dcb157d208`).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Schema & Migration

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Design | Finalize columns/indexes for new tables, confirm with current models | @codex | ✅ |
| A2 | DB | Add SQLAlchemy models under auth persistence | @codex | ✅ |
| A3 | DB | Write Alembic migration merging heads | @codex | ✅ |

### Workstream B – Validation & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | QA | Run `hatch run lint` and `hatch run typecheck` | @codex | ✅ |
| B2 | Docs | Update milestone/rollout notes after implementation | @codex | ✅ |

### Workstream C – Feature Wiring

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Auth | MFA service + routes + security event emission | @codex | ✅ |
| C2 | Compliance | Consent record/read endpoints | @codex | ✅ |
| C3 | Notifications | Notification preference CRUD | @codex | ✅ |
| C4 | Usage | Usage counter integration + read API | @codex | ✅ |
| C5 | Security | Wire security event emission across auth flows | @codex | ✅ |
| C6 | Auth | Enforce MFA during session issuance (password login + recovery) and add TOTP rate limiting | @codex | ⏳ |
| C7 | Security | Include IP/UA hashes in password/MFA security events; add request_id tagging | @codex | ⏳ |
| C8 | Notifications | Enforce tenant membership on notification prefs; replace select+insert with ON CONFLICT upsert | @codex | ⏳ |
| C9 | Usage | Make usage counter increments atomic (ON CONFLICT) and preserve SQLite compatibility | @codex | ⏳ |
| C10 | Tests | Add integration tests: real TOTP verify, notification upsert conflict, usage upsert conflict | @codex | ⏳ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Align | Confirm schema + tracker | Tracker drafted, table list locked | ✅ | 2025-12-06 |
| P1 – Impl | Models + migration + static checks | Code merged, lint/typecheck green | ⏳ | 2025-12-06 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Current alembic heads (`fd0d6a8ba881`, `b6dcb157d208`).
- None external (Stripe/Vault not involved).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| SQLite compatibility issues with new columns/types | Med | Use JSONB/Text fallbacks already in repo; avoid PG-only features beyond ENUM/CITEXT; test via typecheck/lint. |
| Migration branch conflicts | Low | Merge both current heads in new revision. |
| Unused tables causing drift | Low | Keep scope minimal; document usage + planned services. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd apps/api-service && hatch run lint`
- `cd apps/api-service && hatch run typecheck`
- (Post-approval) `just migrate` against dev DB to apply new tables.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Apply migration via `just migrate` after code lands.
- No feature flags; tables are additive and inert until wired to services/UI.
- No data backfill required (new tables start empty).

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-07 — Added follow-up tasks for MFA enforcement, rate limits, tenant guards, atomic upserts, and integration tests.
- 2025-12-06 — Added unit + contract tests for MFA, consents, notifications, usage; lint/typecheck passing.
- 2025-12-06 — Wired MFA, consent, notifications, usage counters, and security events; APIs added and checks green.
- 2025-12-06 — Migration applied locally (alembic upgrade heads); rollout notes finalized.
- 2025-12-06 — Added MFA/consent/notification/usage/security tables + migration; lint/typecheck green.
- 2025-12-06 — Created milestone and locked target table set.
