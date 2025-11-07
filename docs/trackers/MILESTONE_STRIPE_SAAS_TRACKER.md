# Milestone: Stripe SaaS Enablement

## Objective
- Wire the existing Stripe gateway, webhook intake, and Redis stream into a cohesive SaaS billing loop that keeps Postgres subscriptions, usage, and tenant notifications in sync with Stripe events.
- Ship developer ergonomics (env guards, setup script, fixtures) so anyone can spin up billing locally without hand-editing secrets.
- Provide the operational visibility (metrics, replay tooling, docs) needed to debug billing flows before promoting the starter to production environments.

## Scope
- **In**: Stripe config validation, developer onboarding script, webhook → domain orchestration, Redis/SSE billing stream, observability/tests/runbooks.
- **Out**: Non-Stripe gateways, external analytics, full pricing UX (owned by frontend milestone), production Stripe account provisioning.

## Architecture Guardrails
1. BillingService remains the single writer to `TenantSubscription`/usage tables; webhook handlers call service methods instead of touching ORM models directly.
2. StripeClient centralizes retries/metrics; higher layers only translate domain errors and do not duplicate retry logic.
3. Redis stream payloads are normalized `BillingEventPayload` objects so the frontend sees stable schemas regardless of Stripe event noise.
4. Env validation happens during FastAPI lifespan start; missing Stripe keys or plan maps fail fast with actionable error messages.
5. Every webhook path persists the raw Stripe payload before processing and records success/failure timestamps for replay.

## Work Breakdown

| ID | Area | Exit Criteria | Status | Notes |
|----|------|---------------|--------|-------|
| STRIPE-01 | Configuration Guardrails | `ENABLE_BILLING` startup hook enforces `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRODUCT_PRICE_MAP`, and logs masked summaries; docs updated with troubleshooting matrix. | Completed | FastAPI lifespan now fails fast when Stripe envs are missing and logs masked `stripe_config` summaries; troubleshooting matrix captured in `docs/billing/stripe-setup.md`. |
| STRIPE-02 | Developer Setup Script | `pnpm stripe:setup` verifies Stripe CLI auth, optionally runs `make dev-up`, checks Postgres/Redis, captures secrets into `.env.local`, and prints next steps; documented in `docs/scripts/stripe-setup.md`. | Completed | Replaced the TS helper with `scripts/stripe/setup.py` (Python). It provisions Starter/Pro products + 7-day-trial prices via the Stripe SDK, records the resulting `STRIPE_PRODUCT_PRICE_MAP`, and writes secrets into `.env.local`. |
| STRIPE-03 | Gateway Observability | `StripeGateway` emits structured logs + Prom metrics, surfaces domain-specific error codes, and maps plan codes via `stripe_product_price_map`; unit tests cover retries/idempotency. | Not Started | Update `app/services/payment_gateway.py`, `app/infrastructure/stripe/client.py`, `app/observability/metrics.py`. |
| STRIPE-04 | Webhook → Domain Sync | `_dispatch_event` transforms subscription/invoice events into `BillingService` calls, updates Postgres, records usage deltas, and stores reconciliation metadata; replay CLI handles failed events. | Not Started | Touches `app/presentation/webhooks/stripe.py`, `app/services/billing_service.py`, new CLI/replay helpers, migrations if new tables needed. |
| STRIPE-05 | Billing Stream Integration | Redis backend publishes normalized per-tenant events triggered by webhook state changes; `/api/v1/billing/stream` delivers keep-alive+payloads with contract/integration tests; frontend receives schema doc. | Not Started | Update `app/services/billing_events.py`, `app/api/v1/billing/router.py`, add tests + docs. |
| STRIPE-06 | Tests & Runbooks | Fixture-driven integration tests (`tests/integration/test_stripe_webhook.py`, new SSE tests) plus `docs/billing/stripe-runbook.md` covering replay, secret rotation, and alert response. | Not Started | Also adds CI targets (`make test-stripe`, `make stripe-replay`). |

## Execution Plan
1. **STRIPE-01 – Environment Guardrails**: Extend `app/core/config.py` and the FastAPI lifespan to validate `ENABLE_BILLING`, Stripe keys, and plan maps at startup, with troubleshooting guidance captured in `docs/billing/stripe-setup.md`.
2. **STRIPE-02 – Developer Setup Script**: Deliver the Python-based `scripts/stripe/setup.py` plus the `pnpm stripe:setup` command so new contributors can authenticate the Stripe CLI, launch Postgres/Redis, auto-provision Starter/Pro prices, and persist secrets into `.env.local` safely.
3. **STRIPE-03 – Gateway Observability**: Update `StripeGateway`/`StripeClient` to emit structured logs and Prometheus metrics, enforce centralized retries, and translate plan codes via `stripe_product_price_map`, backed by unit tests.
4. **STRIPE-04 – Webhook → Domain Sync**: Implement webhook orchestration that stores raw payloads, records processing metadata, and routes events through `BillingService` APIs plus replay tooling (CLI + persistence) without touching ORM models directly.
5. **STRIPE-05 – Billing Stream Integration**: Finish the Redis-backed publisher and `/api/v1/billing/stream` SSE endpoint so normalized `BillingEventPayload` messages reach tenants with keep-alives, schema docs, and contract/integration tests.
6. **STRIPE-06 – Tests & Runbooks**: Add fixture-driven integration suites (webhook ingestion, SSE), convenience Make targets, and `docs/billing/stripe-runbook.md` covering replay, secret rotation, and operational debugging.

## Risks & Mitigations
- **Webhook fan-out lag**: If Redis or Postgres is slow, events could back up. Mitigation: add retry/backoff with Prometheus alerts on backlog depth.
- **Fixture drift**: Stripe payloads evolve; keep fixtures versioned and linted in CI so replay stays reliable.
- **Secrets mishandling**: Setup script must never print raw keys; redact logs and guard `.env.local` permissions.

## Acceptance Criteria
1. Starting the FastAPI app with `ENABLE_BILLING=true` and missing Stripe envs fails with a descriptive error referencing the milestone docs.
2. Triggering `customer.subscription.updated` via replay updates `TenantSubscription` rows, emits a Redis event, and surfaces metrics/log entries.
3. `pnpm stripe:setup` gets a new developer from zero to working billing config (verified in README walkthrough).
4. CI has a `make test-stripe` job covering webhook ingestion, replay, and SSE publishing with fixtures.
5. Runbook details how to inspect stored Stripe events, reprocess failures, rotate webhook secrets, and validate Redis stream consumers.

## Dependencies
- Postgres migrations for billing tables already exist (`20251106_120000` and follow-ups); reuse them.
- Redis required when `ENABLE_BILLING_STREAM=true`; document fallback behavior when disabled.
- OpenAI Agent SDK integration work is complete and unaffected but should be regression-tested after billing changes.

## Reporting
- Update `docs/trackers/ISSUE_TRACKER.md` after each STRIPE-0X item lands so progress stays auditable.
- Log operational learnings or edge cases in `docs/billing/stripe-runbook.md` as they surface.
