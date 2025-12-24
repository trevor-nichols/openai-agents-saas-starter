<!-- SECTION: Metadata -->
# Milestone: CLI ↔ TUI Parity & IA Redesign

_Last updated: 2025-12-24_  
**Status:** Planned  
**Owner:** Platform Foundations  
**Domain:** CLI  
**ID / Links:** [Parity checklist](docs/trackers/checklist/CLI_TUI_PARITY.md), [CLI snapshot](packages/starter_cli/SNAPSHOT.md)

---

<!-- SECTION: Objective -->
## Objective

Deliver a professional, fully featured Textual TUI that reaches functional parity with the Starter CLI, using a clean navigation structure, consistent interaction patterns, and a global context panel for env controls. Outcome: operators can complete all CLI workflows from the TUI with the same fidelity and auditability.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- All CLI commands/subcommands have a TUI surface or are explicitly documented as out-of-scope
- TUI navigation reorganized into collapsible categories (Overview / Onboarding / Operations / Security & Auth / Billing & Usage / Release & Admin / Advanced)
- Global TUI “Context” panel exposes `--env-file`, `--skip-env`, `--quiet-env` equivalents
- Existing panes updated to match CLI knobs and statuses (wizard, setup hub, logs, infra, providers, stripe)
- New panes added for missing CLI workflows (doctor, start/stop, release, config, api export, auth, usage sync/export, stripe dispatches, status ops, util)
- Shared UI patterns established (action form + output/log + status table) without duplicating domain logic
- Tests and checks pass (CLI + repo standards)
- Parity tracker updated with final status

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- TUI information architecture redesign with collapsible categories
- Global context panel for env controls and reloading
- Shared action/prompt execution patterns for workflows
- Parity expansion for all CLI commands/subcommands
- Updates to TUI summaries/status tables to reflect new capabilities
- Documentation updates (parity tracker + milestone)

### Out of Scope
- Changes to backend business logic or API contracts
- New provider integrations or billing features
- Non-Textual UIs (web/desktop)

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⚠️ | Direction agreed; detailed implementation plan pending final review |
| Implementation | ⏳ | Not started |
| Tests & QA | ⏳ | Not started |
| Docs & runbooks | ⚠️ | Parity checklist exists; milestone draft in progress |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

Key decisions:
- Navigation becomes category-based with collapsible groups to reduce cognitive load.
- Global “Context” panel holds env controls (equivalent to `--env-file`, `--skip-env`, `--quiet-env`).
- TUI must remain a thin presentation layer: all logic stays in existing workflows/services.
- Standardize panes on a shared “Action Form → Run → Output/Logs → Status Table” pattern.
- Prefer reusing `HubService` snapshots and existing workflow runners; avoid duplicating domain logic.

New/updated modules (planned):
- `starter_cli/ui/layout` (collapsible nav + global context panel)
- `starter_cli/ui/panes/*` expansions and new panes for missing CLI workflows
- Shared UI helpers: workflow runner/presenter adapters, reusable form components

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Information Architecture & Navigation

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | UI | Define collapsible category model + update `sections.py` | PF | ⏳ |
| A2 | UI | Update `StarterTUI` nav + command palette to support groups | PF | ⏳ |
| A3 | UI | Add “Advanced” grouping for power-user features | PF | ⏳ |

### Workstream B – Global Context & Execution Framework

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | UI | Add global Context panel (env files, skip/quiet flags, reload) | PF | ⏳ |
| B2 | UI | Create shared action form + output/log panel pattern | PF | ⏳ |
| B3 | UI | Standard workflow runner helper (reuse prompts + logs) | PF | ⏳ |

### Workstream C – Enhance Existing Panes

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Wizard | Add missing CLI flags (schema, report-only, export paths, automation overrides) | PF | ⏳ |
| C2 | Setup Hub | Execute actions (not just print commands) | PF | ⏳ |
| C3 | Logs | Add service selection, errors toggle, follow/lines, archive | PF | ⏳ |
| C4 | Infra | Add compose/vault logs/ps/verify + JSON deps export | PF | ⏳ |
| C5 | Providers | Add strict toggle and clear status messaging | PF | ⏳ |

### Workstream D – New Operational Panes

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Doctor | Run doctor + export JSON/Markdown | PF | ⏳ |
| D2 | Start/Stop | Full start/stop controls with detached/log/pid options | PF | ⏳ |
| D3 | Release | Release DB workflow + summary output | PF | ⏳ |
| D4 | Config | Schema dump + inventory export | PF | ⏳ |
| D5 | API | OpenAPI export flow | PF | ⏳ |

### Workstream E – Security & Auth

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| E1 | Auth | Issue service account tokens (form + output format) | PF | ⏳ |
| E2 | Auth | Key rotation (optional kid) | PF | ⏳ |
| E3 | Auth | JWKS print | PF | ⏳ |

### Workstream F – Billing & Usage

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| F1 | Stripe | Add dispatch list/replay/validate fixtures | PF | ⏳ |
| F2 | Usage | Export report + sync entitlements (all flags) | PF | ⏳ |

### Workstream G – Status & Advanced Utilities

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| G1 | Status | Subscriptions list/revoke, incident resend | PF | ⏳ |
| G2 | Util | Run-with-env command builder | PF | ⏳ |

### Workstream H – QA & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| H1 | Docs | Update parity checklist + milestone tracker | PF | ⏳ |
| H2 | Tests | Add/expand CLI/TUI tests where needed | PF | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | IA + parity mapping approved | Design locked, tracker accepted | ✅ | 2025-12-24 |
| P1 – Framework | Navigation + Context panel + shared runner | New UI framework merged | ⏳ | 2025-12-31 |
| P2 – Core Parity | Enhance existing panes + add core new panes | 70% parity checklist closed | ⏳ | 2026-01-10 |
| P3 – Full Parity | Advanced/utility panes + polish | 100% parity checklist closed | ⏳ | 2026-01-20 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Textual widgets supporting grouped/collapsible nav
- Existing workflow/service APIs (no new domain logic added)
- Repo testing standards (CLI tests + lint/typecheck)

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope creep from parity expansion | High | Phase delivery, lock MVP parity per phase |
| UI complexity & inconsistent patterns | Med | Enforce shared action/runner patterns and design tokens |
| Duplicated logic between CLI/TUI | Med | Route all actions through existing workflows/services |
| Operator confusion with new nav | Low | Clear categories + consistent labels; update docs |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_cli && hatch run lint && hatch run typecheck && hatch run test`
- Validate TUI flows manually for each new pane (Wizard/Stripe/Start/Stop/Auth/Status)
- Run parity checklist review and mark each item as complete

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migration steps; TUI changes are additive
- Global Context panel reuses CLI env behavior; document in release notes

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-24 — Initial milestone drafted from parity review and IA decisions.
