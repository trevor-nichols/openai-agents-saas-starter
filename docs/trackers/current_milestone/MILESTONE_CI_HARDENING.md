<!-- SECTION: Metadata -->
# Milestone: CI Hardening & Supply-Chain Guardrails

_Last updated: 2025-12-26_  
**Status:** In Progress  
**Owner:** Platform Foundations  
**Domain:** Cross-cutting  
**ID / Links:** docs/ops/runbook-release.md, docs/trackers/ISSUE_TRACKER.md

---

<!-- SECTION: Objective -->
## Objective

Harden CI beyond tests with security and supply-chain guardrails while keeping PRs fast. Fix the release workflow so it reliably publishes Python package wheels and provenance artifacts for a professional, resume-ready release pipeline.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- Release workflow builds wheels for `starter_contracts`, `starter_console`, and `starter_providers` and publishes SBOMs
- Dependency Review check runs on PRs
- CodeQL SAST runs on main and on a schedule
- Secret scanning runs on PRs and main
- Container image vulnerability scanning runs on main/tag builds
- Build provenance attestations are generated for release artifacts
- Dependabot updates are configured (actions, Python, JS)
- CI workflows validate cleanly (`python tools/ci/check_workflows.py`)
- Docs/trackers updated

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Release workflow fixes for wheel builds + SBOM outputs
- Dependency Review (PR-time)
- CodeQL SAST (main + scheduled)
- Secret scanning (PR + main)
- Container image vulnerability scanning (main/tags)
- Build provenance attestation for release artifacts
- Dependabot configuration
- Tracker updates for rollout and status checks

### Out of Scope
- Application feature changes or refactors
- Security remediation work beyond CI signals
- Runtime infrastructure changes (deployments, secrets rotation)

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ | Clear CI/workflow additions defined; PRs kept fast by moving heavy scans to main/schedule. |
| Implementation | ✅ | CI guardrails and release attestations added; awaiting rollout. |
| Tests & QA | ⏳ | CI changes pending validation via Actions runs. |
| Docs & runbooks | ✅ | Runbook updated with CI/security gates and artifact provenance. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Add security guardrail workflows under `.github/workflows/` with minimal permissions.
- Keep PR checks lightweight (Dependency Review + secrets scan).
- Schedule heavier jobs (CodeQL, image scans) on main and nightly/weekday cron.
- Use per-package SBOMs and provenance attestations for release artifacts.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Release Workflow Corrections

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | Release | Build wheels per package and publish artifacts | PF | ✅ |
| A2 | Release | Emit per-package SBOMs (pip-audit) | PF | ✅ |
| A3 | Release | Add provenance attestation for release artifacts | PF | ✅ |

### Workstream B – Supply-Chain Guardrails

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | CI | Dependency Review action on PRs | PF | ✅ |
| B2 | CI | CodeQL SAST on main + schedule | PF | ✅ |
| B3 | CI | Secrets scan on PR + main | PF | ✅ |
| B4 | CI | Image vulnerability scan on main/tags | PF | ✅ |
| B5 | CI | Dependabot updates for actions/Python/JS | PF | ✅ |

### Workstream C – Governance & Docs

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | Docs | Update runbook with new required checks | PF | ⏳ |
| C2 | Ops | Update branch protection required checks | PF | ✅ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Scope, sequencing, owner confirmed | Tracker created | ✅ |
| P1 – Implementation | Add workflows + config | New CI jobs visible in Actions | ✅ |
| P2 – Rollout | Require checks + update docs | Branch protection updated | ✅ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- GitHub Actions runners with Docker and Node/Python toolchains
- Registry credentials for image scanning on main/tags
- GitHub OIDC support for provenance attestations

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| CI duration increase | Med | Keep heavy scans on main/schedule; avoid PR builds for CodeQL/image scans. |
| False positives from scans | Med | Start with HIGH/CRITICAL only; tune configs over time. |
| Registry auth gaps | Med | Use GHCR by default; gate scans to pushed images only. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `python tools/ci/check_workflows.py`
- Verify new workflows appear in GitHub Actions and complete successfully
- Confirm SARIF/alerts show in Security tab for CodeQL + image scans (if enabled)
- Ensure release tags publish wheels + SBOMs and provenance attestations

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- Add new required status checks in branch protection once green on main.
- Run nightly/weekday scheduled jobs to keep PRs fast.
- Document expected alerts and response process in the release runbook.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-26 — Release workflow fixed to build per-package wheels and publish SBOM artifacts.
- 2025-12-26 — Added CI guardrails (Dependency Review, CodeQL, secrets scan, image scans), dependabot config, and release attestations.
- 2025-12-26 — Runbook updated with CI/security expectations and release artifact provenance notes.
- 2025-12-26 — Branch protection now requires CI + security workflows on `main`.
- 2025-12-26 — Required check names aligned with build matrix jobs; Providers CI now runs on all PRs.
