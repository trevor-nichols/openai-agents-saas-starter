# Signup & Identity Lifecycle Domain

Groups self-serve onboarding flows: invites, signup requests, signup orchestration, email verification, and password recovery. These services bridge anonymous visitors into authenticated tenants and enforce the org’s signup posture.

## Flows at a glance
- Public signup (`POST /api/v1/auth/register`): Creates tenant + owner user in provisioning state, attempts billing, promotes to active on success, returns session tokens, and triggers email verification.
- Access request (`POST /api/v1/auth/request-access`): Collects leads when policy is `invite_only` or `approval`; operators later approve/reject.
- Invite redemption: Required when `SIGNUP_ACCESS_POLICY` is not `public`; tokens are reserved during signup and finalized or released on success/failure.
- Email verification: Sent after signup; marks email verified and revokes old sessions once the token is redeemed.
- Password recovery: Issues reset tokens and resets credentials with policy + reuse enforcement.

## Services and responsibilities
- `SignupService` (`signup_service.py`): Orchestrates signup by delegating to specialized helpers for invite policy enforcement, provisioning, billing, notifications, and telemetry.
- `SignupInvitePolicyService` (`invite_policy.py`): Reserves/validates invite context when signup is not public.
- `SignupProvisioningService` (`provisioning.py`): Creates tenant + owner records in a single transaction, then finalizes or deprovisions on downstream outcomes.
- `SignupBillingService` (`billing.py`): Applies billing enablement rules and trial-day selection before provisioning subscriptions.
- `SignupNotificationService` (`notifications.py`): Triggers email verification as a best-effort follow-up.
- `SignupTelemetry` (`telemetry.py`): Emits signup completion events + activity breadcrumbs.
- `InviteService` (`invite_service.py`): Operator-facing issuance, reservation, redemption, and revocation of signup invites; backs approval flows and rate-limit guarded redemptions.
- `SignupRequestService` (`signup_request_service.py`): Manages inbound access requests, quotas, honeypot checks, and operator approvals that mint invites.
- `EmailVerificationService` (`email_verification_service.py`): Mints verification tokens, persists them in the token store, and delivers via Resend (or logs). Redeeming marks the user verified and revokes existing sessions.
- `PasswordRecoveryService` (`password_recovery_service.py`): Issues password reset tokens, enforces password policy/reuse via `UserService`, and revokes sessions on successful reset.

## API entrypoints
- `GET /api/v1/auth/signup-policy`: Returns current access policy (`public`, `invite_only`, `approval`) for clients.
- `POST /api/v1/auth/register`: Runs `SignupService.register` with optional `invite_token`, `plan_code`, and `trial_days`.
- `POST /api/v1/auth/request-access`: Submits a signup request (with honeypot + rate limits); only meaningful when policy is not `public`.
- `GET /api/v1/auth/signup-requests`: Operator list view (scope `auth:signup_requests`).
- `POST /api/v1/auth/signup-requests/{id}/approve|reject`: Operator decisions; approval issues an invite linked to the request.

## Configuration (env / settings)
- `SIGNUP_ACCESS_POLICY` (`public` | `invite_only` | `approval`) and `ALLOW_PUBLIC_SIGNUP` derive exposure.
- Rate limits: `SIGNUP_RATE_LIMIT_PER_HOUR`, `SIGNUP_RATE_LIMIT_PER_IP_DAY`, `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY`, `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY`; enforced via Redis-backed `RateLimitService`.
- Requests quota: `SIGNUP_CONCURRENT_REQUESTS_LIMIT` caps pending access requests per IP.
- Billing: `ENABLE_BILLING`, `SIGNUP_DEFAULT_PLAN_CODE`, `SIGNUP_DEFAULT_TRIAL_DAYS`, `ALLOW_SIGNUP_TRIAL_OVERRIDE`; signup skips billing when disabled.
- Invites: `SIGNUP_INVITE_RESERVATION_TTL_SECONDS` controls hold time while signup runs.
- Email flows: `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES`, `RESEND_*` template IDs, `AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER`; password reset uses `PASSWORD_RESET_TOKEN_TTL_MINUTES` and `AUTH_PASSWORD_RESET_TOKEN_PEPPER`.

## Operational notes
- Signup writes tenant, user, membership, and password history in one transaction; tenant starts in `provisioning`, user starts as `pending`, and slug collisions raise `TenantSlugCollisionError`.
- Invite reservations are always released or finalized (best-effort cleanup on exceptions).
- Email verification and password reset tokens are hashed and fingerprinted (IP/UA) before storage; Resend delivery errors surface as 5xx to callers.
- Billing provisioning failures return 4xx/5xx, mark the tenant deprovisioned, disable the owner user, and emit `signup.*` breadcrumbs.

## Testing touchpoints
- Unit coverage: `tests/unit/accounts/test_signup_service.py`, `test_signup_request_service.py`, `test_email_verification_service.py`, `test_password_recovery_service.py`, plus auth API contract tests under `tests/contract` (notably `test_auth_signup_register.py`) and `tests/smoke/http/test_auth_smoke.py`.
