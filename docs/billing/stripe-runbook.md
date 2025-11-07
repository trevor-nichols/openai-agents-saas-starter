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
2. Determine remediation: fix downstream issue (e.g., database constraint, missing tenant), then replay by posting the stored payload back into `/webhooks/stripe` with the original signature removed (set `STRIPE_WEBHOOK_SECRET` in curl and recompute). A future CLI helper will automate this replay.
3. Update status: once the replay succeeds the repository marks the event as `processed`. If manual intervention is required, annotate incident notes and reference the `stripe_event_id` for auditability.

## Local Testing

- Use `stripe listen --forward-to http://localhost:8000/webhooks/stripe` to mirror live/test events.
- Sample webhook invocation:
  ```bash
  stripe trigger customer.subscription.created \
    --override '{"customer":"{{CUSTOMER_ID}}","metadata":{"tenant_id":"default"}}'
  ```
- Inspect stored events via `psql` or any SQL client pointed at the Postgres instance started by `make dev-up`.

## TODOs / Open Items

- Automate event replay via CLI helper (future STRIPE-06 scope).
- Integrate specific event handlers (subscription sync, invoice state machine) once STRIPE-05+ lands.
- Expand observability with dashboards/alerts keyed off `stripe_webhook_events_total`.
