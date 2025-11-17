# DB Release Automation & Plan Seeding Milestone

_Last updated: November 17, 2025 — Archived_

## Objective
Create an auditable, automation-friendly release flow that guarantees Alembic migrations and billing plan seeding run in the correct order before Stripe/provider integrations are enabled. Fulfillment of DB-007 removes any manual guesswork from production deploys and allows CI/CD to gate releases on a single command.

## Current Gaps
1. `AUTO_RUN_MIGRATIONS` is intentionally `false` in production, so pods never self-heal schema drift.
2. Operators must remember to run `make migrate` + Stripe provisioning manually; steps vary by team and are not written down.
3. The Starter CLI wizard only offers an optional `Run make migrate now?` prompt—no enforcement, no logging, and no non-interactive pathway.
4. There is no post-run verification or artifact proving which Alembic revision/Stripe price IDs were applied, blocking audit and rollback readiness.

## Success Criteria
| Area | Requirement |
| --- | --- |
| Runbook | A single source of truth (`docs/ops/db-release-playbook.md`) that documents prerequisites, commands, verification queries, rollback steps, and evidence capture. |
| Automation | `python -m starter_cli.cli release db` orchestrates migrations + plan seeding with structured logging, timestamps, and JSON output for CI/CD. |
| Verification | Command fails fast when Alembic has pending revisions, when seeded plans are missing, or when Stripe provisioning/price map sync does not complete. |
| Artifact | Each run emits `var/reports/db-release-<timestamp>.json` capturing git SHA, Alembic head, seeded plan codes/ids, Stripe product/price IDs, and operator metadata. |
| Tracker closure | DB-007 row in `docs/trackers/ISSUE_TRACKER.md` references the runbook and CLI automation, status flipped to Resolved once tests/docs land. |

## Scope & Boundaries
| Area | In Scope | Out of Scope |
| --- | --- | --- |
| Backend schema | Running Alembic migrations, verifying seeded billing data. | Creating new schema, squashing or rewriting history. |
| Billing ops | Provisioning Stripe products/prices via existing CLI, syncing `STRIPE_PRODUCT_PRICE_MAP`. | Rebuilding the billing domain or adding new plans. |
| Tooling | Enhancing Starter CLI, docs, and Make targets to codify steps. | Changing FastAPI runtime to auto-run migrations in prod. |
| Observability | Capturing run artifacts + logs for audits. | Building a monitoring dashboard (future nice-to-have). |

## Deliverables
1. **Runbook** – `docs/ops/db-release-playbook.md` describing roles, prerequisites, env parity, exact commands, and rollback/recovery instructions.
2. **Release Command** – New CLI surface (`starter_cli.cli release db`) with interactive + headless modes, dependency gates, and JSON artifacts.
3. **Verification Guards** – SQL health checks (ensure baseline plans exist, Alembic head matches). Non-zero exit on failures.
4. **CI/CD Hook** – Example GitHub Actions snippet (or doc) demonstrating how to invoke the release command before promoting an image.
5. **Tracker Updates** – ISSUE_TRACKER + CLI milestone tracker referencing the runbook and automation, marking DB-007 complete when merged.

## Implementation Phases
| Phase | Focus | Owner(s) | Exit Criteria |
| --- | --- | --- | --- |
| P0 Alignment | Confirm prerequisites, choose CLI command name/flags, align on artifact schema. | Platform Foundations + Billing | Signed-off spec appended to this doc. |
| P1 Runbook | Draft and review `docs/ops/db-release-playbook.md`. Include manual fallback steps in case automation is unavailable. | Docs/Platform | Runbook approved + linked from README + ISSUE_TRACKER. |
| P2 Automation | Implement CLI release command, integrate `make migrate`, `stripe setup`, verification queries, JSON artifact writer, and headless flags. | CLI Team | Command passes local E2E test, emits artifact, handles failure paths. |
| P3 Tests & CI | Add unit tests/stubs for CLI, add migration verification test, wire CI example/gate, update trackers + changelog. | QA/CLI | Tests merge cleanly, DB-007 moved to Resolved. |

## Work Breakdown Structure
### 1. Documentation
- Draft the runbook with the following sections: Audience, Prereqs, Pre-flight checklist, Execution order, Post-run verification SQL, Failure handling, Evidence capture, FAQ.
- Add a short summary + link to `README.md` (backend section) and `docs/billing/stripe-runbook.md` (cross-reference for plan expectations).

### 2. Starter CLI Enhancements
- Add new `release` command group with `db` subcommand; reuse `wizard.context.run_migrations()` helper or introduce a shared `AutomationRunner` to unify logging.
- Parameters: `--non-interactive`, `--skip-stripe`, `--skip-db-checks`, `--summary-path`, `--json`.
- Steps inside command:
  1. Load env files via `EnvFile` helpers.
  2. Run `make migrate` via `subprocess` (same as wizard) but enforce success.
  3. Optionally run `stripe setup --non-interactive ...` or a lighter `stripe plans verify` when env already has product/price IDs.
  4. Query Postgres via async SQLAlchemy (reuse existing session factory) to confirm `billing_plans` table contains expected codes + non-null `stripe_price_id`.
  5. Write artifact to `var/reports/db-release-YYYYMMDDTHHMMSSZ.json` and echo summary.

### 3. Verification & Testing
- Unit tests: simulate success/failure paths with patched subprocess + Postgres session to assert proper exit codes/logs.
- Integration smoke: run command against SQLite/fakeredis (respecting repo `conftest.py`) to ensure hermetic tests pass.
- Post-merge: optional manual run documented in runbook for first deploy.

### 4. Tracker & Communication
- Update `docs/trackers/ISSUE_TRACKER.md` notes for DB-007 to point to the runbook + CLI command.
- Add row to `docs/trackers/complete/MILESTONE_STARTER_CLI_AUTOMATION_2025-11-15.md` changelog when automation lands.
- Announce in release notes / README so operators adopt the new flow.

## Testing & Validation Strategy
- **Pre-merge** – CLI unit tests (subprocess mocks), docs lint/check (vale optional), `hatch run typecheck` to keep repo health.
- **Post-deploy** – Runbook instructs capturing `alembic current` output, verifying `billing_plans` includes both codes, and confirming Stripe dashboard entries.
- **Rollback** – Document `alembic downgrade -1` + Stripe price archival guidelines inside the runbook.

## Risks & Mitigations
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Stripe automation unavailable in air-gapped CI | Release blocks. | Provide `--skip-stripe` flag with manual instructions + checklist for attaching evidence. |
| CLI command fails midway (migrations succeed, Stripe fails) | Partial state leads to confusion. | Command logs each step + writes partial artifact with status `failed`, runbook includes cleanup steps. |
| Env drift between `.env.local` and deployment secret store | Automation seeds wrong DB. | Runbook requires confirming target DATABASE_URL + includes `starter_cli config dump-schema` pointer. |

## Completion Summary
All deliverables graduated to documentation ownership. `docs/ops/db-release-playbook.md` contains the standing instructions, and future DB-007 follow-ups will spin new tickets if scope expands.

## Changelog
- **2025-11-17** – Milestone document created; initial runbook draft added under `docs/ops/db-release-playbook.md`.
- **2025-11-17** – Tracker archived under `docs/trackers/complete/` with runbook sign-off.
- **2025-11-17** – `starter_cli.cli release db` shipped with Stripe embedding, plan verification, and JSON artifacts; runbook + ISSUE_TRACKER updated and DB-007 closed.
