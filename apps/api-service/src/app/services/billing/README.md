# Billing Domain

Tenant subscription orchestration, usage metering, Stripe connectivity, and the developer-facing event stream used by the web app. The services in this folder hide the payment processor behind a `PaymentGateway` protocol and persist normalized state in Postgres.

## What lives here
- `billing_service.py` — core facade for plans, subscriptions, usage, and invoice ingestion. It uses a `BillingRepository` (Postgres in `infrastructure/persistence/billing/postgres.py`) plus a `PaymentGateway` (Stripe by default).
- `payment_gateway.py` — gateway protocol + Stripe implementation. Handles customer/subscription provisioning, usage recording, and error mapping with metrics.
- `billing_events/` — normalizes processed Stripe events and broadcasts them per-tenant:
  - `normalizer.py` → converts raw Stripe payloads into concise `BillingEventPayload`s.
  - `publisher.py` → emits events to a `BillingEventBackend` (Redis streams) and logs activity.
  - `history.py` → pages through persisted Stripe events for the `/billing/events` API.
  - `service.py` → coordinates publisher + history reader, with `subscribe()` for live streams.
- `stripe/dispatcher.py` — runs Stripe webhook events through handlers that sync subscriptions/invoices back into our domain (`BillingService`), then hands a broadcast context to `billing_events`.
- `stripe/retry_worker.py` — background loop that replays failed dispatch attempts.
- `stripe/event_models.py` — small dataclasses shared across dispatcher + billing events.

## Data + persistence
- Postgres tables defined in `infrastructure/persistence/billing/models.py`:
  - `billing_plans` + `plan_features` — plan catalog with feature toggles and metering hints.
  - `billing_customers` — Stripe customer linkage for pre-subscription payment methods.
  - `tenant_subscriptions` — current subscription state with processor IDs and metadata.
  - `subscription_usage` — metered usage records (idempotent via external event keys).
  - `subscription_invoices` — invoice snapshots tied to subscriptions.
- Repository: `PostgresBillingRepository` maps the domain types and enforces UUID tenant IDs.

## Runtime flows
- **Plan catalog**: `BillingService.list_plans()` reads the plan table; plan ↔ Stripe price mapping is provided via `STRIPE_PRODUCT_PRICE_MAP`.
- **Start/update/cancel subscription**: `BillingService` calls the gateway (`StripeGateway`) to mutate Stripe, then persists the normalized subscription locally. Validation errors become domain-specific exceptions that translate to HTTP 4xx.
- **Billing customer**: `BillingService` can create a Stripe customer before subscription start, storing the customer ID in `billing_customers` for payment method + portal operations.
- **Usage recording**: `BillingService.record_usage()` posts usage to Stripe (metered subscription item) and records the same usage row in Postgres with idempotency support.
- **Payment methods + portal**: `BillingService` requests portal sessions, setup intents, and payment method updates via the gateway and keeps customer metadata in Postgres.
- **Upcoming invoice preview**: `BillingService.preview_upcoming_invoice()` asks Stripe for an invoice preview with optional seat overrides, returning plan names from the local catalog.
- **Processor sync (webhooks)**:
  1) Stripe webhook payloads are stored under `infrastructure/persistence/stripe`.
  2) `stripe/dispatcher.py` pulls stored events, builds processor snapshots, and invokes:
     - `sync_subscription_from_processor(...)` for subscription lifecycle changes.
     - `ingest_invoice_snapshot(...)` for invoice + usage deltas.
  3) The dispatcher returns a broadcast context that `billing_events/publisher.py` turns into tenant-scoped events (Redis stream) and activity log entries.
  4) `stripe/retry_worker.py` periodically replays failed dispatch rows.
- **Event history/stream**:
  - `/api/v1/billing/tenants/{tenant_id}/events` paginates normalized history via `BillingEventHistoryReader`.
  - `/api/v1/billing/stream` exposes a tenant-scoped SSE feed backed by Redis streams (`RedisBillingEventBackend`), with replay-on-startup support.

## API surface (FastAPI `api/v1/billing/router.py`)
- `GET /billing/plans` — list available plans.
- `GET /billing/tenants/{tenant_id}/subscription` — fetch current subscription.
- `POST /billing/tenants/{tenant_id}/subscription` — start a subscription (owner/admin only).
- `PATCH /billing/tenants/{tenant_id}/subscription` — update auto-renew, seats, billing email.
- `POST /billing/tenants/{tenant_id}/subscription/plan` — change plan immediately or at period end.
- `POST /billing/tenants/{tenant_id}/subscription/cancel` — cancel now or at period end.
- `POST /billing/tenants/{tenant_id}/portal` — create a Stripe billing portal session.
- `GET /billing/tenants/{tenant_id}/payment-methods` — list saved payment methods.
- `POST /billing/tenants/{tenant_id}/payment-methods/setup-intent` — create a setup intent for new payment methods.
- `POST /billing/tenants/{tenant_id}/payment-methods/{payment_method_id}/default` — set default payment method.
- `DELETE /billing/tenants/{tenant_id}/payment-methods/{payment_method_id}` — detach a payment method.
- `POST /billing/tenants/{tenant_id}/upcoming-invoice` — preview next invoice totals (viewer allowed).
- `POST /billing/tenants/{tenant_id}/usage` — record metered usage (idempotent key optional).
- `GET /billing/tenants/{tenant_id}/events` — paginated Stripe event history.
- `GET /billing/stream` — SSE stream of normalized billing events (requires `enable_billing_stream`).

## Configuration knobs (env)
- `STRIPE_SECRET_KEY` — required for gateway calls.
- `STRIPE_WEBHOOK_SECRET` — verifies incoming webhooks (handled in the webhook router).
- `STRIPE_PRODUCT_PRICE_MAP` — plan-code → price-id mapping (JSON or `starter=price_123,...`).
- `STRIPE_PORTAL_RETURN_URL` — override the return URL used for Stripe billing portal sessions.
- `BILLING_EVENTS_REDIS_URL` — optional Redis URL for billing streams (falls back to `REDIS_URL`).
- `ENABLE_BILLING_STREAM` — toggles live event streaming; `ENABLE_BILLING_STREAM_REPLAY` replays stored events into Redis on startup.
- `ENABLE_BILLING_RETRY_WORKER` — runs the dispatcher retry loop in-process; `BILLING_RETRY_DEPLOYMENT_MODE` is a doc string for ops (inline/dedicated).

## Developer notes
- Stripe event handling is idempotent: dispatcher tracks per-event dispatch rows; usage/invoice upserts guard via idempotency keys.
- Tenant IDs must be UUIDs at the persistence layer; non-UUIDs are treated as missing to avoid 500s.
- When changing plan codes or adding features, update both the database seed/migration and `STRIPE_PRODUCT_PRICE_MAP`.
- The billing stream is optional but powers the UI’s live billing timeline; ensure Redis is available if enabled.
