# Structured Logging Overhaul (OBS-006)

**Last Updated:** 2025-11-17  
**Owner:** Platform Foundations – Observability  
**Status:** Approved – implementation in progress

## 1. Goals & Non-Goals

### Goals
- Emit JSON logs with a predictable schema so downstream sinks (Datadog, OTLP, stdout collectors) can index correlation IDs, tenant metadata, and rate-limit signals.
- Provide a single log helper + formatter that every FastAPI request, Stripe worker, and CLI workflow can rely on without bespoke logger setup.
- Propagate correlation IDs, tenant/provider context, and worker metadata through async tasks so background jobs share the same trace IDs as their triggering request.
- Allow operators to switch sinks (`stdout`, Datadog HTTP intake, OTLP/HTTP) purely via `Settings` without code changes.

### Non-Goals
- Replacing Prometheus metrics (logs complement metrics, not replace them).
- Shipping end-to-end distributed tracing. We scope this milestone to logs; OTLP traces remain a future project.
- Implementing log sampling/retention policies (left to the sink/back-end).

## 2. Canonical Log Schema

| Key | Type | Notes |
|-----|------|-------|
| `ts` | string (RFC 3339) | UTC timestamp emitted by formatter. |
| `level` | string | Lowercase level (`info`, `warning`, `error`, etc.). |
| `logger` | string | Logger name (`app.observability`, `app.middleware.http`). |
| `service` | string | `settings.app_name`. |
| `environment` | string | `settings.environment`. |
| `event` | string | Required machine-friendly event identifier (`signup.invite_sent`, `stripe.worker.retry`). |
| `message` | string | Optional human-friendly string; defaults to `event`. |
| `correlation_id` | string? | Attached when present in the current log context (HTTP middleware seeds it). |
| `tenant_id` | string? | Propagated from dependency/context helpers. |
| `user_id` | string? | Provided by auth services when available. |
| `worker_id` | string? | Non-HTTP worker identifier (Stripe dispatcher, cron). |
| `fields` | object | Arbitrary event metadata (quota, provider_name, retry counts, etc.). |
| `exc_type` / `exc_message` / `exc_traceback` | string? | Populated automatically when `exc_info` is provided. |

Context + event-specific keys are flattened at the top level except for `fields`, which groups mutable data that changes per event. This keeps indexes predictable while still allowing rich metadata.

## 3. Context Propagation Contract

- Introduce `log_context` helpers backed by a `contextvars.ContextVar` to store `correlation_id`, `tenant_id`, `provider`, `worker_id`, etc.
- HTTP middleware seeds `correlation_id` for every request then enters a scoped context so downstream handlers automatically inherit it.
- Background workers and CLI tasks call `bind_log_context(worker_id="stripe-dispatcher")` during start-up.
- Dependencies (e.g., `require_tenant`) extend the context with tenant/provider metadata before handing off to services. Context managers ensure we never leak previous request data across asyncio tasks.

## 4. Sink Configuration Strategy

- `configure_logging(settings)` centralizes `logging.config.dictConfig` so both FastAPI (`anything-agents/main.py`) and worker entry points can initialize logging consistently.
- Supported sinks for OBS-006:
  - `stdout` (default): single `StreamHandler` → JSON formatter.
  - `datadog`: custom HTTP handler posts batches to `https://http-intake.logs.<site>/api/v2/logs` using `LOGGING_DATADOG_API_KEY`.
  - `otlp`: OTLP/HTTP handler posts JSON payloads to `LOGGING_OTLP_ENDPOINT` with optional headers JSON.
  - `none`: attaches a `NullHandler` (tests/benchmarks).
- Future sinks (Kafka, S3) would plug into the same factory without changing callers.

## 5. Failure Handling

- Sink handlers swallow transport errors after emitting a secondary `logging.getLogger("app.observability").error` with `event="logging.sink_error"` + reason, ensuring the application never crashes due to logging backends.
- When sink misconfiguration is detected (e.g., `logging_sink="datadog"` without API key), `configure_logging` raises during startup to fail fast rather than silently downgrade to stdout.
- JSON serialization falls back to `_serialize` helper that formats datetimes and sets while leaving other objects to Python’s default repr for transparency.

## 6. Implementation Checklist

1. Add context helpers + JSON formatter + sink factory in `app/observability/logging.py`.
2. Wire `configure_logging(settings)` inside `anything-agents/main.py` before the FastAPI app instantiates middleware; expose the same helper for worker entry points.
3. Update `app/middleware/logging.py` to rely on `log_event` and scoped log context rather than string formatting.
4. Expand rate-limit + Stripe worker instrumentation to include `correlation_id`, `tenant_id`, and worker metadata (covered by follow-up tests once sinks are live).
5. Document operational guidance here and reference it from `docs/trackers/ISSUE_TRACKER.md`.

## 7. Testing Strategy

- Unit tests target the formatter (stable keys, exception serialization) and context helpers (nesting, cleanup).
- Integration-style tests run the middleware against a mocked request to ensure correlation IDs propagate to downstream log events and rate-limit errors emit the expected fields.
- CLI + worker smoke tests rely on `configure_logging` to ensure sink mismatches raise during CI rather than at runtime.
