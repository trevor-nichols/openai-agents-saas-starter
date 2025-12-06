# Run Events Dashboard (sample Grafana spec)

Panels (suggested)
- Ingest rate & outcomes: stacked bar of `agent_run_events_projection_total` by result (success/error/conflict) with tenant filter.
- Ingest latency: P50/P95/P99 of `agent_run_events_projection_duration_seconds` (histogram_quantile) over 10m, split by agent.
- Read rate & latency: `agent_run_events_read_total` by mode (transcript/full) and P95 `agent_run_events_read_duration_seconds`.
- Drift: table of `agent_run_events_drift` non-zero values with conversation_id, tenant, magnitude.
- Event volume: events per conversation/run (sum of rows returned) and top-N conversations by volume.
- Storage health (requires pg exporter): table size of `agent_run_events`, index bloat, last vacuum/analyze timestamps.

Filters
- Tenant (label matcher on metrics)
- Agent
- Mode (transcript/full)

SLO overlays
- Projection P95 < 5s; Read P95 < 2s.

Notes
- Built for Prometheus-scraped metrics. If you enable the bundled optional OpenTelemetry collector, add a Prometheus exporter or scrape the api-service directly.
- Conflict spikes usually indicate duplicate response_id/sequence pairs; investigate upstream idempotency.
- Drift indicates mismatch between SDK message count and event log; reproject only if/when backfill exists.
