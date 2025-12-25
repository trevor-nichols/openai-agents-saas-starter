<!-- SECTION: Metadata -->
# Milestone: Setup Wizard UX + Presets Redesign

_Last updated: 2025-12-24_  
**Status:** In Progress  
**Owner:** @codex  
**Domain:** CLI  
**ID / Links:** [docs/trackers/templates/MILESTONE_TEMPLATE.md], [docs/trackers/current_milestones/SETUP_WIZARD_REDESIGN_SPEC.md], [docs/ops/setup-wizard-presets.md], [packages/starter_console/README.md], [packages/starter_console/src/starter_console/workflows/setup/_wizard/sections]

---

<!-- SECTION: Objective -->
## Objective

Deliver a deterministic, audit‑friendly, and intuitive setup wizard with hosting presets, progressive disclosure, and a clean linear flow. The wizard should feel product‑grade for first‑time users and remain safe, resumable, and automation‑ready for CI/CD.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Wizard order + prompts are re‑specified in the schema and enforced in TUI/headless runs.
- Hosting presets (Local Docker / Cloud Managed / Enterprise Custom) drive defaults and prompt gating.
- Setup Menu shows completion, staleness, and diffs based on redacted snapshots.
- New/updated CLI tests cover schema gating, presets, and resume flows.
- Docs updated (`packages/starter_console/README.md`, `docs/trackers/CONSOLE_ENV_INVENTORY.md`).
- `hatch run lint` + `hatch run typecheck` pass for CLI.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Redesign wizard order + prompt list (schema‑first).
- Hosting presets + profile selection logic.
- TUI UX redesign to reflect new flow and progressive disclosure.
- Redacted snapshot artifact + diff summary on re‑runs.
- Test updates for schema gating, preset defaults, and resume behavior.

### Out of Scope
- Backend feature changes unrelated to wizard prompts.
- New providers beyond current set (Vault/Infisical/AWS/Azure; S3/GCS/Azure Blob/MinIO).
- Frontend feature work outside of generated env changes.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Spec + schema map now cover presets, advanced toggle, and diff artifacts. |
| Implementation | ✅ | Presets, snapshot/diff artifacts, and schema gating wired into wizard + setup menu. |
| Tests & QA | ⚠️ | New tests added; run lint/typecheck + CLI unit suite to confirm. |
| Docs & runbooks | ✅ | README + inventory updated; preset runbook added. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Schema‑first: `packages/starter_console/src/starter_console/workflows/setup/schema.yaml` is the single source of truth.
- Preset engine: new hosting presets map to defaults + skip rules (Local Docker / Cloud Managed / Enterprise Custom).
- Resume + audit: keep `var/reports/wizard-state.json`, add redacted `setup-snapshot.json` + diff summary.
- TUI: reorganize panes to reflect linear steps and show preset context + progress.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Product/UX Spec + Schema

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | CLI | Draft final wizard order + prompt list with required/optional flags | @codex | ✅ |
| A2 | CLI | Define hosting presets and mapping rules | @codex | ✅ |
| A3 | CLI | Update schema.yaml to encode presets + skip rules | @codex | ✅ |

### Workstream B – CLI Wizard Logic

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | CLI | Implement preset resolver + defaults injector | @codex | ✅ |
| B2 | CLI | Add redacted snapshot + diff summary artifacts | @codex | ✅ |
| B3 | CLI | Update setup menu to surface snapshot/diff | @codex | ✅ |

### Workstream C – TUI Redesign

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | CLI | Refresh wizard UI order + section labels | @codex | ✅ |
| C2 | CLI | Add preset banner + step descriptions | @codex | ⏳ |
| C3 | CLI | Improve progress + next‑step affordances | @codex | ⏳ |

### Workstream D – Tests + Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | Tests | Add unit tests for preset gating & diff output | @codex | ✅ |
| D2 | Docs | Update CLI README + env inventory | @codex | ✅ |
| D3 | Docs | Add short runbook for preset usage | @codex | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Final spec + prompt list + presets | Spec approved + schema plan | ✅ | 2025-12-28 |
| P1 – Schema/Preset | Preset rules + schema updates | New schema validated by tests | ✅ | 2026-01-05 |
| P2 – CLI Logic | Snapshot/diff + menu updates | New artifacts working end‑to‑end | ✅ | 2026-01-12 |
| P3 – TUI | UI redesign + new flow | Usable TUI with preset context | ⏳ | 2026-01-19 |
| P4 – QA/Docs | Tests + docs + polish | Lint/typecheck green; docs shipped | ⏳ | 2026-01-23 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None (contained to CLI + docs). Optional: review from Platform Foundations.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Preset rules over‑simplify real deployments | Med | Allow “Enterprise Custom” preset + advanced toggle. |
| Schema drift vs docs | Med | Auto‑generate inventory + enforce with CLI tests. |
| TUI scope creep | Low | Keep visual changes minimal; focus on flow + context. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `cd packages/starter_console && hatch run lint`
- `cd packages/starter_console && hatch run typecheck`
- `cd packages/starter_console && hatch run test tests/unit/workflows/setup tests/unit/ui`
- Manual smoke: `starter-console setup wizard --profile demo` and `setup menu`.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No migrations required.
- CLI artifacts written under `var/reports/`.
- Presets only change default answers and skip logic; all env outputs remain compatible.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-24 — Draft milestone created (spec + plan pending).
- 2025-12-24 — Presets, snapshot/diff artifacts, schema gating, and docs wired; tests added.
