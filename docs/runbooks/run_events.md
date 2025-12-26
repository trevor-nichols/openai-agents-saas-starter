# Run Events (Full-Fidelity History) Runbook

## What is covered
- Projection of SDK run items into `agent_run_events`.
- Serving conversation events via `/conversations/{id}/events` (transcript/full modes).
- Retention and cleanup.

## Key metrics
- `agent_run_events_projection_total{result}` — success/error/conflict counts.
- `agent_run_events_projection_duration_seconds` — ingest latency; target P95 < 5s.
- `agent_run_events_read_total{mode,result}` — read attempts by mode.
- `agent_run_events_read_duration_seconds` — read latency; target P95 < 2s.
- `agent_run_events_drift{conversation_id}` — sdk_message_count minus event_log_count (non-zero indicates mismatch).

## Common alerts (example rules in docs/ops/alerts/run_events.prom.yml)
- Projection errors high.
- Projection conflicts rising.
- Projection/read latency above SLO.
- Drift detected.

## How to respond
- Projection errors/conflicts: check api-service logs around inserts; confirm `response_id`/`sequence_no` inputs; look for IntegrityErrors.
- Latency: inspect DB load, slow queries, index health; verify `ix_agent_run_events_conv_seq` exists and vacuum/analyze recency.
- Drift: confirm the conversation is still active; if mismatch persists, reproject that conversation. In greenfield environments drift should stay at zero.

## Retention & cleanup
- TTL defaults: `RUN_EVENTS_TTL_DAYS=180` (prod), `RUN_EVENTS_TTL_DAYS=30` (staging/dev recommended via env files).
- Batch knobs: `RUN_EVENTS_CLEANUP_BATCH` (default 10k), `RUN_EVENTS_CLEANUP_SLEEP_MS` (throttle).
- Cleanup command (env-loaded via Starter Console):
  - Dry run: `just cleanup-run-events dry_run=true`
  - Override TTL: `just cleanup-run-events days=90`

## Validation checklist
- Generate a conversation with a tool call; hit `/conversations/{id}/events?mode=full` and expect tool + reasoning entries.
- Confirm metrics show non-zero projection and read counts; latency under SLOs.
- Run `just cleanup-run-events dry_run=true` and verify a log line with `matches` count; ensure no rows deleted in dry-run.

## Ownership / escalation
- This starter ships metrics and sample alert rules; adopters wire them into their own monitoring (Prometheus/Grafana or the optional bundled OpenTelemetry collector). No default paging is configured.
