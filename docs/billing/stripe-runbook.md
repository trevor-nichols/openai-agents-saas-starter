# Stripe Billing Runbook

This document outlines the operator workflows for receiving, inspecting, and replaying Stripe webhook events in the `anything-agents` backend.

## Event Intake

- Endpoint: `POST /webhooks/stripe` (non-versioned FastAPI route).
- Authentication: Stripe signature verification using `STRIPE_WEBHOOK_SECRET`.
- Storage: Every event (handled or not) is persisted in the `stripe_events` table with its raw payload, tenant hint, timestamps, and processing outcome.
- Streaming: When `ENABLE_BILLING_STREAM=true`, processed events are normalized and pushed over Redis pub/sub so `/api/v1/billing/stream` (and the frontend dashboard) can reflect status changes in real time.

### Metrics & Logs

- `stripe_webhook_events_total{event_type,result}` – count of accepted/duplicate/failed events.
- Structured logs emitted with `stripe_event_id`, `event_type`, and `tenant_hint` for correlation.
- The Prometheus `/metrics` endpoint exposes counters/histograms for API and webhook calls.

## Replay & Recovery

1. Locate failures:
   ```sql
   select stripe_event_id, event_type, processing_error
   from stripe_events
   where processing_outcome = 'failed'
   order by received_at desc;
   ```
2. Determine remediation: fix downstream issue (e.g., database constraint, missing tenant), then use the replay CLI to reprocess the event(s):

   ```bash
   # List failed events
   make stripe-replay ARGS="list --status failed"

   # Dry-run a specific replay
   make stripe-replay ARGS="replay --event-id evt_123 --dry-run"

   # Replay everything currently failed back into the local webhook
   make stripe-replay ARGS="replay --status failed --limit 10"
   ```

   The CLI reads `.env.local` for `DATABASE_URL` and `STRIPE_WEBHOOK_SECRET`, signs each stored payload, and POSTs to `/webhooks/stripe`. Use `--webhook-url` to target staging/production.

3. Update status: once the replay succeeds the repository marks the event as `processed`. If manual intervention is required, annotate incident notes and reference the `stripe_event_id` for auditability.

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
4. **Metrics** – monitor `stripe_webhook_events_total{result="broadcast_failed"}` for spikes.

## TODOs / Open Items

- Integrate specific event handlers (subscription sync, invoice state machine) once STRIPE-05+ lands.
- Expand observability with dashboards/alerts keyed off `stripe_webhook_events_total`.
