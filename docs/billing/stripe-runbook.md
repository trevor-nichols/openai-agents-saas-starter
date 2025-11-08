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
- `stripe_dispatch_retry_total{result}` – emits `success`/`failed` labels each time the retry worker replays a dispatch, confirming whether auto-heal is progressing.
- `stripe_billing_stream_events_total{source,result}` – counts webhook vs. replay publish attempts across outcomes (`published`, `replayed`, `failed`, `normalization_failed`, `skipped_*`).
- `stripe_billing_stream_backlog_seconds` – gauge showing how far the Redis bookmark trails real time; rises when the stream cannot keep pace.
- Structured logs emitted with `stripe_event_id`, `event_type`, and `tenant_hint` for correlation.
- `stripe_gateway_operation_*` histograms/counters back gateway calls (`start_subscription`, `record_usage`, etc.); dashboard panes group by `operation` + `plan_code`.
- The Prometheus `/metrics` endpoint exposes counters/histograms for API and webhook calls.
- Secret rotation bookmarks – document planned maintenance in the alert channel and follow the [Stripe Secret Rotation SOP](#stripe-secret-rotation-sop) so transient errors correlate with the expected cadence.

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
2. **SSE endpoint** – `curl -H "X-Tenant-Id: <tenant>" -H "X-Tenant-Role: owner" http://localhost:8000/api/v1/billing/stream` should return a continuous event stream (ping comments every 15s). Headers are optional but, when provided, must align with the tenant/role embedded in the JWT.
3. **Frontend panel** – the Agent dashboard displays subscription/invoice/usage cards from the stream payload. If it stalls, verify cookies include the tenant metadata and inspect browser devtools for SSE disconnects.
4. **Metrics** – monitor `stripe_webhook_events_total{result="dispatch_failed"}` plus `stripe_billing_stream_events_total{result="failed"}`/`stripe_billing_stream_backlog_seconds` to catch stuck fan-out or Redis lag.
5. **Automated suites** – run `make test-stripe` (fixture-driven webhook + SSE tests) and `make lint-stripe-fixtures` before pushing changes so replay tooling stays in sync.
6. **Secret rotations** – after updating Stripe credentials, work through the validation checklist in the [Stripe Secret Rotation SOP](#stripe-secret-rotation-sop) to confirm new keys and webhook signatures are live.

## Stripe Secret Rotation SOP

This standard operating procedure covers the two long-lived Stripe credentials used by the backend:

- `STRIPE_SECRET_KEY` (server-side API key)
- `STRIPE_WEBHOOK_SECRET` (signature validation secret for `/webhooks/stripe`)

### Cadence

- API key: rotate at least every 90 days, or immediately after a suspected compromise or whenever Stripe flags the key.
- Webhook secret: rotate monthly (Stripe CLI frequently issues new secrets) and whenever the webhook endpoint is recreated or moved.

### Pre-rotation checklist

1. Announce the maintenance window in the ops channel and confirm no ongoing billing incidents.
2. Ensure you can restart the FastAPI app (or redeploy) within the window.
3. Have access to the Stripe Dashboard (Developers → API keys / Webhooks) and this repo’s secrets store (`.env`, Vault, or deployment-specific manager).
4. Open `docs/billing/stripe-setup.md` for reference on required env vars.

### Rotation steps – API key (`STRIPE_SECRET_KEY`)

1. In the Stripe Dashboard, create a **new restricted secret key** with the same permissions as the current one.
2. Update the key in your secret manager (`.env.local`, Vault, Kubernetes secret, etc.) **without deleting** the previous value yet.
3. Deploy/restart the FastAPI app so the new key is loaded; verify startup logs show the masked key prefix/suffix you expect.
4. Run `make test-stripe` against a staging environment to exercise subscription creation and usage recording with the new key.
5. Once satisfied, delete or revoke the old key in Stripe to prevent reuse.

### Rotation steps – Webhook secret (`STRIPE_WEBHOOK_SECRET`)

1. For local dev, rerun `stripe listen --forward-to http://localhost:8000/webhooks/stripe` to generate a new `whsec_...` secret. For hosted environments, open Stripe Dashboard → Developers → Webhooks → your endpoint → **Reveal secret** and click **Rotate secret**.
2. Update the secret manager and redeploy/restart the API so the new secret is active.
3. Send a test webhook (`stripe trigger invoice.payment_succeeded` or use the dashboard) and confirm `/webhooks/stripe` returns HTTP 202.
4. Watch `stripe_webhook_events_total{result="invalid_signature"}`—spikes after the rotation mean a consumer is still sending the old signature; update all webhook senders before deleting the prior secret in Stripe.

### Validation

- Execute `make test-stripe` (or the CI workflow) and ensure both the webhook ingestion test and SSE test pass.
- Tail the application logs for `Stripe billing configuration validated` and confirm no `dispatch_failed` or `stream_failed` entries appear within five minutes of the rotation.
- Check Prometheus: `stripe_gateway_operations_total{result!="success"}` should remain flat, and `stripe_webhook_events_total{result="invalid_signature"}` should be zero.
- Confirm the frontend Billing Activity panel resumes streaming data for at least one tenant.

### Rollback

1. Keep the previous secrets until validation is complete. If issues arise, revert the env values to the prior key/secret and redeploy.
2. Re-run `make test-stripe` to confirm the rollback restored functionality.
3. Investigate the failed rotation (typically a missed redeploy or stale secret store) before attempting again. Document the incident in the ops log.


## Dispatcher Retry Worker

- **Service** – `StripeDispatchRetryWorker` lives in `app/services/stripe_retry_worker.py`. Enable it per-process via `ENABLE_BILLING_RETRY_WORKER=true`. For multi-pod deployments, run exactly one instance with the flag on.
- **Dependencies** – reuses the configured `StripeEventRepository` + `StripeEventDispatcher`; no extra queues required.
- **Behaviour** – polls every 30s, pulls failed dispatch rows whose `next_retry_at` has passed, and calls `dispatcher.replay_dispatch()` so the normal bookkeeping runs (status -> `completed`/`failed`, metrics, billing stream publish).
- **Backoff** – dispatcher failures schedule retries with exponential backoff (30s to 10m). When the root cause persists, rows remain `failed` and alerts stay firing; use the CLI to inspect or force replay with `--yes`.

## Billing Stream Replay Worker

- **Purpose** – On startup the API replays previously processed Stripe events into Redis so new subscribers catch up before receiving live SSE updates.
- **Toggle** – Controlled by `ENABLE_BILLING_STREAM_REPLAY` (defaults to true). Disable this flag on secondary API replicas to avoid duplicate replays; keep it enabled on the worker pod that owns the Redis channel.
- **Failure modes** – If replay is disabled everywhere, newly scaled pods will not backfill historical events—document this expectation for frontend dashboards.

## Rate Limiting & Abuse Controls

- `/api/v1/billing/stream` enforces Redis-backed quotas. Each tenant may initiate at most `BILLING_STREAM_RATE_LIMIT_PER_MINUTE` new subscriptions per minute and hold `BILLING_STREAM_CONCURRENT_LIMIT` simultaneous connections. Defaults ship in `.env.local.example` and can be tuned per environment.
- Exceeding either threshold results in HTTP 429 + `Retry-After` along with structured `rate_limit.block` logs and the Prometheus counter `rate_limit_hits_total{quota="billing_stream_*"}`. Tenants can self-retry after the indicated back-off; operators should avoid manual resets unless absolutely necessary.
- To unblock a tenant manually, remove Redis keys prefixed with `${RATE_LIMIT_KEY_PREFIX}:quota:billing_stream_*:<tenant_id>` (for bursts) or `${RATE_LIMIT_KEY_PREFIX}:concurrency:billing_stream_concurrency:<tenant_id>` (for stuck sockets). Capture the key name, tenant id, and rationale in the incident log before clearing counters.

## Dashboards & Alerts

| Check | Query / Threshold | Notes |
| --- | --- | --- |
| Dispatch failures | `sum(rate(stripe_webhook_events_total{result="dispatch_failed"}[5m])) > 0` | Page on sustained dispatcher failures. Include event type label in alert annotations. |
| Gateway regressions | `sum(rate(stripe_gateway_operations_total{operation="record_usage",result!="success"}[5m]))` | Tracks upstream API issues per operation/plan. Feed into Grafana table grouped by `result`. |
| Streaming backlog | `stripe_billing_stream_backlog_seconds > 120` or sustained `stripe_billing_stream_events_total{result="failed"}` | Alert when bookmark lag > 2m; correlate with Redis health checks and dispatcher retry logs. |
| Retry worker | `increase(stripe_dispatch_retry_total{result="failed"}[5m]) > 0` | Fire when the worker cannot auto-heal dispatch rows; pair with CLI replay to unblock tenants. |

Dashboards should chart:

1. Dispatcher throughput vs. failures (stacked area using `stripe_webhook_events_total`).
2. Gateway latency per operation (`stripe_gateway_operation_duration_seconds_bucket`).
3. Redis SSE freshness – bookmark timestamp vs. `now()`, plus consumer error logs.
4. Billing stream payload schema (subscription/invoice panels) so operators can visually confirm normalized snapshots per tenant during incidents.

## TODOs / Open Items

- Build Grafana dashboard panels for the billing stream payload (subscription vs. invoice vs. usage) to visualize tenant activity.
- Evaluate dedicated worker process vs. in-app task once STRIPE-05 streaming load tests complete.
