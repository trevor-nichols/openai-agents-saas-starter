# EdDSA Authentication Threat Model (Draft)

**Status:** In Review (covers AUTH-001 human login scope)  
**Last Updated:** 2025-11-07  
**Owners:** Platform Security Guild · Backend Auth Pod

---

## 1. Purpose & Scope

- Replace the demo HS256 authentication implementation with an enterprise-grade Ed25519 JWT stack.  
- Define trust boundaries, consumers, and required security controls before implementation work (AUTH-002 → AUTH-006).  
- Capture human login threat considerations outlined in `docs/auth/idp.md` while still excluding long-term external IdP procurement and broader secret-storage infrastructure.

## 2. System Context

### 2.1 Current Token Producers
- `anything-agents/app/api/v1/auth/router.py` issues access tokens from `/auth/token` and `/auth/refresh` using `create_access_token`; both rely on static HS256 secrets today and will migrate to AuthService once EdDSA lands.  
- `anything-agents/app/core/security.py` holds token creation logic (`create_access_token`) and shared secret configuration via `get_settings()`.  
- No additional services mint tokens; CLI utilities or background jobs are not yet present.

### 2.2 Current Token Consumers
- `anything-agents/app/core/security.py:get_current_user` verifies incoming bearer tokens and extracts claims for request-scoped context.  
- `anything-agents/app/api/dependencies/auth.py:require_current_user` exposes `get_current_user` as a FastAPI dependency for routers.  
- `anything-agents/app/api/v1/auth/router.py` uses `require_current_user` to protect `/auth/refresh` and `/auth/me`.  
- `anything-agents/app/api/dependencies/tenant.py` imports `require_current_user` to attach tenant context, preparing multi-tenant routing once auth hardening is complete.

### 2.3 Near-Term & External Consumers (Planned)
- FastAPI routers under `anything-agents/app/api/v1/` (agents, chat, billing, conversations) are expected to depend on `require_current_user` after AUTH-003, enforcing per-tenant authorization.  
- The Next.js frontend (`agent-next-15-frontend`) will consume the access token for API calls and fetch JWKS (`/.well-known/jwks.json`) for client-side introspection as needed.  
- Internal services (analytics, billing pipelines) will verify tokens against the published JWKS; requirements captured in `docs/architecture/authentication-ed25519.md`.  
- Operational tooling (rotation CLI, observability jobs) will call into the forthcoming KeySet and revocation stores to manage key lifecycle.

## 3. Assets & Trust Boundaries

### 3.1 Critical Assets

- **Ed25519 Private Keys (Active & Next):** Signing material used by the Token Service. Stored in a sealed volume or secret manager mount read-only to the FastAPI runtime. Loss compromises every downstream verifier.  
- **JWKS Payloads:** Public key representations served to clients and internal services. Integrity must be guaranteed; tampering enables downgrade or impersonation.  
- **Access Tokens:** Short-lived JWTs carrying principal identity, tenant scope, and authorization data. Typically cached in frontend memory or API gateway headers. Exposure allows replay within TTL.  
- **Refresh Tokens:** Long-lived credentials persisted by AuthService with `jti`, tenant, device fingerprint. Stored hashed-at-rest in Postgres with Redis cache for quick revoke checks.  
- **Revocation Registry:** Redis primary cache plus Postgres fallback mapping `jti` to revocation state. Unavailability or corruption undermines refresh rotation guarantees.  
- **Audit & Metrics Streams:** Structured logs, Prometheus counters, trace IDs that document sign/verify decisions. Required for incident response and repudiation protection.  
- **Configuration & Feature Flags:** `auth_issuer`, `auth_audience`, rotation overlap, dual-signing toggles (via `app/core/config.py`). Incorrect values break verification or weaken protections.

### 3.2 Supporting Components

- **FastAPI Application Tier:** Hosts issuance endpoints (`/api/v1/auth/token`, `/auth/refresh`), JWKS responder (`/.well-known/jwks.json`), and verification dependencies (`require_current_user`, tenant context). Runs inside the application VPC with access to secret mounts, Redis, and Postgres.  
- **Next.js Frontend:** Receives access/refresh tokens, stores access token in memory (or secure cookie once hardened), and invokes backend APIs. Will trigger JWKS refresh through shared client utilities.  
- **Internal Services & Jobs:** Billing, analytics, and streaming workers that will validate JWTs using JWKS and call revocation APIs for break-glass operations.  
- **Secret Manager / Sealed Volume:** Authoritative store for private key material; rotation CLI writes here, runtime reads read-only.  
- **Postgres (Primary DB):** Persists refresh tokens, revocation history, and audit trails requiring durability.  
- **Redis (Cache Layer):** Low-latency revocation lookups and rotation coordination. Treated as non-authoritative but security-sensitive.  
- **CI/CD & Ops Tooling:** Handles key rotation scripts, deployment automation, and environment configuration; requires strict access controls.

### 3.3 Trust Boundaries

- **B1 – Public Client Boundary:** Browser, mobile, and third-party service requests into the API. Inputs are untrusted; rate limiting and token verification occur upon crossing.  
- **B2 – Application Runtime Boundary:** FastAPI service with access to key material, Redis, and Postgres. Attackers gaining execution here can mint tokens; hardening focuses on least privilege and secret isolation.  
- **B3 – Persistence Boundary:** Secrets and revocation state stored in managed services (secret manager, Redis, Postgres). Requires encrypted transport, scoped credentials, and tamper detection.  
- **B4 – Observability & Operations Boundary:** Logging/metrics pipelines, rotation CLIs, and dashboards. Needs authentication and integrity to avoid repudiation or alert fatigue.  
- **B5 – Deployment & Supply Chain Boundary:** Build pipeline, container registry, and dependency management. Malicious artifacts could bypass runtime controls.

### 3.4 Assumptions

- Upstream identity provider (or local credential store) delivers vetted principal data to AuthService per `docs/auth/idp.md`; credential verification UX remains out of scope here.  
- Deployment environments provide TLS termination, WAF, and baseline network segmentation.  
- Secret manager exposes a read-only mount per region and supports atomic key swap operations.  
- Redis and Postgres connections are secured with mutual TLS or equivalent and enforce namespace isolation between tenants/environments.  
- Frontend will not store refresh tokens in browser storage; they remain `httpOnly` cookies or withheld entirely until full flow is defined.

## 4. Threat Scenarios & Mitigations

| STRIDE | Threat Scenario | Target Assets | Consequence | Mitigations (Planned / Required) |
| --- | --- | --- | --- | --- |
| **Spoofing** | Attacker forges JWTs using stolen/semi-trusted key | Ed25519 private keys, access tokens | Full impersonation of any user/tenant | Keys stored in sealed volume; audited rotation CLI generates Ed25519 keypairs and writes directly to secret manager; strict `alg=EdDSA` verification; optional dual-signing only within defined overlap; ops audit of key access logs. |
| **Spoofing** | Replay of intercepted access/refresh tokens | Access/refresh tokens, revocation registry | Session hijack until expiry | Short access TTL (≤15 min); `jti` per token; refresh token rotation with immediate revocation of prior `jti`; device fingerprint binding and anomaly alerts; Vault CLI payloads carry nonce with 5-minute TTL enforced via Redis-backed nonce store (in-memory fallback for dev) to block replay of issuance requests. |
| **Tampering** | Man-in-the-middle swaps `alg` header to HS256 or injects alternate `kid` | JWKS, verification pipeline | Bypass signature validation | Verifier enforces allowed algorithms list (`["EdDSA"]`); reject tokens missing recognized `kid`; JWKS served with ETag + integrity check; config forbids legacy fallback in prod. |
| **Tampering** | Unauthorized modification of revocation cache/store | Revocation registry | Revoked tokens regain validity | Redis access scoped via ACLs; Postgres revocation table write-ahead logs monitored; AuthService compares cache result with signed digest recorded in audit log; periodic reconciliation job. |
| **Repudiation** | User denies activity due to missing audit trail | Audit logs, metrics | Incident response blocked; compliance gaps | Structured JSON logs with trace IDs, `kid`, `jti`, client metadata; logs shipped immutably to central SIEM; access to modify logs restricted; retention meets compliance. |
| **Information Disclosure** | JWKS endpoint leaks inactive/retired keys with metadata revealing rotation cadence | JWKS payloads | Predictable rotation timing aiding attackers | Publish only active & next `kid`; omit private metadata; apply cache-control with short max-age; monitor access via rate-limits and logging. |
| **Information Disclosure** | Secret manager misconfiguration exposes private keys to other services | Ed25519 private keys | Compromise of signing authority | Enforce IAM policies restricting mount to auth service; secrets encrypted at rest; rotation audit; regular access review. |
| **Information Disclosure** | Application logs/metrics capture bearer tokens or key material | Access tokens, refresh tokens, Ed25519 keys | Credential leakage enabling replay or offline attacks | Logging middleware scrubs `Authorization` headers and token payloads; observability schema restricts sensitive fields; CI secret-scanning and linting enforce instrumentation hygiene; privacy reviews before shipping telemetry changes. |
| **Denial of Service** | Redis outage prevents revocation checks | Revocation registry | Refresh token rotation fails open/closed | Implement circuit breaker: fallback to Postgres with timeout; if both unavailable, fail safe (deny refresh) and alert; autoscaling and health probes for cache. |
| **Denial of Service** | Flood of JWKS requests or token validation attempts | JWKS endpoint, token service | Resource exhaustion, legitimate requests dropped | Rate limiting at edge (≤5 req/sec/IP for JWKS); CDN caching; async verification with bounded worker pool; metrics-based autoscaling triggers. |
| **Elevation of Privilege** | Tenant header manipulation to escalate privileges | Tenant context, claims | Cross-tenant data exposure | Tenant ID derived from token claim, not headers, once EdDSA flow lands; until then, enforce server-side validation and anomaly alerts; introduce policy checks in AuthService and routers. |
| **Elevation of Privilege** | Compromised pipeline deploys backdoored auth service | Build pipeline, container registry | Silent token minting/backdoor | Signed container images; dependency scanning; CI attestation; runtime admission policy verifying signatures before deploy. |
| **Spoofing** | Credential stuffing against human login endpoint | User credentials, tenant memberships | Unauthorized access to user accounts | Password policy + bcrypt w/ pepper (per `docs/auth/idp.md`), Redis-backed per-user + per-IP rate limits, automatic lockout after 5 failures/hour, SOC alerts on threshold breach, CAPTCHA/mfa hooks flagged for IDP-005. |
| **Spoofing** | Password reuse with leaked credentials from other services | User credentials | Compromised accounts despite unique tenant | Password history + zxcvbn scoring, haveibeenpwned-style breach-check on reset, forced reset + notification, optional external IdP enforcement via SCIM attributes. |
| **Denial of Service** | Lockout abuse (attacker repeatedly guesses password to freeze account) | User availability, tenant productivity | Legitimate users blocked, support load | Distinguish soft vs hard lockouts, notify user/admin on lock, provide rate-limited unlock API requiring verified email/MFA, SOC monitoring for repeated IP/Subnet abuse, allow break-glass admin override. |
| **Elevation of Privilege** | Tenant escalation by replaying refresh token from different tenant context | Refresh tokens, tenant claims | Cross-tenant data access after login | Bind refresh tokens to `tenant_id` + device fingerprint; rotation-on-use with mismatch detection; lock account + alert when mismatch occurs; require explicit tenant selection for multi-tenant users. |
| **Repudiation** | Audit bypass via log tampering or missing events for human login | Audit logs, compliance evidence | Unable to prove or disprove malicious login | Structured logging mandates for `auth.login`, `auth.lockout`, `auth.unlock`, `auth.policy`; logs shipped to immutable SIEM with retention ≥1 year; daily integrity checks; audit events cross-linked with metrics (`auth_login_attempts_total`). |

## 5. Security Requirements & Controls

### 5.1 Key Management
- R1. Generate Ed25519 key pairs via audited CLI that writes directly to secret manager; prohibit manual key creation.  
- R2. Maintain `KeySet` with `active`, `next`, `retired` states; enforce rotation cadence ≤30 days with overlap ≤24 hours.  
- R3. Restrict filesystem/secret manager mounts to read-only within the FastAPI container; monitor access via IAM logs and trigger alerts on anomalous reads.

### 5.2 Token Issuance
- R4. Centralize issuance within `AuthService`; prohibit direct calls to signer outside service layer.  
- R5. Include mandatory claims per architecture blueprint (`iss`, `aud`, `sub`, `tenant_id`, `scope`, `token_use`, `jti`, `iat`, `nbf`, `exp`); reject issuance missing required attributes.  
- R6. Sign access and refresh tokens with Ed25519 using the active `kid`; enable dual-signing only when `auth_dual_signing_enabled` flag is true and the `auth_dual_signing_overlap_minutes` guardrail is satisfied. `TokenSigner`/`TokenVerifier` (in `app/core/security.py`) enforce `alg=EdDSA`, header `kid` presence, and reject unknown material.

### 5.3 Verification & Consumption
- R7. Verification pipeline (`TokenVerifier`) must enforce `alg=EdDSA` and validate `kid` against cached JWKS; tokens with unknown or retired `kid` fail closed.  
- R8. Enforce strict claim validation: issuer exact match, audience membership, `nbf`/`exp` skew tolerances, tenant scoping, and `token_use` gating for refresh endpoints.  
- R9. Tenant context dependencies must derive tenant identity from token claims rather than headers once the new flow ships; headers become hints only.

### 5.4 Refresh & Revocation
- R10. Persist refresh tokens hashed with salted one-way function; store metadata (`jti`, tenant, device hash, expiry) in Postgres and cache in Redis.  
  - Implemented via `ServiceAccountToken.refresh_token_hash` (bcrypt + per-token salt + `AUTH_REFRESH_TOKEN_PEPPER`) and `signing_kid` (migration `20251106_235500`) so deterministic rehydration can re-sign with the original Ed25519 key; plaintext rows truncated during migration `20251106_230500`.  
- R11. Rotate refresh tokens on every use; previous `jti` marked revoked atomically.  
- R12. Implement reconciliation job comparing Redis cache with Postgres authoritative store; alert on drift or stale entries beyond TTL.  
- R13. Provide administrative API/CLI to revoke tokens by `jti`, `sub`, or tenant and propagate to cache immediately.

### 5.5 JWKS Distribution
- R14. Serve JWKS at `/.well-known/jwks.json` with cache headers (`max-age` ≤300s) and strong ETag; responses signed or hashed to detect tampering if served via CDN.  
- R15. Monitor JWKS access patterns; edge rate limiting (5 req/sec/IP) and WAF rules mitigate scraping or DoS attempts.  
- R16. Document key rollover expectations for internal services; publish versioned JWKS URI for staging vs production.

### 5.6 Observability & Governance
- R17. Emit structured logs (`event`, `result`, `kid`, `jti`, `issuer`, `tenant_id`, `client_id`, timing) for sign/verify operations; ship to centralized SIEM with immutable retention ≥90 days.  
- R18. Provide Prometheus metrics (`jwt_verifications_total`, `jwt_failures_total`, `jwt_revocations_total`, `active_key_age_seconds`, `revocation_cache_latency_ms`) plus JWKS-specific counters (`jwks_requests_total`, `jwks_not_modified_total`); alert thresholds defined per Ops runbook.  
- R19. Integrate trace propagation so token lifecycle can be followed end-to-end across services.  
- R20. Establish incident response playbook covering key compromise, replay attacks, and revocation failures with RTO/RPO targets.

### 5.7 Operational Controls
- R21. Require signed container images and supply-chain attestations before deployment; enforce runtime admission policies.  
- R22. Limit rotation CLI access to a break-glass group with MFA and session recording.  
- R23. Run quarterly rotation/fire-drill exercises validating the ability to revoke and rotate keys within SLA.  
- R24. Include auth pipeline in continuous vulnerability scanning (dependencies and base images) and apply patches within defined timelines.

## 6. Open Questions & Next Actions

### 6.1 Resolved Decisions
- **Multi-region signer policy:** Primary region runs the active signer; secondary regions load the `next` key in standby and promote only via documented failover SOP (`docs/architecture/authentication-ed25519.md`, §9).
- **Device fingerprint binding:** Refresh tokens persist a hashed device fingerprint; mismatches trigger rejection unless a future trusted-device flow overrides (same doc, §9).
- **JWKS access posture:** Endpoint remains publicly readable with edge rate limiting and audit logging; mTLS intentionally deferred per current blueprint (§9).
- **Revocation cache strategy:** Redis is the primary revocation cache with TTL aligned to refresh token lifetime and Postgres authoritative fallback (`docs/architecture/authentication-ed25519.md`, §9).
- **Scope taxonomy:** Scopes standardized to `billing:read`, `billing:manage`, `conversations:read`, `conversations:write`, `conversations:delete`, `tools:read`, `support:*`; read-only surfaces require the relevant `*:read` scope, mutations require `*:write`/`billing:manage`/`conversations:delete`.
- **Service-account issuance:** Non-interactive consumers receive tenant-scoped refresh tokens through AuthService using Vault-managed service-account credentials and a CLI/CI helper; no STS exchange in v1.
- **Frontend refresh tokens:** SPA stores access tokens in memory; refresh tokens are delivered solely via secure, HTTP-only, SameSite=Strict cookies with no client-side JWKS introspection in the initial rollout.

### 6.2 Outstanding Actions
- Finalize `auth_audience` default configuration reflecting approved identifiers (`agent-api`, `analytics-service`, `billing-worker`, `support-console`, `synthetic-monitor`).
- Define AuthService CLI/CI helper specification and workflow for service-account token issuance ahead of AUTH-002 delivery.
- Implement scope enforcement hooks in routers during AUTH-003, aligning with the standardized taxonomy.

> **Next Step:** Circulate this document, collect stakeholder sign-off, and baseline controls before committing to implementation tasks.
