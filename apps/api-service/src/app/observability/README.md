## Observability (api-service)

Structured logging and Prometheus metrics live here. Logging is configured on import in `app/main.py` via `configure_logging(get_settings())`, and metrics are scraped from `/metrics` using `app.presentation.metrics` with the shared `REGISTRY`.

### Logging
- JSON logs with `ts`, `level`, `logger`, `service`, `environment`, and merged contextual fields. Emit via `log_event(...)` (preferred) or a standard logger with `extra={"structured": {...}}`.
- Context propagation uses a `ContextVar` (`log_context`, `bind_log_context`, `clear_log_context`, `get_log_context`). HTTP middleware attaches `correlation_id`, method, path, and client IP; tenant dependencies bind `tenant_id`/`tenant_role`/`user_id`.
- Formatters/sinks live under `logging/`. Supported sinks (choose via comma-separated `LOGGING_SINKS`):
  - `stdout`/`console` (default) — JSON to stdout; optionally duplex error file when `LOGGING_DUPLEX_ERROR_FILE=true`.
  - `file` — dated tree under `LOG_ROOT` (default `var/log/<YYYY-MM-DD>/api/{all,error}.log` + `current` symlink); rotation respects `LOGGING_FILE_MAX_MB`, `LOGGING_FILE_BACKUPS`, `LOGGING_MAX_DAYS`, and `LOGGING_FILE_PATH` for a custom target.
  - `datadog` — HTTP intake (`LOGGING_DATADOG_API_KEY`, optional `LOGGING_DATADOG_SITE`).
  - `otlp` — JSON-over-HTTP (`LOGGING_OTLP_ENDPOINT`, optional `LOGGING_OTLP_HEADERS` JSON string).
  - `none` — installs a `NullHandler` (useful for tests).
- Adding fields: wrap work in `with log_context(...):` or call `bind_log_context(...)`. Prefer `log_event("event.name", level="info|warning|error", **fields)` to keep payloads consistent.

### Metrics
- Prometheus registry is `app.observability.metrics.REGISTRY`; `/metrics` exposes the latest snapshot (`prometheus_client.generate_latest`).
- Buckets: `_LATENCY_BUCKETS` for durations (5ms → 5s), `_TOKEN_BUCKETS` for token counts. Label sanitizers keep missing/None values as `unknown` or booleans as `true|false`.
- Major metric families (counter/gauge/histogram):
  - Auth/JWT: `jwks_requests_total`, signing/verifying totals + `*_duration_seconds`, service-account issuance counts/latency, nonce cache hits/misses.
  - Rate/usage: `rate_limit_hits_total`, `usage_guardrail_decisions_total`, `usage_limit_hits_total`.
  - Billing/Stripe: API call counts/latency, webhook outcomes, gateway operations (by plan), dispatch retries, billing stream publish/backlog gauges.
  - Workflows/vector stores/storage: operation totals and latency histograms for workflow run deletes, vector store ops, storage providers.
  - Memory & conversations: strategy triggers, summary injections, compaction counts, before/after token histograms; run-event projection/read counters, latency, and drift gauge.
  - Containers & notifications: container operation totals/latency, signup attempts/blocks, email/slack delivery counts/latency.
  - Activity log: `activity_events_total`, `activity_stream_publish_total`.
- Emitters: use the provided helpers (`observe_jwt_signing`, `record_rate_limit_hit`, `observe_stripe_api_call`, `observe_storage_operation`, etc.) to ensure labels are sanitized and durations are clamped to ≥0.
- Adding a new metric: define it in `metrics.py` with the shared `REGISTRY`, pick an existing bucket set, add a thin helper that normalizes labels, and reuse the `record_*` / `observe_*` naming pattern.

### Developer quick start
- Defaults: JSON to stdout, no files, `/metrics` available. Start the API (e.g., `just start-backend`) and hit `http://localhost:8000/metrics`.
- File logs: set `LOGGING_SINKS=stdout,file` to write to `var/log/current/api/{all,error}.log`.
- External exporters: set the Datadog/OTLP envs listed above; invalid configs fail fast on startup.
