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
| STRIPE-02 | Developer Setup Script | `pnpm stripe:setup` verifies Stripe CLI auth, optionally runs `make dev-up`, checks Postgres/Redis, captures secrets into `.env.local`, and prints next steps; documented in `docs/scripts/stripe-setup.md`. | Completed | The helper now lives under `python -m starter_cli.app stripe setup`, provisioning Starter/Pro products + 7-day-trial prices via the Stripe SDK, recording `STRIPE_PRODUCT_PRICE_MAP`, and writing secrets into `.env.local`. |
| STRIPE-03 | Gateway Observability | `StripeGateway` emits structured logs + Prom metrics, surfaces domain-specific error codes, and maps plan codes via `stripe_product_price_map`; unit tests cover retries/idempotency. | Completed | Added gateway-level Prom counters/histograms, structured logging + error codes in `app/services/payment_gateway.py`, and metric helpers/tests so Stripe operations are observable end-to-end. |
| STRIPE-04 | Webhook → Domain Sync | `_dispatch_event` transforms subscription/invoice events into `BillingService` calls, updates Postgres, records usage deltas, and stores reconciliation metadata; replay CLI handles failed events. | Completed | Dispatcher now handles invoice/payment events, persists `subscription_invoices` + usage deltas via `BillingService.ingest_invoice_snapshot`, enriches Redis stream payloads with subscription/invoice snapshots, and the runbook documents dashboards/alerts for `stripe_gateway_operation_*` + `stripe_webhook_events_total{result="dispatch_failed"}`. |
| STRIPE-05 | Billing Stream Integration | Redis backend publishes normalized per-tenant events triggered by webhook state changes; `/api/v1/billing/stream` delivers keep-alive+payloads with contract/integration tests; frontend receives schema doc. | Completed | Redis publisher/backlog replay live, dispatcher retry worker + CLI polish shipped, Prom metrics (`stripe_dispatch_retry_total`, `stripe_billing_stream_*`) wired up, and the Billing Activity panel now renders subscription/invoice/usage sections validated by the new SSE integration test. |
| STRIPE-06 | Tests & Runbooks | Fixture-driven integration tests (`tests/integration/test_stripe_webhook.py`, new SSE tests) plus `docs/billing/stripe-runbook.md` covering replay, secret rotation, and alert response. | Completed | Added `make test-stripe`/`make stripe-replay` workflow, replay CLI integration test, billing stream unit coverage for metrics, and runbook/setup docs that spell out verification + recovery drills. |

## Execution Plan
1. **STRIPE-01 – Environment Guardrails**: Extend `app/core/config.py` and the FastAPI lifespan to validate `ENABLE_BILLING`, Stripe keys, and plan maps at startup, with troubleshooting guidance captured in `docs/billing/stripe-setup.md`.
2. **STRIPE-02 – Developer Setup Script**: Deliver the consolidated CLI command (`python -m starter_cli.app stripe setup`, aliased by `pnpm stripe:setup`) so new contributors can authenticate the Stripe CLI, launch Postgres/Redis, auto-provision Starter/Pro prices, and persist secrets into `.env.local` safely.
3. **STRIPE-03 – Gateway Observability**: Update `StripeGateway`/`StripeClient` to emit structured logs and Prometheus metrics, enforce centralized retries, and translate plan codes via `stripe_product_price_map`, backed by unit tests.
4. **STRIPE-04 – Webhook → Domain Sync**: Implement webhook orchestration that stores raw payloads, records processing metadata, and routes events through `BillingService` APIs plus replay tooling (CLI + persistence) without touching ORM models directly.
5. **STRIPE-05 – Billing Stream Integration**: Wire the Redis-backed publisher + backlog replay to `/api/v1/billing/stream`, document the `BillingEventPayload` schema, and ship automated dispatcher retries (worker + CLI polish) so alerts auto-heal.
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
