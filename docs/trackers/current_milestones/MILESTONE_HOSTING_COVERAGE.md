<!-- SECTION: Metadata -->
# Milestone: Hosting Coverage Expansion

_Last updated: 2026-01-02_  
**Status:** Planned  
**Owner:** Platform Foundations  
**Domain:** Infra  
**ID / Links:** [TBD], [docs/ops/hosting-overview.md], [docs/ops/hosting-aws.md], [docs/ops/hosting-azure.md], [docs/ops/container-deployments.md], [docs/ops/setup-wizard-presets.md], [docs/security/secrets-providers.md], [ops/infra/aws], [ops/infra/azure], [.github/workflows/build-images.yml]

---

<!-- SECTION: Objective -->
## Objective

Provide production-grade, modular deployment blueprints for the most common hosting environments (AWS, Azure, GCP, Kubernetes, and single-server/VPS) while keeping a consistent env contract and minimal coupling to application code, so any developer can clone and deploy with clear, defensible architecture.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

- GCP reference blueprint exists and aligns with the AWS/Azure contract (compute, DB, cache, storage, secrets).
- Kubernetes deployment option exists (Helm chart or manifests) with the same env contract and clear separation of API, web, and worker roles.
- Production-grade single-server deployment exists (Compose + reverse proxy with TLS) with documented secrets and backup guidance.
- Docs updated to include GCP/K8s/VPS runbooks and a consolidated “deployment options” page.
- CI validates all new infra directories (terraform fmt/validate, helm lint/template, compose config).
- Trackers updated and the milestone archived on completion.

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- Add `ops/infra/gcp` Terraform blueprint (Cloud Run or equivalent; Cloud SQL, Memorystore, GCS, Secret Manager).
- Add Kubernetes deployment option under `ops/k8s` or `ops/charts` (Helm preferred).
- Add production single-server deployment under `ops/compose` (reverse proxy + TLS + restart policies + backups).
- Normalize provider variable names and env mappings across AWS/Azure/GCP/K8s/Compose.
- Update docs and runbooks to reflect new options.
- Extend CI to validate new infra artifacts.

### Out of Scope
- Automatic `terraform apply` in CI (should remain opt-in and manual).
- Advanced platform-specific features (service mesh, zero-trust networking, custom ingress controllers).
- Multi-region or multi-tenant infrastructure topologies.
- Managed SSO provisioning beyond what the console already supports.

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ⚠️ | AWS/Azure reference blueprints exist; GCP/K8s/VPS designs not formalized. |
| Implementation | ⚠️ | `ops/infra/aws` + `ops/infra/azure` only; local Compose exists; no GCP/K8s/prod Compose. |
| Tests & QA | ⚠️ | CI validates terraform fmt/validate for AWS/Azure only. |
| Docs & runbooks | ⚠️ | AWS/Azure hosting guides exist; no GCP/K8s/VPS runbooks. |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

- **Reference shape today:** containerized API + web with managed Postgres, Redis, object storage, and secrets provider. AWS uses ECS/Fargate + RDS + ElastiCache + S3 + Secrets Manager; Azure uses Container Apps + Postgres Flexible Server + Azure Cache + Blob + Key Vault.
- **Secrets posture:** hosted environments expect secret-manager-backed key storage (`AUTH_KEY_STORAGE_BACKEND=secret-manager`), with the provider chosen via `SECRETS_PROVIDER` and `AUTH_KEY_STORAGE_PROVIDER`.
- **Console presets:** setup wizard supports `aws`, `azure`, `gcp`, and `other` presets but only AWS/Azure have Terraform blueprints today.
- **Design requirement:** keep infra definitions modular, DRY, and aligned to a shared env contract so provider additions do not leak into app logic.

### Coverage Gap Matrix

| Deployment target | Current state | Infra present | Gap |
| --- | --- | --- | --- |
| AWS (ECS/Fargate) | Supported | `ops/infra/aws` | None |
| Azure (Container Apps) | Supported | `ops/infra/azure` | None |
| GCP (Cloud Run/GKE) | Preset only | None | Missing Terraform blueprint |
| Kubernetes (portable) | Mentioned in docs only | None | Missing Helm/manifests |
| Single-server/VPS | Dev Compose only | `ops/compose/*` | Missing production Compose + reverse proxy |
| Infra CI validation | AWS/Azure only | `.github/workflows/build-images.yml` | Missing validation for new infra artifacts |

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

### Workstream A – Contract Alignment + Docs

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | Design | Define a provider-agnostic env/infra contract (vars, secrets, outputs) aligned to AWS/Azure docs. | ⏳ |
| A2 | Docs | Add a “deployment options” overview and update `docs/ops/hosting-overview.md`. | ⏳ |
| A3 | Docs | Draft GCP/K8s/VPS runbooks with prerequisites and step-by-step deploy/rollback. | ⏳ |

### Workstream B – GCP Terraform Blueprint

| ID | Area | Description | Status |
|----|------|-------------|-------|
| B1 | Infra | Create `ops/infra/gcp` with modules for network, compute, DB, cache, storage, secrets. | ⏳ |
| B2 | Infra | Choose default compute target (Cloud Run preferred; GKE optional in docs). | ⏳ |
| B3 | Infra | Add outputs mirroring AWS/Azure (api_url, web_url, storage identifiers, secret references). | ⏳ |
| B4 | Docs | Write `docs/ops/hosting-gcp.md` with env mapping table. | ⏳ |

### Workstream C – Kubernetes Deployment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| C1 | Infra | Add Helm chart with API, web, worker deployments + HPA + probes. | ⏳ |
| C2 | Infra | Provide values for secrets manager integration (External Secrets or CSI). | ⏳ |
| C3 | Docs | Write `docs/ops/hosting-kubernetes.md` + minimal quickstart. | ⏳ |

### Workstream D – VPS / Single-Server Deployment

| ID | Area | Description | Status |
|----|------|-------------|-------|
| D1 | Infra | Add `ops/compose/docker-compose.prod.yml` with reverse proxy (Caddy preferred), TLS, restart policies, and volumes. | ⏳ |
| D2 | Infra | Add sample `Caddyfile`/proxy config + backup guidance. | ⏳ |
| D3 | Docs | Write `docs/ops/hosting-vps.md` with operational steps. | ⏳ |

### Workstream E – CI + Validation

| ID | Area | Description | Status |
|----|------|-------------|-------|
| E1 | CI | Extend CI to run terraform fmt/validate for GCP. | ⏳ |
| E2 | CI | Add helm lint/template checks. | ⏳ |
| E3 | CI | Add compose config validation for prod stack. | ⏳ |

---

<!-- SECTION: Phases -->
## Phases

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | Finalize provider-agnostic contract and target compute choice for GCP | Contract doc + decisions logged | ⏳ |
| P1 – GCP Blueprint | Implement Terraform and hosting guide | `ops/infra/gcp` + `docs/ops/hosting-gcp.md` complete | ⏳ |
| P2 – Kubernetes | Implement Helm chart + runbook | Chart passes lint/template; doc published | ⏳ |
| P3 – VPS | Add production Compose + proxy + runbook | Compose stack validated; docs published | ⏳ |
| P4 – CI/Docs | CI validation + consolidated docs | CI checks green; overview updated | ⏳ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Final decision on GCP compute target (Cloud Run vs GKE default).
- Registry strategy for GCP (Artifact Registry vs GHCR with credentials).
- Secrets provider choice for hosted GCP (Secret Manager vs Infisical/Vault).
- Agreement on Kubernetes secret integration strategy (External Secrets Operator vs CSI driver).

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope creep across providers | High | Lock the env contract first; limit to minimal production blueprint. |
| Inconsistent env mapping | Med | Maintain a single mapping table and shared outputs across providers. |
| Kubernetes complexity | Med | Keep chart minimal; document optional add-ons separately. |
| VPS security gaps | Med | Default to TLS via proxy, strict restart policies, and explicit secrets handling. |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- `terraform fmt -check -recursive ops/infra`  
- `terraform -chdir=ops/infra/<provider> init -backend=false` + `terraform validate`
- `helm lint` + `helm template` (or `kustomize build`) for Kubernetes artifacts
- `docker compose -f ops/compose/docker-compose.prod.yml config`
- Manual smoke: deploy API + web, hit `/health/ready` and `/api/health/ready`

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- All new infra is opt-in; no breaking changes to existing AWS/Azure users.
- Runbooks must include migration + rollback guidance.
- CI should validate but not auto-apply Terraform.

---

<!-- SECTION: Changelog -->
## Changelog

- 2026-01-02 — Initial milestone drafted from current repo state and coverage gaps.
