<!-- SECTION: Title -->
# Observability Collector Milestone — OTLP Dev Stack

_Last updated: November 18, 2025_

## Objective
Bundle a turnkey OpenTelemetry Collector into the starter stack so every tenant (from first-time operators to seasoned SREs) has a drop-in OTLP endpoint, curated exporter presets (stdout + optional Sentry/Datadog), and CLI-guided configuration without touching raw YAML.

### Target Artifact Snapshot
- Collector image: `otel/opentelemetry-collector-contrib:0.139.0` (current GA as of Nov 2025, adds the stable `transform` processor + OTLP HTTP fixes).
- Endpoint surfaced as `http://otel-collector:4318/v1/logs` inside Compose; 4318 exposed to host for external senders.
- Config template under `ops/observability/collector.yaml` with commented exporters for Sentry (OTLP HTTP) and Datadog (otlphttp → datadog exporter) plus passthrough stdout for dev visibility.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Collector image/version tracking | ✅ Complete | Pinned to `otel/opentelemetry-collector-contrib:0.139.0`; doc + tracker updated Nov 18. |
| Docker Compose integration | ✅ Complete | `otel-collector` service, Just hooks, and config renderer now live. |
| Starter CLI onboarding | ✅ Complete | Wizard prompts for OTLP sink, bundled collector toggle, and Sentry/Datadog exporters; headless keys documented. |
| Documentation & runbooks | ✅ Complete | `docs/observability/README.md` covers setup, env vars, exporters, verification steps, and automated smoke test instructions. |
| QA / smoke validation | ✅ Complete | `api-service/tests/integration/test_observability_collector.py` spins up the collector via Docker and asserts logs hit the debug exporter. |

## Deliverables
1. **Collector Infrastructure** — Compose service, health checks, and Just recipe to manage lifecycle alongside Postgres/Redis/Vault.
2. **Config Templates** — Opinionated `collector.yaml` with processors/exporters for stdout + opt-in SaaS targets (Sentry, Datadog) via env vars.
3. **CLI Experience** — Setup wizard step that captures logging sink choice, writes the appropriate env vars, and, when OTLP+collector is selected, injects the default endpoint + vendor tokens.
4. **Docs & Runbooks** — `docs/observability/README.md` (or section in ops guide) describing local/prod topologies, version upgrade steps, and sample vendor wiring.
5. **Validation** — Automated smoke test ensuring FastAPI emits logs that appear in the collector stdout exporter; optionally add CI job or developer script.

## Work Plan
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Finalize collector version pin + changelog watcher (start with 0.139.0). | Platform Foundations | ✅ Completed | Nov 18 |
| 2 | Add `otel-collector` service to `ops/compose/docker-compose.yml`, mount generated config, expose 4318/4317, and update Just recipes. | Platform Foundations | ✅ Completed | Nov 18 |
| 3 | Author config renderer (`ops/observability/render_collector_config.py`) with env-driven Sentry/Datadog exporters. | Platform Foundations | ✅ Completed | Nov 18 |
| 4 | Extend Starter CLI setup wizard to include "Observability" step (sink selection, OTLP endpoint/header prompts, toggle for bundled collector). | Platform Foundations | ✅ Completed | Nov 18 |
| 5 | Update docs (`docs/trackers/ISSUE_TRACKER.md`, `docs/observability/README.md`) with quick-start + production guidance. | Platform Foundations | ✅ Completed | Nov 18 |
| 6 | Add smoke tests (pytest fixture or integration script) verifying logs reach the collector stdout exporter when Compose stack runs. | Platform Foundations | ✅ Completed | Nov 18 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Collector image drift introduces breaking config changes. | Medium | Track upstream release notes monthly; keep config minimal and documented. |
| Operators misunderstand exporter credentials living in plain env vars. | Medium | Document secret handling + recommend Vault/Secrets Manager for prod tokens. |
| Additional container increases local resource usage. | Low | Allow opt-out flag/Just helper (e.g., `just observability-down`) and document CPU/memory expectations. |

## Changelog
- **2025-11-18** — Collector service/config renderer/CLI/doc updates merged; smoke tests added via `api-service/tests/integration/test_observability_collector.py`.
- **2025-11-18** — Milestone created, version pinned to 0.139.0, Issue BE-008 opened for tracking.
- **2025-11-18** — Debug exporter now defaults to `detailed`, `.env` templates expose `OTEL_DEBUG_VERBOSITY`, docs were updated, and the smoke test reads combined `docker logs` output so OTLP payload assertions pass on hosts where the log stream lands on stderr.
