# Users service

Orchestrates account authentication and password lifecycle on top of the shared user repository. It sits behind the auth routers and token service, enforcing lockout/throttling rules, password policy/history, and tenant-aware scope resolution.

## What it owns
- Auth pipeline: verifies credentials, enforces lockout + IP throttling, records login events, and returns `AuthenticatedUser` with role-derived scopes.
- Password lifecycle: creation, user-initiated changes, admin resets, token-based resets, hashing/rehash (`PASSWORD_HASH_VERSION`), history checks, and strength validation.
- Tenant context: resolves memberships and raises when a tenant is missing or ambiguous, then maps roles → scopes.
- Status enforcement: blocks disabled/pending/locked users and clears lock state after successful authentication.
- Observability: persists login events with hashed IPs and optionally streams activity logs.

## Key pieces
- `UserService` (`service.py`): main façade used by the auth routes and `AuthService`. Methods: `authenticate`, `load_active_user`, `change_password`, `admin_reset_password`, `reset_password_via_token`, `register_user`.
- `build_user_service` / `get_user_service` (`factory.py`): wire dependencies from the container (`Settings`, `UserRepository`, activity service, IP throttler). This is what API routes call.
- Collaborators:
  - `UserRepository` (Postgres + Redis-backed) for users, password history, lock counters, login events, and status.
  - `LoginEventRecorder` (`login_events.py`): stores login events and emits activity logs.
  - `LockoutManager` (`lockout.py`): per-tenant lockout window/threshold + status transitions.
  - `PasswordPolicyManager` (`passwords.py`): history + strength enforcement via `core.password_policy`.
  - `LoginThrottle` (`throttling.py`): Redis-backed IP throttling for login attempts.
  - `resolve_membership` + `scopes_for_role` (`membership.py`, `scopes.py`): tenant selection and role → scopes mapping.
  - Errors in `errors.py`: `InvalidCredentialsError`, `IpThrottledError`, `UserLockedError`, `UserDisabledError`, `MembershipNotFoundError`, `TenantContextRequiredError`, `PasswordPolicyViolationError`.

## Where it is used
- API: `app/api/v1/auth/routes_passwords.py` (`/password/change`, `/password/reset`) and other auth flows reach it through `get_user_service`.
- Auth token issuance: `app/services/auth_service.py` uses `UserService.authenticate` to validate credentials before issuing tokens.
- Password recovery: `signup/password_recovery_service.py` calls `reset_password_via_token`.

## Configuration knobs (Settings)
- IP throttle: `AUTH_CACHE_REDIS_URL`/`REDIS_URL`, `auth_ip_lockout_threshold`, `auth_ip_lockout_window_minutes`, `auth_ip_lockout_duration_minutes`.
- Lockout: `auth_lockout_threshold`, `auth_lockout_window_minutes`, `auth_lockout_duration_minutes`.
- Passwords: `auth_password_history_count` plus global password policy settings in `core.password_policy`.

## Developing against it
- Ensure Postgres migrations are applied; the user repository depends on the auth tables and Redis for counters/history.
- Prefer `get_user_service()` from the container instead of instantiating directly so the shared throttler/activity services are reused.
- For local debugging without Redis IP throttling, pass a `NullLoginThrottle` into `build_user_service`, but keep throttling enabled in shared environments.
