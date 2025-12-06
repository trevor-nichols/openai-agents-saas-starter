# Logging & Telemetry Unification Milestone

_Last updated: November 20, 2025_

## Objective
Provide a single, professional-grade logging experience across backend, frontend, and operator tooling. Defaults stay lightweight (stdout/console), while operators can opt into structured sinks (file, OTLP, Datadog) and view everything through the Starter CLI without crossing import boundaries.

## Scope & Deliverables
1) **Backend sinks** — JSON logging remains the default; add file rotation option alongside existing stdout/datadog/otlp/none.
2) **Frontend logger** — Shared logger abstraction with pluggable transports (console, beacon → backend), level gating, and client-side scrubbing of sensitive fields.
3) **Frontend log ingest** — Authenticated, rate-limited backend endpoint (feature-gated) to accept browser logs and emit via structured logger.
4) **Operator UX** — Starter CLI wizard captures logging choices; `infra logs` command tails logs per service; docs/runbook updated; optional local OTel collector helper acknowledged but remains opt-in.

## Success Criteria
- Backend can write structured logs to stdout or rotating file without code changes; OTLP/Datadog still work.
- Frontend emits through one logger; no stray `console.debug` helpers remain in chat/analytics paths.
- Browser logs can flow to backend when enabled; protected by auth + size caps + scrubbing.
- Operators can configure and tail logs via CLI without importing FastAPI/Next code.
- Documentation describes local vs. production setups plus quickstart commands.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Backend sink options | ✅ Complete | File sink added with rotating handler + JSON output; defaults remain stdout. |
| Frontend logger abstraction | ✅ Complete | Shared `lib/logging` added; chat + analytics migrated; beacon transport stubbed. |
| Frontend log ingest API | ✅ Complete | Feature-gated POST route with rate limit + size cap; Next.js proxy at /api/logs forwards to /api/v1/logs. |
| CLI ergonomics | ✅ Complete | `starter-cli logs tail` added for api/frontend (ingest), postgres/redis, and OTEL collector. |
| Docs/runbooks | ✅ Complete | Observability README and CLI docs updated with log tailing and ingest notes. |

## Work Plan
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Add file sink support (env configurable path/rotation) + unit tests in backend logging module. | Platform Foundations | ✅ Completed | Nov 2025 |
| 2 | Introduce shared frontend logger (`lib/logging`) with level gating, scrubbing, console/beacon transports; migrate chat/analytics callers. | Platform Foundations | ✅ Completed | Nov 2025 |
| 3 | Add feature-gated frontend log ingest endpoint with auth, rate limit, body size cap; tests for auth/limit/error paths. | Platform Foundations | ✅ Completed | Nov 2025 |
| 4 | Update Starter CLI wizard (observability section) to surface new envs; add `logs tail` command for api/frontend/collector + compose infra. | Platform Foundations | ✅ Completed | Nov 2025 |
| 5 | Update docs (`docs/observability` + trackers) and add quickstart/just recipes for local tails and optional OTel helper. | Platform Foundations | ✅ Completed | Nov 2025 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Log PII leakage from browser payloads | Medium | Client-side scrubbing of auth/cookie/password fields; server-side size caps and allowlist of keys. |
| File sink introduces disk growth | Low | Use rotating handler with size/backup limits; disabled by default. |
| CLI log-tail command drifts from compose/service names | Low | Derive targets from existing Just/compose naming; keep command purely subprocess-based. |
| Beacon transport fails silently in some browsers | Low | Fallback to fetch with timeout; keep console as default in dev. |

## Changelog
- **2025-11-20** — Milestone created; scope and work plan defined.
