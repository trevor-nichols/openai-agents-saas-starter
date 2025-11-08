# Stripe Billing Runbook

This document outlines the operator workflows for receiving, inspecting, and replaying Stripe webhook events in the `anything-agents` backend.

## Event Intake

- Endpoint: `POST /webhooks/stripe` (non-versioned FastAPI route).
- Authentication: Stripe signature verification using `STRIPE_WEBHOOK_SECRET`.
- Storage: Every event (handled or not) is persisted in the `stripe_events` table with its raw payload, tenant hint, timestamps, and processing outcome.
- Dispatching: The webhook now fans out via `StripeEventDispatcher`, which (a) syncs subscription snapshots through `BillingService`, (b) ingests invoice/payment events into `subscription_invoices` + metered usage tables, and (c) records per-handler dispatch rows for replay.
- Streaming: When `ENABLE_BILLING_STREAM=true`, dispatcher outcomes (subscription snapshots, invoice metadata, usage deltas) are normalized and pushed over Redis so `/api/v1/billing/stream` and the frontend dashboard stay in sync without hitting Postgres.

### Metrics & Logs

- `stripe_webhook_events_total{event_type,result}` – count of accepted/duplicate/failed/dispatched events.
- `stripe_webhook_events_total{result="dispatch_failed"}` – primary alert for dispatcher regressions (firing when >0 for 5 minutes).
- Structured logs emitted with `stripe_event_id`, `event_type`, and `tenant_hint` for correlation.
- `stripe_gateway_operation_*` histograms/counters back gateway calls (`start_subscription`, `record_usage`, etc.); dashboard panes group by `operation` + `plan_code`.
- The Prometheus `/metrics` endpoint exposes counters/histograms for API and webhook calls.

## Replay & Recovery

1. Locate failures:
   ```sql
   select d.id as dispatch_id,
          e.stripe_event_id,
          e.event_type,
          d.last_error,
          d.attempts
   from stripe_event_dispatch d
   join stripe_events e on e.id = d.stripe_event_id
   where d.status = 'failed'
   order by d.created_at desc;
   ```
2. Determine remediation: fix downstream issues (e.g., tenant metadata, plan mismatches), then use the replay CLI to reset and re-run dispatches. The CLI now supports pagination for `list` and asks for confirmation before replaying multiple dispatches (override with `--yes`):

   ```bash
   # List failed dispatches for the billing_sync handler (page 2)
   make stripe-replay ARGS="list --handler billing_sync --status failed --page 2"

   # Replay a specific dispatch UUID
   make stripe-replay ARGS="replay --dispatch-id 7ad7c7bc-..."

   # Replay everything currently failed (limit 10, auto-confirm)
   make stripe-replay ARGS="replay --status failed --limit 10 --yes"

   # Replay based on Stripe event ids (dispatch rows are created automatically)
   make stripe-replay ARGS="replay --event-id evt_123 --event-id evt_456"
   ```

   The CLI now talks directly to Postgres: it resets the `stripe_event_dispatch` rows to `pending`, invokes the dispatcher in-process, and updates the parent `stripe_events` row—no webhook POSTs required.

3. Update status: once the replay succeeds the dispatch row flips to `completed` and the parent entry returns to `processed`. Capture the `dispatch_id` + `stripe_event_id` in incident notes to keep the audit trail intact.

4. Automatic retries: the `StripeDispatchRetryWorker` polls for failed dispatch rows whose `next_retry_at` has elapsed and replays them automatically. Alerts on `stripe_webhook_events_total{result="dispatch_failed"}` clear as soon as the worker reprocesses the backlog; consult logs with `dispatch_id` metadata for any rows that continue to fail after exponential backoff (30s → 1m → 2m → 4m → 8m, capped at 10m).

## Billing Stream Payload Schema

Normalized `BillingEventPayload` messages delivered over `/api/v1/billing/stream` follow this schema:

```json
{
  "tenant_id": "tenant-123",
  "event_type": "invoice.payment_succeeded",
  "stripe_event_id": "evt_...",
  "occurred_at": "2025-11-07T00:00:00Z",
  "summary": "Invoice paid",
  "status": "paid",
  "subscription": {
    "plan_code": "starter",
    "status": "active",
    "seat_count": 5,
    "auto_renew": true,
    "current_period_start": "2025-11-01T00:00:00Z",
    "current_period_end": "2025-12-01T00:00:00Z",
    "trial_ends_at": null,
    "cancel_at": null
  },
  "invoice": {
    "invoice_id": "in_123",
    "status": "paid",
    "amount_due_cents": 2500,
    "currency": "usd",
    "billing_reason": "subscription_cycle",
    "hosted_invoice_url": "https://...",
    "collection_method": "charge_automatically",
    "period_start": "2025-11-01T00:00:00Z",
    "period_end": "2025-12-01T00:00:00Z"
  },
  "usage": [
    {
      "feature_key": "messages",
      "quantity": 1200,
      "period_start": "2025-10-31T00:00:00Z",
      "period_end": "2025-11-30T23:59:59Z",
      "amount_cents": 600
    }
  ]
}
```

- **Backlog handling** – `BillingEventsService` replays `StripeEvent` records processed after the last Redis bookmark during FastAPI startup, then streams new ones via Redis `XADD`. Consumers receive historic events before live ones.
- **Keep-alives** – the SSE endpoint sends `: ping` comments every 15 seconds while idle so browsers keep the socket open.
- **Redis durability** – stream entries retain for 24h (`stream_ttl_seconds`) and cap at 1024 entries per tenant by default; tune via `BillingEventsService` configuration if needed.

## Local Testing

- Use `stripe listen --forward-to http://localhost:8000/webhooks/stripe` to mirror live/test events.
- Sample webhook invocation:
  ```bash
  stripe trigger customer.subscription.created \
    --override '{"customer":"{{CUSTOMER_ID}}","metadata":{"tenant_id":"default"}}'
  ```
- Inspect stored events via `psql` or any SQL client pointed at the Postgres instance started by `make dev-up`.
- Validate fixture coverage locally:
  ```bash
  make lint-stripe-fixtures
  make test-stripe
  ```

## Streaming Health Checks

1. **Redis** – `make dev-up` already launches Redis. Inspect `billing:events:last_processed_at` via `redis-cli` to ensure bookmarks advance.
2. **SSE endpoint** – `curl -H "X-Tenant-Id: <tenant>" -H "X-Tenant-Role: owner" http://localhost:8000/api/v1/billing/stream` should return a continuous event stream (ping comments every 15s).
3. **Frontend panel** – the Agent dashboard displays the live Billing Activity list. If it stalls, verify cookies include the tenant metadata and inspect browser devtools for SSE disconnects.
4. **Metrics** – monitor `stripe_webhook_events_total{result="dispatch_failed"}` to catch domain sync issues and `stripe_webhook_events_total{result="broadcast_failed"}` for SSE fan-out regressions.

## Dispatcher Retry Worker

- **Service** – `StripeDispatchRetryWorker` lives in `app/services/stripe_retry_worker.py` and starts automatically when `ENABLE_BILLING=true`.
- **Dependencies** – reuses the configured `StripeEventRepository` + `StripeEventDispatcher`; no extra queues required.
- **Behaviour** – polls every 30s, pulls failed dispatch rows whose `next_retry_at` has passed, and calls `dispatcher.replay_dispatch()` so the normal bookkeeping runs (status -> `completed`/`failed`, metrics, billing stream publish).
- **Backoff** – dispatcher failures schedule retries with exponential backoff (30s to 10m). When the root cause persists, rows remain `failed` and alerts stay firing; use the CLI to inspect or force replay with `--yes`.

## Dashboards & Alerts

| Check | Query / Threshold | Notes |
| --- | --- | --- |
| Dispatch failures | `sum(rate(stripe_webhook_events_total{result="dispatch_failed"}[5m])) > 0` | Page on sustained dispatcher failures. Include event type label in alert annotations. |
| Gateway regressions | `sum(rate(stripe_gateway_operations_total{operation="record_usage",result!="success"}[5m]))` | Tracks upstream API issues per operation/plan. Feed into Grafana table grouped by `result`. |
| Streaming backlog | `stripe_webhook_events_total{result="broadcast_failed"}` + Redis TTL (`billing:events:last_processed_at`) lag | Alert when bookmark lag > 2m; if Redis is healthy but SSE consumers lag, inspect worker logs for retry churn. |

Dashboards should chart:

1. Dispatcher throughput vs. failures (stacked area using `stripe_webhook_events_total`).
2. Gateway latency per operation (`stripe_gateway_operation_duration_seconds_bucket`).
3. Redis SSE freshness – bookmark timestamp vs. `now()`, plus consumer error logs.
4. Billing stream payload schema (subscription/invoice panels) so operators can visually confirm normalized snapshots per tenant during incidents.

## TODOs / Open Items

- Build Grafana dashboard panels for the billing stream payload (subscription vs. invoice vs. usage) to visualize tenant activity.
- Evaluate dedicated worker process vs. in-app task once STRIPE-05 streaming load tests complete.
