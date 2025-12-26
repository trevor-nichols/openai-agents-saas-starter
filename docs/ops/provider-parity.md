# Third-Party Provider Parity (OPS-003)

Stripe and Resend back core SaaS features (billing and transactional email). Historically the
backend only logged warnings when their environment variables were missing, which meant
staging/production could boot with partially configured providers. OPS-003 introduces explicit
validation so every environment that advertises a provider either supplies the required secrets or
keeps the feature disabled.

## Enforcement matrix

| Provider | Feature Toggle | Required Env Vars | Dev (`ENVIRONMENT=development`) | Hardened envs (`ENVIRONMENT!=development` & `DEBUG=false`) |
| --- | --- | --- | --- | --- |
| OpenAI | n/a (agent runtime) | `OPENAI_API_KEY` | Warning only | Startup fails with `RuntimeError` until configured |
| Stripe | `ENABLE_BILLING=true` | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRODUCT_PRICE_MAP` | CLI still exits non-zero (see below), FastAPI logs warnings only when billing is disabled | Startup fails with `RuntimeError` until every variable is present |
| Resend | `RESEND_EMAIL_ENABLED=true` | `RESEND_API_KEY`, `RESEND_DEFAULT_FROM` | Warning only | Startup fails with actionable `RuntimeError` |

The FastAPI lifespan now runs these checks before configuring Redis, billing, or agents. Any fatal
violations halt the process immediately so health probes never turn green with a misconfigured stack.

## Validation entrypoints

1. **Runtime:** importing `app.main` triggers the same validation, so `cd apps/api-service && hatch run serve`,
   `pytest`, and CI Gunicorn boots all share the guard.
2. **Operator console:** run `cd packages/starter_console && starter-console providers validate` (or
   `just validate-providers`). The command loads `.env.compose` and `apps/api-service/.env.local`,
   reuses the backend validator, and exits non-zero whenever billing is enabled but Stripe vars are
   missing—even in local/dev mode—to stay consistent with FastAPI startup. Pass `--strict` to treat
   Resend warnings as fatal as well.
3. **CI Jobs:** call the CLI with `--strict` prior to building containers to ensure the pipeline
   fails before Docker images, migrations, or deployment steps run.

The validator surfaces structured log output similar to:

```
[WARN][providers] [OPENAI] OPENAI_API_KEY is required for the agent runtime.
[WARN][providers] [RESEND] RESEND_EMAIL_ENABLED=true requires RESEND_API_KEY.
[ERROR][providers] [STRIPE] ENABLE_BILLING=true requires STRIPE_SECRET_KEY.
```

## Remediation checklist

1. Inspect `apps/api-service/.env.local` (or the secrets source for your deployed environment) and populate the
   missing variables listed in the error message.
2. Rerun `cd packages/starter_console && starter-console providers validate --strict` to confirm the issue is resolved.
3. Redeploy the backend only after the validator returns success.

### Provider-specific notes

- **OpenAI:** `OPENAI_API_KEY` is required for agent execution. Missing keys surface as warnings in local dev and fatal errors in hardened environments.
- **Stripe:** `docs/billing/stripe-setup.md` covers the provisioning workflow, plan map formats, and
  troubleshooting steps. The validator piggybacks on `Settings.required_stripe_envs_missing()` so
  a single `RuntimeError` lists every missing variable.
- **Resend:** Configure the API key and default From address in `apps/api-service/.env.local`. Template IDs remain
  optional, but populate them before production so transactional email matches approved copy.

## Tracking & reporting

- Issue tracker row: `docs/trackers/ISSUE_TRACKER.md#L54`.
- Detailed milestone log: `docs/trackers/OPS-003_THIRD_PARTY_ENV_PARITY.md`.
- Console reference: `starter_console/README.md` (Providers command section).
