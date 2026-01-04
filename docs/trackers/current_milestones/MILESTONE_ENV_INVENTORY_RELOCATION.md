<!-- SECTION: Metadata -->
# Milestone: Console Env Inventory Relocation

_Last updated: 2026-01-04_  
**Status:** In Progress  
**Owner:** @codex  
**Domain:** Console | Cross-cutting  
**ID / Links:** Docs: `docs/contracts/settings.schema.json`, `docs/contracts/settings.md`

---

<!-- SECTION: Objective -->
## Objective

Relocate the generated console environment inventory into the contracts area so the
canonical env contract, its human summary, and the derived inventory live together
under `docs/contracts/` with clear tooling defaults and minimal drift risk.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Inventory file lives at `docs/contracts/inventories/console-env-inventory.md`.
- Console/CI tooling defaults reference the new location.
- Operator docs link to the new location.
- Snapshot/docs updated where relevant.
- `starter-console config write-inventory` emits to the new path by default.
- Tests/linters remain green (or explicitly noted if not run).

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Move inventory doc to contracts inventory directory.
- Update console tooling, CLI help text, and CI verifier to new path.
- Update operator docs referencing the inventory.

### Out of Scope
- Changes to settings schema generation or runtime settings models.
- Reworking the inventory format beyond the location change.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Aligns derived inventory with canonical contracts. |
| Implementation | ⏳ | Move + references pending. |
| Tests & QA | ⏳ | Validation after edits. |
| Docs & runbooks | ⏳ | Hosting docs need path update. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Canonical env contract remains `docs/contracts/settings.schema.json`.
- Human-readable contract remains `docs/contracts/settings.md`.
- Inventory stays Markdown (operator-friendly) but is generated from schema to avoid drift.
- Tooling defaults updated to point at the contracts inventory location.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Docs & Contracts

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Docs | Move inventory doc into `docs/contracts/inventories/`. | ⏳ |
| A2 | Docs | Update hosting docs + snapshot references. | ⏳ |

### Workstream B – Tooling & Console

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Console | Update CLI defaults + UI pane path. | ⏳ |
| B2 | Tools | Update inventory verifier path + messaging. | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- None.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Stale references to the old path | Med | Repo-wide search and updates. |
| Inventory drift after move | Low | Keep verifier default aligned to new path. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `python tools/cli/verify_env_inventory.py`
- (Optional) `starter-console config write-inventory` and confirm output path.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- No runtime behavior change; documentation/tooling path update only.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-04 — Tracker created; relocation in progress.
