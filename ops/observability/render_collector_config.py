"""Render an OpenTelemetry Collector config based on env variables.

This script keeps the generated config file under ``var/observability`` in sync so
docker-compose can mount it into the collector container. Exporters for Sentry
and Datadog are enabled only when the required env vars are populated, keeping
the default pipeline lightweight for local development.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml


DEFAULT_OUTPUT = Path("var/observability/collector.generated.yaml")


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_headers(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"LOGGING_OTLP_HEADERS must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):  # pragma: no cover - defensive
        raise SystemExit("LOGGING_OTLP_HEADERS must decode to an object")
    return {str(key): str(value) for key, value in parsed.items()}


def _build_config(env: dict[str, str]) -> dict:
    http_port = env.get("OTEL_COLLECTOR_HTTP_PORT", "4318")
    grpc_port = env.get("OTEL_COLLECTOR_GRPC_PORT", "4317")
    diag_port = env.get("OTEL_COLLECTOR_DIAG_PORT", "13133")

    exporters: dict[str, dict] = {
        "debug": {"verbosity": env.get("OTEL_DEBUG_VERBOSITY", "detailed")},
    }
    pipeline_exporters: list[str] = ["debug"]

    sentry_endpoint = env.get("OTEL_EXPORTER_SENTRY_ENDPOINT", "").strip()
    sentry_auth = env.get("OTEL_EXPORTER_SENTRY_AUTH_HEADER", "").strip()
    if sentry_endpoint:
        exporter_name = "otlphttp/sentry"
        exporter: dict[str, object] = {
            "endpoint": sentry_endpoint,
            "compression": "gzip",
            "timeout": "5s",
        }
        headers = {}
        if sentry_auth:
            headers["Authorization"] = sentry_auth
        extra_headers = _load_headers(env.get("OTEL_EXPORTER_SENTRY_HEADERS"))
        headers.update(extra_headers)
        if headers:
            exporter["headers"] = headers
        exporters[exporter_name] = exporter
        pipeline_exporters.append(exporter_name)

    datadog_key = env.get("OTEL_EXPORTER_DATADOG_API_KEY", "").strip()
    if datadog_key:
        exporter_name = "datadog"
        exporters[exporter_name] = {
            "api": {
                "site": env.get("OTEL_EXPORTER_DATADOG_SITE", "datadoghq.com"),
                "key": datadog_key,
            },
            "metrics": {"flush_interval": "15s"},
        }
        pipeline_exporters.append(exporter_name)

    config = {
        "receivers": {
            "otlp": {
                "protocols": {
                    "grpc": {"endpoint": f"0.0.0.0:{grpc_port}"},
                    "http": {
                        "endpoint": f"0.0.0.0:{http_port}",
                        "cors": {"allowed_origins": ["*"]},
                    },
                }
            }
        },
        "processors": {
            "memory_limiter": {
                "check_interval": "5s",
                "limit_mib": int(env.get("OTEL_MEMORY_LIMIT_MIB", "512")),
            },
            "batch": {
                "send_batch_size": 512,
                "send_batch_max_size": 1024,
                "timeout": "1s",
            },
        },
        "exporters": exporters,
        "extensions": {
            "health_check": {"endpoint": f"0.0.0.0:{diag_port}"},
        },
        "service": {
            "telemetry": {
                "logs": {"level": env.get("OTEL_COLLECTOR_LOG_LEVEL", "debug")}
            },
            "extensions": ["health_check"],
            "pipelines": {
                "logs": {
                    "receivers": ["otlp"],
                    "processors": ["memory_limiter", "batch"],
                    "exporters": pipeline_exporters,
                }
            },
        },
    }
    return config


def main() -> int:
    env = dict(os.environ)
    if not _truthy(env.get("ENABLE_OTEL_COLLECTOR")):
        # Nothing to do if the collector isn't enabled for this profile.
        return 0

    output_path = Path(env.get("OTEL_COLLECTOR_CONFIG_PATH", DEFAULT_OUTPUT))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config = _build_config(env)
    output_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    print(f"Wrote OpenTelemetry Collector config to {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
