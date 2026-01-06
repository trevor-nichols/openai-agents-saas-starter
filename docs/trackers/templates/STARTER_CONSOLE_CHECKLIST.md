# Starter Console Setup Checklist

- Profile: `demo`
- Generated: 2026-01-05 00:00:00 UTC
- Loaded env files: _(none loaded via --env-file)_
- Tracker reference: `docs/trackers/complete/MILESTONE_TRACKER.md`
- Regenerate: `starter-console setup wizard --profile demo --report-only --output checklist --markdown-summary-path <path>`

## M1 - Secrets & Key Management
Rotate and harden keys.

- [ ] `AUTH_PASSWORD_PEPPER` — ❌ missing
- [ ] `AUTH_REFRESH_TOKEN_PEPPER` — ❌ missing
- [ ] `VAULT_ADDR` _(optional)_ — ❌ missing
- [ ] `VAULT_TOKEN` _(optional)_ — ❌ missing
- [ ] `VAULT_TRANSIT_KEY` _(optional)_ — ❌ missing
- [ ] `secret_warnings` — ⚠️ warning — SECRET_KEY is using the starter value; AUTH_KEY_STORAGE_PATH still points to var/keys/keyset.json

## M2 - Provider & Infra Provisioning
Validate third-party credentials & database.

- [ ] `OPENAI_API_KEY` — ❌ missing
- [ ] `STRIPE_SECRET_KEY` — ❌ missing
- [ ] `STRIPE_WEBHOOK_SECRET` — ❌ missing
- [ ] `RESEND_API_KEY` _(optional)_ — ❌ missing
- [ ] `DATABASE_URL` _(optional)_ — ❌ missing
- [ ] `REDIS_URL` — ❌ missing
- [ ] `RATE_LIMIT_REDIS_URL` _(optional)_ — ❌ missing
- [ ] `AUTH_CACHE_REDIS_URL` _(optional)_ — ❌ missing
- [ ] `SECURITY_TOKEN_REDIS_URL` _(optional)_ — ❌ missing
- [ ] `BILLING_EVENTS_REDIS_URL` _(optional)_ — ❌ missing
- [x] `stripe_plan_map` _(optional)_ — ✅ ok — Plan map configured.

## M3 - Tenant & Observability
Baseline tenant + logging + geo telemetry.

- [ ] `TENANT_DEFAULT_SLUG` — ❌ missing
- [ ] `LOGGING_SINKS` — ❌ missing
- [ ] `GEOIP_PROVIDER` — ❌ missing

## M4 - Signup & Worker policy
Ensure signup controls & billing workers match deployment.

- [ ] `SIGNUP_ACCESS_POLICY` — ❌ missing
- [ ] `SIGNUP_RATE_LIMIT_PER_HOUR` — ❌ missing
- [ ] `SIGNUP_RATE_LIMIT_PER_IP_DAY` — ❌ missing
- [ ] `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY` — ❌ missing
- [ ] `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY` — ❌ missing
- [ ] `SIGNUP_CONCURRENT_REQUESTS_LIMIT` — ❌ missing
- [ ] `SIGNUP_DEFAULT_TRIAL_DAYS` — ❌ missing
- [ ] `BILLING_RETRY_DEPLOYMENT_MODE` — ❌ missing
- [x] `retry_worker` — ✅ ok — inline
