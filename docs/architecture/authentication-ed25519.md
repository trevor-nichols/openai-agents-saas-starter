# Authentication Architecture Plan — Ed25519 Rollout

**Last Updated:** 2025-11-06  
**Owner:** Platform Security Guild  
**Status:** Draft (awaiting AUTH-001 threat-model review)

## 1. Goals & Non-Goals

### Goals
- Replace demo authentication with a production-grade JWT system signed with Ed25519 (EdDSA).
- Retain clean architecture boundaries (presentation → application → domain → infrastructure) while isolating crypto concerns.
- Enable Ed25519 signing with a simple key-management story (single active key, easy replacement) and public verification without third-party authorization services.
- Provide predictable, auditable behaviour with first-class observability and testing.

### Non-Goals
- Implementing a user identity provider or UI flows (assume upstream IdP or local user store already exists/arrives later).
- Adding OAuth/OIDC flows beyond JWT issuance and verification.
- Building secret-storage infrastructure; we integrate with an existing sealed volume or secret manager abstraction.

## 2. Current Context

- `api-service/app/core/security.py` currently issues HS256 tokens with static `secret_key` and bcrypt password helpers.
- No dedicated key lifecycle, no JWKS publication, and no revocation/rotation support.
- Tests live under `api-service/tests` with mixed unit/integration coverage, minimal fixtures for auth.
- Milestone tracker `MILESTONE_AUTH_EDDSA_TRACKER.md` defines high-level work items AUTH-001…AUTH-006 that this document elaborates.

## 3. Architectural Overview

```
┌─────────────────────────────────────────────┐
│ Presentation Layer (FastAPI Routers)        │
│ ├─ app/api/v1/auth/router.py                │
│ └─ app/presentation/health.py               │
├─────────────────────────────────────────────┤
│ Application Services                        │
│ ├─ AuthService (new)                        │
│ ├─ ConversationService                      │
│ └─ BillingService                           │
├─────────────────────────────────────────────┤
│ Domain Layer                                │
│ ├─ TokenClaims (value object)               │
│ ├─ KeySet (aggregate)                       │
│ └─ Repositories / Policies                  │
├─────────────────────────────────────────────┤
│ Infrastructure Layer                        │
│ ├─ EdDSASigner / EdDSAVerifier (cryptography)│
│ ├─ KeyStorageAdapter (filesystem/secret mgr)│
│ ├─ RevocationStore (Postgres)               │
│ └─ JWKSResponder                            │
└─────────────────────────────────────────────┘
```

### Key Components

- **AuthService (new)**: Lives under `app/services/auth_service.py`. Coordinates token issuance, refresh, revocation, and introspection. Depends on domain abstractions, not concrete crypto.
- **Key Management Module (`app/core/keys.py`)**: Loads the single active Ed25519 key, materializes JWK payloads, and persists material to either the filesystem or the Vault KV-backed secret manager adapter (`app/infrastructure/security/vault_kv.py`).
- **Refresh Token Store (`app/infrastructure/persistence/auth/`)**: Postgres + Redis repository for refresh-token reuse and revocation. `ServiceAccountToken` rows capture tenant/account/scope tuples, while `RedisRefreshTokenCache` accelerates lookups for `force=False` reuse from `AuthService`.
- **Signer/Verifier Interfaces**: `app/core/security.py` exposes `TokenSigner`/`TokenVerifier` abstractions backed by Ed25519 key material from `KeySet`, enforcing `alg=EdDSA` while always using the lone active signing key.
- **Revocation Store**: Postgres-backed repository under `app/infrastructure/persistence/auth/postgres.py` to track refresh tokens and revoked `jti` values, leveraging existing async engine.
- **JWKS Endpoint**: Router `app/presentation/well_known.py` exposes `/.well-known/jwks.json`, pulling from `KeySet.materialize_jwks()` and serving the active key. Responses include `Cache-Control`, strong `ETag`, and `Last-Modified` headers so downstream verifiers can rely on conditional GETs (`If-None-Match`) to avoid unnecessary downloads.
- **Key CLI (`auth keys rotate`, `auth jwks print`)**: Lives alongside the service-account helper in `app/cli/auth_cli.py`; `keys rotate` generates a fresh Ed25519 keypair and immediately replaces the active key in the configured storage backend, while `jwks print` dumps the current JWKS payload for audits or runbooks without hitting the HTTP endpoint.
- **Observability Surface (`app/observability/*`, `/metrics`)**: Dedicated `metrics.py` registers Prometheus counters/histograms for signing, verification, JWKS, nonce cache, and service-account issuance, while `logging.py` centralizes structured JSON log emission. FastAPI exposes `GET /metrics` for scrapes and `auth.observability` logger streams to the SIEM.
- **Signup Telemetry**: `signup_attempts_total{result,policy}` and `signup_blocked_total{reason}` capture `/auth/register` and `/auth/request-access` outcomes so SecOps can alert on surges before approvals are touched.

## 4. Data & Configuration

### Claims Schema (draft)
- `iss` (string) — issuer, defaults to `settings.auth_issuer`.
- `aud` (array|string) — consumers; enforce per-client values.
- `sub` (uuid|string) — principal identifier.
- `tenant_id` (uuid) — multi-tenant context.
- `scope` (string) — space-delimited permissions.
- `token_use` (enum) — `access` | `refresh`.
- `jti` (uuid) — unique token id for revocation.
- `iat`, `exp`, `nbf` — standard temporal claims.

### Settings Additions (`app/core/config.py`)
- `auth_audience: list[str]` — defaults to `["agent-api", "analytics-service", "billing-worker", "support-console", "synthetic-monitor"]`; override with a JSON array via `AUTH_AUDIENCE` (comma-separated strings remain backward compatible) and keep ordering stable across services.
- `auth_key_storage_backend: str` — `file` (default) or `secret-manager`.
- `auth_key_storage_path: str` — filesystem location for keyset JSON when using the file backend.
- `auth_key_secret_name: str` — secret-manager entry name/path (e.g., `kv/data/auth/keyset`) for environments storing the keyset outside the filesystem. Used by the Vault KV adapter to read/write the serialized KeySet document.
- `auth_jwks_cache_seconds: int` — legacy cache-control knob retained for backwards compatibility.
- `auth_jwks_max_age_seconds: int` — preferred cache-control max-age for JWKS responses (defaults to 300 seconds; override via `AUTH_JWKS_MAX_AGE_SECONDS`).
- `auth_jwks_etag_salt: str` — salt mixed into JWKS ETag derivation so hashes remain unpredictable; configure via `AUTH_JWKS_ETAG_SALT`.
- `auth_refresh_token_pepper: str` — server-side secret concatenated with refresh tokens before hashing; must be unique per environment and rotated when compromise is suspected.
- `signup_rate_limit_per_hour` / `_per_ip_day` / `_per_email_day` / `_per_domain_day` — layered quotas enforced before touching the database. Defaults (20/hr, 100/day, 3/email-day, 20/domain-day) can be tuned via the CLI wizard.
- `signup_concurrent_requests_limit` — caps outstanding approval requests per IP (default 3) by counting pending rows before inserting another submission.
- Honeypot + UA fingerprinting — `/auth/request-access` accepts a hidden honeypot input and stores a SHA-256 hash of the user agent so operators can correlate noisy bots without keeping raw fingerprints.
- Additional knobs (`auth_issuer`, TTLs) will land with the AUTH-003 service refactor.

### Persistence Schema (AUTH-002/AUTH-003)
- `service_account_tokens` — captures issued refresh tokens for service-account tuples with columns `(account, tenant_id, scope_key, scopes JSON, refresh_token_hash, refresh_jti, signing_kid, fingerprint, issued_at, expires_at, revoked_at, revoked_reason)`. `refresh_token_hash` stores the bcrypt(+pepper) digest; `signing_kid` records which Ed25519 key produced the token so reuse logic can deterministically reconstruct the same JWS even after rotations. The partial unique index enforces a single active token per `(account, tenant_id, scope_key)` tuple, while Redis (`auth:refresh:*`) mirrors the latest active row (plaintext, TTL-scoped) for low-latency reuse.

## 5. Token Flow Sequences

1. **Login / Token Issue**
   - Router validates credentials → AuthService issues refresh + access tokens.
   - Tokens signed with active Ed25519 key. Response includes `kid` and expiry metadata.
   - Refresh token persisted with `jti`, `tenant_id`, hashed fingerprint, and expiry.

2. **Access Verification (API Call)**
   - HTTPBearer dependency extracts token → TokenVerifier checks signature (`alg=EdDSA`, `kid` lookup).
   - Claims validated (issuer, audience, expiry, revocation) → user context returned to route.

3. **Manual Key Replacement**
   - When needed, operators run `auth keys rotate` to generate a new Ed25519 keypair and replace the active key in storage (file or Vault).
   - JWKS payload updates automatically because `KeySet.materialize_jwks()` always reflects the single active key; consumers poll `/.well-known/jwks.json` according to the published `Cache-Control` headers and honor `ETag` to avoid stale caches.

4. **Revocation**
   - On refresh misuse or manual kill, revoke `jti` via repository + optional cache (Redis).
   - Verifier consults revocation store (with local cache) as part of validation pipeline.

## 6. Testing & Quality Strategy

- **Directory Layout** (restructure as part of AUTH-003 prerequisite):
  - `tests/unit/` — pure unit tests (e.g., TokenClaims validation, KeySet rotation logic).
  - `tests/integration/` — existing DB-backed suites (rename/migrate current integration suite here).
  - `tests/contract/` — FastAPI endpoint tests using TestClient with Redis/Postgres doubles (fakeredis + sqlite).
  - `tests/e2e/` (optional later) — docker-compose driven smoke tests.
- **Fixtures**: Create shared fixtures under `tests/conftest.py` for fake key storage, Redis-backed revocation store (fakeredis), and token factories.
- **Coverage**: Enable `pytest --cov=app --cov-report=xml` in CI; fail if coverage for `app/core/security.py`, `app/core/keys.py`, and `app/services/auth_service.py` < 90%.
- **Static Analysis**: Update Ruff profile to flag insecure JWT usage (`flake8-bandit` rule S320 equivalent) and ensure `algorithms` arg enforced.

## 7. Observability & Alerts

### Metrics Surface
- `jwks_requests_total`, `jwks_not_modified_total` — JWKS responder traffic counters.
- `jwt_signings_total{result,token_use}` / `jwt_signing_duration_seconds{result,token_use}` — emitted by `TokenSigner`.
- `jwt_verifications_total{result,token_use}` / `jwt_verification_duration_seconds{result,token_use}` — emitted by `TokenVerifier`.
- `service_account_issuance_total{account,result,reason,reused}` / `service_account_issuance_latency_seconds{account,result,reason,reused}` — emitted by `AuthService` (success, cached reuse, validation errors, rate limits, signer issues, catalog outages).
- `nonce_cache_hits_total`, `nonce_cache_misses_total` — emitted from Vault nonce enforcement to spot replay attempts.
- All series live inside `app/observability/metrics.py`, registered against a dedicated registry scraped via `GET /metrics` (new FastAPI route in `app/presentation/metrics.py`).

### Structured Logging
- Centralized helper `app/observability/logging.py` writes single-line JSON (`auth.observability` logger) with shared schema.
- Events include: `token_sign`, `token_verify`, `service_account_issuance`, `service_account_rate_limit`, `vault_signature_verify`, and `vault_nonce_cache`.
- Each event carries contextual fields (e.g., `{result, token_use, kid, duration_seconds, account, limit_type, reason}`) so SIEM queries/alerts can pivot without regexing free-form text.

### Alerting Targets
1. **JWT Verification Failure Rate**: `increase(jwt_verifications_total{result="failure"}[5m]) / increase(jwt_verifications_total[5m]) > 0.01` → PagerDuty (Sev2). Runbook: confirm JWKS freshness, inspect signer health, roll keyset back if necessary.
2. **Service-Account Issuance Latency**: `histogram_quantile(0.95, rate(service_account_issuance_latency_seconds_bucket{result="success"}[5m])) > 2` seconds → #auth-runtime Slack. Runbook covers Redis/Vault latency checks plus signer saturation review.
3. **Nonce Replay Spike**: `rate(nonce_cache_hits_total[5m]) ≥ 5` → #security-ops Slack to investigate potential credential replay. Runbook pulls Vault audit logs + client metadata.

Dashboards should pin these metrics, annotate alert firings, and link back to this section plus the incident SOP so AUTH-005 assurances remain auditable.

### `/auth/register` Failure Modes
Public signup flows run through the transactional `SignupService`. Clients and operators should expect the following responses and react accordingly:

| HTTP Status | Condition | Notes |
|-------------|-----------|-------|
| **403 FORBIDDEN** | `SIGNUP_ACCESS_POLICY` is not `public`. | Server short-circuits before any DB work and surfaces `PublicSignupDisabledError` so deployments can go invite/approval-only without code changes. |
| **409 CONFLICT** | Email already exists or slug allocation exceeds retries. | Email collisions are detected inside the transaction (before inserts) and raise `EmailAlreadyRegisteredError`; slug collisions are extremely rare and map to `TenantSlugCollisionError`. No tenant rows are persisted in either case. |
| **429 TOO MANY REQUESTS** | IP exceeded `signup_rate_limit_per_hour`. | Enforced via the shared rate limiter; `Retry-After` communicates when the next attempt is allowed. |
| **502 BAD GATEWAY** | Billing gateway rejected the initial plan/trial. | Tenant + owner accounts remain active; ops can retry plan creation or fall back to a free tier. The response includes `BillingProvisioningError` detail for observability. |

Any other exception bubbles up as a 500 and emits the `signup.*` structured log events for incident response. Keep this table synchronized with `app/api/v1/auth/router.py` and the settings described in Section 3.

## 8. Implementation Alignment with Milestones

| Milestone Item | Key Deliverables Here |
| -------------- | --------------------- |
| AUTH-001 | Sections 1–5 inform threat-model workshop; update after review. |
| AUTH-002 | Sections 3 & 4 define KeySet and storage interfaces. |
| AUTH-003 | Sections 3, 5, and 6 detail service refactor and required tests. |
| AUTH-004 | Section 3 (JWKS) + Section 7 (caching/logging). |
| AUTH-005 | Section 7 enumerates observability requirements. |
| AUTH-006 | Sections 5 (rotation) and 7 (runbooks) guide rollout. |

## 9. Open Questions
- **Multi-region replication**: Keys replicate across regions via existing secret manager; single active signer per region with documented failover to promote the standby region's "next" key.
- **Refresh token/device binding**: Refresh tokens store a device fingerprint hash; mismatched fingerprints trigger rejection unless a future trusted-device flow overrides.
- **JWKS access control**: JWKS remains publicly readable with edge rate limiting (5 req/sec/IP) and audit logging rather than mTLS.
- **Revocation cache backend**: Redis serves as primary revocation cache with TTL equal to refresh token lifetime; Postgres fallback if Redis unavailable.
- **Test suite layout**: Restructure tests into `tests/unit`, `tests/contract`, and `tests/integration` prior to auth implementation; enforce coverage gates in CI accordingly.
- **Scope taxonomy**: Version 1 scopes standardized to `billing:read`, `billing:manage`, `conversations:read`, `conversations:write`, `conversations:delete`, `tools:read`, `support:*`; read-only endpoints gate on `* :read` scopes, mutations on `* :write`/`billing:manage` and `conversations:delete`.
- **Service-account issuance**: Non-interactive consumers obtain tenant-scoped refresh tokens via AuthService using managed Vault credentials and a CLI/CI helper; no STS exchange required in v1.

> **Next Action:** Review in AUTH-001 workshop, assign owners to answer open questions, and update this blueprint before implementation sprints begin.

## 10. Service Wiring & Testing Guidelines

- **Application container:** Auth-adjacent services (user service, session service, service-account token service, password recovery, email verification, rate limiter, etc.) are registered on the global `ApplicationContainer` (`app/bootstrap/container.py`). Each module exposes a `get_*` helper that simply returns `get_container().<service>`; startup wiring in `main.py` is responsible for building the concrete instances via the helper builders in `app/services/**/builders.py`.
- **Explicit builders:** When adding a service, provide a `build_*` helper that accepts explicit dependencies (settings, repositories, Redis clients). Startup code should call the builder, store the result on the container, and routes should access it through the `get_*` proxy. This keeps wiring deterministic while preserving clean architecture boundaries.
- **Testing pattern:** `tests/conftest.py` calls `reset_container()` before every test. Fixtures should override dependencies by assigning to the container (e.g., `get_container().auth_service = FakeAuthService()`), rather than monkeypatching `app.services.*` globals. This mirrors production wiring and prevents hidden state from leaking between tests.
- **Failure modes:** Container accessors raise `RuntimeError` if a requested service hasn’t been configured. Ensure new services are wired in `main.py` (or in the relevant test fixture) before calling their proxies so failures occur during startup rather than mid-request.
