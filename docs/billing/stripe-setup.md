# Stripe Setup (STRIPE-01)

This guide explains the minimum configuration required to turn on billing with Stripe in the `anything-agents` backend. The gateway, webhooks, and automation (STRIPE-02+) are still under active development, but the settings below must already be in place so the service can boot safely when `ENABLE_BILLING=true`.

## Prerequisites

1. **Durable storage** – Billing requires Postgres. Ensure `USE_IN_MEMORY_REPO=false` and provide a valid `DATABASE_URL`. The Docker helper `make dev-up` launches Postgres + Redis with the correct defaults sourced from `.env.compose` and your `.env.local`.
2. **Stripe account access** – You need permission to view the project in the Stripe Dashboard so you can create products/prices and view API/webhook keys.
3. **Local env files** – Never commit secrets. Copy `.env.example` to `.env.local` and keep your Stripe credentials there (gitignored).

## Required environment variables

| Variable | Description | Where to find it |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | Server-side API key (starts with `sk_live_` or `sk_test_`). | Stripe Dashboard → Developers → API keys. |
| `STRIPE_WEBHOOK_SECRET` | Signing secret used to verify Stripe webhooks (starts with `whsec_`). | Stripe Dashboard → Developers → Webhooks (or `stripe listen --print-secret`). |
| `STRIPE_PRODUCT_PRICE_MAP` | Mapping of billing plan codes (e.g., `starter`, `pro`) to Stripe price IDs. Accepts JSON or comma-delimited `plan=price` pairs. | Create products/prices in Stripe, copy the resulting `price_...` identifiers. |

Add the variables plus the existing toggles to `.env.local`:

```env
USE_IN_MEMORY_REPO=false
ENABLE_BILLING=true
STRIPE_SECRET_KEY=sk_test_your_project_key
STRIPE_WEBHOOK_SECRET=whsec_your_signing_secret
# JSON and comma-delimited formats are both accepted
STRIPE_PRODUCT_PRICE_MAP={"starter":"price_starter","pro":"price_pro"}
```

> ⚠️ **Secrets stay local** – Do not reuse the placeholder values from `.env.example`, do not commit real keys, and avoid exporting them in your shell history. The backend now fails fast if these values are missing while billing is enabled, so empty strings will not bypass the guard.

## Enabling billing end-to-end

1. Populate the variables above in `.env.local`.
2. Ensure Postgres is running (`make dev-up`) and run migrations (`make migrate`).
3. Flip `ENABLE_BILLING=true` and restart the FastAPI server (`hatch run serve` or your preferred process manager).
4. On startup the app verifies that Stripe settings are present before wiring the billing repository. Misconfigurations surface immediately with an error that lists the missing env vars.

## Upcoming automation

STRIPE-02 introduces `scripts/stripe/setup.ts`, an interactive helper that will walk developers through Stripe CLI auth, test data creation, and `.env.local` updates. That script is **coming soon**; until it lands you must enter the keys manually following the steps above.
