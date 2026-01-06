<!-- SECTION: Metadata -->
# Milestone: Configurable Setup Profiles

_Last updated: 2026-01-05_  
**Status:** Complete  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** [Docs: docs/contracts/setup-profiles.md]

---

<!-- SECTION: Objective -->
## Objective

Deliver a data-driven profile system for the Starter Console setup wizard that supports
default profiles, custom profiles, auto-detection, and TUI exposure while preserving
clean architecture and portability.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Profile contract implemented in `starter_contracts` with schema validation and tests.
- Default demo/staging/production profiles encoded and aligned with current behavior.
- `config/starter-console.profile.yaml` override/extension file supported.
- Auto-detect + explicit selection wired into CLI and TUI.
- Wizard sections consume profile policy (no hardcoded profile branching).
- Checklist/audit uses profile policy for required/optional checks.
- Manifest output captures selected profile + locked override exceptions.
- `hatch run lint` / `hatch run typecheck` (console/contracts) pass.
- Docs and trackers updated.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Profile policy contract + loader in `starter_contracts`.
- Profile registry + detection logic in `starter_console`.
- Wizard defaults, automation gates, and validators driven by policy.
- TUI profile picker and auto-detect hinting.
- Portable project config at `config/starter-console.profile.yaml`.
- New documentation + audit manifest.

### Out of Scope
- Redesigning the entire wizard UX flow.
- New hosting presets beyond current set.
- Changes to runtime env schema outside the wizard surface.
- Backward compatibility shims (pre-release repo).

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Contract drafted and encoded in starter_contracts. |
| Implementation | ✅ | Phases P1–P5 complete; TUI + docs/QA shipped. |
| Tests & QA | ✅ | Profile policy integration + manifest coverage added. |
| Docs & runbooks | ✅ | Console + setup docs updated; contract aligned. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Profile policy lives in `starter_contracts` (shared, versioned).
- Console uses a registry to load built-ins + project overrides (no duplicate logic).
- Wizard sections consume a `ProfilePolicy` to drive defaults and validations.
- Auto-detect uses a deterministic precedence chain with audit logging.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract and Loader

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Contracts | Add profile schema + loader + validation | ✅ |
| A2 | Contracts | Add default profiles YAML | ✅ |
| A3 | Tests | Unit tests for schema merge + detect | ✅ |

### Workstream B – Console Registry + CLI

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Profile registry + detection chain | ✅ |
| B2 | Console | CLI flag + config file support | ✅ |
| B3 | Console | Manifest output in `var/reports` | ✅ |

### Workstream C – Wizard Integration

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Console | Replace hardcoded profile checks with policy | ✅ |
| C2 | Console | Drive defaults/choices/required via policy | ✅ |
| C3 | Console | Audit/checklist align to policy | ✅ |

### Workstream D – TUI Exposure

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Console | Profile picker + detected hint | ✅ |
| D2 | Console | Display locked/overridden state | ✅ |

### Workstream E – Docs + QA

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | Docs | Update console README + setup docs | ✅ |
| E2 | Tests | Add wizard integration tests | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Finalize policy schema + defaults | Docs approved | ✅ |
| P1 – Contract | Loader + validation + tests | Contracts tests green | ✅ |
| P2 – Console | Registry + CLI + manifest | CLI uses registry and emits manifest | ✅ |
| P3 – Integration | Wizard + checklist | Wizard uses policy end-to-end | ✅ |
| P4 – UX | TUI + CLI polish | TUI profile selection complete | ✅ |
| P5 – QA | Docs + verification | Lint/typecheck green | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None identified.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Policy complexity grows | Med | Keep schema minimal; iterate only when needed. |
| Profile overrides create drift | Med | Add manifest output + locked override logs. |
| Duplicate logic between schema.yaml and policy | Med | Keep schema.yaml for prompt dependencies only. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_contracts && hatch run lint && hatch run typecheck`
- `cd packages/starter_console && hatch run lint && hatch run typecheck`
- Wizard smoke run with demo profile (headless + TUI).

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- New profiles are enabled by creating/overriding `config/starter-console.profile.yaml`.
- No data migration; `.env` remains canonical.
- Rollback by removing profile file and using `--profile demo`.

---

<!-- SECTION: Post-Review Findings -->
## Post-Review Findings (2026-01-05)

| ID | Severity | Finding | Recommendation |
| --- | --- | --- | --- |
| FR-1 | Medium | TUI Doctor “Auto” uses `ENVIRONMENT` only and bypasses the profile registry (config/STARTER_PROFILE/detect rules). | Use `load_profile_registry()` + `select_profile()` for TUI auto-resolution; keep manual override but validate it against the registry and surface the chosen source. |
| FR-2 | Medium | `detect.any` rules can match all envs when only `key` is provided (no equals/contains/present). | Require at least one predicate in `detect.any.env` and raise a schema error when empty. |
| FR-3 | Medium | `geoip_required_mode` accepts any string; typos silently disable enforcement. | Validate against an enum (e.g., `disabled`, `warn`, `error`) in schema parsing. |
| FR-4 | Low | `priority: 0` in detect rules is treated as `100` due to `or` fallback. | Parse with explicit `None` check so zero is preserved. |
| FR-5 | Low | Profile manifest ignores frontend locked overrides because frontend env is not passed. | Load frontend env (`apps/web-app/.env.local`) and pass to `write_profile_manifest()` in CLI + TUI flows. |
| FR-6 | Low | `allow: []` cannot explicitly disable automation; empty list currently means “allow all”. | Distinguish “unset” vs “empty”: `allow: null` → allow all, `allow: []` → allow none; update policy type, merge logic, docs, and tests. |

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-05 — Contract schema + defaults + tests landed (P1 complete).
- 2026-01-05 — Console registry + CLI selection + manifest output landed (P2 complete).
- 2026-01-05 — Wizard + checklist now consume profile policy end-to-end (P3 complete).
- 2026-01-05 — TUI profile picker + locked/override display landed (P4 complete).
- 2026-01-05 — Docs + QA updates completed for setup profiles (P5 complete).
