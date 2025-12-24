# Setup Wizard Redesign Spec (v1)

_Last updated: 2025-12-24_

## Goals
- Deliver a predictable, linear setup flow that feels product‑grade and is safe to re‑run.
- Encode ordering + dependency logic in the wizard schema so TUI, headless, and docs remain consistent.
- Introduce hosting presets to reduce cognitive load and align defaults with deployment intent.
- Produce auditable artifacts (summary + redacted snapshot + diff) on every run.

---

## Proposed Wizard Order (Linear)
0. Welcome + Mode
1. Profile + Hosting Preset
2. Core & Metadata
3. Infra & Database
4. Secrets & Key Management
5. Security & Rate Limits
6. AI Providers
7. Storage
8. Billing & Email
9. Usage & Entitlements
10. Observability & GeoIP
11. Integrations
12. Signup & Worker Policies
13. Frontend
14. Dev User (optional)
15. Summary + Next Steps

---

## Hosting Presets (New)

### Preset: `local_docker`
- DB: local compose (`STARTER_LOCAL_DATABASE_MODE=compose`)
- Redis: local default (`redis://localhost:6379/0`)
- Secrets: `vault_dev` (or fallback to file when Vault disabled)
- Key storage: `file`
- Storage: `minio`
- Billing: off by default
- Observability: stdout/file only; collector optional

### Preset: `cloud_managed`
- DB: external `DATABASE_URL` required
- Redis: external `REDIS_URL` required
- Secrets provider default depends on `cloud_provider`:
  - aws → `aws_sm`
  - azure → `azure_kv`
  - gcp → `infisical_cloud` (or `vault_hcp` if preferred by ops)
- Storage provider default depends on `cloud_provider`:
  - aws → `s3`
  - azure → `azure_blob`
  - gcp → `gcs`
- Billing: default on (but requires Stripe keys)

### Preset: `enterprise_custom`
- No defaults beyond required keys.
- All advanced prompts available.

---

## Advanced Prompt Toggle (New)
- `show_advanced_prompts` gate controls fine‑tuning prompts (rate limits, cache TTLs, image defaults, optional provider fields).
- Defaults:
  - demo/dev → false
  - staging/prod → true (unless overridden)

---

## Artifact Strategy (New)

### Existing artifacts (keep)
- `var/reports/setup-summary.json`
- `var/reports/cli-one-stop-summary.md`
- `var/reports/verification-artifacts.json`

### New artifacts
- `var/reports/setup-snapshot.json` (redacted snapshot: no secrets; hashed values for change detection)
- `var/reports/setup-diff.md` (summary of changes since last run)

Behavior:
- On wizard start, compute diff vs last snapshot and show in UI.
- On wizard completion, write new snapshot + diff.

---

## Prompt Inventory (Ideal)

### 0) Welcome + Mode
- setup mode: interactive/headless
- `show_advanced_prompts`
- resume previous run

### 1) Profile + Hosting Preset
- `profile`
- `hosting_preset`
- `cloud_provider` (if preset is cloud)
- automation toggles: `auto_infra`, `auto_secrets`, `auto_stripe`, `auto_migrations`

### 2) Core & Metadata
- `ENVIRONMENT`, `DEBUG`, `PORT`
- `APP_PUBLIC_URL`, `API_BASE_URL`
- `ALLOWED_HOSTS`, `ALLOWED_ORIGINS`
- `AUTO_RUN_MIGRATIONS`, `DATABASE_ECHO`
- `REQUIRE_EMAIL_VERIFICATION`

### 3) Infra & Database
- `STARTER_LOCAL_DATABASE_MODE` (compose/external)
- `DATABASE_URL` (if external)
- `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (if compose)
- `REDIS_URL` + optional `RATE_LIMIT_REDIS_URL`, `AUTH_CACHE_REDIS_URL`, `SECURITY_TOKEN_REDIS_URL`, `BILLING_EVENTS_REDIS_URL`

### 4) Secrets & Key Management
- Core secrets: `SECRET_KEY`, `AUTH_*_PEPPER`, `AUTH_SESSION_ENCRYPTION_KEY`, `AUTH_SESSION_IP_HASH_SALT`
- `SECRETS_PROVIDER` + provider‑specific credentials
- `AUTH_KEY_STORAGE_BACKEND`, `AUTH_KEY_STORAGE_PROVIDER`, `AUTH_KEY_SECRET_NAME`
- `ENABLE_SECRETS_PROVIDER_TELEMETRY`, `ROTATE_SIGNING_KEYS`

### 5) Security & Rate Limits
- lockouts, token TTLs, JWKS cache, status subscription limits
- request throttles (chat/billing)
- `RATE_LIMIT_KEY_PREFIX`

### 6) AI Providers
- `OPENAI_API_KEY` required
- optional `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`

### 7) Storage
- `STORAGE_PROVIDER`, `STORAGE_BUCKET_PREFIX`
- provider‑specific credentials
- image defaults (advanced)

### 8) Billing & Email
- `ENABLE_BILLING`, `ENABLE_BILLING_STREAM`
- Stripe keys + price map + webhook secret
- Resend toggles + credentials
- optional: `RUN_STRIPE_SEED`, `RUN_MIGRATIONS_NOW`

### 9) Usage & Entitlements
- `ENABLE_USAGE_GUARDRAILS`
- cache TTL/backend + redis url
- plan codes + limits
- `ENABLE_VECTOR_LIMIT_ENTITLEMENTS`

### 10) Observability & GeoIP
- logging sinks + file settings
- otlp + collector toggles
- datadog/sentry exporters
- frontend log ingest toggle
- geoip provider + keys/paths

### 11) Integrations
- Slack status notifications + channels + test send

### 12) Signup & Worker Policies
- signup exposure policy + rate limits
- default plan + trial days
- billing retry worker mode + replay toggle

### 13) Frontend
- `PLAYWRIGHT_BASE_URL`, `AGENT_API_MOCK`
- cookie policy toggles
- `NEXT_PUBLIC_LOG_LEVEL`, `NEXT_PUBLIC_LOG_SINK`

### 14) Dev User
- dev user defaults + optional auto‑generated password

### 15) Summary + Next Steps
- list artifacts + highlight diffs
- recommended commands

---

## Implementation Notes
- Encode ordering in `section_specs.py` + `schema.yaml`.
- Preset engine should inject defaults before prompt evaluation (schema‑aware).
- Resume uses `wizard-state.json`; new snapshot/diff drive setup menu status.
- TUI should show preset badge + “advanced prompts enabled” indicator.

