# Stripe Developer Setup Script (STRIPE-02)

`python -m starter_cli.app stripe setup` is the interactive helper that bootstraps billing end-to-end for local development. It wraps the Stripe CLI, Docker/Postgres helpers, and the official Stripe Python SDK so you only need to provide your Stripe secrets and pick the monthly price for each plan (Starter + Pro). The command creates or reuses the corresponding Stripe products/prices with a 7-day trial and writes the resulting configuration into `apps/api-service/.env.local`.

## Prerequisites

- Python 3.11+ with access to the repository’s virtual environment (install with `pip install '.[dev]'` or `pip install stripe` at minimum).
- Stripe CLI installed (`stripe --version`). The assistant can open the guided auth page and run `stripe login --interactive` for you.
- Docker + `just` if you want the helper to launch the local Postgres stack via `just dev-up`.
- A Stripe account that can create API keys, webhook endpoints, products, and prices.

## Running the script

```bash
pnpm stripe:setup   # invokes python -m starter_cli.app stripe setup
```

### What happens during the run?

1. **Stripe CLI check** – Verifies installation/auth. If auth is missing it can open <https://dashboard.stripe.com/stripe-cli/auth> and run `stripe login --interactive` inline.
2. **Postgres helper** – Offers to run `just dev-up` and (optionally) executes a `psql` smoke test against your `DATABASE_URL` (discovered from `apps/api-service/.env.local`, `apps/api-service/.env`, `.env.compose`, or manual input).
3. **Stripe provisioning** – Prompts for `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the monthly price for each plan. Using the official Stripe SDK it:
   - creates (or updates) the `starter` and `pro` products,
   - ensures each product has a monthly price with a 7-day trial, and
   - records the resulting price IDs in `STRIPE_PRODUCT_PRICE_MAP`.
4. **Env writer** – Stores the secrets + JSON map inside `apps/api-service/.env.local` and flips `ENABLE_BILLING=true`. Existing values are detected so you can opt to keep them.

Sample output (abbreviated):

```
[INFO] Stripe SaaS setup assistant starting…
[SUCCESS] stripe version 1.18.3
[INFO] Start or refresh the local Postgres stack via `just dev-up`? (Y/n)
...
[SUCCESS] Configured Starter (USD 29.00) → price_1Qabcd...
[SUCCESS] Configured Pro (USD 79.00) → price_1Qefgh...
[SUCCESS] Stripe configuration captured in apps/api-service/.env.local
{
  "STRIPE_SECRET_KEY": "sk_test…1234",
  "STRIPE_WEBHOOK_SECRET": "whsec…abcd",
  "STRIPE_PRODUCT_PRICE_MAP": {
    "starter": "price_1Qabcd…",
    "pro": "price_1Qefgh…"
  },
  "ENABLE_BILLING": true
}
```

If a step fails (missing CLI, Docker unavailable, `psql` not installed, or Stripe API errors) the script prints a descriptive warning so you can resolve the issue before retrying.

## Relationship to STRIPE-01

The FastAPI startup guard (STRIPE-01) still requires `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRODUCT_PRICE_MAP` whenever `ENABLE_BILLING=true`. Running `pnpm stripe:setup` guarantees those values are present, validated, and tied to real Stripe products/prices.

## Extending the helper

- STRIPE-03/04/05 build on the same configuration; no additional Stripe setup is required once this script completes successfully.
- The script is intentionally idempotent: rerunning it reuses products/prices tagged with `metadata["starter_cli_plan_code"]` so you won’t accumulate duplicates.
- Contributions welcome—see `starter_cli/commands/stripe.py` for implementation details or to add additional plan types in the future.
