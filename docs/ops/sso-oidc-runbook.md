# OIDC SSO Runbook (Google preset)

Last updated: January 1, 2026

This runbook explains how to provision and operate Google OIDC SSO in api-service.

## Prerequisites

1. Google OAuth client (Web) with redirect URI:
   - `<APP_PUBLIC_URL>/auth/sso/google/callback`
2. Postgres and Redis available (provider configs in Postgres; PKCE/state/nonce in Redis).
3. SSO client secret encryption key configured:
   - Prefer `SSO_CLIENT_SECRET_ENCRYPTION_KEY`
   - Fallbacks: `AUTH_SESSION_ENCRYPTION_KEY` or `SECRET_KEY`

## Provisioning (recommended: Starter Console)

### Option A: Setup wizard
1. Run `starter-console setup`.
2. In the Providers section, enable Google SSO and provide the Google client ID/secret.
3. Choose scope:
   - `global` uses a single shared provider config (no tenant id/slug).
   - `tenant` requires `TENANT_ID` or `TENANT_SLUG`.
4. Select the auto-provision policy:
   - `invite_only` (default)
   - `domain_allowlist` (requires `ALLOWED_DOMAINS`)
   - `disabled`

### Option B: Headless CLI
Global example:
```
starter-console sso setup \
  --provider google \
  --scope global \
  --issuer-url https://accounts.google.com \
  --client-id <client-id> \
  --client-secret <client-secret> \
  --scopes "openid,email,profile" \
  --auto-provision-policy invite_only \
  --non-interactive
```

Tenant-scoped example:
```
starter-console sso setup \
  --provider google \
  --scope tenant \
  --tenant-slug acme \
  --issuer-url https://accounts.google.com \
  --client-id <client-id> \
  --client-secret <client-secret> \
  --scopes "openid,email,profile" \
  --auto-provision-policy domain_allowlist \
  --allowed-domains "acme.com" \
  --non-interactive
```

Notes:
- `token-auth-method=none` requires PKCE (`--pkce-required`).
- `SSO_GOOGLE_*` env vars are optional and used as defaults in the console; the runtime reads provider configs from Postgres.

## Runtime settings

These are runtime settings (not stored in the provider config row):
- `SSO_STATE_TTL_MINUTES` (default 10)
- `SSO_CLOCK_SKEW_SECONDS` (default 60)
- `SSO_START_RATE_LIMIT_PER_MINUTE` (default 30)
- `SSO_CALLBACK_RATE_LIMIT_PER_MINUTE` (default 30)
- `SSO_CLIENT_SECRET_ENCRYPTION_KEY` (recommended)

## Validation

1. List enabled providers for a tenant:
   - `GET /api/v1/auth/sso/providers?tenant_id=<uuid>` (or `tenant_slug=<slug>`)
2. Start flow:
   - `POST /api/v1/auth/sso/google/start` with tenant selector.
   - Confirm an `authorize_url` is returned.
3. Callback:
   - Verify session cookies are set and the response indicates success or MFA challenge.

## Monitoring

Logs emit structured events (JSON) with `reason` codes:
- `auth.sso.start`
- `auth.sso.callback`
- `auth.sso.linked`
- `auth.sso.provisioned`
- `auth.sso.failure`

Use these to filter for provisioning failures, invalid tokens, or policy blocks.

## Troubleshooting

Common issues and checks:
- **`state_invalid` / `provider_mismatch`**: Redis state/nonce expired or mismatched. Confirm Redis availability and `SSO_STATE_TTL_MINUTES`.
- **`token_exchange_failed` / `token_verification_failed`**: Issuer, audience, or JWKS mismatch. Confirm `issuer_url`, `discovery_url`, and Google OAuth client settings.
- **`email_unverified` / `domain_not_allowed` / `invite_required`**: Auto-provision policy blocked login. Verify `AUTO_PROVISION_POLICY` and `ALLOWED_DOMAINS`.
- **`identity_conflict`**: Existing identity linked to another user; resolve manually before retrying.

## Rotation & Updates

1. Rotate the client secret in Google.
2. Re-run `starter-console sso setup` to upsert the new secret (stored encrypted).
3. If you rotate `SSO_CLIENT_SECRET_ENCRYPTION_KEY`, re-run the setup command to re-encrypt secrets.

## Operational checklist

- [ ] Google OAuth client configured with correct redirect URI.
- [ ] Provider config seeded (global or tenant-scoped).
- [ ] `SSO_CLIENT_SECRET_ENCRYPTION_KEY` set (or fallback key present).
- [ ] Rate limits tuned for expected login volume.
- [ ] Logs show `auth.sso.*` events during test sign-ins.
