# Authentication Architecture Plan — Ed25519 Rollout

**Last Updated:** 2025-11-06  
**Owner:** Platform Security Guild  
**Status:** Draft (awaiting AUTH-001 threat-model review)

## 1. Goals & Non-Goals

### Goals
- Replace demo authentication with a production-grade JWT system signed with Ed25519 (EdDSA).
- Retain clean architecture boundaries (presentation → application → domain → infrastructure) while isolating crypto concerns.
- Enable deterministic key rotation and public verification without third-party authorization services.
- Provide predictable, auditable behaviour with first-class observability and testing.

### Non-Goals
- Implementing a user identity provider or UI flows (assume upstream IdP or local user store already exists/arrives later).
- Adding OAuth/OIDC flows beyond JWT issuance and verification.
- Building secret-storage infrastructure; we integrate with an existing sealed volume or secret manager abstraction.

## 2. Current Context

- `anything-agents/app/core/security.py` currently issues HS256 tokens with static `secret_key` and bcrypt password helpers.
- No dedicated key lifecycle, no JWKS publication, and no revocation/rotation support.
- Tests live under `anything-agents/tests` with mixed unit/integration coverage, minimal fixtures for auth.
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
- **Key Management Module (`app/core/keys.py`)**: Loads active and next Ed25519 keys, exposes rotation window semantics, materializes JWK payloads, and validates key age policies. Supports both filesystem persistence and the Vault KV-backed secret manager adapter (`app/infrastructure/security/vault_kv.py`) so production environments can store private material outside the container image.
- **Refresh Token Store (`app/infrastructure/persistence/auth/`)**: Postgres + Redis repository for refresh-token reuse and revocation. `ServiceAccountToken` rows capture tenant/account/scope tuples, while `RedisRefreshTokenCache` accelerates lookups for `force=False` reuse from `AuthService`.
- **Signer/Verifier Interfaces**: `app/core/security.py` now exposes `TokenSigner`/`TokenVerifier` abstractions backed by Ed25519 key material from `KeySet`, enforcing `alg=EdDSA` and wiring in optional dual signing based on `auth_dual_signing_enabled`.
- **Revocation Store**: Postgres-backed repository under `app/infrastructure/persistence/auth/postgres.py` to track refresh tokens and revoked `jti` values, leveraging existing async engine.
- **JWKS Endpoint**: Router `app/presentation/well_known.py` exposes `/.well-known/jwks.json`, pulling from `KeySet.to_jwks()` and attaching cache headers so downstream verifiers can poll on a fixed cadence.
- **Rotation CLI (`auth keys rotate`)**: Lives alongside the service-account helper in `app/cli/auth_cli.py`; generates Ed25519 keypairs, persists them via the configured storage backend, and prints the public JWK for distribution workflows.

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
- `auth_audience: list[str]` — defaults to `["agent-api", "analytics-service", "billing-worker", "support-console", "synthetic-monitor"]`; override with a JSON array via `AUTH_AUDIENCE` and keep ordering stable across services.
- `auth_key_storage_backend: str` — `file` (default) or `secret-manager`.
- `auth_key_storage_path: str` — filesystem location for keyset JSON when using the file backend.
- `auth_key_secret_name: str` — secret-manager entry name/path (e.g., `kv/data/auth/keyset`) for environments storing the keyset outside the filesystem. Used by the Vault KV adapter to read/write the serialized KeySet document.
- `auth_jwks_cache_seconds: int` — cache-control max-age for the JWKS endpoint responses.
- `auth_rotation_overlap_minutes: int` — guardrail ensuring `active` and `next` keys do not diverge beyond the approved overlap window.
- `auth_dual_signing_enabled: bool` — feature flag enabling dual signing with the active + next keys during staged rotations.
- `auth_dual_signing_overlap_minutes: int` — maximum window dual signing is allowed before raising, keeping overlap bounded.
- `auth_refresh_token_pepper: str` — server-side secret concatenated with refresh tokens before hashing; must be unique per environment and rotated when compromise is suspected.
- Additional knobs (`auth_issuer`, TTLs, dual signing flag) will land with the AUTH-003 service refactor.

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

3. **Rotation**
   - Ops pre-load next key material (same KeySet contract).
   - Dual-signing optional: TokenSigner signs with both old/new keys while verifiers trust both `kid`s.
   - Once overlap window expires, retire old key; JWKS updates automatically.

4. **Revocation**
   - On refresh misuse or manual kill, revoke `jti` via repository + optional cache (Redis).
   - Verifier consults revocation store (with local cache) as part of validation pipeline.

## 6. Testing & Quality Strategy

- **Directory Layout** (restructure as part of AUTH-003 prerequisite):
  - `tests/unit/` — pure unit tests (e.g., TokenClaims validation, KeySet rotation logic).
  - `tests/integration/` — existing DB-backed suites (rename/migrate current integration suite here).
  - `tests/contract/` — FastAPI endpoint tests using TestClient with in-memory dependencies.
  - `tests/e2e/` (optional later) — docker-compose driven smoke tests.
- **Fixtures**: Create shared fixtures under `tests/conftest.py` for fake key storage, in-memory revocation store, and token factories.
- **Coverage**: Enable `pytest --cov=app --cov-report=xml` in CI; fail if coverage for `app/core/security.py`, `app/core/keys.py`, and `app/services/auth_service.py` < 90%.
- **Static Analysis**: Update Ruff profile to flag insecure JWT usage (`flake8-bandit` rule S320 equivalent) and ensure `algorithms` arg enforced.

## 7. Observability & Ops

- **Logging**: Structured JSON logs via existing middleware, including fields `event=jwt.verify`, `kid`, `issuer`, `result`.
- **Metrics**: Add Prometheus counters (`jwt_verifications_total`, `jwt_failures_total`), gauges for `active_key_age_seconds`, and alerts on sustained failure rate >1% over 5 minutes.
- **Runbooks**: Document rotation SOP, emergency revoke procedure, and how to regenerate JWKS.
- **Security Audits**: Schedule quarterly key rotation tests and dependency scanning (SCA) for cryptography libraries.

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
