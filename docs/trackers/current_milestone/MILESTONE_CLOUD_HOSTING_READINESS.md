<!-- SECTION: Metadata -->
# Milestone: Cloud Hosting Readiness (AWS + Azure)

_Last updated: 2025-12-22_  
**Status:** Planned  
**Owner:** @codex  
**Domain:** Cross-cutting  
**ID / Links:** Docs: `README.md`, `docs/ops/`, `docs/security/`, `docs/trackers/CLI_ENV_INVENTORY.md`

---

<!-- SECTION: Objective -->
## Objective

Make the starter production-ready for AWS and Azure hosting with a clean, cloud-agnostic architecture: containerized services, first‑class cloud storage providers, reference infrastructure blueprints, and documented operational guidance so both technical and non‑technical operators can deploy with confidence.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- API + web apps ship container images with reproducible builds, non‑root runtime, and documented env contracts.
- AWS + Azure reference architectures exist (Terraform/Bicep or equivalent) with clear outputs and minimal coupling.
- Object storage supports S3 and Azure Blob (in addition to MinIO/GCS), with provider validation + CLI onboarding.
- Hosting docs include step‑by‑step setup, topology guidance (billing worker), and rollback notes.
- CI/build scripts can produce/publish images; migrations and health checks documented for deploys.
- `hatch run lint` / `hatch run typecheck` / `pnpm lint` / `pnpm type-check` pass; new tests added where appropriate.
- Docs/trackers updated; risks recorded and mitigations documented.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Containerization for `api-service` and `web-app` (Dockerfiles, build docs, entrypoints).
- Cloud storage providers: AWS S3 and Azure Blob.
- Cloud secret managers: already supported (AWS SM, Azure KV); ensure docs + CLI flows align with hosting guidance.
- Reference infra blueprints for AWS + Azure (managed Postgres + Redis + storage + secrets + compute).
- Deployment/runbook docs, including billing worker topology, migrations, and observability.
- CI/CD hooks for building images (GitHub Actions or scripts in `ops/`).

### Out of Scope
- Multi‑region active/active deployment.
- Full SSO/IdP integrations.
- Provider‑specific cost optimization or autoscaling tuning beyond sensible defaults.
- Full Kubernetes Helm charts unless required by the chosen cloud blueprint.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⚠️ | Cloud‑agnostic but lacks deployment blueprints + container build artifacts. |
| Implementation | ⚠️ | No Dockerfiles; storage lacks S3/Azure Blob providers. |
| Tests & QA | ⚠️ | Unit coverage good; no provider tests for new storage backends yet. |
| Docs & runbooks | ⚠️ | Local/CLI flows documented; no AWS/Azure hosting playbooks. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- Preserve clean boundaries: cloud integrations live in `app/infrastructure/` and `starter_contracts` only; CLI stays provider‑agnostic with declarative onboarding.
- Keep cloud deployment artifacts isolated under `ops/` (no app imports), with minimal coupling to runtime code.
- Storage providers follow existing `StorageProviderProtocol`; config lives in settings + `starter_contracts.storage`.
- Deployment topologies explicitly cover billing worker placement (inline vs dedicated).

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Containerization & Build Artifacts

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| A1 | API | Add production Dockerfile + entrypoint for `api-service` with non‑root user and healthcheck. | @codex | ⏳ |
| A2 | Web | Add production Dockerfile for `web-app` (Next.js 16, Node 22) with runtime env contract. | @codex | ⏳ |
| A3 | Ops | Add build docs + optional compose app stack for local container runs. | @codex | ⏳ |

### Workstream B – Cloud Storage Providers

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| B1 | Backend | Implement AWS S3 provider (native creds chain) and Azure Blob provider. | @codex | ⏳ |
| B2 | Contracts | Extend `starter_contracts.storage` literals/configs for S3 + Azure Blob. | @codex | ⏳ |
| B3 | CLI | Add onboarding + validation for new providers; update inventory + schema docs. | @codex | ⏳ |
| B4 | Tests | Add provider unit tests and registry validation. | @codex | ⏳ |

### Workstream C – AWS/Azure Reference Architectures

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| C1 | AWS | Infra blueprint for ECS/Fargate (or App Runner), RDS, ElastiCache, S3, Secrets Manager. | @codex | ⏳ |
| C2 | Azure | Infra blueprint for Container Apps (or AKS), Azure DB for Postgres, Azure Cache for Redis, Blob, Key Vault. | @codex | ⏳ |
| C3 | Docs | Deployment guides + environment variable mapping tables. | @codex | ⏳ |

### Workstream D – CI/CD & Ops Runbooks

| ID | Area | Description | Owner | Status |
|----|------|-------------|-------|--------|
| D1 | CI | Add image build/publish workflow (GitHub Actions) and artifact versioning. | @codex | ⏳ |
| D2 | Ops | Add migration/runbook steps + billing worker topology guidance per cloud. | @codex | ⏳ |

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

| Phase | Scope | Exit Criteria | Status | Target |
| ----- | ----- | ------------- | ------ | ------ |
| P0 – Alignment | Confirm target platforms + blueprint choices | Design notes + plan approved | ✅ | 2025-12-22 |
| P1 – Containers | Dockerfiles + build docs | Images build locally; health checks pass | ⏳ | 2025-12-29 |
| P2 – Storage | S3 + Azure Blob providers + CLI onboarding | Tests pass; provider validation works | ⏳ | 2026-01-12 |
| P3 – Infra | AWS + Azure blueprints + docs | IaC validates; docs complete | ⏳ | 2026-01-26 |
| P4 – CI/QA | CI build pipeline + runbooks | Pipelines green; runbooks updated | ⏳ | 2026-02-02 |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Cloud accounts (AWS + Azure) for validation/testing.
- Terraform/Bicep toolchains (or agreed alternatives).
- Docker build tooling for CI/CD.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| No container build artifacts currently | High | Add Dockerfiles early (Phase P1). |
| Storage provider gaps for S3/Azure Blob | High | Implement providers + tests before infra docs. |
| Secrets in local templates | High | Audit and scrub sensitive defaults; update `.env.local.example`. |
| Cloud blueprint complexity | Med | Prefer managed services + minimal modules; keep infra separate. |
| Billing worker topology confusion | Med | Explicit docs + sample configs for single vs multi‑replica. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Backend: `cd apps/api-service && hatch run lint && hatch run typecheck`
- Frontend: `cd apps/web-app && pnpm lint && pnpm type-check`
- CLI: `cd packages/starter_cli && hatch run lint && hatch run typecheck`
- Targeted tests for new storage providers + CLI onboarding.
- Smoke run: build containers, run migrations, hit `/api/health` and `/api/health/ready`.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- New storage providers toggled via `STORAGE_PROVIDER` with explicit env configs.
- Cloud blueprints must expose `APP_PUBLIC_URL`, `API_BASE_URL`, `DATABASE_URL`, Redis URLs, and secrets provider envs.
- Billing worker guidance must be followed for multi‑replica API deployments.

---

<!-- SECTION: Changelog -->
## Changelog

- 2025-12-22 — Created milestone and initial plan for cloud hosting readiness.
