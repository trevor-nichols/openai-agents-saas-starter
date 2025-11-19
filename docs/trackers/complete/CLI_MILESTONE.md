# CLI Milestone Tracker

## Vision
Deliver a clean implementation of the redesigned Starter CLI wizard so operators can complete all foundational setup tasks (infra, secrets, providers, env files) in one guided pass, leaving only `hatch run serve` and `pnpm dev` afterward.

## Guiding Principles
- Automation-first: Docker, Vault, Stripe, and verification flows run automatically when enabled.
- Dependency-aware UX: prompts and tasks appear only when their prerequisites are satisfied.
- Durable artifacts: every run produces auditable JSON/Markdown plus structured automation logs.
- Operator empathy: the wizard surfaces progress, retries, and remediation steps without leaving the UI.

## Milestones
| Phase | Description | Deliverables | Owner | Status | Target |
| --- | --- | --- | --- | --- | --- |
| M1 – Schema & Engine | Introduce declarative prompt/automation schema, evaluator, and persisted wizard state. Retrofit existing sections to honor skip-logic while keeping the legacy console UI available behind `--no-tui`. | `starter_cli/workflows/setup/schema.yaml`, graph evaluator, skip-logic tests, updated audit to record dependency outputs. | Platform Foundations | ✅ Complete (2025-11-17) | 2025-11-24 |
| M2 – TUI Shell | Build Rich-based UI shell with navigation rail, context forms, and streaming log pane. Feature-flag with `--no-tui` until stable, then default on. | `starter_cli/workflows/setup/ui/*`, navigation + log widgets, accessibility review, fallback flag. | Platform Foundations | ✅ Complete (2025-11-17) | 2025-12-01 |
| M3 – Automation Expansion | Extend `InfraSession` automation to manage Docker, Vault, Stripe seeding, migrations, Redis warm-up, and GeoIP downloads with retry + telemetry hooks. | Updated `infra.py`, new automation handlers, verification artifact schema bump, regression tests. | Platform Foundations | ✅ Complete (2025-11-17) | 2025-12-08 |
| M4 – Final UX & Exit Checklist | Polish dependency-driven forms, introduce final checklist (only `hatch run serve`/`pnpm dev` remain), add "keep Docker running" toggle, and refresh CLI docs. | Updated wizard copy, summary templates, README/AGENTS notes, screencast. | Platform Foundations | ✅ Complete (2025-11-17) | 2025-12-12 |
| M5 – Package Extraction | Split the CLI into adapters/commands/services/workflows, add the new composition root, migrate wizard/secrets workflows into `starter_cli/workflows`, and co-locate CLI tests under `starter_cli/tests`. | New `app.py` + `container.py`, adapters/core/services modules, refreshed `SNAPSHOT.md`, updated docs + trackers, tests relocated from `api-service/tests`. | Platform Foundations | ✅ Complete (2025-11-18) | 2025-12-05 |

## Risks & Mitigations
- **Schema drift** between CLI and backend env inventory → add contract tests against `starter_cli/core/inventory.py`.
- **Operator confusion during transition** → keep legacy mode available and document flags prominently.
- **Automation flakiness** (Docker/Stripe) → implement exponential backoff + surfaced remediation text per milestone.

## Next Actions
1. Dogfood the new wizard with at least two fresh checkouts and capture feedback for the screencast.
2. Add regression tests that cover schema skip-logic plus automation fallbacks (tracked under QA backlog).
3. Socialize the new `--auto-*` flags and dashboard workflow with the ops and DX channels.
4. Roll out the `--export-answers` helper + production `--strict` alias to onboarding docs and gather DX feedback after two production runs.
