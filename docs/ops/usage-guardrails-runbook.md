<!-- SECTION: Title -->
# Usage Guardrails Runbook — Plan-Aware Metering

_Last updated: November 18, 2025_

This runbook explains how to enable, monitor, and troubleshoot the plan-aware usage guardrails that gate `/api/v1/chat` and `/api/v1/chat/stream`. The guardrails meter `messages`, `input_tokens`, and `output_tokens`, enforce plan entitlements before GPT-5.1 executes, and emit structured signals any time a tenant approaches or exceeds quota.

## Enablement Checklist

1. **Billable environment** – Guardrails require billing to be enabled (`ENABLE_BILLING=true`) so `BillingService` can read subscriptions + plans.
2. **Starter CLI wizard** – Run `cd packages/starter_cli && python -m starter_cli.app setup wizard` (or `just cli cmd="setup wizard"`) and complete the new **Usage & Entitlements** section, or re-run just that section with `--sections usage`. Provide:
   - `ENABLE_USAGE_GUARDRAILS=true`
   - `USAGE_GUARDRAIL_CACHE_TTL_SECONDS` (default `30`)
   - `USAGE_GUARDRAIL_SOFT_LIMIT_MODE` (`warn` or `block`)
   - `USAGE_GUARDRAIL_CACHE_BACKEND` (`redis` recommended; use `memory` for single-node dev)
   - `USAGE_GUARDRAIL_REDIS_URL` when the backend is `redis` (leave blank to inherit `REDIS_URL`)
   - Plan codes + per-feature soft/hard limits; the wizard emits `var/reports/usage-entitlements.json` as the operator artifact.
3. **Plan metadata** – Run `python -m starter_cli.app usage sync-entitlements` to upsert plan features from `var/reports/usage-entitlements.json` into `plan_features`. Use `--dry-run` to preview and `--prune-missing` to delete stale rows.
4. **Deploy / restart API** – When FastAPI boots it wires `UsageRecorder` + `UsagePolicyService` automatically whenever billing + guardrails are enabled.
5. **Smoke test** – Issue two requests against `/api/v1/chat`: one baseline (expect 200) and one where you temporarily lower a plan limit via SQL to force a 429. Confirm the error payload contains `code=usage_limit_exceeded`, `plan_code`, and `feature_key`.

### Seeding plan entitlements

```
cd packages/starter_cli && python -m starter_cli.app usage sync-entitlements \
  --plan starter --plan pro \
  --prune-missing
```

- Defaults to `var/reports/usage-entitlements.json`; override with `--path` when promoting artifacts between environments.
- `--dry-run` reports inserts/updates/deletes without touching the database (safe for CI audits).
- `--allow-disabled-artifact` lets you replay artifacts generated while guardrails were disabled, which is useful when reusing answers between environments.
- The command errors if the target plan code does not exist, so seed plans via Stripe/migrations before syncing entitlements.

### Exporting dashboard artifacts

Run the CLI exporter whenever operators need an audit-friendly snapshot of usage vs. plan limits:

```
cd packages/starter_cli && python -m starter_cli.app usage export-report \
  --tenant acme \
  --plan starter \
  --period-start 2025-11-01T00:00:00Z \
  --period-end 2025-12-01T00:00:00Z
```

- JSON and CSV artifacts land in `var/reports/usage-dashboard.{json,csv}` unless overridden with
  `--output-json/--output-csv`. Pass `--no-json` or `--no-csv` to disable one of the formats.
- Use `--feature input_tokens --feature output_tokens` to reduce payload size when sharing with
  finance/ops stakeholders.
- `--warn-threshold` controls when a feature is marked as `approaching` in the report (defaults to 80%).
- Artifacts are safe to check into the operator evidence bundle alongside the wizard answers files.

## Monitoring & Alerting

### Prometheus Metrics

| Metric | Description | Sample query |
| --- | --- | --- |
| `usage_guardrail_decisions_total{decision,plan_code}` | Count of guardrail evaluations per decision (`allow`, `soft_limit`, `hard_limit`). | `sum by (plan_code, decision) (increase(usage_guardrail_decisions_total[5m]))` |
| `usage_limit_hits_total{plan_code,limit_type,feature_key}` | Hard/soft limit hits keyed by plan + feature. Soft-limit entries also fire when `USAGE_GUARDRAIL_SOFT_LIMIT_MODE=warn`. | `sum by (feature_key, plan_code) (rate(usage_limit_hits_total{limit_type="hard_limit"}[5m]))` |
| `rate_limit_hits_total{quota,scope}` | Reference metric to distinguish rate-limit noise from usage guardrail blocks. | `sum by (quota) (increase(rate_limit_hits_total[5m]))` |

Dashboards should chart:
- Allow vs. block trends per plan.
- Top features that trigger hard limits (stacked bar from `usage_limit_hits_total`).
- Soft-limit warnings by tenant count (derived from logs or the metric label set).

Alert suggestions:
- **Hard-limit flood** – `sum(rate(usage_limit_hits_total{limit_type="hard_limit"}[1m])) > 5` for 5 minutes. Indicates runaway tenants or misconfigured limits.
- **Policy failure** – Alert on HTTP 402 spikes coming from `usage_policy_configuration_error` (see logs).

### Logs

`app/api/dependencies/usage.py` emits structured JSON for every violation:
- `code`: `usage_limit_exceeded` or `usage_soft_limit_exceeded`.
- `plan_code`, `tenant_id`, `feature_key`, `limit_type`, `limit_value`, `usage`, `window_start`, `window_end`.
- Hard-limit blocks log at `ERROR` right before the 429 is raised; soft limits log at `WARNING` but still allow the request.

Ingestion tips:
- Route the JSON logs through OTLP (default via `LOGGING_SINKS=otlp` + the bundled collector) so they land in your SIEM with preserved fields.
- Pair log volume with counter data by charting `count_over_time({code="usage_limit_exceeded"}[5m])` in Loki or equivalent.

## Troubleshooting Playbook

| Symptom | Likely Cause | Actions |
| --- | --- | --- |
| 429 with `usage_limit_exceeded` but tenant insists they upgraded | Subscription metadata is stale or cached totals are outdated. | 1) Inspect `usage_guardrail_decisions_total` for the tenant’s plan. 2) Flush/adjust the Redis or materialized-view cache (set `USAGE_GUARDRAIL_CACHE_TTL_SECONDS=0` temporarily). 3) Verify plan features in Postgres/Stripe match the entitlement report emitted by the CLI. |
| 402 `usage_policy_configuration_error` | Tenant lacks an active subscription or plan definition. | Use `BillingService.get_subscription` via the admin shell or inspect the `tenant_subscriptions` table. Seed missing records and retry. |
| Requests slip through even though usage is above the soft limit | Soft-limit mode is set to `warn`. | Flip `USAGE_GUARDRAIL_SOFT_LIMIT_MODE=block` via the wizard/infra secrets and redeploy. |
| Metrics missing | `/metrics` endpoint not scraped or guardrails disabled. | Hit `GET /metrics` and ensure both counters appear; verify `ENABLE_USAGE_GUARDRAILS` is true in runtime env + FastAPI logs show "Usage guardrails enabled" during boot. |

## Operational Checklist

- [ ] `ENABLE_USAGE_GUARDRAILS=true` and cache/soft-limit env vars managed via the CLI wizard or secrets store.
- [ ] `usage_guardrail_decisions_total` present on the Prometheus `/metrics` output and ingested into dashboards.
- [ ] Alerts configured for hard-limit spikes and policy configuration errors.
- [ ] `cd packages/starter_cli && python -m starter_cli.app usage sync-entitlements` has been run after every plan limit change (use `--dry-run` first in CI).
- [ ] `cd packages/starter_cli && python -m starter_cli.app usage export-report` captured the current billing period snapshot and artifacts stored under `var/reports/`.
- [ ] Runbook + plan entitlements reviewed whenever pricing/plan tiers change.
- [ ] `var/reports/usage-entitlements.json` stored with the rest of the operator artifacts for auditability.
