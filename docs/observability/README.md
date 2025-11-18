<!-- SECTION: Title -->
# Observability Stack & Bundled OpenTelemetry Collector

_Last updated: November 18, 2025_

This doc explains how the starter repo ships a turnkey OpenTelemetry Collector so every operator—from first-time users to enterprise SREs—gets a local OTLP endpoint without wiring their own infra. The same flow scales to production by pointing the FastAPI backend at any external collector or SaaS OTLP intake.

## TL;DR

1. Run the Starter CLI setup wizard (interactive or headless) and select `otlp` as your logging sink.
2. When prompted, choose **“Start bundled OpenTelemetry Collector”** to let docker compose manage the collector container.
3. (Optional) Enable Sentry and/or Datadog exporters directly from the wizard—provide the OTLP endpoint + bearer token for Sentry or the API key + site for Datadog.
4. The wizard writes the env vars below to `.env.local`, and `make dev-up` renders `var/observability/collector.generated.yaml` before launching `otel/opentelemetry-collector-contrib:0.139.0` with those settings.
5. FastAPI points `LOGGING_OTLP_ENDPOINT` at `http://otel-collector:4318/v1/logs` automatically, so structured logs flow through the collector and on to any configured exporters.

## Services & Ports

| Service | Container name | Default host ports | Notes |
| --- | --- | --- | --- |
| Postgres | `agents-postgres` | `5432` | Unchanged from the base stack. |
| Redis | `agents-redis` | `6379` | Unchanged from the base stack. |
| OpenTelemetry Collector | `agents-otel-collector` | `4318` (OTLP/HTTP), `4317` (OTLP/gRPC), `13133` (health/diagnostics) | Runs only when `ENABLE_OTEL_COLLECTOR=true` (set by the wizard). |

The collector image is pinned to `otel/opentelemetry-collector-contrib:0.139.0`, the latest GA cut as of Nov 18, 2025. Upgrade cadence lives in `docs/trackers/MILESTONE_OBSERVABILITY_COLLECTOR.md`.

## Environment Variables

| Env Var | Purpose | Wizard support |
| --- | --- | --- |
| `LOGGING_SINK` | Set to `otlp` to route FastAPI logs through OTLP/HTTP. | ✅ |
| `ENABLE_OTEL_COLLECTOR` | `true` launches the bundled `otel-collector` service via `make dev-up`. | ✅ |
| `LOGGING_OTLP_ENDPOINT` | Auto-set to `http://otel-collector:4318/v1/logs` when the bundled collector is enabled (you can override for remote collectors). | ✅ |
| `LOGGING_OTLP_HEADERS` | Optional JSON map for custom headers when pointing directly at a SaaS OTLP endpoint. | ✅ |
| `OTEL_COLLECTOR_HTTP_PORT` / `OTEL_COLLECTOR_GRPC_PORT` / `OTEL_COLLECTOR_DIAG_PORT` | Host port mappings for the container; defaults are 4318/4317/13133. | Manual override in `.env.local`. |
| `OTEL_MEMORY_LIMIT_MIB` | Process memory limiter for the collector (default `512`). | Manual override in `.env.local`. |
| `OTEL_DEBUG_VERBOSITY` | Controls the bundled `debug` exporter detail level (`detailed` by default so collector logs include payloads). | Manual override in `.env.local`. |
| `OTEL_EXPORTER_SENTRY_ENDPOINT` | Sentry OTLP/HTTP endpoint (e.g., `https://o11y.ingest.sentry.io/api/<project>/otlp`). | ✅ (only when bundled collector enabled). |
| `OTEL_EXPORTER_SENTRY_AUTH_HEADER` | Authorization header value (typically `Bearer <token>`). | ✅ |
| `OTEL_EXPORTER_SENTRY_HEADERS` | Optional JSON for additional OTLP headers to send to Sentry. | ✅ |
| `OTEL_EXPORTER_DATADOG_API_KEY` | Datadog API key for the collector’s native Datadog exporter. | ✅ |
| `OTEL_EXPORTER_DATADOG_SITE` | Datadog site (defaults to `datadoghq.com`). | ✅ |

The wizard stores secrets in `.env.local` only. The generated collector config lives under `var/observability/collector.generated.yaml`, which is gitignored to avoid leaking API keys.

## Code Flow

- `ops/observability/render_collector_config.py` reads the env vars above and emits `var/observability/collector.generated.yaml` whenever `ENABLE_OTEL_COLLECTOR=true`.
- `make dev-up` (and the CLI’s `starter_cli infra compose up`) call the renderer before running `docker compose up ... otel-collector` so the container always mounts a fresh config.
- `docker-compose.yml` defines the `otel-collector` service with the generated config volume and exposes the OTLP/diagnostic ports for local use.

## Exporter Presets

### Sentry

1. During the wizard, answer **Yes** when asked “Forward logs to Sentry from the bundled collector?”
2. Supply your project’s OTLP endpoint and bearer token.
3. Optionally add extra headers (e.g., `{"sentry-release": "agent-starter@1.0.0"}`).

The renderer adds an `otlphttp/sentry` exporter to the collector config with gzip compression and your headers. Logs continue streaming locally via the `debug` exporter, so you can verify payloads even if Sentry rejects them.

### Datadog

1. Answer **Yes** when asked “Forward logs to Datadog from the bundled collector?”
2. Provide a Datadog API key and select the correct site (`datadoghq.com`, `datadoghq.eu`, etc.).

This enables the collector’s native `datadog` exporter, so OTLP logs are relayed alongside your traces/metrics.

### Additional Destinations

Need another sink (Grafana Loki, Honeycomb, Splunk, etc.)? Copy `ops/observability/render_collector_config.py`, add another exporter block keyed off env vars, and re-run `make dev-up`. Downstream pipelines pick up the change automatically because docker compose mounts the regenerated config on restart.

## Local Verification

```bash
# Start the stack with the collector enabled
$ make dev-up

# Tail collector logs
$ docker compose logs -f otel-collector

# Hit the collector health endpoint
$ curl http://localhost:${OTEL_COLLECTOR_DIAG_PORT:-13133}/healthz
```

You should see structured JSON logs coming from FastAPI and mirrored by the collector’s debug exporter. If Sentry/Datadog credentials are wrong, the collector logs emit transport errors—fix the env vars and rerun `make dev-up` to regenerate the config.

### Automated Smoke Test

Run the integration test whenever you need proof that FastAPI → OTLP → collector debug exporter still works:

```bash
$ hatch run pytest anything-agents/tests/integration/test_observability_collector.py \
    -m integration -k collector
```

The test renders a one-off collector config, starts `otel/opentelemetry-collector-contrib` via Docker, emits a unique `log_event`, and asserts that the message shows up in the collector’s stdout logs. It skips automatically when Docker isn’t available.

## Production Notes

- You can keep using the bundled collector in production (deploy it alongside FastAPI) or point `LOGGING_OTLP_ENDPOINT` at your managed OpenTelemetry Collector / SaaS endpoint.
- For production secrets, use the existing secrets-provider workflow (Vault, AWS Secrets Manager, Infisical, etc.) to template `.env` before rendering the collector config—never commit the generated file.
- If you disable the bundled collector later, rerun the wizard (or edit `.env.local`) to set `ENABLE_OTEL_COLLECTOR=false`. FastAPI can still log to any external OTLP endpoint—only the docker compose automation is tied to this flag.
