# Auth services

Developer-facing overview of how authentication is wired across the API: issuing/verifying JWTs, managing human sessions, handling MFA, and minting service-account tokens.

## What this area does
- Issues short-lived access tokens and long-lived refresh tokens for human users via `UserSessionService`, including optional MFA challenges and session device tracking.
- Persists and revokes session metadata (fingerprints, GeoIP, user-agent summaries) through `SessionStore` backed by the `UserSessionRepository`.
- Issues, reuses, and rate-limits service-account refresh tokens via `ServiceAccountTokenService`, enforcing the catalog in `core/service_accounts.py`.
- Wraps the pieces behind the `AuthService` façade and exposes FastAPI dependencies (`require_current_user`, `require_scopes`, `require_verified_user`, tenant helpers) used by routers under `app/api/v1/auth/**`.
- Publishes auth-related activity/security events (logins, revocations, service-account issuance) for audit and observability.

## Key modules
- `auth_service.py`: Thin façade composing session + service-account sub-services and wiring token verification for refresh/logout flows.
- `auth/session_service.py`: Human login/refresh/logout/session revocation; rotates refresh tokens, enforces tenant context, and embeds claims (`sub=user:<uuid>`, `tenant_id`, `roles`, `scope`, `email_verified`, `sid`) into access tokens.
- `auth/refresh_token_manager.py`: Convenience wrapper over `RefreshTokenRepository` (Postgres + Redis cache in `infrastructure/persistence/auth/repository.py`), handles jti lookup/revocation and list views for service-account tokens.
- `auth/session_store.py`: Persists session metadata via `UserSessionRepository`, enriching with GeoIP (`GeoIPService`) and user-agent summaries when available.
- `auth/service_account_service.py`: Issues service-account refresh tokens with per-account/global burst limits, catalog validation, and optional tenant scoping; reuses an active token unless `force=true`.
- `auth/mfa_service.py`: TOTP enrollment/verification, recovery codes, and revocation; used by `UserSessionService` to gate logins when MFA methods exist.
- `auth/builders.py`: Factory helpers that pull repositories from the container, attach `RefreshTokenManager`/`SessionStore`, and build session or service-account services for wiring.
- `core/security.py`: Ed25519 signer/verifier, password hashing, `get_current_user` dependency, and JWKS serving (keys stored at `var/keys/keyset.json` by default).

## Request and token flows
- **Human login**: `UserSessionService.login_user` authenticates via `UserService`, optionally returns an MFA challenge token if verified methods exist, otherwise issues access/refresh tokens (EdDSA-signed). Refresh tokens are saved with jti + fingerprint and linked session id; access tokens carry scopes/roles and `email_verified`.
- **Refresh**: `refresh_user_session` verifies the refresh token (must have `token_use=refresh`), revokes the presented jti, loads the active user, and re-issues a rotated refresh + new access token while updating session metadata.
- **Logout/revocation**: `logout_user_session` and `revoke_user_session_by_id` revoke refresh tokens in storage and mark the matching session revoked; `revoke_user_sessions` bulk-revokes all sessions for a user (e.g., after password change).
- **Service accounts**: `ServiceAccountTokenService.issue_refresh_token` validates account/scopes/tenant against the catalog, enforces burst limits, reuses an existing active token when scopes/tenant match (unless `force`), and logs activity per tenant when applicable.
- **Dependencies**: Routers use `require_current_user` for auth, `require_scopes` / `require_verified_scopes` for scope checks, and `get_tenant_context` + `require_tenant_role` to enforce tenant role constraints based on JWT claims and optional `X-Tenant-*` headers.

## Persistence and configuration
- Domain contracts live in `app/domain/auth.py`; repositories are implemented under `infrastructure/persistence/auth/` (refresh tokens hashed with `AUTH_REFRESH_TOKEN_PEPPER`, sessions stored with optional IP encryption).
- Key settings (see `core/settings/security.py`): `ACCESS_TOKEN_EXPIRE_MINUTES`, `AUTH_REFRESH_TOKEN_TTL_MINUTES`, `REQUIRE_EMAIL_VERIFICATION`, `MFA_CHALLENGE_TTL_MINUTES`, lockout and rate-limit knobs, key storage backend/path, and auth audience list.
- Ed25519 keysets are loaded via `core/keys.py`; default file backend reads/writes `var/keys/keyset.json` (managed by the CLI/just tasks). JWKS is exposed at `/.well-known/jwks.json` with configurable cache headers.

## API surface
- Human flows: `app/api/v1/auth/routes_sessions.py` (login/refresh/logout), `routes_passwords.py` (reset/change), `routes_email.py` (verification), `routes_mfa.py` (enroll/verify/revoke), `routes_signup.py` and `routes_signup_requests.py` for onboarding.
- Service accounts: `routes_service_accounts.py` (catalog) and `routes_service_account_tokens.py` (issue/list/revoke tokens).
- Dependencies for other domains live in `app/api/dependencies/auth.py` and `app/api/dependencies/tenant.py`; most routers compose them for guardrails instead of re-implementing checks.

## How to work with it
- Use `auth_service` from `app/services/auth_service.py` for issuing/refreshing/revoking tokens in business logic; prefer the FastAPI dependencies for request-time enforcement.
- When adding storage backends, implement `RefreshTokenRepository` and/or `UserSessionRepository` under `infrastructure/persistence/auth/` and wire them through the container or `build_session_service`.
- Update the service-account catalog in `core/service_accounts.yaml` (or code) when adding machine principals; keep scope naming consistent (`<namespace>:<verb>`), and document any new scopes in router schemas.
- Keep TTLs and peppers configured via environment (.env files); do not bypass rotation—refresh tokens are single-use after `refresh_user_session` revokes the presented jti.
