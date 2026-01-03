<!-- SECTION: Metadata -->
# Milestone: Terraform Export Pipeline

_Last updated: 2026-01-03_  
**Status:** Completed (Review remediation in progress)  
**Owner:** Platform Foundations  
**Domain:** Console / Infra  
**ID / Links:** [docs/ops/hosting-overview.md], [ops/infra/**], [packages/starter_console/SNAPSHOT.md]

---

<!-- SECTION: Objective -->
## Objective

Ship a safe, optional Terraform tfvars export pipeline in the Starter Console so teams can bootstrap AWS/Azure/GCP blueprints without locking themselves into any one path or leaking secrets by default.

---

<!-- SECTION: Review Decisions (Post-Implementation) -->
## Review Decisions (2026-01-03)

**Owner:** Platform Foundations  

1. **Validation parity:** Filled-mode validation must mirror Terraform validations exactly.  
   - Accepts `api_env` / `api_secrets` map keys when Terraform does.
   - Honors `auth_key_storage_provider` fallback to `secrets_provider` when unset.
2. **Secrets handling:** `api_secrets` / `web_secrets` are treated as sensitive and redacted by default.
3. **Registry rules:** Enforce registry credential requirements exactly as Terraform does:
   - AWS: `registry_username` + `registry_password` when `registry_server` is set.
   - Azure: `registry_username` + (`registry_password` or `registry_password_secret_id`) when `registry_server` is set.
   - GCP: no extra enforcement beyond Terraform.
4. **Maintainability:** Modularize `terraform_spec` into provider-specific modules plus shared models.

---

<!-- SECTION: Review Addendum (Post-Review) -->
## Review Addendum (2026-01-03)

**Owner:** Platform Foundations  

### Additional decision
- **Validation parity scope:** Treat *all* Terraform `validation {}` rules as required parity, including ranges, enums, cross-field comparisons, and disallowed map keys. This is the long-term, professional approach to avoid drift and keep CLI failures aligned with Terraform behavior.

### Review findings
1. **Validation gaps:** Export validation currently enforces required/any-of rules but does not cover non-required Terraform validations (ranges, enums, cross-field comparisons, and map-key constraints) across AWS/Azure/GCP.  
2. **Test gaps:** Unit tests validate schema coverage and a subset of required/alias rules but do not cover the missing validation behaviors.  
3. **Repo hygiene:** Several deliverables for the milestone are untracked and must be staged to ensure review completeness (docs + contracts + console + tests).

### Review findings (delta)
1. **AWS validation parity:** `storage_provider` is not enforced in the spec/export validation, so filled mode can accept non-`s3` values that Terraform rejects.  
2. **Map-key alias parity:** Dotted-path checks (e.g., `api_env.AUTH_KEY_SECRET_NAME`) require non-empty values, but Terraform validations only require key presence. This can false-fail filled exports and violates the “accepts map keys” decision.  
3. **Docs example correctness:** The `api_secrets` CLI example uses escaped quotes inside single quotes, yielding invalid JSON in most shells.  
4. **Repo hygiene (verification):** Milestone deliverables remain untracked and must be staged before final review completion.

### Review sign-offs (2026-01-03)
- ✅ AWS `storage_provider` validation parity (spec + tests)
- ✅ Map-key alias parity for requirement checks (key presence semantics)
- ✅ Docs example JSON correctness + snippet validation
- ✅ Repo hygiene: deliverables staged for review

### Review follow-ups (2026-01-03)
#### Findings
1. **Validation presence semantics:** String presence checks always trimmed whitespace, diverging from Terraform rules that use raw length/equality (registry credential gating, `redis_auth_token`).  
2. **Public API completeness:** `TerraformRangeCheck` was not re-exported from `starter_contracts.infra`, so consumers could not import the full validation check surface.  
3. **Extra-var collisions:** Case-sensitive checks allowed `--extra-var` keys to collide with known variables or each other by casing only.

#### Sign-offs (2026-01-03)
- ✅ Presence semantics now match Terraform per rule (raw vs trimmed).
- ✅ `TerraformRangeCheck` exported from `starter_contracts.infra` and `starter_contracts.infra.terraform_spec`.
- ✅ Extra-var collision checks are case-insensitive.

### Recommendations
- Add provider-level validation rules to the Terraform spec (shared models + provider modules).  
- Enforce validation rules in the export service for `filled` mode, and surface warnings in `template` mode.  
- Expand unit tests to cover the full validation matrix for AWS/Azure/GCP, including negative cases.

### Long-term professional approach (systemic)
- **Parity as a contract:** Treat `ops/infra/**/variables.tf` validations as the canonical contract; add a lightweight “parity checklist” for each provider that must be signed off when Terraform variables change.  
- **Spec-driven validation:** Keep validation rules in `starter_contracts` and ensure `TerraformExportService` consumes them without bespoke provider logic; this preserves clean layering and minimizes drift.  
- **Test matrix + regression locks:** Add validation matrix tests per provider (positive/negative) and keep a small golden set that proves key parity behaviors (map-key presence, enums, ranges, comparisons).  
- **Docs + examples as tested artifacts:** Add a tiny doc-snippet test or smoke harness to validate CLI examples that include JSON payloads; this prevents regressions in public-facing docs.  
- **Repository hygiene gates:** Enforce “no untracked deliverables” before review close-out using a simple pre-merge checklist or CI rule.

### Remediation (New)
- **Phase R5 – Full Terraform Validation Parity (Planned)**
  - Add validation rules for ranges, enums, cross-field comparisons, and disallowed map keys.
  - Wire validation into `TerraformExportService` and CLI warning output.
  - Add unit tests for each provider’s validation rules (negative + positive paths).
  - **Exit:** `hatch run lint`, `hatch run typecheck`, and `hatch run test unit -k terraform` green for `starter_contracts` + `starter_console`.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Canonical Terraform export schema lives in `starter_contracts` and covers AWS/Azure/GCP inputs.
- `starter-console infra terraform export` renders HCL (default) or JSON to a safe, gitignored path.
- Export merges inputs from CLI flags + answers file + env files with deterministic precedence.
- Secrets are **redacted by default**; `--include-secrets` is explicit and documented.
- Provider-specific required inputs render as placeholders when missing (template mode).
- Export validation mirrors Terraform validation rules (including map-key allowances and provider fallbacks).
- Docs: usage guide + hosting overview updates + console README.
- Tests: unit coverage for mapping/validation/redaction + CLI smoke.
- `hatch run lint` and `hatch run typecheck` pass after each phase.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Provider-agnostic export schema + provider-specific variable metadata.
- Export service that renders tfvars (HCL/JSON) and handles redaction.
- CLI command for headless export with deterministic defaults.
- Minimal documentation + examples for AWS/Azure/GCP.

### Out of Scope
- Automatic Terraform init/apply or state management.
- TUI wizard prompts for every Terraform variable (defer to a later milestone).
- Cloud-specific provisioning logic beyond the existing blueprints.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Schema + CLI-first design implemented. |
| Implementation | ⚠️ | Review remediation in progress to align validation + redaction. |
| Tests & QA | ⚠️ | Coverage expanding to include conditional rules + map-key validation. |
| Docs & runbooks | ⚠️ | Examples updated for new validation requirements. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

### Key decisions (answered)
- **Schema source of truth:** add a declarative Terraform input spec under `starter_contracts` (not parsing HCL) to keep console logic portable and testable.
- **Output default:** `var/infra/<provider>/terraform.tfvars` (gitignored, non-invasive).
- **Formats:** HCL default; JSON optional for CI pipelines.
- **Secrets:** redacted by default; `--include-secrets` required to emit literal values.
- **Modes:** `template` emits placeholders for required fields; `filled` requires inputs or fails fast.
- **Provider coverage:** AWS, Azure, GCP (based on `ops/infra/**/variables.tf`).
- **TUI:** full wizard integration deferred; CLI-first is the production-grade foundation.

### Export contract (high level)
- **Common inputs:** `project_name`, `environment`, `api_image`, `web_image`, `worker_image`, `api_env`, `web_env`, `api_secrets`, `web_secrets`, registry overrides, secrets provider + key storage values.
- **AWS required:** `region`, `db_password`, `storage_bucket_name`, `aws_sm_signing_secret_arn`, `auth_key_secret_arn`/`auth_key_secret_name`, `api_secrets` (DB/Redis).
- **Azure required:** `region`, `storage_account_name`, `key_vault_name`, `log_analytics_name`, `db_admin_password`, `auth_signing_secret_name`, `auth_key_secret_name`, `api_secrets` (DB/Redis).
- **GCP required:** `project_id`, `region`, `api_base_url`, `app_public_url`, `db_password`, `storage_bucket_name`, `gcp_sm_signing_secret_name`, `auth_key_secret_name`, `api_secrets` (DB/Redis).
- **Advanced inputs:** sizing, retention, private networking, TLS flags, scaling limits, etc. (included only when requested).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract & Schema

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Contracts | Add Terraform export schema + provider variable metadata under `starter_contracts/infra`. | ✅ |
| A2 | Contracts | Define required/optional flags, defaults, and secret classification. | ✅ |
| A3 | Tests | Unit tests validating schema completeness for AWS/Azure/GCP required inputs. | ✅ |

### Workstream B – Export Service

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Add `TerraformExportService` (HCL/JSON render + redaction). | ✅ |
| B2 | Console | Merge input sources (CLI > answers file > env files > defaults). | ✅ |
| B3 | Tests | Unit tests for redaction + template/filled modes. | ✅ |

### Workstream C – CLI Integration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Console | `starter-console infra terraform export` command + flags. | ✅ |
| C2 | Console | CLI UX guardrails (fail-fast on missing required in filled mode). | ✅ |
| C3 | Tests | Command-level tests (non-interactive, dry output). | ✅ |

### Workstream D – Docs & Examples

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Docs | Add usage guide + examples (HCL + JSON). | ✅ |
| D2 | Docs | Update hosting overview + console README references. | ✅ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Lock schema decisions + CLI UX | Milestone tracker approved | ✅ |
| P1 – Schema | Contract + required inputs + tests | A1–A3 complete; lint/typecheck green | ✅ |
| P2 – Export Service | Rendering + redaction + merge rules | B1–B3 complete; lint/typecheck green | ✅ |
| P3 – CLI | Command + validation + tests | C1–C3 complete; lint/typecheck green | ✅ |
| P4 – Docs | Usage guide + updates | D1–D2 complete | ✅ |

---

<!-- SECTION: Review Remediation Plan -->
## Review Remediation Plan

### Phase R1 – Schema Parity + Modularization (✅ 2026-01-03)
- Update Terraform spec rules to mirror provider validations (map-key allowances, auth key provider fallback).
- Mark `api_secrets` / `web_secrets` as sensitive by default.
- Modularize `starter_contracts.infra.terraform_spec` into provider modules + shared models.
- Expand contract tests to cover conditional/validation parity.
- **Exit:** `hatch run lint` + `hatch run typecheck` green for `starter_contracts`. (Completed 2026-01-03)

### Phase R2 – Export Service Alignment (✅ 2026-01-03)
- Update export validation to recognize map-key requirements.
- Ensure redaction respects new sensitivity flags and template placeholders.
- Add unit tests for new requirement flows (map keys, fallback logic).
- **Exit:** `hatch run lint` + `hatch run typecheck` + terraform-related unit tests green for `starter_console`. (Completed 2026-01-03)

### Phase R3 – CLI/UX Validation (✅ 2026-01-03)
- Validated CLI guardrails against updated validation (no CLI code changes required).
- CLI unit coverage exercised via `hatch run test unit -k terraform`.
- **Exit:** `hatch run lint` + `hatch run typecheck` + CLI unit tests green for `starter_console`. (Completed 2026-01-03)

### Phase R4 – Docs & Examples (✅ 2026-01-03)
- Updated Terraform export guide example to satisfy new validation requirements.
- Console README / hosting overview references unchanged (already current).
- **Exit:** docs reflect new rules; manual smoke ran: `starter-console --skip-env infra terraform export --provider gcp --mode template --format hcl`. (Completed 2026-01-03)

---

<!-- SECTION: Dependencies -->
## Dependencies

- Existing Terraform blueprints in `ops/infra/**` (already present).
- Starter Console environment schema (existing wizard/answers file).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Schema drift from Terraform variables | Med | Centralize schema + add unit coverage for required inputs per provider. |
| Secrets accidentally written to repo | High | Default output to `var/infra/**` + redaction by default + explicit `--include-secrets`. |
| Over-scoped UX | Med | CLI-first; TUI prompts deferred to later milestone. |
| Confusing defaults | Med | Template mode + documentation with concrete examples. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- `cd packages/starter_console && hatch run test unit -k terraform`
- Manual smoke: `starter-console infra terraform export --provider gcp --mode template --format hcl`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Feature is opt-in; no runtime behavior changes.
- Default output goes to `var/infra/**` (gitignored).
- Documented CLI flags for secrets redaction and JSON output.
- No migrations or backend changes.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-03 — Milestone drafted and aligned on CLI-first export approach.
- 2026-01-03 — Added Terraform export schema + tests for AWS/Azure/GCP coverage.
- 2026-01-03 — Implemented export service + unit coverage for template/filled modes.
- 2026-01-03 — Added Terraform export CLI command + command-level tests.
- 2026-01-03 — Published Terraform export docs + references.
