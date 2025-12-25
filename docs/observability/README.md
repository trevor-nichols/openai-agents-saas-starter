<!-- SECTION: Title -->
# Observability Stack & Bundled OpenTelemetry Collector

_Last updated: November 18, 2025_

This doc explains how the starter repo ships a turnkey OpenTelemetry Collector so every operator—from first-time users to enterprise SREs—gets a local OTLP endpoint without wiring their own infra. The same flow scales to production by pointing the FastAPI backend at any external collector or SaaS OTLP intake.

## TL;DR

1. Run the Starter Console setup wizard (interactive or headless) and select `otlp` as your logging sink.
2. When prompted, choose **“Start bundled OpenTelemetry Collector”** to let docker compose manage the collector container.
3. (Optional) Enable Sentry and/or Datadog exporters directly from the wizard—provide the OTLP endpoint + bearer token for Sentry or the API key + site for Datadog.
4. The wizard writes the env vars below to `apps/api-service/.env.local`, and `just dev-up` renders `var/observability/collector.generated.yaml` before launching `otel/opentelemetry-collector-contrib:0.139.0` with those settings.
5. FastAPI points `LOGGING_OTLP_ENDPOINT` at `http://otel-collector:4318/v1/logs` automatically, so structured logs flow through the collector and on to any configured exporters.

## Services & Ports

| Service | Compose service | Default host ports | Notes |
| --- | --- | --- | --- |
| Postgres | `postgres` | `${POSTGRES_PORT:-5432}` | Part of the base local stack when `STARTER_LOCAL_DATABASE_MODE=compose` (default). |
| Redis | `redis` | `${REDIS_PORT:-6379}` | Unchanged from the base stack. |
| OpenTelemetry Collector | `otel-collector` | `${OTEL_COLLECTOR_HTTP_PORT:-4318}` (OTLP/HTTP), `${OTEL_COLLECTOR_GRPC_PORT:-4317}` (OTLP/gRPC), `${OTEL_COLLECTOR_DIAG_PORT:-13133}` (health/diagnostics) | Runs only when `ENABLE_OTEL_COLLECTOR=true` (set by the wizard). |

The collector image is pinned to `otel/opentelemetry-collector-contrib:0.139.0`, the latest GA cut as of Nov 18, 2025. Upgrade cadence lives in `docs/trackers/MILESTONE_OBSERVABILITY_COLLECTOR.md`.

## Environment Variables

| Env Var | Purpose | Wizard support |
| --- | --- | --- |
| `LOGGING_SINKS` | Comma-separated logging sinks (`stdout`, `file`, `datadog`, `otlp`, `none`). | ✅ |
| `LOG_ROOT` | Base directory for dated log roots (`<LOG_ROOT>/<YYYY-MM-DD>/<component>`). Defaults to `var/log`. | Manual |
| `LOGGING_MAX_DAYS` | Prune dated log folders older than N days (0 disables). | Manual |
| `LOGGING_DUPLEX_ERROR_FILE` | When `LOGGING_SINKS` includes `stdout`, also write errors to `<date>/api/error.log`. | Manual |
| `LOGGING_FILE_PATH` / `LOGGING_FILE_BACKUPS` / `LOGGING_FILE_MAX_MB` | File sink location and rotation settings. | ✅ |
| `ENABLE_FRONTEND_LOG_INGEST` | Expose `/api/v1/logs` (auth required by default). | ✅ |
| `ALLOW_ANON_FRONTEND_LOGS` | Allow anonymous ingest when signature is valid (see below). | Manual |
| `FRONTEND_LOG_SHARED_SECRET` | HMAC secret for signed anonymous frontend logs. | Manual |
| `LOGGING_SINKS=otlp` settings | `LOGGING_OTLP_ENDPOINT`, `LOGGING_OTLP_HEADERS`. | ✅ |
| `ENABLE_OTEL_COLLECTOR` | `true` launches bundled collector via `just dev-up`. | ✅ |
| `OTEL_COLLECTOR_HTTP_PORT` / `OTEL_COLLECTOR_GRPC_PORT` / `OTEL_COLLECTOR_DIAG_PORT` | Host port mappings for collector. | Manual |
| `OTEL_MEMORY_LIMIT_MIB` | Collector memory cap (default 512). | Manual |
| `OTEL_DEBUG_VERBOSITY` | Collector debug exporter verbosity (`detailed` default). | Manual |
| `OTEL_EXPORTER_SENTRY_*` | Sentry OTLP settings. | ✅ |
| `OTEL_EXPORTER_DATADOG_*` | Datadog exporter settings. | ✅ |

### Local file logging layout (new)

- When `LOG_ROOT` is set (or when `LOGGING_SINKS=file`), FastAPI writes JSON logs to dated folders: `LOG_ROOT/YYYY-MM-DD/api/all.log` and `error.log`. A helper symlink `LOG_ROOT/current` points at the latest folder.
- `starter-console start dev --detached` and the new `starter-console logs tail` respect this layout; `--errors` tails `error.log`.
- Retention: set `LOGGING_MAX_DAYS` to prune old dated folders on startup; `starter-console logs archive --days N` can zip+prune manually.

### Frontend log ingest

- By default, the Next.js client logger uses `beacon` in local dev; it posts to `/api/logs` → `/api/v1/logs` (backend) when `ENABLE_FRONTEND_LOG_INGEST=true`.
- Auth is required unless `ALLOW_ANON_FRONTEND_LOGS=true` **and** the client sends `X-Log-Signature` = `hex(hmac_sha256(FRONTEND_LOG_SHARED_SECRET, raw_body))`.
- Server/dev console output can also be tee’d to `LOG_ROOT/<date>/frontend/all.log` / `error.log` when you wrap dev with `node scripts/with-log-root.js` (already wired into `pnpm dev`).

The wizard stores secrets in `apps/api-service/.env.local` only. The generated collector config lives under `var/observability/collector.generated.yaml`, which is gitignored to avoid leaking API keys.

## Code Flow

- `ops/observability/render_collector_config.py` reads the env vars above and emits `var/observability/collector.generated.yaml` whenever `ENABLE_OTEL_COLLECTOR=true`.
- `just dev-up` (and the CLI’s `starter-console infra compose up`) call the renderer before running `docker compose up ... otel-collector` so the container always mounts a fresh config.
- `ops/compose/docker-compose.yml` defines the `otel-collector` service with the generated config volume and exposes the OTLP/diagnostic ports for local use.

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

Need another sink (Grafana Loki, Honeycomb, Splunk, etc.)? Copy `ops/observability/render_collector_config.py`, add another exporter block keyed off env vars, and re-run `just dev-up`. Downstream pipelines pick up the change automatically because docker compose mounts the regenerated config on restart.

## Local Verification

```bash
# Start the stack with the collector enabled
$ just dev-up

# Tail service logs from one place
$ starter-console logs tail --service api --service collector

# Tail collector logs
$ docker compose logs -f otel-collector

# Hit the collector health endpoint
$ curl http://localhost:${OTEL_COLLECTOR_DIAG_PORT:-13133}/healthz
```

You should see structured JSON logs coming from FastAPI and mirrored by the collector’s debug exporter. If Sentry/Datadog credentials are wrong, the collector logs emit transport errors—fix the env vars and rerun `just dev-up` to regenerate the config.

### Log Tailing Notes

- `logs tail` reads the backend rotating file sink when `LOGGING_SINKS=file` (set via the wizard). For stdout-only deployments, run the API in a separate terminal instead.
- When `ENABLE_FRONTEND_LOG_INGEST=true`, the Next.js beacon transport forwards browser events to `/api/v1/logs`; they appear as `frontend.log` entries in backend tails. Without ingest, view the Next.js dev server stdout.

### Automated Smoke Test

Run the integration test whenever you need proof that FastAPI → OTLP → collector debug exporter still works:

```bash
$ cd apps/api-service
$ hatch run pytest tests/integration/test_observability_collector.py \
    -m integration -k collector
```

The test renders a one-off collector config, starts `otel/opentelemetry-collector-contrib` via Docker, emits a unique `log_event`, and asserts that the message shows up in the collector’s stdout logs. It skips automatically when Docker isn’t available.

## Production Notes

- You can keep using the bundled collector in production (deploy it alongside FastAPI) or point `LOGGING_OTLP_ENDPOINT` at your managed OpenTelemetry Collector / SaaS endpoint.
- For production secrets, use the existing secrets-provider workflow (Vault, AWS Secrets Manager, Infisical, etc.) to template `.env` before rendering the collector config—never commit the generated file.
- If you disable the bundled collector later, rerun the wizard (or edit `apps/api-service/.env.local`) to set `ENABLE_OTEL_COLLECTOR=false`. FastAPI can still log to any external OTLP endpoint—only the docker compose automation is tied to this flag.
