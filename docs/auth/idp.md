# Human Identity Provider Requirements

**Status:** Active requirements (security review required)  
**Last Updated:** 2025-11-07  
**Owners:** Platform Security Guild · Backend Auth Pod

---

## 1. Purpose & Alignment
- Replace the `/api/v1/auth/token` demo credentials with a production-grade human login path backed by a persistent identity provider (IdP) while preserving the ability to switch to an external IdP without changing caller contracts.
- Provide canonical requirements for IDP-002 through IDP-006 so backend, frontend, and ops teams deliver against the same contract.
- Extend the existing EdDSA token stack (AUTH-002/003) to cover human principals without reworking downstream APIs.

## 2. User Lifecycle & Tenant Model
| State | Description | Allowed Actions | Transition Triggers |
| --- | --- | --- | --- |
| `pending` | User invited but not yet activated (password reset or IdP confirmation outstanding). | View invite metadata, complete activation, cancel invite. | Activation link completion, admin cancel, invite expiry. |
| `active` | Fully provisioned user mapped to one or more tenant memberships. | Login, refresh, call APIs within granted roles/scopes. | Lockout threshold hit, admin disable, tenant removal. |
| `disabled` | Admin-suspended user; credentials retained for audit but login blocked. | None except audit & reinstatement by privileged admin. | Manual enable, automated re-enable SOP (optional, logged). |
| `locked` | Temporary lock due to rate-limit breach or security trigger. | No login; refresh tokens invalidated; unlock after TTL or admin override. | TTL expiry, unlock workflow, SOC escalation. |

Tenant relationships (canonical definitions in `docs/auth/roles.md`):
- A user may belong to multiple tenants; each membership carries a single TenantRole (`owner`, `admin`, `member`, `viewer`).
- Platform-level access is modeled separately via `platform_role` on the user record and is not part of tenant roles.
- Tokens carry a single `tenant_id` claim; multi-tenant users choose the tenant context during login. Scoped tenant switching endpoints are not exposed in this release.
- Removing the last tenant membership implicitly disables the account until a new tenant is assigned.

## 3. Credential Policy (Passwords + Secrets)
- **Hashing:** bcrypt `$2b$` with cost `work_factor >= 13`, salted per bcrypt spec plus a global pepper `AUTH_PASSWORD_PEPPER` loaded from secret storage. Pepper rotation requires rehash on next successful login.
- **Entropy requirements:** minimum 14 characters, must include characters from ≥2 classes (upper/lower/numeric/symbol). Password blacklist enforced via zxcvbn-derived scoring ≥ 3.
- **Storage:** `users.password_hash` stores bcrypt output only; pepper never persisted. Password history table retains the last 5 hashes to prevent reuse.
- **Reset flow:** activation + reset tokens are single-use, 15-minute TTL, signed via EdDSA (same signer, distinct `token_use=reset`). Tokens stored hashed in Postgres to allow revocation.
- **Operational APIs:** `/api/v1/auth/password/change` (self-service, requires a valid access token) and `/api/v1/auth/password/reset` (owner/support scope, per-tenant) now front the reset flow so UI + support tooling can orchestrate policy-compliant changes without touching storage internals.

## 4. Login Attempt Limits & Lockouts
- **Per-User Counter:** Redis key `auth:lockout:user:{user_id}` increments on failed login; 1-hour TTL sliding window.
- **Thresholds:** 5 consecutive failures ⇒ user enters `locked` state; refresh tokens revoked; account unlocks automatically after TTL or via admin API. Admin notifications rely on logs/alerts rather than webhook automation.
- **Global IP Guardrail:** `auth:lockout:ip:{/24}` counters throttle credential stuffing; 50 failures per minute triggers a configurable block (see `AUTH_IP_LOCKOUT_WINDOW_MINUTES` + `AUTH_IP_LOCKOUT_DURATION_MINUTES`) and structured alert.
- **Observation:** Lockout events emit `auth.lockout` log with `tenant_id`, `ip_hash`, `user_id`, and `reason` for SOC review.

## 5. Auditing & Telemetry
- **Structured Logs:**
  - `auth.login` (success/failure) with `user_id`, `tenant_id`, result, `kid`, source IP hash, user agent fingerprint.
  - `auth.refresh`, `auth.logout`, `auth.unlock`, `auth.policy` (admin actions).
- **Retention:** 1 year online in Loki + cold storage per compliance; at least 90 days queryable.
- **Metrics exposed at `/metrics`:**
  - Counters: `auth_login_attempts_total{result=}`, `auth_lockouts_total{reason=}`, `auth_refresh_issued_total`, `auth_password_resets_total`.
  - Histograms: `auth_login_latency_seconds`, `auth_password_verify_seconds`.
- **Tracing:** Trace IDs propagate across login + downstream service calls via `x-trace-id` header; spans annotate result + tenant.
- **Auditable Events:** All admin state changes (disable/enable, tenant assignment, password reset initiation) recorded in `user_audit_log` with actor, timestamp, before/after diff.

## 6. Token & Claim Rules
### 6.1 Access Tokens
- **Algorithm:** EdDSA (Ed25519) only; `alg` header fixed to `EdDSA`, `kid` references active key.
- **Lifetime:** 15 minutes default; configurable per environment but capped at 30 minutes.
- **Claims:**
  - `iss`: `https://agents.internal.openai.com` (configurable `auth_issuer`).
  - `aud`: array including `agent-api` plus optional service audiences (billing, analytics) tied to requested scopes.
  - `sub`: `user:{uuid}` unique per human principal.
  - `tenant_id`: UUID referencing active tenant context.
  - `roles`: array of tenant roles for the active tenant; canonical values `owner`, `admin`, `member`, `viewer`.
  - `scopes`: array of granted scopes; subset of global taxonomy.
  - `jti`: UUIDv7 for replay detection; stored in Redis w/ TTL = token lifetime for telemetry only (no revocation required for access tokens).
  - `iat`/`nbf`: issued-at and not-before set to same epoch seconds, derived from signer clock.
  - `exp`: `iat + lifetime`.
  - `token_use`: literal `access` to disambiguate from service-account / reset tokens.
- **Validation:** Downstream services must enforce `aud`, `tenant_id`, and `scopes`; unauthorized scope usage returns 403.

### 6.2 Refresh Tokens
- **Format:** 256-bit random secret encoded as `base64url(<random bytes>::<jti>)` and treated as an opaque string that is immediately hashed at rest.
- **Storage:** `refresh_tokens` table stores bcrypt(+pepper) hash, `user_id`, `tenant_id`, `signing_kid`, `fingerprint_hash`, `expires_at`, `revoked_at`, `reason`.
- **Lifetime:** 30 days max; rotation required on every refresh (rotate-on-use). Old token invalidated immediately; reuse attempts trigger lockout event + device notification stub.
- **Claims embedded:** When minting, include `iss`, `sub`, `tenant_id`, `scopes`, `token_use=refresh`, `jti`, `iat`, `exp`. Not exposed to clients except as opaque string.
- **Revocation:** Admin logout, lockout, or password reset sets `revoked_at` and caches `jti` in Redis for TTL = remaining lifetime to short-circuit DB lookups.

## 7. OIDC SSO (Optional, Google First)
- **Flow:** OIDC Authorization Code with PKCE; state + nonce stored in Redis for `SSO_STATE_TTL_MINUTES` and treated as single-use.
- **Endpoints:** `/api/v1/auth/sso/{provider}/start`, `/api/v1/auth/sso/{provider}/callback`, `/api/v1/auth/sso/providers`.
- **Provider config:** Tenant-scoped rows in Postgres with a global fallback row (`tenant_id IS NULL`) when tenant config is absent.
- **Security hardening:** Allowed ID token algorithms are enforced (RS/PS/ES only). Token endpoint auth method is validated against discovery metadata. ID tokens require `exp` + `iat` and nonce validation.
- **Provisioning policy:** Default `invite_only`; `domain_allowlist` optional; `disabled` blocks auto-provisioning. Verified email required for provisioning and identity linking.
- **MFA:** If the user has enrolled methods, SSO returns an MFA challenge (HTTP 202), same as password login.
- **Secrets:** Client secrets are encrypted at rest using `SSO_CLIENT_SECRET_ENCRYPTION_KEY` (fallback: `AUTH_SESSION_ENCRYPTION_KEY` or `SECRET_KEY`).
- **Ops:** `starter-console sso setup` + setup wizard can seed the provider config; env keys are `SSO_GOOGLE_*` for the initial Google preset.
- **Frontend/BFF:** The web app uses Next API routes (`/api/v1/auth/sso/*`) to broker start/callback and to set session cookies. The user-facing callback page is `/auth/sso/{provider}/callback`.
- **Tenant selector required:** Frontend must send exactly one of `tenant_id` (UUID) or `tenant_slug`. Missing/both values return 400/409.
- **Login hint:** When the email input is valid, the frontend forwards it as `login_hint`.
- **Redirect continuity:** `redirectTo` is stored in a short-lived HttpOnly cookie during SSO start; callback validates it as a relative path and redirects on success.
- **Runbook:** See `docs/ops/sso-oidc-runbook.md` for provisioning, validation, and rotation guidance.

## 8. External IdP Compatibility
- **Protocols:** Must support OIDC Authorization Code flow with PKCE and SCIM 2.0 provisioning. Local implementation mirrors these contracts to allow proxying to Auth0/Okta without changing callers.
- **Attribute Mapping:** Standardize on `email`, `name`, `roles` claim (TenantRole values), `external_id`. Store mapping so `sub` continuity is preserved if/when we swap IdPs.
- **Just-In-Time Provisioning:** When operating against an external IdP, we can JIT create users on first login if tenant + role info present; otherwise require SCIM sync before login succeeds.
- **Session Federation:** Access/refresh tokens remain our own; external IdP handles primary auth but exchanges for our tokens via OIDC token endpoint. This doc ensures our token schema remains stable for that flow.
- **Secrets & Rotation:** External IdP client secrets live alongside current pepper/keys; document rotation procedures in your security runbook and keep the process audited.

## 9. Governance
- This document plus the updated threat model are required inputs to the security review.
- Backend + security leads must sign off before identity-provider changes are deployed.
- Any change to password policy, lockout thresholds, or token schema requires updating this doc and notifying the platform security review channel.
