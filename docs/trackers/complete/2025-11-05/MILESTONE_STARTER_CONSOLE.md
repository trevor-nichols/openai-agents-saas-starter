# Starter Console Milestone Tracker

This tracker captures the Starter Console setup flow plus the recommended environment “profiles” we should support. Treat it as the source of truth when aligning automation expectations, documentation, and onboarding guides.

## Goals
- Guarantee that `starter-console setup wizard` guides an operator from zero env vars to a runnable stack with auditable artifacts.
- Keep the demo profile blazing fast by prefilling sensible defaults, deferring optional providers, and embracing Docker Compose for Postgres/Redis.
- Maintain parity between the wizard questionnaire and the docs so every prompt has clear rationale and fallback guidance.

## Profiles To Support
1. **Demo-Lite (default `--profile demo`)**
   - Compose-managed Postgres + Redis (leave `DATABASE_URL` blank to rely on docker-compose defaults).
   - Secrets provider `vault_dev` with verification disabled for speed.
   - Billing, Resend, Slack, GeoIP all **off** to shrink dependencies.
   - Inline billing worker with replay enabled, insecure cookies allowed.
   - Automation: `--auto-infra`, `--auto-secrets`, `--auto-migrations`, `--auto-redis`, `--no-auto-geoip`.
2. **Demo-Full (still `--profile demo`, but “parity mode”)**
   - Same infra automation as Demo-Lite, but flip on billing + Stripe plan map, Resend, Slack test message, GeoIP (MaxMind download).
   - Use this before handing off to QA so we verify integrations without leaving localhost.
3. **Staging**
   - Requires managed Postgres URL + TLS Redis endpoints.
   - Secrets provider: `vault_hcp` or cloud secret manager with Vault verification **enabled** (non-negotiable).
   - Billing, usage guardrails, Slack, observability sinks must all be exercised; automation limited to migrations/redis/geoip (no Docker/Vault helpers).
4. **Production**
   - Headless (`--strict --profile production`) runs only; answers supplied via repo-stored JSON/vars in CI.
   - Enforces Vault verification, dedicated billing worker, secure cookies only, and brings its own automation hooks (migrations/geoip).
   - Stripe provisioning and Resend onboarding run outside the wizard; the setup flow just validates keys.

## Wizard Sections & Expectations
| Section | Purpose | Demo-Lite Defaults | Higher Environment Requirements |
| --- | --- | --- | --- |
| Core & Metadata | ENV label, URLs, auth defaults | Keep defaults (`ENVIRONMENT=development`; `DEBUG` auto-derives); auto migrations true | Explicit hostnames; derived `DEBUG=false` outside dev; stricter CORS |
| Secrets & Vault | Generate peppers, choose provider, optional signing key rotation | Autogenerate peppers, `vault_dev`, verification off | Real secret manager, Vault verification on, rotate keys each milestone |
| Security & Rate Limits | Lockouts, JWKS cache, rate limit redis prefix | Accept defaults to stay unblocked | Tune email/reset throttles per policy, JWKS salt stored in secret manager |
| Providers & Infra | DB URL, AI providers, Redis pools, Stripe, Resend | OpenAI key only; leave `DATABASE_URL` empty; Redis=localhost; skip billing/email | Managed DB URL, TLS Redis per workload, Stripe secrets + plan map, Resend templates |
| Usage & Entitlements | Plan guardrails + entitlements artifact | Skipped (billing off) | Required when billing on; produce `var/reports/usage-entitlements.json` |
| Observability | Tenant slug, logging sink, GeoIP | `LOGGING_SINKS=stdout`, `GEOIP_PROVIDER=none` | Datadog/OTLP endpoints, GeoIP provider tokens, optional collector exporters |
| Integrations | Slack incident notifications | Disabled | Slack bot token, channel map, send test |
| Signup & Worker | Signup policy, rate limits, billing worker topology | `invite_only`, inline worker, insecure cookies allowed | `approval` or `invite_only`, dedicated worker, auto-generated worker overlay |
| Frontend | Next.js envs (API URL, Playwright, cookie posture) | `API_BASE_URL` canonical; frontend mirrors to `NEXT_PUBLIC_API_URL`; allow insecure cookies in demo | HTTPS URLs only, secure cookies, Playwright hitting deployed host |

## Suggested Workflow
1. **Verify dependencies once**  
   `starter-console infra deps`
2. **Bootstrap Demo-Lite**  
   ```bash
   starter-console setup wizard \
     --profile demo \
     --auto-infra --auto-secrets --auto-migrations --auto-redis \
     --no-auto-geoip
   ```
3. **Seed a test tenant/user** (unblocks frontend login)  
   ```bash
   starter-console users seed \
     --email dev@example.com \
     --password "Passw0rd!" \
     --display-name "Dev Admin"
   ```
4. **Issue a service-account token** for API smoke tests  
   ```bash
   starter-console auth tokens issue-service-account \
     --account demo-bot \
     --scopes chat:write,conversations:read
   ```
5. **Promote configs**  
   - Copy `apps/api-service/.env.local` + `web-app/.env.local` outputs into the staging secrets store.
   - Re-run the wizard with `--profile staging --no-auto-infra --no-auto-secrets` to validate hosted dependencies before shipping.
6. **Document findings**  
   - Check `var/reports/setup-summary.json` and `cli-one-stop-summary.md` into the operator runbook for each milestone.
   - Regenerate `docs/trackers/templates/STARTER_CONSOLE_CHECKLIST.md` via `starter-console setup wizard --profile <profile> --report-only --output checklist --markdown-summary-path docs/trackers/templates/STARTER_CONSOLE_CHECKLIST.md` so Platform Foundations has the latest checkbox set.
   - Update this tracker whenever prompts change or new providers appear.

## Just Automation
Use the new Make targets to keep each milestone repeatable:

| Target | Description | Notes |
| --- | --- | --- |
| `just setup-demo-lite` | Runs dependency check, launches the wizard with Demo-Lite flags, then seeds a dev user. | Requires user input for secrets; auto-starts Compose for seeding. Afterwards run `just api` + `just issue-demo-token`. |
| `just setup-demo-full` | Same as Demo-Lite but keeps every automation switch on (`--auto-geoip`, `--auto-stripe`). | Useful for parity testing once Resend/Stripe creds exist. |
| `just setup-staging [setup_staging_answers=path]` | Runs the wizard with staging-safe automation; optional answers file enables headless mode. | Compose/Vault helpers disabled; ensure hosted Postgres/Redis URLs exist beforehand. |
| `just setup-production setup_production_answers=path` | Strict, headless production run. | Provide an answers JSON per environment (committed to a secure store). |
| `just seed-dev-user` | Starts Compose (if needed) and uses `starter-console users seed`. | Customize via `SETUP_USER_EMAIL`, `SETUP_USER_PASSWORD`, `SETUP_USER_TENANT`, etc. |
| `just issue-demo-token` | Calls the CLI token issuer once FastAPI is running. | `SETUP_SERVICE_ACCOUNT`, `SETUP_SERVICE_SCOPES`, `SETUP_SERVICE_TENANT` override defaults. |

Environment variable knobs for automation:

- `SETUP_USER_EMAIL`, `SETUP_USER_NAME`, `SETUP_USER_PASSWORD`, `SETUP_USER_TENANT`, `SETUP_USER_TENANT_NAME`, `SETUP_USER_ROLE`
- `SETUP_SERVICE_ACCOUNT`, `SETUP_SERVICE_SCOPES`, `SETUP_SERVICE_TENANT`
- `SETUP_STAGING_ANSWERS`, `SETUP_PRODUCTION_ANSWERS`

Document the resulting `var/reports/*.json` files (and any answer files) whenever these targets are exercised so other environments stay reproducible.

Reference templates live under `docs/environments/`. Copy `staging.answers.template.json` or `production.answers.template.json` into a secure location, populate the real secrets, and point the `SETUP_*_ANSWERS` environment variable at that file before running the Make target.

Regenerate the environment inventory after prompt/schema updates with:

```bash
starter-console config write-inventory --path docs/trackers/CONSOLE_ENV_INVENTORY.md
```

## Next Steps
- [x] Convert this tracker into a checklist template referenced by Platform Foundations.
- [x] Backfill staging/production answer files in `docs/environments/` so `--strict` runs have blessed defaults.
- [x] Align `docs/trackers/CONSOLE_ENV_INVENTORY.md` with the Local-Full profile to ensure parity coverage.
