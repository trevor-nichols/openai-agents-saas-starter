# Milestone: EdDSA Trustworthy Authentication Pipeline

## Objective
- Deliver an enterprise-grade JWT authentication system using Ed25519 (EdDSA) without external authorization SaaS.
- Establish in-house key lifecycle management, observability, and rollout controls ready for multi-service consumption.

## Architecture Decisions (2025-11-06)
- **Signing Algorithm**: Mandate Ed25519 signatures for access and refresh tokens; enforce `alg=EdDSA` in verifiers, retain optional RSA256 fallback disabled by default.
- **Key Management**: Introduce `app/core/keys.py` owning key generation, rotation, revocation, and JWK publishing; keys stored in sealed volume or secret manager mounted read-only at runtime.
- **Token Service**: Refactor `app/core/security.py` to use signer/validator interfaces, strict claim validation (iss/aud/sub/jti/exp/nbf), and refresh token rotation with revocation tracking.
- **Public Distribution**: Expose an authenticated-optional JWKS endpoint under `/.well-known/jwks.json` with cache headers, ETag support, and signature coverage for keyset integrity.
- **Observability & Governance**: Emit structured audit logs, Prometheus counters, and alert thresholds for token validation failures, rotation drift, and key age; embed SOPs into runbooks.
- **Rollout Strategy**: Support dual-signing canary in staging, progressive rollout, and post-cutover validation before retiring legacy algorithms.

## Work Breakdown

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| AUTH-001 | Threat Modeling & Requirements | Document JWT consumers, trust boundaries, risk scenarios, and policy guardrails. | – | Planned |
| AUTH-002 | Ed25519 Key Infrastructure | Build key lifecycle module, secure storage contract, CLI utilities, and rotation SOP. | – | Planned |
| AUTH-003 | JWT Service Refactor | Implement EdDSA signer/validator interfaces, strict claim schema, and exhaustive tests. | – | Planned |
| AUTH-004 | JWKS Distribution Surface | Ship JWKS endpoint, caching strategy, and integration tests with Next.js client. | – | Planned |
| AUTH-005 | Observability & Alerts | Add structured logging, metrics, dashboards, and alerting around auth pipeline. | – | Planned |
| AUTH-006 | Staged Rollout & Postmortem | Execute dual-signing canary, production cutover, and retrospective documentation. | – | Planned |

## Notes & Assumptions
- PyJWT ≥2.10 with `cryptography` backend satisfies EdDSA support; ensure dependency alignment in `pyproject.toml` and lockfiles.
- Private keys live outside source control; local dev uses generated test keys with explicit warnings to prevent promotion.
- Refresh token storage may leverage existing Postgres infrastructure; if so, enforce tenant scoping and TTL cleanup jobs.
- Frontend must gracefully handle JWKS cache refresh; coordinate with `agent-next-15-frontend` for hook updates.
- Multi-region deployments replicate key material via approved secret manager; single signer per region with documented failover promotion.
- Refresh tokens bind to device fingerprint hash; mismatches trigger rejection unless trusted-device flows are implemented later.
- JWKS endpoint remains public with edge rate limiting and audit logging; reject mTLS for now.
- Redis provides primary revocation cache with Postgres fallback; cache TTL matches refresh token lifetime.
- Test suite refactor to `tests/unit`, `tests/contract`, `tests/integration` precedes AUTH-003 implementation and coverage gates enforced in CI.
- Secret manager (Ops-managed Vault HA cluster) guarantees ≥99.95% monthly availability with 15-minute RTO; sealed volume mounts refresh within 5 minutes after failover. Schedule key rotations outside the weekly Sunday 02:00–03:00 UTC maintenance window to avoid transient read errors.
- Risk: vault failover can impose up to 60-second read latency spikes; mitigation: token service caches active/next keypair in memory and alerts if refresh exceeds 30 seconds so on-call can verify vault health.
- Sealed key volume (EFS-backed read-only mount) inherits 99.9% regional availability; cross-region replication completes within 10 minutes. Mitigation for prolonged regional outage is documented failover promoting standby region’s `next` key after audit sign-off.
- Scope taxonomy locked for v1: `billing:read`, `billing:manage`, `conversations:read`, `conversations:write`, `conversations:delete`, `tools:read`, `support:*`; enforce read-only vs. mutate semantics accordingly.
- Service-account issuance: non-interactive consumers receive tenant-scoped refresh tokens through AuthService using Vault-managed service credentials and CLI/CI helper; no STS exchange required in v1.
- Refresh-token persistence: service-account refresh tokens will reuse the unified revocation store (Redis + Postgres) planned in AUTH-003. `force=false` will return existing active tokens per account/tenant/scope tuple; issuance endpoint will check the store before minting new tokens and the CLI will support revocation hooks once exposed.
- Vault Transit payloads include nonce/iat/exp claims; AuthService persists nonce fingerprints through a Redis-backed (in-memory fallback) cache to block replay within the 5-minute signing window.

## Execution Plan

### AUTH-001 — Threat Modeling & Requirements
1. Inventory services validating tokens and map data flows (frontend, FastAPI routers, future services).
2. Capture threat scenarios (token theft, downgrade attacks, replay, rotation failure) and mitigations.
3. Review with security stakeholders; sign off on acceptance criteria and non-goals.

### AUTH-002 — Ed25519 Key Infrastructure
1. Implement `KeySet` domain abstraction (active, next, retired) with rotation windows.
2. Provide CLI/management tasks to generate Ed25519 keypairs and publish public JWK bundles.
3. Define storage adapter contracts (filesystem, secret manager) and integration tests.

### AUTH-003 — JWT Service Refactor
1. Introduce signer/validator interfaces consumed by `security.py` and auth routers.
2. Enforce claim validation (`iss`, `aud`, `sub`, `jti`, `exp`, `nbf`, `scope`, `token_use`).
3. Deliver unit + contract tests covering success, expiry, malformed tokens, wrong issuer, revoked `jti`.

### AUTH-004 — JWKS Distribution Surface
1. Serve JWKS under `/.well-known/jwks.json` with `kid` alignment and cache headers.
2. Add integration test ensuring Next.js client refreshes keys and validates EdDSA tokens.
3. Document consumption guidelines for internal services.

### AUTH-005 — Observability & Alerts
1. Emit structured logging for sign/verify events (success/failure reasons, `kid`).
2. Instrument Prometheus/Grafana dashboards for error rates, key age, rotation countdown.
3. Establish alert thresholds and runbooks for auth incidents.

### AUTH-006 — Staged Rollout & Postmortem
1. Enable dual-signing in staging, monitor metrics, and gather QA sign-off.
2. Schedule production cutover, enforce EdDSA-only verification, and retire legacy path.
3. Conduct retrospective capturing lessons, update documentation, and archive artifacts.

## Progress Log
- _2025-11-06_: Milestone initiated; issues AUTH-001 through AUTH-006 added to `ISSUE_TRACKER.md`.
- _2025-11-06_: Draft architecture blueprint published at `docs/architecture/authentication-ed25519.md` pending AUTH-001 review.
- _2025-11-06_: Test suite reorganized into `tests/unit`, `tests/contract`, and `tests/integration` to unblock upcoming auth work.
- _2025-11-06_: Cross-team review approved scope taxonomy, audience identifiers, frontend refresh-token strategy, and service-account issuance approach; SLA findings added to Notes & Assumptions.
- _2025-11-06_: Vault Transit signing plan documented (`docs/security/vault-transit-signing.md`); refresh-token reuse strategy aligned with upcoming revocation store implementation.
- _2025-11-06_: Key lifecycle module (`app/core/keys.py`), `auth keys rotate` CLI command, JWKS stub, and Vault KV secret-manager adapter published; tracker + blueprint updated to reflect new storage adapters and public key surface.
- _2025-11-06_: Refresh-token repository (`app/domain/auth.py`, `app/infrastructure/persistence/auth/…`) + Alembic migration landed; AuthService now reuses cached tokens (Postgres + Redis) when `force=False` and persists revocations via the new store.
- _2025-11-06_: `service_account_tokens.refresh_token_hash` now stores bcrypt(+pepper) digests; migration `20251106_230500` truncates legacy plaintext rows and `AUTH_REFRESH_TOKEN_PEPPER` setting shipped to satisfy threat-model requirement R10.
- _2025-11-06_: EdDSA signer/validator interfaces replace HS256 helpers, `AUTH_DUAL_SIGNING_ENABLED`/`AUTH_DUAL_SIGNING_OVERLAP_MINUTES` landed, `service_account_tokens.signing_kid` added via migration `20251106_235500`, and auth contract/unit tests cover tampering, unknown kid, and expiry flows.
