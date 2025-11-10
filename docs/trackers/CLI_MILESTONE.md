# CLI Milestone Tracker

_Last updated: 2025-11-10_

## Purpose

Document the outstanding deliverables we have already promised for the bootstrap CLI so we can plan implementation work, staffing, and verification. All scope items below come directly from active/open tracker entries or specs that defer action to the CLI rather than the FastAPI backend.

## Milestone Summary

| Milestone | Focus | Issue Coverage | Target Outcomes | Status |
| --- | --- | --- | --- | --- |
| M1 – Secrets & Key Management | Replace repo secrets with operator-supplied values and wire Vault Transit for service-account issuance. | SEC-007, SEC-008 | CLI rotates peppers/keys, stores them in Vault (or guarded local files), and configures AuthService to require Vault-signed requests outside dev. | In Progress |
| M2 – Provider & Infra Provisioning | Enforce required third-party keys, managed Redis configuration, and migration/plan seeding workflows. | OPS-003, INFRA-004, DB-007 | CLI refuses to finish until Stripe/Resend/OpenAI keys and Redis endpoints are validated, then runs `make migrate` + plan seeding with recorded outputs. | In Progress |
| M3 – Tenant & Observability Guardrails | Ensure tenant attribution, log forwarding, and GeoIP enrichment are configured during setup. | BE-012, OBS-006, OBS-007 | CLI scaffolds tenant-aware metadata defaults, enables JSON logging or external sinks, and wires GeoIP providers (or explicit "none" choice). | In Progress |
| M4 – Signup & Worker Policy Controls | Capture launch-time decisions for signup exposure and background worker scaling. | AUTH-011, OPS-004 | CLI toggles public vs invite-only signup, sets rate/quota caps, and documents whether a dedicated Stripe retry worker deployment is required. | In Progress |

### Architecture Guardrails for CLI Implementation

- **Single entrypoint:** Consolidate all operator tooling (existing auth token helper, future setup workflows, Stripe helpers, frontend env bootstrap) under a dedicated repo-root CLI package (e.g., `cli/`) exposed via `python -m anything_agents.cli` plus a Hatch/Make alias so both backend and frontend setup flows share the same surface.
- **Modular subcommands:** Keep functional areas in separate modules (`auth.py`, `setup.py`, `stripe.py`, etc.) but expose them via shared argument parsing so interactive setup flows can reuse secrets/key helpers already defined in the auth CLI.
- **Interactive + headless modes:** Default to a guided TUI/prompt flow for first-time setups while supporting flag-driven, non-interactive execution for CI/CD. Each milestone deliverable should note both interaction models.
- **Shared helpers:** Extract the current Vault signing/key-loading utilities from `app/cli/auth_cli.py` into a reusable `common.py` so future setup commands inherit the same security posture without duplication.
- **Required vs optional prompts:** Every interactive step labels variables as "required before production" vs "optional/default-ok" (peppers, Stripe/Resend keys, Vault inputs, JWKS/cache knobs) and the CLI enforces entry of the high-risk secrets before proceeding.
- **Guided wizard UX:** Implement a progress-based wizard with profiles (local dev / staging / production), dependency-aware branching (billing → Stripe, email → Resend, Vault → transit inputs), and optional dry-run/headless modes so operators across skill levels can configure backend + frontend envs in one pass.
- **Implementation roadmap:** Execute in phases—(1) scaffold repo-root CLI package + entrypoint, (2) migrate existing auth and Stripe scripts into the new structure, (3) ship the core setup wizard shell, (4) layer feature sections (secrets, providers, tenant/observability, signup/worker) iteratively, and (5) add frontend env generation and non-interactive flags before deprecating legacy scripts.

### Status Update – 2025-11-10

- Phase 1 remains complete: `anything_agents.cli` is the single entrypoint (Hatch/Make/`aa-cli`) and now owns the Stripe + auth flows outright (legacy shims removed).
- Phase 2 now covers the full milestone surface: the setup wizard is modularized under `anything_agents/cli/setup/*`, supports headless execution via `--non-interactive` + `--answers-file`/`--var`, verifies Vault Transit connectivity, validates Redis/Stripe/Resend inputs, offers optional migration + seeding hooks, captures tenant slug/logging sink/GeoIP decisions, and records signup + worker policy posture (including retry-worker deployment mode).
- Note (2025-11-10): `auth-cli` and `scripts/stripe/setup.py` have been removed in favor of the consolidated CLI (`python -m anything_agents.cli …`). Update automation to call the new entrypoint.
- Next refinements: extend the backend to consume the new logging/GeoIP settings and add CLI report exporters for infra audit trails.

## Detailed Scope

### M1 – Secrets & Key Management (SEC-007, SEC-008)

- **Secret rotation workflow:** Prompt for new signing keys, JWT peppers, and refresh-token peppers; support generating Ed25519 keysets; write them to Vault or encrypted local storage. Fail fast if operators attempt to reuse starter secrets.
- **Env template alignment:** Emit `.env.local` entries with inline comments mirroring the template so operators understand which knobs can remain at defaults when features are disabled.
- **Vault-onboarding helper:** Ask for Vault address, authentication method (AppRole/OIDC/mTLS), and Transit mounts. Validate connectivity and store configuration in `.env`/`.env.compose` equivalents consumed by FastAPI.
- **Service-account hardening:** Provide guided steps (and linting) that ensure `/auth/service-accounts/issue` is locked to Vault-signed requests whenever Vault is available, falling back to `dev-local` only in explicitly flagged environments.
- **Documentation artifacts:** Generate or update runbooks explaining how to rotate keys later using the same CLI flow, referencing `auth keys rotate` for parity with existing tooling.

### M2 – Provider & Infra Provisioning (OPS-003, INFRA-004, DB-007)

- **Third-party credential capture:** Require Stripe secret/webhook keys, Resend toggles (`RESEND_EMAIL_ENABLED`, `RESEND_API_KEY`, `RESEND_DEFAULT_FROM`, `RESEND_BASE_URL`, optional template IDs), and the OpenAI API key before continuing; optionally capture Tavily. Persist validated values to the appropriate env files, label them as required vs optional in the generated summary, and redact when printing logs.
- **Plan map + billing config:** Walk operators through selecting plans (Starter/Pro), update `STRIPE_PRODUCT_PRICE_MAP`, and sync with the Stripe setup script when present.
- **Managed Redis guidance:** Collect Redis URLs, enforce TLS/auth flags, and encourage separate logical DBs for rate limiting, nonce cache, and billing streams. Emit warnings and docs if users insist on single-instance dev defaults.
- **Migration + seeding runner:** Wrap `make migrate` and plan-seeding helpers so first deploys run schema migrations and Stripe catalog seeding in a predictable order with logged timestamps for auditability.

### M3 – Tenant & Observability Guardrails (BE-012, OBS-006, OBS-007)

- **Tenant metadata validation:** During setup, require a default tenant slug/UUID and surface guidance for integrating tenant-aware metadata into conversation ingestion so `tenant_id` never falls back to the shared “default”.
- **Structured logging sink selection:** Offer presets (stdout JSON, Datadog, OTLP/HTTP). Update FastAPI settings + middleware toggles and verify sample log emission when operators choose anything other than stdout.
- **GeoIP provider integration:** Let users opt into a provider (MaxMind, IP2Location, etc.) by supplying API keys/license paths or intentionally choose `null` so dashboards show "unknown" with justification. Persist config and update observability docs accordingly.

### M4 – Signup & Worker Policy Controls (AUTH-011, OPS-004)

- **Signup exposure & quotas:** Provide interactive prompts (or flags) to set `allow_public_signup`, invite-only toggles, per-IP tenant creation quotas, and rate-limit overrides. Emit summaries so operators can document their chosen posture.
- **Retry worker deployment guidance:** Detect whether the Stripe retry worker should run inside the main API pod or separately; update `ENABLE_BILLING_RETRY_WORKER`/`ENABLE_BILLING_STREAM_REPLAY` values and print the recommended deployment topology.
- **Policy audit artifacts:** Produce a short report (Markdown/JSON) summarizing signup + worker decisions that can be checked into infra repos for later review.

---

**Next actions:** scope acceptance tests per milestone, align owners, and connect this tracker to the ISSUE_TRACKER entries above so progress stays in sync.
