<!-- SECTION: Title -->
# Usage Guardrails Milestone — Plan-Aware Metering

_Last updated: November 18, 2025_

## Objective
Give operators a turnkey way to meter agent usage (messages, input tokens, output tokens), enforce subscription entitlements before GPT-5.1 runs, and push matching usage to Stripe + internal analytics without manual wiring. The Starter Console must make these controls opt-in, configurable, and understandable for both seasoned platform teams and no-code operators.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Repository contract for usage rollups | ✅ Completed | `BillingRepository.get_usage_totals` now aggregates per-feature quantities over arbitrary windows with tests. |
| Automatic metering from chat workflows | ✅ Completed | UsageRecorder now captures messages/input/output tokens directly from `AgentService` chat + stream paths. |
| Quota enforcement before chat execution | ✅ Completed | UsagePolicyService + FastAPI dependency block or warn before GPT-5.1 runs (sync + stream), with structured errors. |
| Starter Console onboarding | ✅ Completed | New "Usage & Entitlements" wizard section toggles guardrails, prompts for plan dimensions, and writes `var/reports/usage-entitlements.json`. |
| Observability & operator docs | ✅ Completed | Prometheus counters (`usage_guardrail_decisions_total`, `usage_limit_hits_total`) and structured logs now ship with a dedicated runbook in `docs/ops/usage-guardrails-runbook.md`. |

## Deliverables
1. **Usage Recorder Service** — Captures per-request deltas (messages=1, SDK token counts) and invokes `BillingService.record_usage` + internal persistence automatically.
2. **Usage Policy Service** — Reads tenant subscription, plan features, and current-period totals; blocks or warns when hard/soft limits are exceeded, surfacing actionable FastAPI errors.
3. **Aggregation Layer** — Cached/materialized rollups by tenant/feature/period powering enforcement, dashboards, and future analytics exports.
4. **Starter Console Experience** — New wizard section to select metering dimensions, seed default plan limits, and skip metering entirely if desired; outputs env + plan fixture updates.
   - NOTE: The emitted `var/reports/usage-entitlements.json` is an operator artifact only; plan features still need to be seeded into Postgres (e.g., via migrations or a loader script) so the backend can enforce those limits.
5. **Observability & Docs** — Structured logs/metrics for quota hits, dashboard queries, README + runbook updates, and troubleshooting guidance.

## Milestone Phases
| Phase | Scope | Exit Criteria |
| --- | --- | --- |
| P1 — Data Foundations | Add repository queries (`get_usage_totals`), rollup view/cache, and fixtures for plan feature limits. | Tests cover rollup queries; `subscription_usage` view/API returns totals per feature/period. |
| P2 — Metering + Enforcement | Introduce `UsageRecorder` within `agent_service`, collect usage from chat/stream endpoints, and enforce via `UsagePolicyService`. | Each chat request logs/records messages+token deltas; hard-limit breach returns 429 with structured payload. |
| P3 — Starter Console Enablement | Wizard prompts for metering dimensions + default limits, writes `.env` and plan seed updates, supports opt-out. | Headless + interactive flows verified; docs show how to toggle per environment. |
| P4 — Observability & Docs | Emit metrics/logs, add dashboards/docs/runbooks, and wire alerts for sustained quota hits. | Prometheus counter `usage_limit_hits_total` live, README/runbooks updated, dashboard screenshot captured. |

## Work Plan
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Extend `BillingRepository` with `get_usage_totals` + aggregation view/cache, update unit/integration tests. | Platform Foundations | ✅ Completed | Nov 18 |
| 2 | Implement `UsageRecorder` + SDK instrumentation to emit message/token deltas after every chat (sync + streaming). | Platform Foundations | ✅ Completed | Nov 18 |
| 3 | Build `UsagePolicyService` + FastAPI dependency, wire chat routes to enforce per-plan hard/soft limits with descriptive 429s. | Platform Foundations | ✅ Completed | Nov 18 |
| 4 | Add Starter Console “Usage & Entitlements” wizard section (dimension selection, default plan limits, skip path) + tests. | Platform Foundations | ✅ Completed | Nov 18 |
| 5 | Document operator workflow (README, billing runbook, new troubleshooting doc) and add metrics/logging for quota hits. | Platform Foundations | ✅ Completed | Nov 18 |
| 6 | Build entitlement loader that ingests `usage-entitlements.json` and upserts plan features in Postgres/Stripe. | Platform Foundations | ✅ Completed | Nov 18 |
| 7 | Replace in-process usage totals cache with a Redis-backed/shared implementation surfaced via CLI settings. | Platform Foundations | ✅ Completed | Nov 18 |
| 8 | Build CLI dashboard/export workflow (usage report JSON/CSV) so operators can inspect per-tenant usage + remaining quota without wiring a UI. | Platform Foundations | ✅ Completed | Nov 18 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Token counts vary between SDK releases. | Medium | Normalize via SDK usage objects, add contract tests, and expose calibration env var for future providers. |
| Quota lookups add latency to chat endpoints. | Medium | Use cached rollups (Redis/materialized view) with async refresh + fallback to “allow + log” if store unavailable. |
| Operators misconfigure plan limits in CLI. | Low | Provide curated presets per plan template, validation hints, and summary output before writing files. |

## Changelog
- **2025-11-18** — Milestone created; BE-009 opened in `ISSUE_TRACKER.md` to track implementation.
- **2025-11-18** — Phase P1 data foundations kicked off: repository now exposes `get_usage_totals`, Postgres implementation aggregates per-feature windows, and unit tests cover filtering + multiple features.
- **2025-11-18** — Phase P2 instrumentation landed: new UsageRecorder service plus `AgentService` chat/stream pathways now emit messages/input/output token usage automatically with unit coverage.
- **2025-11-18** — UsagePolicyService wired into chat/stream FastAPI routes with enforcement dependency + contract tests.
- **2025-11-18** — Setup wizard gains "Usage & Entitlements" section that toggles guardrails and persists per-plan limits to `var/reports/usage-entitlements.json` for operators.
- **2025-11-18** — Phase P4 closed: guardrail evaluations now emit Prometheus metrics + structured logs, README references the new `Usage Guardrails` runbook, and operators have troubleshooting/alerting guidance.
- **2025-11-18** — Follow-up scope scheduled: entitlement loader + Redis-backed usage cache added ahead of the dashboard/export stretch; telemetry provider toggles are tracked separately under the observability milestone.
- **2025-11-18** — Task 8 kicked off: CLI `starter-console usage export-report` will read Postgres rollups and write `var/reports/usage-dashboard.{json,csv}` so operators can ship usage data into admin dashboards without additional services.
- **2025-11-18** — CLI exporter shipped: modular usage report service + tests, `usage export-report` command, default artifacts under `var/reports/usage-dashboard.*`, and runbook/README updates.
- **2025-11-18** — CLI usage command `starter-console usage sync-entitlements` now syncs `usage-entitlements.json` into `plan_features` with dry-run + prune flags, closing work item #6.
- **2025-11-18** — Usage cache now supports Redis via `USAGE_GUARDRAIL_CACHE_BACKEND`/`USAGE_GUARDRAIL_REDIS_URL`, and the setup wizard exposes those prompts so operators can pick Redis or per-process memory.
