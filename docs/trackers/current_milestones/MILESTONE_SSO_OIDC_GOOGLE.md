<!-- SECTION: Metadata -->
# Milestone: Optional OIDC SSO (Google)

_Last updated: 2026-01-01_  
**Status:** Complete  
**Owner:** Platform Foundations / Backend Auth Pod  
**Domain:** Cross-cutting  
**ID / Links:** docs/auth/idp.md, docs/architecture/authentication-ed25519.md, docs/frontend/data-access.md

---

<!-- SECTION: Objective -->
## Objective

Add production-grade, optional OIDC SSO with Google as the first provider, while keeping password login intact. The system should be provider-agnostic, tenant-aware, and aligned with existing auth/token architecture so future IdPs can be added without redesign.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- OIDC SSO start + callback endpoints implemented with PKCE + state/nonce validation
- Per-tenant provider configs and user identity links persisted in Postgres with migrations
- Global provider fallback supported via a single NULL-tenant config row (used only when a tenant config is absent)
- Auto-provision policy default = invite_only with domain allowlist support
- SSO login reuses existing token issuance, including MFA challenge flow when methods are enrolled
- OIDC security hardening: enforce allowed ID token algorithms (discovery-aware) + token endpoint auth method validation
- PKCE enforcement respects provider config (pkce_required)
- SSO state store treats malformed payloads as invalid/expired (no 500s)
- Starter Console setup flow supports optional SSO configuration and can seed provider config
- Wizard supports tenant-scoped config via slug or UUID
- Frontend login can initiate SSO and complete callback, storing session cookies via Next API routes
- OpenAPI artifacts + generated SDK refreshed
- Backend: `hatch run lint`, `hatch run typecheck`, tests pass
- Frontend: `pnpm lint`, `pnpm type-check` pass
- Console: `cd packages/starter_console && hatch run lint` and `... typecheck` pass
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- OIDC provider abstraction + Google preset (issuer, scopes, discovery, JWKS validation)
- SSO state store (Redis) for PKCE verifier, state, nonce
- New domain models + repository interfaces for provider config and identity links
- Postgres persistence + Alembic migration
- Auth service integration for token issuance and MFA challenge handling
- API routes and Pydantic schemas for SSO start/callback + provider listing
- Console wizard prompts + optional seed script to configure SSO
- Frontend login option and callback handling via Next API routes
- Observability events for SSO success/failure/linking/provisioning
- Tests (unit + contract + smoke gating) and docs updates

### Out of Scope
- SCIM provisioning
- SAML support
- IdP-initiated SSO
- Session management with external IdP (logout propagation)
- Multi-provider policy orchestration beyond Google (future-ready but not shipped here)

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Detailed API plan captured in this tracker |
| Implementation | ✅ | Backend hardening + console integration + frontend SSO flow complete |
| Tests & QA | ✅ | Unit/contract/smoke coverage in place; frontend lint/type-check verified |
| Docs & runbooks | ✅ | IdP doc + runbook updated with SSO flow details |

---

## Engineering Review Findings (2026-01-01)

| ID | Finding | Action | Status |
| --- | --- | --- | --- |
| R1 | Redis SSO state parsing can 500 on malformed payloads (non-dict/missing keys). | Guard payload decoding + return invalid/expired when malformed; add unit tests. | ✅ |
| R2 | Wizard always requires client secret before token auth method selection; `none` auth method cannot be configured. | Gate client secret prompt on chosen token auth method; document behavior. | ✅ |
| R3 | No direct unit tests for state-store decoding and OIDC hardening (alg allowlist + token auth method validation). | Add focused unit tests to cover these branches. | ✅ |
| R4 | Unrelated edits in older milestone docs included in diff. | Confirm whether to keep or revert before merge. | ✅ |
| R5 | OIDC ID token verification does not require `exp`/`iat` claims (PyJWT defaults allow missing `exp`). | Require `exp` + `iat` via `jwt.decode(..., options={"require": ["exp", "iat"]})`; add unit coverage for missing claims. | ✅ |
| R6 | SSO start request validation returns 422 from Pydantic when tenant context is missing/both set, but the milestone error contract expects 400/409. | Normalize to explicit HTTP errors in the route layer (consistent with `/sso/providers`), or adjust contract/tests to accept 422 if desired. | ✅ |
| R7 | Invite-only acceptance path does not catch `TeamMemberAlreadyExistsError` on existing-user invite acceptance, so membership races can bubble as 500s. | Treat `TeamMemberAlreadyExistsError` as a soft success (return user) or map to a deterministic SSO error; add a unit test. | ✅ |
| R8 | Local artifact committed: `apps/api-service/src/app/services/sso/__pycache__/`. | Remove from working tree and ensure git ignores Python bytecode artifacts. | ✅ |
| R9 | Unrelated edits to completed milestones still present in working tree. | Decide to keep or revert the changes before merging this milestone. | ✅ |
| R10 | Global scope SSO config can silently retain tenant_id/slug values, causing tenant-scoped seeding/probes even when `SSO_GOOGLE_SCOPE=global`. | Enforce global scope exclusivity (reject or clear tenant_id/slug) and add unit/probe coverage. | ✅ |
| R11 | Domain-allowlist path does not emit `auth.sso.provisioned` when an existing user is newly added to a tenant. | Emit provisioning audit event for the membership add path + unit coverage. | ✅ |
| R12 | Contract tests do not assert tenant-selection error semantics for `/auth/sso/providers` or `/auth/sso/{provider}/start`. | Add contract coverage for missing/both tenant selectors (400/409). | ✅ |
| R13 | Docs/runbooks (e.g., `docs/auth/idp.md`) not updated to reflect SSO implementation details. | Update IdP doc + runbook notes to capture OIDC SSO behavior. | ✅ |

---

## Verification (2026-01-01)

- api-service: `hatch run lint`
- api-service: `hatch run typecheck`
- api-service: `hatch run test tests/unit/services/test_sso_oidc_client.py tests/unit/services/test_sso_service.py` (runner executed the full unit suite due to `tests/unit/` path: 934 passed, 26 skipped, 53 deselected)
- starter-console: `hatch run test` (236 passed, 1 skipped)
- web-app: `pnpm lint`
- web-app: `pnpm type-check`

---

## Follow-up Milestone

- 2026-01-01 — Created follow-up milestone for multi-provider console support: `docs/trackers/current_milestones/MILESTONE_SSO_OIDC_MULTI_PROVIDER_CONSOLE.md`.

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Primary protocol: OIDC Authorization Code with PKCE. State + nonce stored in Redis with short TTL.
- Provider configuration is tenant-scoped in Postgres; a NULL-tenant row is treated as a global fallback.
- Identity mapping table links internal users to `(provider, subject)` plus issuer and email.
- SSO callback reuses existing token issuance (EdDSA JWTs) and returns the same response shape as `/auth/token` (MFA challenge compatible).
- Auto-provision policy is tenant-configured; default is invite_only for this repo.
- Local MFA is enforced for SSO logins if the user has enrolled methods (consistent with password login).
- OIDC hardening: enforce allowed ID token algorithms (discovery-aware, asymmetric-only) and validate token endpoint auth method against discovery metadata.

<!-- SECTION: Design Decisions -->
## Design Decisions

- **ID token algorithms (discovery-aware):** Use `id_token_signing_alg_values_supported` when present. Enforce an asymmetric-only allowlist (`RS256/384/512`, `PS256/384/512`, `ES256/384/512`). Reject `none` and all `HS*`. Default to `RS256` for Google; allow per-provider overrides.
- **Token endpoint auth method:** Support `client_secret_post` (default), `client_secret_basic`, and `none` (public clients + PKCE). Validate configured method against discovery metadata when available. Design to extend to `private_key_jwt` later without schema breakage.
- **Provider-agnostic config:** Keep SSO flow data-driven. Store configurable provider options (auth method, alg allowlist, optional auth params) in provider config rather than code branches.
- **Console UX:** Provide a “Google preset” and a “Custom OIDC” path; keep advanced fields behind optional prompts to avoid overwhelming operators.

### Starter Console Integration Notes (Observed + Proposed)

- Setup wizard is sectioned under `packages/starter_console/src/starter_console/workflows/setup/_wizard/sections/` with
  gating in `schema.yaml` and UI wiring in `section_specs.py`.
- Provider prompts live in `sections/providers.py` and already run post-provider automations (Stripe, migrations, Redis).
- The console can run backend scripts via `services/infra/backend_scripts.py` (pattern used by dev-user + Stripe flows).

Recommended integration:
- Add optional SSO prompts under the Providers section (toggle + Google fields + policy controls).
- Add a backend seed script to upsert `sso_provider_configs`, then trigger it from the wizard
  (optionally via a new `AUTO_SSO` automation phase that runs after migrations).
- Add a dedicated `starter-console sso setup` command for headless provisioning (mirrors Stripe flow).
- Surface redirect URI guidance from `APP_PUBLIC_URL` + `/auth/sso/{provider}/callback` in the wizard output.

Proposed modules (names may shift but boundaries hold):
- `app/domain/sso.py` (provider config + identity link contracts)
- `app/services/sso/` (OIDC client, SSO flow orchestration)
- `app/infrastructure/persistence/auth/models/sso.py` (ORM models)
- `app/infrastructure/persistence/auth/sso_repository.py` (repos)
- `app/api/v1/auth/routes_sso.py` (SSO endpoints)

---

<!-- SECTION: API Service Detailed Plan -->
## API Service Implementation Plan (Detailed)

This section documents the backend architecture and step-by-step plan to avoid surprises.

### 1) Settings, Inputs, and Constraints

- **Redirect base URL:** Use `APP_PUBLIC_URL` from `app/core/settings/application.py` and append `/auth/sso/{provider}/callback`.
- **Tenant selection:** `POST /api/v1/auth/sso/{provider}/start` requires `tenant_id` or `tenant_slug` for deterministic routing.
- **Global provider fallback:** If a tenant has no provider config, use the global row (`tenant_id IS NULL`) for provider settings. Tenant selection still comes from the request.
- **Redis:** Reuse the `auth_cache` Redis client for SSO state/nonce/PKCE storage.
- **New settings (suggested):** `SSO_STATE_TTL_MINUTES`, `SSO_CLOCK_SKEW_SECONDS`, optional `SSO_ALLOWED_ISSUERS` in a new `app/core/settings/sso.py` mixin.

### 2) Data Model

#### 2.1 `sso_provider_configs`
Tenant-scoped provider configuration with a global fallback row.

Suggested columns:
- `id` UUID PK
- `tenant_id` UUID NULLABLE (NULL = global fallback)
- `provider_key` (e.g., `google`)
- `enabled` boolean
- `issuer_url` (OIDC issuer)
- `client_id`
- `client_secret_encrypted` (bytes, via `app/infrastructure/security/cipher.py`)
- `discovery_url` (optional override)
- `scopes` (JSONB array; default includes `openid email profile`)
- `pkce_required` boolean (true)
- `auto_provision_policy` enum: `disabled | invite_only | domain_allowlist`
- `allowed_domains` (JSONB array)
- `default_role` (tenant role used for auto-provision)
- `created_at`, `updated_at`

Constraints/indices:
- Unique `(tenant_id, provider_key)`
- Unique global per provider: partial unique index on `provider_key` where `tenant_id IS NULL`

#### 2.2 `user_identities`
Links users to external IdP subjects.

Suggested columns:
- `id` UUID PK
- `user_id` UUID FK -> `users.id`
- `provider_key`
- `issuer`
- `subject` (OIDC `sub`)
- `email`
- `email_verified` boolean
- `profile_json` (JSONB, optional)
- `linked_at`, `last_login_at`, `created_at`, `updated_at`

Constraints/indices:
- Unique `(provider_key, issuer, subject)`
- Unique `(user_id, provider_key)` to avoid multiple identities from the same provider for a user
- Index on `user_id`

### 3) Domain Contracts + Repositories

- `app/domain/sso.py`
  - `SsoProviderConfig`, `SsoProviderConfigRepository`
  - `UserIdentity`, `UserIdentityRepository`
  - `SsoAutoProvisionPolicy` enum
- `app/infrastructure/persistence/auth/models/sso.py` for ORM models
- `app/infrastructure/persistence/auth/sso_repository.py`
  - `fetch_provider_config(tenant_id, provider_key)` (tenant-first, fallback to global)
  - `get_identity_by_subject(provider_key, issuer, subject)`
  - `get_identity_by_user(user_id, provider_key)`
  - `link_identity(...)` (upsert semantics)

### 4) OIDC Client + SSO Service

#### 4.1 OIDC Client
- `app/services/sso/oidc_client.py`
  - `fetch_discovery_document(issuer_url)`
  - `exchange_code_for_tokens(...)`
  - `verify_id_token(...)` using JWKS and PyJWT
  - Validations: `iss`, `aud`, `exp`, `nbf`, `nonce`, clock skew, and `email_verified == true`

#### 4.2 SSO State Store
- `app/services/sso/state_store.py`
  - Redis-backed `set_state(state, payload, ttl)`, `consume_state(state)`
  - Payload: `tenant_id`, `provider_key`, `pkce_verifier`, `nonce`, `redirect_uri`, `requested_scopes`
  - `consume_state` is single-use (delete on read)

#### 4.3 SsoService
- `app/services/sso/service.py`
  - `start_sso(tenant_id|slug, provider_key, login_hint?) -> authorize_url`
  - `complete_sso(code, state) -> UserSessionTokens or MfaChallenge`
  - Uses `UserService`, `TenantMembershipService`, `TeamInviteService`, and `AuthService`
  - Auto-provision rules (see section 6)
  - Identity linking rules (see section 6)

### 5) API Routes + Schemas

#### Public auth routes
- `POST /api/v1/auth/sso/{provider}/start`
  - Request: `{ tenant_id | tenant_slug, login_hint? }`
  - Response: `{ authorize_url }`
- `POST /api/v1/auth/sso/{provider}/callback`
  - Request: `{ code, state }`
  - Response: `UserSessionResponse` or `MfaChallengeResponse`
- `GET /api/v1/auth/sso/providers`
  - Request: `{ tenant_id | tenant_slug }`
  - Response: enabled providers + display metadata

#### Tenant admin routes
- `POST/GET/DELETE /api/v1/tenants/{tenant_id}/sso/providers/{provider}`
  - CRUD for provider config
  - Requires `tenant:manage` / admin role

### 6) Identity Linking + Auto-Provisioning Rules (Invite-Only Default)

Resolution order on callback:
1) Find existing identity by `(provider, issuer, subject)` -> load user.
2) If not found, try email match:
   - Must have `email_verified=true`.
   - If user exists and already member of tenant -> link identity + proceed.
   - If user exists but not a member -> check auto-provision policy.
3) If no user exists -> auto-provision policy gate.

Invite-only policy (default):
- Require an active invite for that email + tenant.
- Add repository methods for email-based acceptance:
  - `find_active_invite_by_email(tenant_id, email)`
  - `accept_invite_by_id_for_existing_user(invite_id, user_id)`
  - `accept_invite_by_id_for_new_user(invite_id, user_id)` (creates user with random password hash)
- Mark invite accepted and create membership in one transaction.

Domain-allowlist policy:
- If domain matches allowed list, create user + membership with `default_role`.
- If user exists, add membership if missing.

Disabled:
- Reject if no membership exists or no identity found.

### 7) MFA Behavior (Professional Default)

- If user has verified MFA methods, issue a challenge and return `202` (same as password login).
- Future option: `sso_mfa_policy` (`require_local` default, `trust_idp` optional).

### 8) Security + Observability

- PKCE (S256) required.
- Single-use state/nonce stored in Redis (TTL configurable).
- Strict ID token validation (issuer, audience, exp, nonce).
- Log events: `auth.sso.start`, `auth.sso.callback`, `auth.sso.linked`, `auth.sso.provisioned`, `auth.sso.failure`.
- Rate limit start/callback endpoints with existing rate limiter.

### 9) Error Handling (Explicit, Predictable)

- `400` invalid request (missing tenant, malformed code/state)
- `401` invalid or unverifiable ID token
- `403` policy violation (SSO disabled, invite-only without invite, email not verified)
- `409` tenant selection required or identity conflict
- `503` provider discovery/token exchange failure

### 10) Backend Implementation Steps (Ordered)

1) Add `app/core/settings/sso.py` and wire into `Settings`.
2) Add domain contracts in `app/domain/sso.py`.
3) Add ORM models + Alembic migration (provider configs + identities).
4) Implement repositories and persistence adapters.
5) Implement OIDC client + SSO state store (Redis).
6) Implement SsoService (start + callback orchestration).
7) Integrate with AuthService/UserSessionService for token issuance + MFA.
8) Add API routes + Pydantic schemas.
9) Add contract + unit tests (SSO flows + policy edges).
10) Wire services into `app/bootstrap/container.py`.

---

<!-- SECTION: Smoke Philosophy (optional) -->
## Smoke Philosophy (Optional)

- SSO smoke tests are gated behind explicit env flags and use deterministic local IdP fixtures.
- Default CI remains deterministic and does not require external IdP connectivity.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A - Domain + Persistence

| ID | Area | Description | Status |
|----|------|-------------|--------|
| A1 | Domain | Add provider config + identity link contracts | ✅ |
| A2 | DB | ORM models and repositories for configs + links | ✅ |
| A3 | DB | Alembic migration (tables + indexes + constraints) | ✅ |

### Workstream B - Backend Services + API

| ID | Area | Description | Status |
|----|------|-------------|--------|
| B1 | OIDC | Provider client with discovery, JWKS validation, token exchange | ✅ |
| B2 | SSO | PKCE/state store + start/callback service | ✅ |
| B3 | Auth | Token issuance + MFA challenge integration for SSO logins | ✅ |
| B4 | API | Routes + schemas for SSO start/callback + provider listing | ✅ |
| B5 | Observability | Structured events for SSO success/failure/provision/link | ✅ |
| B6 | OIDC | Enforce allowed ID token algorithms (discovery-aware) + validate token endpoint auth method | ✅ |
| B7 | SSO | Honor provider `pkce_required` in authorize and token exchange flows | ✅ |
| B8 | SSO | Treat malformed/invalid Redis state payloads as invalid state (no 500s) | ✅ |

### Workstream C - Console Integration

| ID | Area | Description | Status |
|----|------|-------------|--------|
| C1 | Wizard | Add optional SSO prompts in Providers section (enable toggle + Google config + policy) | ✅ |
| C2 | Seed | Backend seed script to upsert `sso_provider_configs` (JSON output for CLI) | ✅ |
| C3 | Console | `starter-console sso setup` command + wizard automation hook (post-migrations) | ✅ |
| C4 | Status | Add non-fatal SSO status probe/validation (DB-backed) for console hub | ✅ |
| C5 | Docs | Merge console tracker summary into this milestone | ✅ |
| C6 | Wizard | Allow tenant-scoped SSO config by slug or UUID (not slug-only) | ✅ |

#### Console Tracker Summary (merged)

- Status: In Progress
- Owner: Platform Foundations
- Scope: Wizard prompts, CLI provisioning, automation hooks, and console hub SSO status probe
- Progress:
  - ✅ Wizard prompts under Providers section
  - ✅ `starter-console sso setup` command + backend seed script
  - ✅ Wizard automation hook (post-migrations)
  - ✅ SSO status probe/validation in the console hub

### Workstream D - Frontend Integration

#### Frontend Integration Plan (Approved)

- **Tenant selection required:** SSO provider listing + start requires explicit tenant selector (slug or UUID). UI keeps SSO options hidden/disabled until a tenant value is supplied. A shared helper will resolve slug vs UUID to avoid sending both.
- **Login hint:** When the email field is a valid email, send `login_hint` in SSO start requests; otherwise omit.
- **Redirect continuity:** Preserve `redirectTo` through the IdP round-trip using a short-lived HttpOnly cookie set by the SSO start BFF route. Validate that redirects are relative-path only; clear the cookie after success. Callback falls back to validated query param, then `/dashboard`.
- **UI/UX:** Add a dedicated “Continue with” SSO section below the password form. Only render provider buttons when `/auth/sso/providers` returns enabled providers. Provide loading + error states.
- **Callback page:** Create a dedicated callback page that exchanges `code` + `state` via the BFF callback route, persists cookies, handles MFA challenge via the existing dialog, and redirects on success. On failure, show a clear error with a link back to sign-in.

| ID | Area | Description | Status |
|----|------|-------------|--------|
| D1 | API routes | Next API routes to call SSO start/callback | ✅ |
| D2 | UI | Login page shows "Continue with Google" only when `/auth/sso/providers` returns it | ✅ |
| D3 | Callback | Auth callback page sets session cookies + redirects | ✅ |

### Workstream E - Tests + Docs

| ID | Area | Description | Status |
|----|------|-------------|--------|
| E1 | Unit | PKCE/state store, token validation, identity linking | ✅ |
| E2 | Contract | New SSO endpoints under `tests/contract` | ✅ |
| E3 | Smoke | Optional SSO smoke gated by env + local IdP | ✅ |
| E4 | Docs | Update idp.md + API docs + runbooks | ✅ |
| E5 | OpenAPI | Export fixtures + regenerate web SDK | ✅ |
| E6 | Unit | Add SSO policy/identity edge coverage (invite-only new user, domain reject, identity conflict) | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 - Alignment | Finalize schema + flow + console seeding plan | Design reviewed and agreed | ✅ |
| P1 - Backend | Domain, persistence, services, API | SSO endpoints functional in local dev | ✅ |
| P2 - Console + Frontend | Wizard, seed flow, login + callback UI | Local end-to-end SSO happy path | ✅ |
| P3 - Tests + Docs | Unit/contract/smoke + docs | All checks green, docs updated | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Redis (for SSO state/PKCE storage)
- Postgres (SSO provider config + identity link tables)
- Existing auth services + token signer/verifier
- Google OIDC application configuration (client id/secret + redirect URI)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Incorrect ID token validation | High | Verify issuer, audience, nonce, exp, and JWKS signature; strict error handling |
| Account takeover via email mismatch | High | Require `email_verified=true` and enforce domain allowlist + identity linking rules |
| Multi-tenant ambiguity | Med | Require tenant_id when multiple configs exist; return clear error |
| SSO bypasses MFA | Med | Reuse MFA challenge flow when methods are enrolled |
| Config drift between console and DB | Med | Seed script + console automation; surface config in tenant settings endpoints |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `hatch run lint`, `hatch run typecheck`, and targeted pytest suites
- Frontend: `pnpm lint` and `pnpm type-check`
- Console: `cd packages/starter_console && hatch run lint` and `... typecheck`
- Contract tests for SSO endpoints
- Optional smoke tests gated by env flags for local IdP

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Enable SSO by creating a provider config (tenant-scoped or global fallback).
- Console wizard can capture Google OAuth credentials and seed the DB via a backend script.
- Redirect URI is derived from `APP_PUBLIC_URL` + `/auth/sso/{provider}/callback`.
- Rollback: disable provider config or remove row; password login remains intact.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-01 - Milestone created.
- 2026-01-01 - Phase 1A complete: SSO settings + domain contracts + ORM models + migration.
- 2026-01-01 - Phase 1B complete: repositories + SSO state store + OIDC client core.
- 2026-01-01 - Phase 1C complete: SSO service orchestration + provisioning policy handling.
- 2026-01-01 - Phase 1D complete: API routes + request/response schemas for SSO.
- 2026-01-01 - Phase 1E (partial): unit + contract tests for SSO service and endpoints.
- 2026-01-01 - B5 complete: failure/error observability with reason codes for SSO flow.
- 2026-01-01 - E3 complete: gated HTTP smoke test for SSO provider list/start.
- 2026-01-01 - Workstream C1-C3 complete: console wizard prompts, seed script, automation, and CLI setup command.
