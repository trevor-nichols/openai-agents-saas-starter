<!-- SECTION: Title -->
# Starter CLI One-Stop Milestone

_Last updated: November 15, 2025_

## Objective
Transform the Starter CLI from an env-file wizard into a single operator entrypoint that can validate prerequisites, provision local infra (Postgres/Redis/Vault), capture secrets, seed Stripe, and emit auditable status reports so any engineer—or newcomer evaluating the repo—can stand up the full stack with minimal context.

## Scope & Exit Criteria
| Area | In Scope | Exit Criteria |
| --- | --- | --- |
| Prerequisite detection | Docker/Compose, Hatch, Node/pnpm, Stripe CLI | `infra deps` expands into structured telemetry + actionable tips surfaced in the wizard pre-check. |
| Guided automation | Setup wizard, secrets onboarding, Stripe provisioning | Wizard gains opt-in automation toggles (`--auto-infra`, `--auto-stripe`) and surfaces when automation succeeded/failed, falling back to manual steps gracefully. |
| Infra orchestration | Postgres + Redis compose stack, Vault dev signer | CLI can start/stop infra through existing Just recipes (`infra compose`, `infra vault`) and capture logs/summaries for the milestone report. |
| Provider workflows | Vault dev/HCP, AWS Secrets Manager, Azure Key Vault, Infisical | Each runner reports verification artifacts (e.g., transit probe, AWS `GetSecretValue`) and records env deltas in the milestone summary. |
| Stripe enablement | Product/price seeding, keys + webhook secrets, billing toggles | `stripe setup` can be invoked from the wizard when credentials are available, and its outputs are appended to the wizard audit. |
| Reporting & UX | Summary view + JSON artifact | Every automation step emits structured results in `var/reports/cli-one-stop-summary.json` plus console badges so users can share proof of setup (resume/demo ready). |

## Phase Plan
| Phase | Focus | Status | Target |
| --- | --- | --- | --- |
| P1 Foundation | Expand `infra deps` telemetry + wizard preflight hook. | Completed | Nov 15 |
| P2 Wizard UX | Add automation toggles, context-aware prompts, and failure fallbacks. | Completed | Nov 15 |
| P3 Infra Automation | Wire `infra compose` + `infra vault` controls (start/stop/status/log capture). | Completed | Nov 15 |
| P4 Provider Deepening | Surface Vault/AWS/Azure/Infisical verification artifacts + secret diffs in reports. | Completed | Nov 15 |
| P5 Billing & Stripe | Embed `stripe setup` automation, capture plan metadata, enable billing toggles. | Completed | Nov 15 |
| P6 Reporting & Docs | Produce summary JSON + md snippet, update README + runbooks to market one-stop experience. | Completed | Nov 15 |

## Current Health Snapshot
| Capability | Status | Notes |
| --- | --- | --- |
| Env collection | ✅ Stable | Milestone wizard already covers all backend + frontend env vars with audit support. |
| Infra orchestration | ✅ Automated | InfraSession now boots/stops docker compose + Vault dev signer when automation is enabled, with dependency-aware gating and cleanup. |
| Secrets onboarding | ⚠️ Partial | Provider runners validate connectivity but don’t persist verification evidence into reports. |
| Stripe automation | ⚠️ Interactive only | Requires standalone `stripe setup`; env outputs aren’t merged back into wizard audit (pending Phase 5). |
| Auditability | ⚠️ Limited | `setup wizard --summary-path …` emits milestone data, but automation tasks have no structured success/failure records yet. |

## Key Deliverables
1. **Wizard Preflight Panel** – surfaces `infra deps` results at the start, blocking automation when prerequisites fail and offering quick fixes.
2. **Automation Hooks** – new flags (`--auto-infra`, `--auto-stripe`, `--auto-secrets`) that call the respective CLI subcommands within milestones, with streaming status updates.
3. **Infra Session Controller** – shared helper that starts/stops Docker compose + Vault dev signer, tails logs on failure, and attaches metadata to the audit.
4. **Provider Verification Ledger** – stores hashed evidence (e.g., Vault transit key name, AWS secret ARN) plus timestamp per provider in `var/reports`.
5. **Stripe Turnkey Flow** – optional embedded run that seeds plans, writes env vars, validates webhook endpoint reachability, and replays fixtures automatically.
6. **One-Stop Summary Artifact** – consolidated JSON + human-readable summary capturing all automation steps, ready to screenshot or attach in onboarding docs/resume.

## Setup Requirements Inventory (Source of Truth)
This section captures every prerequisite a new operator must satisfy today. Each row links back to the owning doc so implementation can reference authoritative details, and marks whether the one-stop milestone should automate it (`Auto?`).

### Backend (FastAPI) – from `api-service/README.md`
| Area | Manual Steps Today | Auto? | Notes/Dependencies |
| --- | --- | --- | --- |
| Python tooling | Install Python 3.11+, Hatch, project deps (`pip install 'api-service[dev]'`, `hatch env create`). | ⚠️ Assist | CLI can confirm Hatch + deps (via `infra deps`). Full install remains manual but add guidance/remediation text. |
| Env file | Copy `.env.local.example` → `.env.local`, fill every secret (peppers, keys, Vault vars). | ✅ Target | Wizard already collects values; automation ensures file creation plus diff logging. |
| Secrets & peppers | Generate `SECRET_KEY`, `AUTH_*` peppers, session salts. | ✅ Target | Wizard milestone M1 covers; ensure outputs flagged in summary with “generated” markers. |
| Persistence config | Supply `DATABASE_URL`, `REDIS_URL`, `BILLING_EVENTS_REDIS_URL`, `AUTO_RUN_MIGRATIONS`. | ✅ Target | Wizard M2 collects; automation should validate connectivity post-compose. |
| Providers (AI/Email) | Populate `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `RESEND_*`, etc. | ⚠️ Assist | Wizard prompts; automation limited to validation (ping key endpoints when safe). |
| Vault transit | Provide `VAULT_*` & optionally run `just vault-up` + verification script. | ✅ Target | Auto-start dev signer (with consent) + run transit probe; record evidence hash. |
| Stripe + billing | Run `stripe setup`, seed plans, capture webhook secret, set `ENABLE_BILLING*`. | ✅ Target | Embed CLI `stripe setup`, ensure env update + summary capture. |
| Migrations | `just migrate` after infra up. | ⚠️ Assist | Provide optional hook post-infra start to run migrations, but keep opt-in due to destructive nature. |

### Frontend (Next.js) – from `web-app/README.md`
| Area | Manual Steps Today | Auto? | Notes/Dependencies |
| --- | --- | --- | --- |
| Node toolchain | Install Node 20+, pnpm; run `pnpm install`. | ⚠️ Assist | CLI can verify versions via `infra deps` and prompt to run `pnpm install`, but not install automatically. |
| Env file | `web-app/.env.local` with API URL, cookies, Playwright base URL. | ✅ Target | Wizard already writes; ensure automation regenerates file when backend URL changes. |
| API client | Run `pnpm generate` (HeyAPI). | ⚠️ Assist | Document reminder post-wizard; optional future hook but not in current milestone scope. |
| Dev server | `pnpm dev` once backend is reachable. | ℹ️ Inform | Out of scope to auto-launch UI, but summary should list command. |

### CLI & Infra (root README, starter_cli/README.md, justfile)
| Area | Manual Steps Today | Auto? | Notes/Dependencies |
| --- | --- | --- | --- |
| Prereq audit | Run `python -m starter_cli.app infra deps`. | ✅ Target | Wizard preflight should call and display structured output. |
| Docker services | `just dev-up`, `just dev-down`, `just dev-logs`, `just dev-ps`. | ✅ Target | `InfraSession` now issues `infra compose up/down` when automation is enabled, captures failures/logs, and falls back to manual commands when gated. |
| Vault dev signer | `just vault-up`, `just vault-down`, `just vault-logs`, `just verify-vault`. | ✅ Target | Hooked into Secrets milestone when Vault automation enabled. |
| Stripe CLI presence | Manual install + `stripe login`. | ✅ Target | Preflight now checks for the `stripe` binary/version; automation toggles rely on this signal before running provisioning flows. |
| Reports | Wizard writes `var/reports/setup-summary.json`. | ✅ Target | Extend to include automation transcript + artifacts. |

### External Providers & Security
| Provider | Manual Workflow | Auto? | Notes |
| --- | --- | --- | --- |
| Vault (dev/HCP) | Choose runner via `secrets onboard vault-*`, manually export env updates. | ✅ Target | CLI to store verification metadata + optionally run `infra vault` helpers. |
| AWS Secrets Manager / Azure Key Vault / Infisical | Run `secrets onboard <provider>`, paste outputs into env files. | ⚠️ Assist | Automation limited to capturing outputs + validation evidence; actual provisioning remains manual. |
| Stripe | `stripe setup` interactive prompts. | ✅ Target | Embed inside wizard with resume support. |
| Resend / Email | Manual API key creation, update `.env.local`. | ⚠️ Assist | CLI can validate API key but not create provider accounts. |

> This inventory should stay in sync with root `README.md`, `api-service/README.md`, and `web-app/README.md`. Any new requirement uncovered during implementation must be added here first, then reflected in the relevant docs.

## Milestone Backlog
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Extend `infra deps` to emit machine-readable JSON + remediation text; invoke it automatically at wizard start. | Platform Foundations | Completed | Nov 22 |
| 2 | Introduce wizard flags/ctx for automation (`auto_infra`, `auto_stripe`, `auto_secrets`) and expose toggles in interactive prompts. | Platform Foundations | Completed | Nov 15 |
| 3 | Build `InfraSession` helper encapsulating compose/vault start/stop/log capture; integrate into wizard Secrets/Providers milestones. | Platform Foundations | Completed | Nov 15 |
| 4 | Record provider verification evidence (Vault transit probe, AWS Secret ARN, Azure key vault URI, Infisical workspace ID) inside the wizard audit + summary file. | Platform Foundations | Completed | Nov 15 |
| 5 | Embed `stripe setup` flow post-provider milestone (respecting headless answers); persist plan metadata + billing toggles back into context/env writers. | Platform Foundations | Completed | Nov 15 |
| 6 | Enhance summary writer to include automation transcript + links to collected artifacts, writing to `var/reports/cli-one-stop-summary.json`. | Platform Foundations | Todo | Dec 4 |
| 7 | Update root README + starter_cli/README with “One-Stop Mode” section, usage examples, and resume-friendly highlights. | Platform Foundations | Todo | Dec 6 |

## Implementation Plan
1. **Preflight Telemetry & Guardrails**
   - Expand `infra deps` to output structured JSON (versions, pass/fail, remediation hints) and a summarized table.
   - Add a wizard preflight step that consumes this data, blocks automation when critical checks fail, and surfaces fix instructions inline.
2. **Wizard Context Enhancements**
   - Extend the wizard context with automation flags (`auto_infra`, `auto_stripe`, `auto_secrets`) and persisted status per milestone (pending/running/succeeded/failed).
   - Update CLI argument parsing plus interactive prompts to toggle these flags, storing operator consent for audit logs.
3. **InfraSession Orchestrator**
   - Implement a reusable helper that wraps `infra compose` + `infra vault` commands, capturing stdout/stderr, exit codes, and emitting structured events back to the wizard UI.
   - Ensure automatic cleanup (stop containers, summarize volume locations) on success/failure, and expose manual fallback commands in the transcript.
4. **Provider Verification Ledger**
   - Standardize a `VerificationRecord` model that stores provider type, evidence hash/identifier, timestamp, and command metadata.
   - Instrument Vault, AWS Secrets Manager, Azure Key Vault, and Infisical runners to emit records whenever connectivity checks succeed; serialize these into the wizard context and final summary artifact.
5. **Embedded Stripe Automation**
   - Allow the Providers milestone to invoke `stripe setup` once prerequisites pass (Stripe CLI present, secrets captured).
   - Pipe outputs (plan IDs, product/price map, webhook secret) back into the wizard’s env writer and verification ledger, plus handle headless mode by reading answers files for required inputs.
6. **Reporting & Artifact Generation**
   - Enhance the summary writer to include: preflight results, automation transcript (per step timing/status), provider verification ledger, and any generated env diff.
   - Default output to `var/reports/cli-one-stop-summary.json` with optional Markdown snippet for README/Resume screenshots.
7. **Documentation & DX Polish**
   - Update root README + `starter_cli/README.md` with a “One-Stop Mode” walkthrough (usage, flags, sample output, troubleshooting).
   - Link the milestone tracker and summary artifact locations so future reviewers can trace exactly what the automation covered.

## Risks & Mitigations
1. **Docker Access in CI** – Automated compose runs may fail under limited permissions. _Mitigation_: detect `CI=true` and downgrade automation to instructions-only mode while marking status as “skipped due to CI constraints.”  
2. **Secrets Leakage** – Capturing verification artifacts risks logging sensitive values. _Mitigation_: hash or redact secrets before persisting; store only identifiers (ARNs, key IDs) plus timestamps.  
3. **Long-Running Stripe Calls** – Embedding `stripe setup` can slow the wizard. _Mitigation_: add clear progress output, allow `--skip-stripe-cli`, and support resuming from cached milestone states.  
4. **State Drift** – Auto-started Docker services may remain running after failures. _Mitigation_: `InfraSession` ensures `finally` cleanup and exposes manual remediation instructions in the summary.  
5. **User Trust** – Automating infra for newcomers might feel intrusive. _Mitigation_: default to prompts explaining what will change, require explicit consent, and document fallback commands.

## Changelog
- **2025-11-15**: Tracker created to scope one-stop automation initiative (env preflight, infra orchestration, provider verification, Stripe embedding, reporting).
- **2025-11-15**: Stage 1 complete — `infra deps` now emits structured JSON (status, version, remediation hints) and the setup wizard runs a preflight, persisting dependency telemetry for later automation gates.
- **2025-11-15**: Stage 2 (Wizard UX) — Added automation toggles/flags with dependency-aware blocking, recorded preferences in the wizard context/audit, and expanded preflight checks to include the Stripe CLI.
- **2025-11-15**: Stage 3 (Infra automation) — Introduced `InfraSession`, wiring `infra compose`/`infra vault` run loops into the wizard with cleanup + log capture; automation now starts/stops Docker + Vault when enabled and records status in the milestone summary.
- **2025-11-15**: Stage 4 (Provider verification ledger) — Extended secrets providers to emit verification artifacts (Vault, AWS Secrets Manager, Azure Key Vault, Infisical) and wired them into a shared ledger plus the wizard summary (`verification_artifacts` block) so audits capture identifiers + status.
- **2025-11-15**: Stage 5 (Stripe automation) — Embedded the Stripe setup flow behind the automation flag, added dependency/headless gating, logged automation status, and recorded plan/webhook verification artifacts surfaced in the Providers milestone + summary.
- **2025-11-15**: Stage 6 (Reporting & Docs) — Added Markdown summary output, automation transcript, and verification ledger references; updated README/CLI docs to describe One-Stop Mode artifacts so the milestone can be archived.
- **2025-11-16**: Regression fix — Setup wizard now serializes `AUTH_AUDIENCE` as a JSON array while the FastAPI settings parser accepts both JSON and comma-separated formats, ensuring CLI-generated configs remain compatible with the auth validators.
- **2025-11-16**: Signup controls — Wizard prompts capture the new layered throttling knobs (`SIGNUP_RATE_LIMIT_PER_*`, `SIGNUP_CONCURRENT_REQUESTS_LIMIT`), audit output verifies them, and docs reference the defaults so AUTH-011 Phase 3 stays in sync with CLI automation.
